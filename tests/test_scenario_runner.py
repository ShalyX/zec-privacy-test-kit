import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("scenario_runner", ROOT / "scenario_runner.py")
runner = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(runner)


class FakeWallet:
    def __init__(self, responses=None):
        self.responses = responses or {}
        self.calls = []

    def call(self, method, params=None):
        self.calls.append((method, params or []))
        response = self.responses.get(method)
        if callable(response):
            return response(method, params or [])
        if isinstance(response, Exception):
            raise response
        return response


class SubmissionCheckpoint(unittest.TestCase):
    def test_saved_txid_is_reused_without_wallet_call(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"request_sha256": "request", "state": "submitted",
                                              "txid": "a" * 64}))
            wallet = FakeWallet()
            outcome = runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual(outcome["txid"], "a" * 64)
            self.assertEqual(wallet.calls, [])

    def test_pending_operation_is_resolved_and_persisted(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"request_sha256": "request", "state": "operation_pending",
                                              "operation_id": "opid-1"}))
            wallet = FakeWallet({"z_getoperationstatus": [
                {"id": "opid-1", "status": "success", "result": {"txid": "b" * 64}}
            ]})
            outcome = runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual(outcome["txid"], "b" * 64)
            self.assertEqual(json.loads(checkpoint.read_text())["state"], "submitted")
            self.assertEqual([call[0] for call in wallet.calls], ["z_getoperationstatus"])

    def test_new_submission_is_called_once_then_resumed_by_operation_id(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            wallet = FakeWallet({"z_sendmany": "opid-2", "z_getoperationstatus": []})
            first = runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            second = runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual(first["state"], "operation_pending")
            self.assertEqual(second["state"], "operation_pending")
            self.assertEqual([call[0] for call in wallet.calls].count("z_sendmany"), 1)
            self.assertNotIn("source", checkpoint.read_text())
            self.assertNotIn("recipient", checkpoint.read_text())

    def test_checkpoint_precedes_the_wallet_submission_effect(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"

            def inspect_checkpoint(method, params):
                self.assertEqual(json.loads(checkpoint.read_text())["state"], "submission_started")
                return "opid-before-effect"

            wallet = FakeWallet({"z_sendmany": inspect_checkpoint})
            runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual(json.loads(checkpoint.read_text())["state"], "operation_pending")

    def test_uncertain_submission_is_checkpointed_and_never_retried(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            wallet = FakeWallet({"z_sendmany": RuntimeError("transport failed")})
            with self.assertRaises(runner.ScenarioError):
                runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual(json.loads(checkpoint.read_text())["state"], "submission_uncertain")
            with self.assertRaises(runner.ScenarioError):
                runner.submit_or_resume(wallet, checkpoint, "request", "source", "recipient", "0.01")
            self.assertEqual([call[0] for call in wallet.calls].count("z_sendmany"), 1)

    def test_checkpoint_cannot_be_reused_for_a_different_request(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"request_sha256": "old", "state": "submitted",
                                              "txid": "c" * 64}))
            with self.assertRaises(runner.ScenarioError):
                runner.submit_or_resume(FakeWallet(), checkpoint, "new", "source", "recipient", "0.01")

    def test_failed_operation_can_only_recover_from_recipient_matching_tx(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"request_sha256": "request", "state": "failed",
                                              "operation_id": "opid-3", "error_code": -4}))
            recipient = FakeWallet({
                "getwalletstatus": {"locked": False,
                                    "node_tip": {"height": 10, "blockhash": "tip"},
                                    "wallet_tip": {"height": 10, "blockhash": "tip"}},
                "z_viewtransaction": {"status": "waiting", "confirmations": -1, "outputs": [
                    {"account_uuid": "account", "outgoing": False,
                     "valueZat": 100_000, "pool": "ironwood"}
                ]},
            })
            value = runner.recover_checkpoint(recipient, checkpoint, "request", "d" * 64,
                                              100_000, "account")
            self.assertEqual(value["state"], "submitted")
            self.assertEqual(value["txid"], "d" * 64)

    def test_recovery_rejects_transaction_without_matching_recipient_note(self):
        with tempfile.TemporaryDirectory() as directory:
            checkpoint = Path(directory) / "checkpoint.json"
            checkpoint.write_text(json.dumps({"request_sha256": "request", "state": "failed"}))
            recipient = FakeWallet({
                "getwalletstatus": {"locked": False,
                                    "node_tip": {"height": 10, "blockhash": "tip"},
                                    "wallet_tip": {"height": 10, "blockhash": "tip"}},
                "z_viewtransaction": {"status": "waiting", "confirmations": -1, "outputs": []},
            })
            with self.assertRaises(runner.ScenarioError):
                runner.recover_checkpoint(recipient, checkpoint, "request", "e" * 64,
                                          100_000, "account")
            self.assertEqual(json.loads(checkpoint.read_text())["state"], "failed")

    def test_rpc_urls_must_be_plain_loopback_http(self):
        self.assertEqual(runner.require_loopback("http://127.0.0.1:50232"),
                         "http://127.0.0.1:50232")
        for value in ["https://127.0.0.1:50232", "http://wallet.example:50232",
                      "http://user:pass@127.0.0.1:50232", "http://127.0.0.1"]:
            with self.subTest(value=value), self.assertRaises(runner.ScenarioError):
                runner.require_loopback(value)

    def test_regtest_guard_requires_expected_genesis(self):
        runner.assert_regtest(FakeWallet({"getblockhash": runner.REGTEST_GENESIS}))
        with self.assertRaises(runner.ScenarioError):
            runner.assert_regtest(FakeWallet({"getblockhash": "f" * 64}))


if __name__ == "__main__":
    unittest.main()
