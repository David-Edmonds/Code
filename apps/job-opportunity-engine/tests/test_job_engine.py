from __future__ import annotations

import json
from pathlib import Path
import tempfile
import unittest

from job_engine import main, score_job, score_jobs

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
JOBS = json.loads((ROOT / "examples/sample_jobs.json").read_text(encoding="utf-8"))


class EngineTests(unittest.TestCase):
    def test_strong_bi_role(self):
        result = score_job(JOBS[0], PROFILE)
        self.assertGreaterEqual(result["score"], 85)
        self.assertEqual(result["fit"], "strong_fit")
        self.assertFalse(result["blocked"])

    def test_residence_requirement_is_flagged_not_assumed(self):
        result = score_job(JOBS[1], PROFILE)
        self.assertFalse(result["blocked"])
        self.assertTrue(any("U.S. residence" in flag for flag in result["review_flags"]))

    def test_data_entry_and_low_salary_are_blocked(self):
        result = score_job(JOBS[2], PROFILE)
        self.assertTrue(result["blocked"])
        self.assertEqual(result["fit"], "blocked")
        self.assertLessEqual(result["score"], 49)

    def test_non_remote_role_is_blocked(self):
        result = score_job(JOBS[3], PROFILE)
        self.assertTrue(result["blocked"])
        self.assertTrue(any("remote-only" in blocker.lower() for blocker in result["blockers"]))

    def test_unknown_salary_gets_review_flag(self):
        result = score_job(JOBS[4], PROFILE)
        self.assertFalse(result["blocked"])
        self.assertTrue(any("compensation" in flag.lower() for flag in result["review_flags"]))

    def test_results_are_ranked(self):
        results = score_jobs(JOBS, PROFILE)
        self.assertEqual(results[0]["id"], "synthetic-001")
        self.assertEqual([r["score"] for r in results], sorted((r["score"] for r in results), reverse=True))

    def test_cli_writes_json_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            output = Path(directory) / "results.json"
            csv_output = Path(directory) / "results.csv"
            code = main([
                "--profile", str(ROOT / "profile.json"),
                "--input", str(ROOT / "examples/sample_jobs.json"),
                "--output", str(output),
                "--csv", str(csv_output),
            ])
            self.assertEqual(code, 0)
            self.assertEqual(json.loads(output.read_text())["result_count"], len(JOBS))
            self.assertIn("rank,score,fit", csv_output.read_text())


if __name__ == "__main__":
    unittest.main()
