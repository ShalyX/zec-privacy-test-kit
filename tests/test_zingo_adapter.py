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
    def test_public_example_omits_private_derived_identifiers(self):
        example = ROOT / "examples" / "public-testnet-report.json"
        report = json.loads(example.read_text(encoding="utf-8"))
        self.assertNotIn("request_sha256", report)
        for check in report["checks"]:
            self.assertNotIn("address_sha256", check.get("evidence", {}))
            self.assertNotIn("account_sha256", check.get("evidence", {}))
        self.assertEqual(example.read_bytes(), (ROOT / "demo" / "testnet.json").read_bytes())

    def run_case(self, *, address=ADDRESS, note_value=100000, note_status="confirmed at block height 4490357",
                 note_scope="external", wallet_height=4490359, chain_txid=TXID, canonical=True,
                 include_chain=True, wallet_account=0, chain_overrides=None):
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
                          "isCanonical": canonical, "status": "confirmed", "hasIronwood": True,
                          "hasOrchard": False, "hasSapling": False, "hasSprout": False,
                          "inputCount": 0, "outputCount": 0, "inputs": [], "outputs": [],
                          "valueBalanceIronwoodZat": "10000", "valueBalanceOrchardZat": "0",
                          "valueBalanceSaplingZat": "0"}}
            }
            inputs["chain"]["data"].update(chain_overrides or {})
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
        self.assertEqual([c["status"] for c in report["checks"]], ["pass", "pass", "pass", "pass"])
        self.assertEqual(report["checks"][1]["evidence"]["matching_pools"], ["ironwood"])
        self.assertEqual(report["checks"][2]["check"], "public_chain_exposure")

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

    def test_transparent_input_or_output_fails_without_exporting_address(self):
        for field, count in (("inputs", "inputCount"), ("outputs", "outputCount")):
            with self.subTest(field=field):
                overrides = {field: [{"address": "t1PRIVATEADDRESS", "valueZat": 12345}], count: 1}
                code, report = self.run_case(chain_overrides=overrides)
                self.assertEqual(code, 1)
                self.assertEqual(report["checks"][2]["status"], "fail")
                self.assertNotIn("t1PRIVATEADDRESS", json.dumps(report))
                self.assertNotIn("12345", json.dumps(report))

    def test_cross_pool_net_value_is_flagged(self):
        code, report = self.run_case(chain_overrides={"hasOrchard": True,
            "valueBalanceOrchardZat": "90000", "valueBalanceIronwoodZat": "-80000"})
        self.assertEqual(code, 1)
        check = report["checks"][2]
        self.assertEqual(check["status"], "fail")
        self.assertEqual(check["evidence"]["nonzero_pool_balance_count"], 2)
        self.assertNotIn("90000", json.dumps(check))

    def test_multiple_pools_without_net_crossing_do_not_fail(self):
        code, report = self.run_case(chain_overrides={"hasOrchard": True,
            "valueBalanceOrchardZat": "0"})
        self.assertEqual(code, 0)
        self.assertEqual(report["checks"][2]["status"], "pass")

    def test_missing_or_inconsistent_explorer_fields_remain_unverified(self):
        for overrides in ({"inputCount": None}, {"inputs": [{"address": "t1PRIVATEADDRESS"}]},
                          {"valueBalanceIronwoodZat": None}, {"hasSprout": True}):
            with self.subTest(overrides=overrides):
                code, report = self.run_case(chain_overrides=overrides)
                self.assertEqual(code, 3)
                self.assertEqual(report["checks"][2]["status"], "unverified")


if __name__ == "__main__":
    unittest.main()
