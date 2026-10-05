#!/usr/bin/env python3
"""Run a guarded, regtest-only payment scenario and produce a ztestkit report."""

import argparse
import json
import os
import re
import sys
import time
import urllib.error
import urllib.request
from decimal import Decimal
from pathlib import Path
from urllib.parse import urlsplit

import ztestkit


class ScenarioError(RuntimeError):
    pass


REGTEST_GENESIS = "029f11d80ef9765602235e1bc9727e3eb6ba20839319f761fee920d63401e327"


def require_loopback(url):
    try:
        target = urlsplit(url)
        port = target.port
    except ValueError as exc:
        raise ScenarioError("RPC must use a plain loopback HTTP URL with a port") from exc
    if (target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost"}
            or target.username or target.password or target.path not in {"", "/"}
            or target.query or target.fragment or port is None):
        raise ScenarioError("RPC must use a plain loopback HTTP URL with a port")
    return url


def assert_regtest(node):
    if node.call("getblockhash", [0]) != REGTEST_GENESIS:
        raise ScenarioError("Node RPC is not the expected Zcash regtest chain")


def read_checkpoint(path):
    if not Path(path).exists():
        return None
    try:
        value = json.loads(Path(path).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ScenarioError("Checkpoint is unreadable") from exc
    if not isinstance(value, dict):
        raise ScenarioError("Checkpoint must contain a JSON object")
    return value


def write_checkpoint(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(path.name + ".tmp")
    temporary.write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def operation_id(value):
    if isinstance(value, str) and value.startswith("opid-"):
        return value
    if isinstance(value, dict) and isinstance(value.get("opid"), str):
        return value["opid"]
    raise ScenarioError("Wallet did not return an operation ID")


def operation_txid(entry):
    result = entry.get("result")
    if isinstance(result, str):
        txid = result
    elif isinstance(result, dict):
        txid = result.get("txid")
    else:
        txid = None
    if not isinstance(txid, str) or not re.fullmatch(r"[0-9a-fA-F]{64}", txid):
        raise ScenarioError("Successful operation did not return a transaction ID")
    return txid.lower()


def submit_or_resume(wallet, checkpoint_path, request_sha256, source_address,
                     recipient_address, amount):
    """Advance at most one submission state transition; never blindly resend."""
    checkpoint = read_checkpoint(checkpoint_path)
    if checkpoint:
        if checkpoint.get("request_sha256") != request_sha256:
            raise ScenarioError("Checkpoint belongs to a different payment request")
        state = checkpoint.get("state")
        if state in {"submitted", "mined", "reported"} and checkpoint.get("txid"):
            return checkpoint
        if state in {"submission_started", "submission_uncertain"}:
            raise ScenarioError("Previous submission is uncertain; inspect wallet state before retrying")
        if state == "failed":
            raise ScenarioError("Previous wallet operation failed; use a new checkpoint after review")
        if state != "operation_pending" or not checkpoint.get("operation_id"):
            raise ScenarioError("Checkpoint state is invalid")
        opid = checkpoint["operation_id"]
        finished = wallet.call("z_getoperationstatus", [[opid]]) or []
        if not finished:
            return checkpoint
        entry = finished[0]
        if entry.get("status") == "success":
            value = {"request_sha256": request_sha256, "state": "submitted",
                     "operation_id": opid, "txid": operation_txid(entry)}
            write_checkpoint(checkpoint_path, value)
            return value
        if entry.get("status") in {"failed", "cancelled"}:
            value = {"request_sha256": request_sha256, "state": "failed",
                     "operation_id": opid,
                     "error_code": (entry.get("error") or {}).get("code")}
            write_checkpoint(checkpoint_path, value)
            raise ScenarioError("Wallet operation did not succeed")
        return checkpoint

    write_checkpoint(checkpoint_path, {"request_sha256": request_sha256,
                                       "state": "submission_started"})
    try:
        response = wallet.call("z_sendmany", [
            source_address,
            [{"address": recipient_address, "amount": float(Decimal(amount))}],
            1,
            None,
            "FullPrivacy",
        ])
        opid = operation_id(response)
    except Exception as exc:
        write_checkpoint(checkpoint_path, {"request_sha256": request_sha256,
                                           "state": "submission_uncertain"})
        raise ScenarioError("Submission result is uncertain; inspect wallet state before retrying") from exc
    value = {"request_sha256": request_sha256, "state": "operation_pending",
             "operation_id": opid}
    write_checkpoint(checkpoint_path, value)
    return value


def recover_checkpoint(recipient_wallet, checkpoint_path, request_sha256, txid,
                       expected_zat, account_uuid):
    """Bind an ambiguous operation to a tx only after recipient-side matching."""
    checkpoint = read_checkpoint(checkpoint_path)
    if not checkpoint or checkpoint.get("request_sha256") != request_sha256:
        raise ScenarioError("Recovery checkpoint is missing or belongs to another request")
    if checkpoint.get("state") not in {"failed", "submission_started",
                                        "submission_uncertain", "operation_pending"}:
        raise ScenarioError("Checkpoint is not in a recoverable submission state")
    observation = ztestkit.observe(recipient_wallet, txid, expected_zat, account_uuid)
    if observation.get("evidence", {}).get("matching_shielded_output_count", 0) < 1:
        raise ScenarioError("Recipient wallet did not match the recovery transaction")
    value = {"request_sha256": request_sha256, "state": "submitted",
             "txid": txid.lower()}
    if checkpoint.get("operation_id"):
        value["operation_id"] = checkpoint["operation_id"]
    write_checkpoint(checkpoint_path, value)
    return value


class NodeRpc:
    def __init__(self, url):
        self.url = require_loopback(url)

    def call(self, method, params=None):
        body = json.dumps({"jsonrpc": "2.0", "id": "ztestkit-scenario",
                           "method": method, "params": params or []}).encode()
        request = urllib.request.Request(self.url, data=body,
                                         headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise ScenarioError("Node RPC is unavailable") from exc
        if payload.get("error"):
            raise ScenarioError(f"Node RPC {method} failed")
        return payload.get("result")


def append_scenario_state(report_path, checkpoint):
    path = Path(report_path)
    report = json.loads(path.read_text(encoding="utf-8"))
    report["scenario"] = {
        "state": checkpoint["state"],
        "operation_id_sha256": ztestkit.digest(checkpoint["operation_id"])
        if checkpoint.get("operation_id") else None,
        "checkpoint_request_sha256": checkpoint["request_sha256"],
    }
    path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")


def main(argv=None):
    parser = argparse.ArgumentParser(description="Guarded Zcash regtest privacy scenario")
    parser.add_argument("--uri-file", type=Path, required=True)
    parser.add_argument("--source-address-file", type=Path, required=True)
    parser.add_argument("--sender-rpc-url", required=True)
    parser.add_argument("--sender-rpc-cookie", type=Path, required=True)
    parser.add_argument("--recipient-rpc-url", required=True)
    parser.add_argument("--recipient-rpc-cookie", type=Path, required=True)
    parser.add_argument("--recipient-account-file", type=Path, required=True)
    parser.add_argument("--node-rpc-url", default="http://127.0.0.1:29232")
    parser.add_argument("--checkpoint", type=Path, required=True)
    parser.add_argument("--canary-file", type=Path, required=True)
    parser.add_argument("--log", type=Path, action="append", required=True)
    parser.add_argument("--report", type=Path, required=True)
    parser.add_argument("--recover-txid",
                        help="Bind an ambiguous checkpoint after recipient-side tx matching")
    parser.add_argument("--wait-seconds", type=int, default=180)
    parser.add_argument("--poll-seconds", type=float, default=2)
    args = parser.parse_args(argv)

    try:
        uri = args.uri_file.read_text(encoding="utf-8").strip()
        payments = ztestkit.parse_uri(uri)
        if len(payments) != 1 or payments[0]["amount_zat"] is None:
            raise ScenarioError("Scenario requires exactly one payment with an amount")
        payment = payments[0]
        amount = Decimal(payment["amount_zat"]) / Decimal(100_000_000)
        source_address = args.source_address_file.read_text(encoding="utf-8").strip()
        account_uuid = args.recipient_account_file.read_text(encoding="utf-8").strip()
        if not source_address or not account_uuid:
            raise ScenarioError("Private source address and recipient account files must not be empty")

        sender_url = require_loopback(args.sender_rpc_url)
        recipient_url = require_loopback(args.recipient_rpc_url)
        node = NodeRpc(args.node_rpc_url)
        assert_regtest(node)
        sender = ztestkit.WalletRpc(sender_url, args.sender_rpc_cookie)
        recipient = ztestkit.WalletRpc(recipient_url, args.recipient_rpc_cookie)
        preflight = ztestkit.preflight(payments, recipient)
        if not any(check["check"] == "recipient_preflight" and check["status"] == "pass"
                   for check in preflight):
            raise ScenarioError("Recipient did not pass shielded wallet validation; payment not started")

        request_hash = ztestkit.digest(uri)
        deadline = time.monotonic() + max(args.wait_seconds, 0)
        if args.recover_txid:
            checkpoint = recover_checkpoint(recipient, args.checkpoint, request_hash,
                                            args.recover_txid, payment["amount_zat"], account_uuid)
        else:
            checkpoint = submit_or_resume(sender, args.checkpoint, request_hash,
                                          source_address, payment["address"], str(amount))
        while checkpoint.get("state") == "operation_pending" and time.monotonic() < deadline:
            time.sleep(max(args.poll_seconds, 0.1))
            checkpoint = submit_or_resume(sender, args.checkpoint, request_hash,
                                          source_address, payment["address"], str(amount))
        if checkpoint.get("state") == "operation_pending":
            raise ScenarioError("Wallet operation is still pending; rerun with the same checkpoint")

        if checkpoint.get("state") == "submitted":
            node.call("generate", [1])
            checkpoint["state"] = "mined"
            write_checkpoint(args.checkpoint, checkpoint)

        while time.monotonic() < deadline:
            observation = ztestkit.observe(recipient, checkpoint["txid"],
                                           payment["amount_zat"], account_uuid)
            if observation["status"] != "unverified":
                break
            time.sleep(max(args.poll_seconds, 0.1))

        kit_args = ["--uri-file", str(args.uri_file),
                    "--rpc-url", args.recipient_rpc_url,
                    "--rpc-cookie", str(args.recipient_rpc_cookie),
                    "--account-uuid", account_uuid,
                    "--txid", checkpoint["txid"],
                    "--network", "regtest",
                    "--canary-file", str(args.canary_file),
                    "--report", str(args.report)]
        for log_path in args.log:
            kit_args.extend(["--log", str(log_path)])
        exit_code = ztestkit.main(kit_args)
        checkpoint["state"] = "reported"
        write_checkpoint(args.checkpoint, checkpoint)
        append_scenario_state(args.report, checkpoint)
        return exit_code
    except (OSError, ztestkit.CheckError, ScenarioError) as exc:
        print(f"scenario_runner: {exc}", file=sys.stderr)
        return 3 if isinstance(exc, ScenarioError) else 2


if __name__ == "__main__":
    raise SystemExit(main())
