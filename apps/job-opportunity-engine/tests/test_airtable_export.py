from __future__ import annotations

import csv
import json
from pathlib import Path
import tempfile
import unittest

from airtable_export import FIELD_ORDER, build_rows, main
from job_engine import score_jobs

ROOT = Path(__file__).resolve().parents[1]
PROFILE = json.loads((ROOT / "profile.json").read_text(encoding="utf-8"))
JOBS = json.loads((ROOT / "examples" / "sample_jobs.json").read_text(encoding="utf-8"))


class AirtableExportTests(unittest.TestCase):
    def setUp(self):
        self.results = score_jobs(JOBS, PROFILE)
        self.rows = build_rows(
            JOBS,
            self.results,
            engine_version="test-v1",
            scored_at="2026-08-24T23:59:00Z",
        )

    def test_field_order_matches_private_tracker_schema(self):
        self.assertEqual(list(self.rows[0].keys()), FIELD_ORDER)
        self.assertIn("Review Decision", FIELD_ORDER)
        self.assertIn("Requires U.S. Residence", FIELD_ORDER)
        self.assertIn("Last Scored", FIELD_ORDER)

    def test_strong_fit_maps_to_airtable_choice(self):
        row = next(row for row in self.rows if row["ID"] == "synthetic-001")
        self.assertEqual(row["Fit Tier"], "Strong Fit")
        self.assertEqual(row["Review Decision"], "Unreviewed")
        self.assertGreaterEqual(float(row["Fit Score"]), 85)

    def test_us_residence_and_review_flags_are_preserved(self):
        row = next(row for row in self.rows if row["ID"] == "synthetic-002")
        self.assertEqual(row["Requires U.S. Residence"], "1")
        self.assertIn("U.S. residence", row["Review Flags"])

    def test_blocked_role_maps_to_blocked_choice(self):
        row = next(row for row in self.rows if row["ID"] == "synthetic-003")
        self.assertEqual(row["Fit Tier"], "Blocked")
        self.assertTrue(row["Blockers"])

    def test_cli_writes_import_ready_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            result_file = Path(directory) / "results.json"
            output_file = Path(directory) / "airtable.csv"
            result_file.write_text(json.dumps({"results": self.results}), encoding="utf-8")
            code = main([
                "--jobs", str(ROOT / "examples" / "sample_jobs.json"),
                "--results", str(result_file),
                "--output", str(output_file),
                "--engine-version", "test-v1",
                "--scored-at", "2026-08-24T23:59:00Z",
            ])
            self.assertEqual(code, 0)
            with output_file.open(encoding="utf-8-sig", newline="") as handle:
                rows = list(csv.DictReader(handle))
            self.assertEqual(len(rows), len(JOBS))
            self.assertEqual(list(rows[0].keys()), FIELD_ORDER)
            self.assertEqual(rows[0]["Engine Version"], "test-v1")

    def test_missing_original_job_is_rejected(self):
        with self.assertRaisesRegex(ValueError, "No original job record"):
            build_rows(JOBS[:-1], self.results, engine_version="test-v1")


if __name__ == "__main__":
    unittest.main()
