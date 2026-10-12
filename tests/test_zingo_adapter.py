import importlib.util
import json
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ztestkit", ROOT / "ztestkit.py")
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)

ADDRESS = "utest1" + "q" * 80
TXID = "a" * 64


class ZingoAdapter(unittest.TestCase):
    def run_case(self, *, address=ADDRESS, note_value=100000, note_status="confirmed at block height 4490357",
                 note_scope="external", wallet_height=4490359, chain_txid=TXID, canonical=True,
                 include_chain=True, wallet_account=0):
        with tempfile.TemporaryDirectory(dir=ROOT) as directory:
            folder = Path(directory)
            inputs = {
                "addresses": [{"account": wallet_account, "encoded_address": ADDRESS, "has_orchard": True,
                               "has_sapling": False, "has_transparent": False}],
                "notes": {"ironwood_notes": {"note_summaries": [{"txid": TXID, "value": note_value,
                          "status": note_status, "scope": note_scope, "account_id": 0,
                          "output_index": 0, "memo": "SECRET MEMO"}]},
                          "orchard_notes": {"note_summaries": []}, "sapling_notes": {"note_summaries": []}},
                "height": {"height": wallet_height},
                "chain": {"data": {"txid": chain_txid, "blockHeight": "4490357",
                          "isCanonical": canonical, "status": "confirmed", "hasIronwood": True}}
            }
            for name, value in inputs.items():
                (folder / f"{name}.json").write_text(json.dumps(value), encoding="utf-8")
            args = ["--uri", f"zcash:{address}?amount=0.001", "--network", "testnet",
                    "--zingo-addresses-file", str(folder / "addresses.json"),
                    "--zingo-notes-file", str(folder / "notes.json"),
                    "--zingo-height-file", str(folder / "height.json"),
                    "--txid", TXID,
                    "--canary-file", str(ROOT / "examples" / "canaries.txt"),
                    "--log", str(ROOT / "examples" / "clean-app.log"),
                    "--report", str(folder / "report.json")]
            if include_chain:
                args.extend(["--chain-proof-file", str(folder / "chain.json")])
            code = kit.main(args)
            report = json.loads((folder / "report.json").read_text(encoding="utf-8"))
            text = json.dumps(report)
            self.assertNotIn(ADDRESS, text)
            self.assertNotIn("SECRET MEMO", text)
            self.assertNotIn('"expected_value_zat"', text)
            return code, report

    def test_confirmed_receiver_note_passes_with_redacted_evidence(self):
        code, report = self.run_case()
        self.assertEqual(code, 0)
        self.assertEqual([c["status"] for c in report["checks"]], ["pass", "pass", "pass"])
        self.assertEqual(report["checks"][1]["evidence"]["matching_pools"], ["ironwood"])

    def test_wrong_wallet_address_fails_preflight(self):
        code, report = self.run_case(address="utest1" + "r" * 80)
        self.assertEqual(code, 1)
        self.assertEqual(report["checks"][0]["status"], "fail")

    def test_confirmed_wrong_amount_fails_observation(self):
        code, report = self.run_case(note_value=200000)
        self.assertEqual(code, 1)
        self.assertEqual(report["checks"][1]["status"], "fail")

    def test_stale_scan_and_unconfirmed_note_remain_unverified(self):
        for kwargs in ({"wallet_height": 4490356}, {"note_status": "pending"}):
            with self.subTest(kwargs=kwargs):
                code, report = self.run_case(**kwargs)
                self.assertEqual(code, 3)
                self.assertEqual(report["checks"][1]["status"], "unverified")

    def test_chain_mismatch_or_missing_snapshot_cannot_pass(self):
        for kwargs in ({"chain_txid": "b" * 64}, {"canonical": False}, {"include_chain": False}):
            with self.subTest(kwargs=kwargs):
                code, report = self.run_case(**kwargs)
                self.assertEqual(code, 3)
                self.assertEqual(report["checks"][1]["status"], "unverified")

    def test_internal_note_cannot_prove_external_receive(self):
        code, report = self.run_case(note_scope="internal")
        self.assertEqual(code, 3)
        self.assertEqual(report["checks"][1]["status"], "unverified")

    def test_missing_recipient_account_cannot_pass(self):
        code, report = self.run_case(wallet_account=None)
        self.assertEqual(code, 3)
        self.assertEqual([c["status"] for c in report["checks"][:2]], ["unverified", "unverified"])


if __name__ == "__main__":
    unittest.main()
