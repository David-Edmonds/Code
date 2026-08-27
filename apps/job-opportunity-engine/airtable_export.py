#!/usr/bin/env python3
"""Create an Airtable-import-ready CSV from scored job opportunities.

This module intentionally performs no network requests. It joins the original
job records with deterministic Job Opportunity Engine results and writes a CSV
whose headers match the private Application Tracker table.
"""

from __future__ import annotations

import argparse
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import sys
from typing import Any, Mapping

from job_engine import as_bool, load_jobs

FIT_LABELS = {
    "strong_fit": "Strong Fit",
    "good_fit": "Good Fit",
    "review": "Review",
    "low_fit": "Low Fit",
    "blocked": "Blocked",
}

FIELD_ORDER = [
    "ID",
    "Company",
    "Job Title",
    "Location",
    "Remote",
    "Employment Type",
    "Salary Range",
    "Salary Min",
    "Salary Max",
    "Salary Period",
    "Currency",
    "Posted Date",
    "Source",
    "Source URL",
    "Description",
    "Fit Score",
    "Fit Tier",
    "Review Decision",
    "Requires U.S. Residence",
    "Requires Specific State",
    "Blockers",
    "Review Flags",
    "Scoring Reasons",
    "Engine Version",
    "Last Scored",
]


def load_results(path: Path) -> list[dict[str, Any]]:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"Results file not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc

    results = payload.get("results") if isinstance(payload, dict) else payload
    if not isinstance(results, list) or not all(isinstance(row, dict) for row in results):
        raise ValueError("Results must be a JSON array or an object containing a results array.")
    return results


def normalize_choice(value: Any, choices: Mapping[str, str]) -> str:
    key = str(value or "").strip().lower().replace("_", "-")
    return choices.get(key, str(value or "").strip())


def employment_type(value: Any) -> str:
    return normalize_choice(
        value,
        {
            "full-time": "Full-time",
            "full time": "Full-time",
            "contract": "Contract",
            "contract-to-hire": "Contract-to-hire",
            "contract to hire": "Contract-to-hire",
            "part-time": "Part-time",
            "part time": "Part-time",
        },
    ) or "Other"


def salary_period(value: Any) -> str:
    normalized = str(value or "").strip().lower()
    return {
        "annual": "Annual",
        "annually": "Annual",
        "year": "Annual",
        "yearly": "Annual",
        "hour": "Hourly",
        "hourly": "Hourly",
        "hr": "Hourly",
        "month": "Monthly",
        "monthly": "Monthly",
        "week": "Weekly",
        "weekly": "Weekly",
    }.get(normalized, "")


def checkbox(value: Any) -> str:
    parsed = as_bool(value)
    return "1" if parsed is True else "0"


def display_salary(job: Mapping[str, Any]) -> str:
    minimum = job.get("salary_min")
    maximum = job.get("salary_max")
    if minimum in (None, "") and maximum in (None, ""):
        return ""
    currency = str(job.get("currency") or "USD").upper()
    period = salary_period(job.get("salary_period"))
    period_suffix = {
        "Annual": "/year",
        "Hourly": "/hour",
        "Monthly": "/month",
        "Weekly": "/week",
    }.get(period, "")

    def fmt(value: Any) -> str:
        if value in (None, ""):
            return ""
        try:
            number = float(str(value).replace(",", "").replace("$", ""))
        except (TypeError, ValueError):
            return str(value)
        return f"${number:,.0f}" if currency == "USD" else f"{number:,.0f} {currency}"

    low, high = fmt(minimum), fmt(maximum)
    if low and high:
        return f"{low}–{high}{period_suffix}"
    return f"{low or high}{period_suffix}"


def join_lines(values: Any) -> str:
    if values is None:
        return ""
    if isinstance(values, str):
        return values.strip()
    if isinstance(values, list):
        return "\n".join(str(value).strip() for value in values if str(value).strip())
    return str(values).strip()


def build_rows(
    jobs: list[dict[str, Any]],
    results: list[dict[str, Any]],
    *,
    engine_version: str,
    scored_at: str | None = None,
) -> list[dict[str, Any]]:
    jobs_with_ids = [job for job in jobs if job.get("id") not in (None, "")]
    jobs_by_id = {str(job.get("id")): job for job in jobs_with_ids}
    if len(jobs_by_id) != len(jobs_with_ids):
        raise ValueError("Job IDs must be unique before export.")

    timestamp = scored_at or datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    rows: list[dict[str, Any]] = []
    for result in results:
        job_id = str(result.get("id") or "")
        if not job_id:
            raise ValueError("Every scored result must include an id.")
        job = jobs_by_id.get(job_id)
        if job is None:
            raise ValueError(f"No original job record found for scored result id: {job_id}")

        currency = str(job.get("currency") or "USD").upper()
        if currency != "USD":
            currency = "Other"

        fit_key = str(result.get("fit") or "").strip().lower()
        fit_label = FIT_LABELS.get(fit_key)
        if not fit_label:
            raise ValueError(f"Unknown fit value for {job_id}: {fit_key}")

        row = {
            "ID": job_id,
            "Company": job.get("company") or result.get("company") or "",
            "Job Title": job.get("title") or result.get("title") or "",
            "Location": job.get("location") or "",
            "Remote": checkbox(job.get("remote")),
            "Employment Type": employment_type(job.get("employment_type")),
            "Salary Range": display_salary(job),
            "Salary Min": job.get("salary_min") if job.get("salary_min") not in (None, "") else "",
            "Salary Max": job.get("salary_max") if job.get("salary_max") not in (None, "") else "",
            "Salary Period": salary_period(job.get("salary_period")),
            "Currency": currency,
            "Posted Date": job.get("posted_date") or "",
            "Source": job.get("source") or "",
            "Source URL": job.get("source_url") or result.get("source_url") or "",
            "Description": job.get("description") or "",
            "Fit Score": result.get("score") if result.get("score") is not None else "",
            "Fit Tier": fit_label,
            "Review Decision": "Unreviewed",
            "Requires U.S. Residence": checkbox(job.get("requires_us_residence")),
            "Requires Specific State": checkbox(job.get("requires_specific_state")),
            "Blockers": join_lines(result.get("blockers")),
            "Review Flags": join_lines(result.get("review_flags")),
            "Scoring Reasons": join_lines(result.get("reasons")),
            "Engine Version": engine_version,
            "Last Scored": timestamp,
        }
        rows.append(row)
    return rows


def write_airtable_csv(path: Path, rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELD_ORDER, extrasaction="ignore")
        writer.writeheader()
        writer.writerows(rows)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Create an Airtable-import-ready review queue CSV.")
    parser.add_argument("--jobs", required=True, type=Path, help="Original jobs JSON or CSV")
    parser.add_argument("--results", required=True, type=Path, help="Job Opportunity Engine results JSON")
    parser.add_argument("--output", required=True, type=Path, help="Destination CSV")
    parser.add_argument("--engine-version", default="job-opportunity-engine-v1")
    parser.add_argument("--scored-at", help="Optional ISO timestamp for reproducible exports")
    args = parser.parse_args(argv)

    try:
        rows = build_rows(
            load_jobs(args.jobs),
            load_results(args.results),
            engine_version=args.engine_version,
            scored_at=args.scored_at,
        )
        write_airtable_csv(args.output, rows)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    print(f"Wrote {len(rows)} Airtable review rows to {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
