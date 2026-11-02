import csv
import io
import json
import subprocess
import sys
import tempfile
import unittest
from datetime import date
from pathlib import Path

from vlt import analyse, load
from vlt.report import issues_csv, to_markdown

ROOT = Path(__file__).resolve().parent.parent
SAMPLE = ROOT / "examples" / "sample_vendors.json"
AS_OF = date(2026, 10, 23)
EXPECTED = {
    ("V001", "GO_LIVE_WITHOUT_APPROVAL"), ("V001", "DUE_DILIGENCE_INCOMPLETE"), ("V001", "REASSESSMENT_OVERDUE"), ("V001", "SKIPPED_GATE"),
    ("V002", "GO_LIVE_WITHOUT_APPROVAL"), ("V003", "REASSESSMENT_OVERDUE"), ("V004", "TIER_MISSING"), ("V005", "STALLED_STAGE"),
    ("V006", "OFFBOARD_ACCESS_LINGERING"), ("V006", "OFFBOARD_INCOMPLETE"), ("V007", "OFFBOARD_INCOMPLETE"),
    ("V008", "OFFBOARD_ACCESS_LINGERING"), ("V008", "STALLED_STAGE"), ("V009", "INVALID_TRANSITION"), ("V010", "DUE_DILIGENCE_INCOMPLETE"),
}


class TestSample(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.vendors = load(SAMPLE)
        cls.res = analyse(cls.vendors, as_of=AS_OF)

    def test_finds_exactly_the_injected_problems(self):
        got = {(i["vendor"], i["check"]) for i in self.res["issues"]}
        self.assertEqual(got - EXPECTED, set(), "false positives")
        self.assertEqual(EXPECTED - got, set(), "missed")

    def test_clean_filler_vendors_are_quiet(self):
        self.assertEqual({i["vendor"] for i in self.res["issues"] if i["vendor"] > "V010"}, set())

    def test_sorted_by_severity(self):
        order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        s = [order[i["severity"]] for i in self.res["issues"]]
        self.assertEqual(s, sorted(s))

    def test_pipeline_counts(self):
        self.assertEqual(sum(self.res["pipeline"].values()), 30)
        self.assertEqual(self.res["pipeline"]["offboarded"], 2)

    def test_outputs(self):
        self.assertEqual(len(list(csv.reader(io.StringIO(issues_csv(self.res))))), len(EXPECTED) + 1)
        self.assertIn("## Pipeline", to_markdown(self.res, self.vendors))


class TestCli(unittest.TestCase):
    def run_cli(self, *a):
        return subprocess.run([sys.executable, "-m", "vlt", *a], cwd=ROOT, capture_output=True, text=True)

    def test_writes_files(self):
        with tempfile.TemporaryDirectory() as d:
            r = self.run_cli(str(SAMPLE), "--as-of", "2026-10-23", "--out-dir", d)
            self.assertEqual(r.returncode, 0, r.stderr)
            self.assertEqual(len(json.loads((Path(d) / "report.json").read_text())["issues"]), len(EXPECTED))

    def test_exit_codes(self):
        self.assertEqual(self.run_cli(str(SAMPLE), "--as-of", "2026-10-23", "--fail-on", "critical").returncode, 1)
        self.assertEqual(self.run_cli("nope.json").returncode, 2)
        self.assertEqual(self.run_cli(str(SAMPLE), "--as-of", "later").returncode, 2)
        with tempfile.TemporaryDirectory() as d:
            p = Path(d) / "v.json"
            p.write_text(json.dumps([{"id": "A", "name": "a", "stage": "active", "history": [{"stage": "intake", "date": "2025-01-01"}]}]))
            r = self.run_cli(str(p))
            self.assertEqual(r.returncode, 2)
            self.assertIn("history must end", r.stderr)


if __name__ == "__main__":
    unittest.main()
