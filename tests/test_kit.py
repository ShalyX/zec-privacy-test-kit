import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


ROOT = Path(__file__).resolve().parents[1]
SPEC = importlib.util.spec_from_file_location("ztestkit", ROOT / "ztestkit.py")
kit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(kit)


class Zip321Examples(unittest.TestCase):
    SAPLING = "ztestsapling10yy2ex5dcqkclhc7z7yrnjq2z6feyjad56ptwlfgmy77dmaqqrl9gyhprdx59qgmsnyfska2kez"
    TRANSPARENT = "tmEZhbWHTpdKMw5it8YDspUXSMGQyFwovpU"

    def test_official_single_payment_example(self):
        uri = (f"zcash:{self.SAPLING}?amount=1&memo=VGhpcyBpcyBhIHNpbXBsZSBtZW1vLg"
               "&message=Thank%20you%20for%20your%20purchase")
        result = kit.parse_uri(uri)
        self.assertEqual(result[0]["amount_zat"], 100_000_000)
        self.assertTrue(result[0]["memo_present"])
        self.assertTrue(result[0]["message_present"])

    def test_official_multi_payment_example(self):
        uri = (f"zcash:?address={self.TRANSPARENT}&amount=123.456"
               f"&address.1={self.SAPLING}&amount.1=0.789")
        result = kit.parse_uri(uri)
        self.assertEqual([p["amount_zat"] for p in result], [12_345_600_000, 78_900_000])

    def test_official_invalid_forms(self):
        invalid = [
            f"zcash:?amount=1&address.1={self.SAPLING}",
            f"zcash:?address.0={self.SAPLING}&amount.0=2",
            f"zcash:?amount=1&amount=2&address={self.TRANSPARENT}",
            f"zcash:{self.TRANSPARENT}?amount=1%30",
            f"zcash://{self.TRANSPARENT}?amount=1",
            f"zcash:{self.TRANSPARENT}?req-unknown=1",
            f"zcash:{self.TRANSPARENT}?memo=VGhpcyBpcyBh",
            f"zcash:{self.SAPLING}?memo=A",
            f"zcash:{self.SAPLING}?memo=AA_",
            f"zcash:{self.SAPLING}?amount=0.000000001",
            f"zcash:{self.SAPLING}?amount=21000001",
        ]
        for uri in invalid:
            with self.subTest(uri=uri), self.assertRaises(kit.CheckError):
                kit.parse_uri(uri)


class LeakControl(unittest.TestCase):
    def test_planted_leak_and_clean_control(self):
        canary = ROOT / "examples" / "canaries.txt"
        leaked = kit.scan_canaries([ROOT / "examples" / "leaky-app.log"], canary)
        clean = kit.scan_canaries([ROOT / "examples" / "clean-app.log"], canary)
        self.assertEqual(leaked["status"], "fail")
        self.assertEqual(leaked["evidence"]["findings"][0]["line"], 2)
        self.assertEqual(clean["status"], "pass")
        self.assertNotIn("ORDER-DEMO-7F3C9A", str(leaked))


class CiOutcome(unittest.TestCase):
    def test_fail_unverified_and_input_error_exit_codes(self):
        with tempfile.TemporaryDirectory() as directory:
            report = str(Path(directory) / "report.json")
            self.assertEqual(kit.main(["--uri", "zcash:tmEZhbWHTpdKMw5it8YDspUXSMGQyFwovpU?amount=1",
                                       "--report", report]), 1)
            self.assertEqual(kit.main(["--uri", f"zcash:{Zip321Examples.SAPLING}?amount=1",
                                       "--report", report]), 3)
            self.assertEqual(kit.main(["--uri", "zcash://invalid", "--report", report]), 2)

    def test_wallet_outage_still_writes_redacted_unverified_report(self):
        class UnavailableWallet:
            def call(self, method, params=None):
                raise kit.CheckError("secret wallet detail")

        payment = kit.parse_uri(f"zcash:{Zip321Examples.SAPLING}?amount=0.01")[0]
        checks = kit.preflight([payment], UnavailableWallet())
        checks.append(kit.observe(UnavailableWallet(), "a" * 64, payment["amount_zat"], "private-account"))
        kit.annotate_checks(checks)
        self.assertEqual([check["status"] for check in checks], ["unverified", "unverified"])
        self.assertTrue(all(check["evidence_source"] and check["reproduce"] and
                            check["privacy_boundary"] for check in checks))
        self.assertNotIn("secret wallet detail", json.dumps(checks))
        self.assertNotIn("private-account", json.dumps(checks))

        with tempfile.TemporaryDirectory() as directory, patch.object(kit, "WalletRpc", return_value=UnavailableWallet()):
            report = Path(directory) / "report.json"
            exit_code = kit.main(["--uri", f"zcash:{Zip321Examples.SAPLING}?amount=0.01",
                                  "--rpc-url", "http://127.0.0.1:50233",
                                  "--rpc-cookie", str(Path(directory) / "unused-cookie"),
                                  "--account-uuid", "private-account", "--txid", "a" * 64,
                                  "--report", str(report)])
            self.assertEqual(exit_code, 3)
            exported = report.read_text()
            self.assertEqual([c["status"] for c in json.loads(exported)["checks"]],
                             ["unverified", "unverified", "unverified"])
            self.assertNotIn("secret wallet detail", exported)
            self.assertNotIn("private-account", exported)

    def test_request_only_report_carries_check_context(self):
        with tempfile.TemporaryDirectory() as directory:
            report = Path(directory) / "report.json"
            exit_code = kit.main(["--uri", f"zcash:{Zip321Examples.SAPLING}?amount=0.01",
                                  "--canary-file", str(ROOT / "examples" / "canaries.txt"),
                                  "--log", str(ROOT / "examples" / "clean-app.log"),
                                  "--report", str(report)])
            data = json.loads(report.read_text())
            self.assertEqual(exit_code, 3)
            self.assertEqual(data["schema_version"], 2)
            self.assertEqual([c["status"] for c in data["checks"]],
                             ["unverified", "unverified", "pass"])
            self.assertTrue(all("evidence_source" in c and "reproduce" in c and
                                "privacy_boundary" in c for c in data["checks"]))

    def test_incomplete_wallet_tip_cannot_pass_observation(self):
        class IncompleteWallet:
            def call(self, method, params=None):
                if method == "getwalletstatus":
                    return {"node_tip": {}, "wallet_tip": {}}
                raise AssertionError("Transaction view must not run before sync is established")

        check = kit.observe(IncompleteWallet(), "a" * 64, 1_000_000, "account")
        self.assertEqual(check["status"], "unverified")
        self.assertFalse(check["evidence"]["wallet_synced"])


if __name__ == "__main__":
    unittest.main()
