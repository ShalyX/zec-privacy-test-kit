import importlib.util
import tempfile
import unittest
from pathlib import Path


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


if __name__ == "__main__":
    unittest.main()
