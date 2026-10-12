#!/usr/bin/env python3
"""Local, read-only Zcash payment privacy checks. No spending keys are accepted."""

import argparse
import base64
import hashlib
import json
import re
import sys
import urllib.error
import urllib.request
from decimal import Decimal, InvalidOperation
from pathlib import Path
from urllib.parse import urlsplit


ADDRESS = re.compile(r"^[A-Za-z0-9]+$")
PARAM = re.compile(r"^([A-Za-z][A-Za-z0-9+-]*)(?:\.([1-9][0-9]{0,3}))?$")
AMOUNT = re.compile(r"^[0-9]+(?:\.[0-9]{1,8})?$")
BASE64URL = re.compile(r"^[A-Za-z0-9_-]*$")
QCHAR = re.compile(r"^(?:[A-Za-z0-9_.~!$'()*+,;:@-]|%[0-9A-Fa-f]{2})*$")
KNOWN = {"address", "amount", "memo", "label", "message"}


class CheckError(ValueError):
    pass


def digest(value):
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def parse_uri(uri):
    if not uri.startswith("zcash:") or "#" in uri or uri.startswith("zcash://"):
        raise CheckError("Expected a non-hierarchical zcash: URI")
    body = uri[6:]
    address, separator, query = body.partition("?")
    if address and not ADDRESS.fullmatch(address):
        raise CheckError("Invalid address syntax in URI path")
    if not address and not separator:
        raise CheckError("Payment address is missing")
    payments = {"": {"address": address}} if address else {}
    seen = set()
    if separator:
        if not query:
            raise CheckError("Empty query")
        for pair in query.split("&"):
            if "=" not in pair:
                raise CheckError("Query parameter lacks =")
            key, value = pair.split("=", 1)
            match = PARAM.fullmatch(key)
            if not match:
                raise CheckError("Invalid query parameter name or index")
            name, index = match.group(1), match.group(2) or ""
            if (name, index) in seen:
                raise CheckError("Duplicate parameter and index")
            seen.add((name, index))
            if name.startswith("req-"):
                raise CheckError("Required extension is unsupported")
            if name in ("address", "amount") and not (ADDRESS if name == "address" else AMOUNT).fullmatch(value):
                raise CheckError(f"Invalid {name} syntax")
            if name == "memo" and not BASE64URL.fullmatch(value):
                raise CheckError("Memo must be unpadded base64url")
            if name not in ("address", "amount", "memo") and not QCHAR.fullmatch(value):
                raise CheckError("Invalid query value syntax")
            if name in KNOWN:
                record = payments.setdefault(index, {})
                if name == "address" and "address" in record:
                    raise CheckError("Duplicate payment address")
                record[name] = value
    if not payments or any("address" not in p for p in payments.values()):
        raise CheckError("Every payment index needs an address")
    parsed = []
    for index, record in sorted(payments.items(), key=lambda item: int(item[0] or 0)):
        addr = record["address"]
        if not ADDRESS.fullmatch(addr):
            raise CheckError("Invalid payment address syntax")
        amount_zat = None
        if "amount" in record:
            try:
                amount = Decimal(record["amount"])
            except InvalidOperation as exc:
                raise CheckError("Invalid amount") from exc
            if amount > Decimal("21000000"):
                raise CheckError("Amount exceeds ZEC supply")
            amount_zat = int(amount * 100_000_000)
        if "memo" in record:
            if addr.startswith(("t1", "t2", "tm")):
                raise CheckError("Transparent payment cannot carry a memo")
            try:
                memo = base64.urlsafe_b64decode(record["memo"] + "=" * (-len(record["memo"]) % 4))
            except (ValueError, base64.binascii.Error) as exc:
                raise CheckError("Invalid memo encoding") from exc
            if base64.urlsafe_b64encode(memo).rstrip(b"=").decode() != record["memo"]:
                raise CheckError("Invalid memo encoding")
            if len(memo) > 512:
                raise CheckError("Memo exceeds 512 bytes")
        parsed.append({"index": index, "address": addr, "amount_zat": amount_zat,
                       "memo_present": "memo" in record,
                       "label_present": "label" in record,
                       "message_present": "message" in record})
    return parsed


def network_hint(address):
    # This is a hint only. RPC validation is required for a pass.
    if address.startswith(("uregtest1", "zregtestsapling1", "tm")):
        return "regtest-or-testnet"
    if address.startswith(("utest1", "ztestsapling1", "t2")):
        return "testnet"
    if address.startswith(("u1", "zs1", "t1")):
        return "mainnet"
    return "unknown"


class WalletRpc:
    def __init__(self, url, cookie_path):
        self.url = url
        credential = Path(cookie_path).read_text(encoding="utf-8").strip()
        if ":" not in credential:
            raise CheckError("RPC cookie has no user:password pair")
        self.authorization = "Basic " + base64.b64encode(credential.encode()).decode()

    def call(self, method, params=None):
        data = json.dumps({"jsonrpc": "2.0", "id": "ztestkit", "method": method,
                           "params": params or []}).encode()
        request = urllib.request.Request(self.url, data=data,
                                         headers={"Content-Type": "application/json",
                                                  "Authorization": self.authorization})
        try:
            with urllib.request.urlopen(request, timeout=30) as response:
                payload = json.load(response)
        except (urllib.error.URLError, TimeoutError) as exc:
            raise CheckError(f"Wallet RPC unavailable: {type(exc).__name__}") from exc
        if payload.get("error"):
            # Wallet error messages can contain request data; never copy them to a report.
            raise CheckError(f"Wallet RPC {method} failed")
        return payload.get("result")


def preflight(payments, wallet=None):
    checks = []
    for payment in payments:
        addr = payment["address"]
        evidence = {"address_sha256": digest(addr), "network_hint": network_hint(addr),
                    "memo_present": payment["memo_present"],
                    "label_present": payment["label_present"],
                    "message_present": payment["message_present"]}
        receivers = None
        wallet_error = False
        if wallet:
            try:
                receivers = wallet.call("z_listunifiedreceivers", [addr])
            except CheckError:
                receivers = None
            if receivers is not None:
                evidence["rpc_validated"] = True
            else:
                try:
                    validation = wallet.call("validateaddress", [addr])
                except CheckError:
                    wallet_error = True
                else:
                    if not validation.get("isvalid"):
                        checks.append({"check": "address_valid", "payment_index": payment["index"],
                                       "status": "fail", "reason": "Wallet rejected the address",
                                       "evidence": evidence})
                        continue
                    evidence["rpc_validated"] = True
        transparent = addr.startswith(("t1", "t2", "tm"))
        if receivers is not None:
            evidence["receiver_types"] = sorted(receivers)
            transparent = set(receivers) <= {"p2pkh", "p2sh"}
            shielded = bool(set(receivers) & {"sapling", "orchard", "ironwood"})
        else:
            shielded = bool(evidence.get("rpc_validated") and
                            addr.startswith(("zs1", "ztestsapling1", "zregtestsapling1")))
        if transparent and payment["memo_present"]:
            status, reason = "fail", "Memo requested for transparent recipient"
        elif transparent:
            status, reason = "fail", "Transparent-only recipient reveals output address and amount"
        elif wallet and shielded:
            status, reason = "pass", "Wallet validated a shielded receiver"
        else:
            status, reason = "unverified", ("Wallet RPC unavailable for receiver validation" if wallet_error
                                            else "Receiver capability requires wallet validation")
        checks.append({"check": "recipient_preflight", "payment_index": payment["index"],
                       "status": status, "reason": reason, "evidence": evidence})
        if payment["label_present"] or payment["message_present"]:
            checks.append({"check": "uri_metadata", "payment_index": payment["index"],
                           "status": "fail", "reason": "URI carries human-readable metadata; sharing it exposes context"})
    return checks


def observe(wallet, txid, expected_zat, account_uuid):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", txid):
        raise CheckError("txid must be 64 hex characters")
    try:
        status = wallet.call("getwalletstatus")
    except CheckError:
        return {"check": "recipient_observation", "status": "unverified",
                "reason": "Wallet RPC unavailable for transaction observation",
                "evidence": {"txid": txid}}
    node = status.get("node_tip", {})
    tip = status.get("wallet_tip", {})
    synced = (node.get("height") is not None and node.get("blockhash") is not None
              and node.get("height") == tip.get("height")
              and node.get("blockhash") == tip.get("blockhash"))
    result = {"check": "recipient_observation", "status": "unverified",
              "evidence": {"txid": txid, "wallet_synced": synced,
                           "wallet_height": tip.get("height"), "node_height": node.get("height")}}
    if not synced or status.get("locked"):
        result["reason"] = "Wallet is still syncing or locked"
        return result
    try:
        view = wallet.call("z_viewtransaction", [txid])
    except CheckError:
        result["reason"] = "Wallet RPC unavailable for transaction observation"
        return result
    outputs = [entry for entry in view.get("outputs", [])
               if entry.get("account_uuid") == account_uuid and entry.get("outgoing") is False]
    matches = [entry for entry in outputs if entry.get("valueZat") == expected_zat]
    shielded = [entry for entry in matches if entry.get("pool") in {"sapling", "orchard", "ironwood"}]
    result["evidence"].update({"chain_status": view.get("status"),
                               "confirmations": view.get("confirmations", 0),
                               "account_sha256": digest(account_uuid),
                               "received_output_count": len(outputs),
                               "observed_pools": sorted({entry.get("pool", "unknown") for entry in outputs}),
                               "matching_shielded_output_count": len(shielded),
                               "matching_pools": sorted({entry["pool"] for entry in shielded})})
    if view.get("status") == "mined" and view.get("confirmations", 0) >= 1 and shielded:
        result["status"] = "pass"
        result["reason"] = "Recipient wallet decrypted a confirmed shielded note of the requested amount"
    elif view.get("status") == "mined" and outputs and not shielded:
        result["status"] = "fail"
        result["reason"] = "Confirmed receive lacks a matching shielded note"
    else:
        result["reason"] = "No confirmed matching shielded receive yet"
    return result


def read_evidence_json(path, label):
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (ValueError, UnicodeError) as exc:
        # Parser details may include wallet data. Do not echo them.
        raise CheckError(f"Invalid {label} JSON") from exc


def zingo_preflight(payment, addresses):
    if not isinstance(addresses, list) or not all(isinstance(item, dict) for item in addresses):
        raise CheckError("Invalid Zingo addresses export")
    address = payment["address"]
    matches = [item for item in addresses if item.get("encoded_address") == address]
    evidence = {"address_sha256": digest(address), "network_hint": network_hint(address),
                "wallet_address_match": bool(matches), "memo_present": payment["memo_present"],
                "label_present": payment["label_present"], "message_present": payment["message_present"]}
    if address.startswith(("t1", "t2", "tm")):
        status, reason = "fail", "Transparent-only recipient reveals output address and amount"
    elif not matches:
        status, reason = "fail", "Requested address is absent from the recipient wallet export"
    elif network_hint(address) != "testnet":
        status, reason = "unverified", "Zingo adapter currently validates Testnet addresses only"
    elif type(matches[0].get("account")) is not int or matches[0]["account"] < 0:
        status, reason = "unverified", "Recipient wallet export lacks a valid account ID"
    else:
        status, reason = "pass", "Recipient wallet export derives the requested Testnet address"
        evidence["account_sha256"] = digest(str(matches[0].get("account")))
    return {"check": "recipient_preflight", "payment_index": payment["index"],
            "status": status, "reason": reason, "evidence": evidence,
            "evidence_source": "ZIP-321 request and recipient Zingo addresses JSON export",
            "reproduce": "Export addresses from the same recipient wallet and compare the requested address locally.",
            "privacy_boundary": "Address derivation alone does not prove a payment was received or shielded."}


def zingo_observe(payment, txid, account_id, notes, height, chain):
    if not re.fullmatch(r"[0-9a-fA-F]{64}", txid):
        raise CheckError("txid must be 64 hex characters")
    if not isinstance(notes, dict) or not isinstance(height, dict):
        raise CheckError("Invalid Zingo notes or height export")
    wallet_height = height.get("height")
    if type(wallet_height) is not int or wallet_height < 0:
        raise CheckError("Invalid Zingo wallet height")
    evidence = {"txid": txid, "wallet_height": wallet_height}
    result = {"check": "recipient_observation", "status": "unverified", "evidence": evidence,
              "evidence_source": "Recipient Zingo notes and height JSON exports; operator-supplied public-chain JSON snapshot",
              "reproduce": "Re-export notes and height from the same recipient wallet; save a fresh public transaction JSON response and rerun.",
              "privacy_boundary": "Local exports and an operator-supplied API response are snapshots. This does not prove network-wide privacy or current chain state."}
    if type(account_id) is not int or account_id < 0:
        result["reason"] = "Recipient account ID is missing from the wallet address export"
        return result
    if chain is None:
        result["reason"] = "No independent public-chain snapshot supplied"
        return result
    if not isinstance(chain, dict) or not isinstance(chain.get("data"), dict):
        raise CheckError("Invalid public-chain snapshot")
    public = chain["data"]
    chain_height = public.get("blockHeight")
    try:
        chain_height = int(chain_height) if type(chain_height) in (str, int) else None
    except ValueError:
        chain_height = None
    public_txid = public.get("txid")
    canonical = (isinstance(public_txid, str) and public_txid.lower() == txid.lower() and
                 public.get("isCanonical") is True and public.get("status") == "confirmed" and
                 public.get("hasIronwood") is True and chain_height is not None and chain_height > 0)
    evidence["public_chain_canonical_match"] = canonical
    if not canonical:
        result["reason"] = "Public-chain snapshot does not confirm this canonical Ironwood transaction"
        return result
    evidence["block_height"] = chain_height
    if wallet_height < chain_height:
        result["reason"] = "Recipient wallet scan has not reached the confirmed block"
        return result
    received = []
    for pool in ("ironwood", "orchard", "sapling"):
        section = notes.get(f"{pool}_notes", {})
        if not isinstance(section, dict) or not isinstance(section.get("note_summaries", []), list):
            raise CheckError("Invalid Zingo notes export")
        for note in section.get("note_summaries", []):
            if not isinstance(note, dict):
                raise CheckError("Invalid Zingo notes export")
            note_txid = note.get("txid")
            if isinstance(note_txid, str) and note_txid.lower() == txid.lower() and note.get("scope") == "external" and note.get("account_id") == account_id:
                received.append((pool, note))
    evidence["received_output_count"] = len(received)
    if not received:
        result["reason"] = "No external note for this transaction and recipient account in the supplied wallet export"
        return result
    confirmed = []
    for pool, note in received:
        match = re.fullmatch(r"confirmed at block height ([1-9][0-9]*)", str(note.get("status", "")))
        if match and int(match.group(1)) == chain_height:
            confirmed.append((pool, note))
    if not confirmed:
        result["reason"] = "Recipient note is not confirmed at the public transaction block"
        return result
    matching = [(pool, note) for pool, note in confirmed if type(note.get("value")) is int and
                note["value"] == payment["amount_zat"]]
    evidence["matching_shielded_output_count"] = len(matching)
    evidence["matching_pools"] = sorted({pool for pool, _ in matching})
    if matching:
        result["status"] = "pass"
        result["reason"] = "Recipient wallet decrypted a matching confirmed shielded Testnet note"
    else:
        result["status"] = "fail"
        result["reason"] = "Confirmed recipient note amount does not match the payment request"
    return result


def scan_canaries(log_paths, canary_path):
    canaries = [line.strip() for line in Path(canary_path).read_text(encoding="utf-8").splitlines() if line.strip()]
    if not canaries:
        raise CheckError("Canary file is empty")
    findings = []
    for file_index, path in enumerate(log_paths, 1):
        for line_no, line in enumerate(Path(path).read_text(encoding="utf-8", errors="replace").splitlines(), 1):
            for marker in canaries:
                if marker in line:
                    findings.append({"file_index": file_index, "line": line_no,
                                     "canary_sha256": digest(marker)})
    return {"check": "canary_leak", "status": "fail" if findings else "pass",
            "reason": "Synthetic marker found in supplied log" if findings else "No supplied canary found",
            "evidence": {"files_scanned": len(log_paths), "findings": findings}}


CHECK_CONTEXT = {
    "address_valid": ("ZIP-321 request and recipient wallet address validation",
                      "Rerun this request against the same wallet and inspect address validation.",
                      "Only this wallet's address validation was checked."),
    "recipient_preflight": ("ZIP-321 request and recipient wallet receiver decoding",
                            "Rerun with the request and recipient wallet RPC; inspect receiver types.",
                            "Receiver capability does not prove a payment used a shielded receiver."),
    "uri_metadata": ("ZIP-321 request fields",
                     "Inspect the request for label and message parameters.",
                     "This detects metadata in the supplied URI only."),
    "recipient_observation": ("Recipient wallet getwalletstatus and z_viewtransaction",
                              "Rerun with the same txid, recipient wallet, and account UUID after sync.",
                              "A wallet view cannot establish network-wide privacy or external leaks."),
    "canary_leak": ("Supplied local logs and synthetic canary file",
                    "Rerun with the same canary file and logs; inspect reported file index and line.",
                    "Literal matching covers only supplied files and canaries."),
}


def annotate_checks(checks):
    for check in checks:
        source, reproduce, boundary = CHECK_CONTEXT[check["check"]]
        if check["check"] == "recipient_observation" and check.get("reason") == "No transaction ID supplied":
            source = "No transaction or recipient wallet observation supplied"
            reproduce = "Supply a txid, recipient wallet RPC, and account UUID after payment confirmation."
        elif check["check"] == "recipient_preflight" and check.get("status") == "unverified":
            source = "ZIP-321 request syntax; wallet receiver validation unavailable"
        elif check["check"] == "canary_leak" and check.get("status") == "unverified":
            source = "No complete canary and log input supplied"
            reproduce = "Supply a synthetic canary file and at least one app log."
        check.setdefault("evidence_source", source)
        check.setdefault("reproduce", reproduce)
        check.setdefault("privacy_boundary", boundary)
    return checks


def main(argv=None):
    parser = argparse.ArgumentParser(description="Local Zcash payment privacy test kit")
    request = parser.add_mutually_exclusive_group(required=True)
    request.add_argument("--uri", help="ZIP-321 payment URI; use --uri-file for private values")
    request.add_argument("--uri-file", type=Path, help="File containing one ZIP-321 URI")
    parser.add_argument("--rpc-url", help="Recipient Zallet JSON-RPC URL, loopback only")
    parser.add_argument("--rpc-cookie", type=Path, help="Recipient Zallet cookie file")
    parser.add_argument("--txid", help="Transaction ID to verify in the recipient wallet")
    parser.add_argument("--account-uuid", help="Expected recipient wallet account UUID")
    parser.add_argument("--zingo-addresses-file", type=Path, help="Recipient Zingo addresses JSON export")
    parser.add_argument("--zingo-notes-file", type=Path, help="Recipient Zingo notes JSON export")
    parser.add_argument("--zingo-height-file", type=Path, help="Recipient Zingo height JSON export")
    parser.add_argument("--chain-proof-file", type=Path, help="Saved public-chain transaction JSON snapshot")
    parser.add_argument("--canary-file", type=Path, help="One synthetic canary per line")
    parser.add_argument("--log", type=Path, action="append", default=[], help="App log to scan")
    parser.add_argument("--report", type=Path, required=True, help="Output JSON path")
    parser.add_argument("--network", choices=["regtest", "testnet", "mainnet"],
                        help="Operator-asserted network; recorded as an assertion")
    args = parser.parse_args(argv)
    try:
        uri = args.uri_file.read_text(encoding="utf-8").strip() if args.uri_file else args.uri
        payments = parse_uri(uri)
        zingo_files = (args.zingo_addresses_file, args.zingo_notes_file, args.zingo_height_file)
        zingo_mode = any(zingo_files)
        if zingo_mode and (not all(zingo_files) or args.rpc_url or args.rpc_cookie or args.account_uuid):
            raise CheckError("Provide all three Zingo exports without wallet RPC or account UUID")
        if args.chain_proof_file and not zingo_mode:
            raise CheckError("Public-chain snapshot requires Zingo exports")
        if zingo_mode and args.network != "testnet":
            raise CheckError("Zingo export mode requires --network testnet")
        if bool(args.rpc_url) != bool(args.rpc_cookie):
            raise CheckError("Provide both --rpc-url and --rpc-cookie")
        if args.rpc_url:
            target = urlsplit(args.rpc_url)
            if (target.scheme != "http" or target.hostname not in {"127.0.0.1", "localhost"}
                    or target.username or target.password or target.path not in {"", "/"}
                    or target.query or target.fragment):
                raise CheckError("RPC must use a plain loopback HTTP URL")
            try:
                if target.port is None:
                    raise CheckError("RPC URL needs a port")
            except ValueError as exc:
                raise CheckError("Invalid RPC port") from exc
        wallet = WalletRpc(args.rpc_url, args.rpc_cookie) if args.rpc_url else None
        if zingo_mode:
            if len(payments) != 1 or payments[0]["amount_zat"] is None or not args.txid:
                raise CheckError("Zingo observation needs one payment with an amount and --txid")
            addresses = read_evidence_json(args.zingo_addresses_file, "Zingo addresses")
            notes = read_evidence_json(args.zingo_notes_file, "Zingo notes")
            height = read_evidence_json(args.zingo_height_file, "Zingo height")
            chain = read_evidence_json(args.chain_proof_file, "public-chain snapshot") if args.chain_proof_file else None
            checks = [zingo_preflight(payments[0], addresses)]
            if payments[0]["label_present"] or payments[0]["message_present"]:
                checks.append({"check": "uri_metadata", "payment_index": payments[0]["index"],
                               "status": "fail", "reason": "URI carries human-readable metadata; sharing it exposes context"})
            matched_addresses = [item for item in addresses if item.get("encoded_address") == payments[0]["address"]]
            account_id = matched_addresses[0].get("account") if matched_addresses else None
            checks.append(zingo_observe(payments[0], args.txid, account_id, notes, height, chain))
        else:
            checks = preflight(payments, wallet)
        if args.txid and not zingo_mode:
            if not wallet or not args.account_uuid or len(payments) != 1 or payments[0]["amount_zat"] is None:
                raise CheckError("Observation needs wallet RPC, account UUID, and one payment with an amount")
            checks.append(observe(wallet, args.txid, payments[0]["amount_zat"], args.account_uuid))
        elif not args.txid:
            checks.append({"check": "recipient_observation", "status": "unverified",
                           "reason": "No transaction ID supplied"})
        if args.canary_file and args.log:
            checks.append(scan_canaries(args.log, args.canary_file))
        else:
            checks.append({"check": "canary_leak", "status": "unverified",
                           "reason": "Canary file and log were not both supplied"})
        annotate_checks(checks)
        report = {"schema_version": 2, "request_sha256": digest(uri),
                  "network_scope": f"{args.network} (operator asserted)" if args.network else "unverified",
                  "checks": checks,
                  "limits": ["Wallet observation proves only this wallet's view of a confirmed note.",
                             "Canary scan covers only supplied files and literal markers.",
                             "No network observer, RPC transport, browser telemetry, or external logs were tested."]}
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        print(json.dumps({"report": str(args.report), "statuses": [c["status"] for c in checks]}))
        if any(check["status"] == "fail" for check in checks):
            return 1
        if any(check["status"] == "unverified" for check in checks):
            return 3
        return 0
    except (CheckError, OSError) as exc:
        print(f"ztestkit: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
