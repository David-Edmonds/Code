#!/usr/bin/env python3
"""Transparent scoring for remote analytics job opportunities."""

from __future__ import annotations

import argparse
import csv
from datetime import date, datetime
import json
import math
from pathlib import Path
import re
import sys
from typing import Any, Iterable, Mapping

ANNUAL_HOURS = 2080


def text(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").strip().lower())


def combined(job: Mapping[str, Any]) -> str:
    return text(" ".join(str(job.get(k) or "") for k in ("title", "company", "location", "description", "employment_type")))


def has_phrase(haystack: str, phrase: Any) -> bool:
    needle = text(phrase)
    if not needle:
        return False
    if re.fullmatch(r"[a-z0-9+#.]+", needle):
        return bool(re.search(rf"(?<![a-z0-9]){re.escape(needle)}(?![a-z0-9])", haystack))
    return needle in haystack


def as_bool(value: Any) -> bool | None:
    if isinstance(value, bool):
        return value
    value = text(value)
    if value in {"true", "yes", "y", "1", "remote"}:
        return True
    if value in {"false", "no", "n", "0", "onsite", "on-site", "hybrid"}:
        return False
    return None


def as_float(value: Any) -> float | None:
    if value in (None, ""):
        return None
    try:
        number = float(str(value).replace(",", "").replace("$", "").strip())
    except (TypeError, ValueError):
        return None
    return number if math.isfinite(number) and number >= 0 else None


def annual_salary(value: Any, period: Any) -> float | None:
    number = as_float(value)
    if number is None:
        return None
    period = text(period) or "annual"
    if period in {"hour", "hourly", "per hour", "hr"}:
        return number * ANNUAL_HOURS
    if period in {"month", "monthly", "per month"}:
        return number * 12
    if period in {"week", "weekly", "per week"}:
        return number * 52
    return number


def add_component(components: dict[str, Any], name: str, earned: float, possible: float, reasons: list[str]) -> None:
    components[name] = {"earned": round(earned, 1), "possible": possible, "reasons": reasons}


def score_job(job: Mapping[str, Any], profile: Mapping[str, Any]) -> dict[str, Any]:
    if not isinstance(job, Mapping) or not isinstance(profile, Mapping):
        raise TypeError("job and profile must be mappings")

    components: dict[str, Any] = {}
    blockers: list[str] = []
    flags: list[str] = []
    job_text = combined(job)

    remote = as_bool(job.get("remote"))
    location = text(job.get("location"))
    if remote is None and "remote" in location:
        remote = True
    elif remote is None and any(term in location for term in ("hybrid", "onsite", "on-site")):
        remote = False
    if remote is True:
        remote_points, remote_reasons = 25.0, ["Role is explicitly remote."]
    elif remote is False:
        remote_points, remote_reasons = 0.0, ["Role is not fully remote."]
        if profile.get("remote_required", True):
            blockers.append("Remote-only requirement is not met.")
    else:
        remote_points, remote_reasons = 10.0, ["Remote status is not explicit."]
        flags.append("Confirm that the role is fully remote.")

    us_residence = as_bool(job.get("requires_us_residence"))
    if us_residence is None:
        us_residence = any(p in job_text for p in (
            "must reside in the united states", "must reside in the u.s.",
            "must be based in the united states", "us-based remote", "u.s.-based remote",
        ))
    state_residence = as_bool(job.get("requires_specific_state"))
    if us_residence:
        remote_points = max(0.0, remote_points - 5)
        flags.append("Employer requires U.S. residence; verify current physical-location eligibility.")
    if state_residence:
        remote_points = max(0.0, remote_points - 5)
        flags.append("Role has a state-residence requirement; verify eligibility before applying.")
    if profile.get("cross_border_review_required", True):
        flags.append("Verify employer payroll, tax, and work-location rules before treating remote eligibility as confirmed.")
    add_component(components, "remote_location", remote_points, 25, remote_reasons)

    title = text(job.get("title"))
    targets = [text(v) for v in profile.get("target_titles", [])]
    exact = next((target for target in targets if target and target in title), None)
    if exact:
        title_points, title_reasons = 20.0, [f"Title matches target family: {exact}."]
    elif any(term in title for term in ("data analyst", "business intelligence", "bi analyst", "analytics consultant", "reporting analyst", "insights analyst", "operations analyst", "sales operations", "revenue operations")):
        title_points, title_reasons = 16.0, ["Title is in a closely related analytics family."]
    elif "analyst" in title or "analytics" in title:
        title_points, title_reasons = 11.0, ["Title is broadly analytical but not an exact target."]
    else:
        title_points, title_reasons = 3.0, ["Title has weak alignment with target roles."]
    if any(term in title for term in ("senior", "sr.", "sr ", "lead")):
        title_points = min(20.0, title_points + 2)
        title_reasons.append("Seniority aligns with the target level.")
    if any(term in title for term in ("director", "vice president", "vp ")):
        title_points = max(0.0, title_points - 4)
        title_reasons.append("Title may be above the intended hands-on level.")
    add_component(components, "title_fit", title_points, 20, title_reasons)

    weights = profile.get("skill_weights", {})
    total_weight = sum(as_float(v) or 0 for v in weights.values()) if isinstance(weights, Mapping) else 0
    matched = [str(skill) for skill in weights if has_phrase(job_text, skill)] if isinstance(weights, Mapping) else []
    matched_weight = sum(as_float(weights[s]) or 0 for s in matched) if isinstance(weights, Mapping) else 0
    skills_points = 20 * matched_weight / total_weight if total_weight else 0
    skills_reason = f"Matched skills: {', '.join(matched)}." if matched else "No configured priority skills were found."
    add_component(components, "skills_fit", skills_points, 20, [skills_reason])

    floor = float(profile.get("minimum_salary_usd", 80000))
    preferred = float(profile.get("preferred_salary_usd", floor))
    minimum = annual_salary(job.get("salary_min"), job.get("salary_period"))
    maximum = annual_salary(job.get("salary_max"), job.get("salary_period"))
    currency = text(job.get("currency")) or "usd"
    if currency not in {"usd", "us dollars", "$"}:
        pay_points, pay_reasons = 4.0, ["Compensation is not stated in USD."]
        flags.append("Convert compensation to USD and verify employment classification.")
    elif minimum is None and maximum is None:
        pay_points, pay_reasons = 5.0, ["Compensation is not listed."]
        flags.append("Confirm base compensation before investing significant application time.")
    elif maximum is not None and maximum < floor:
        pay_points, pay_reasons = 0.0, [f"Maximum annualized compensation is below the ${floor:,.0f} floor."]
        blockers.append("Compensation ceiling is below the configured minimum.")
    elif minimum is not None and minimum >= preferred:
        pay_points, pay_reasons = 15.0, [f"Minimum annualized compensation meets the ${preferred:,.0f} preferred level."]
    elif minimum is not None and minimum >= floor:
        pay_points, pay_reasons = 13.0, [f"Minimum annualized compensation meets the ${floor:,.0f} floor."]
    elif maximum is not None and maximum >= floor:
        pay_points, pay_reasons = 9.0, ["Range can meet the floor, but its lower end is below target."]
        flags.append("Confirm likely offer position within the compensation range.")
    else:
        pay_points, pay_reasons = 4.0, ["Compensation data is incomplete or ambiguous."]
        flags.append("Confirm base compensation and whether bonuses are included.")
    add_component(components, "compensation_fit", pay_points, 15, pay_reasons)

    groups = profile.get("responsibility_groups", {})
    matched_groups: list[str] = []
    if isinstance(groups, Mapping):
        for group, phrases in groups.items():
            phrases = [phrases] if isinstance(phrases, str) else phrases
            if any(has_phrase(job_text, phrase) for phrase in phrases):
                matched_groups.append(str(group))
    responsibility_points = min(10.0, 10 * len(matched_groups) / max(1, len(groups))) if isinstance(groups, Mapping) else 0
    responsibility_reason = f"Matched responsibility areas: {', '.join(matched_groups)}." if matched_groups else "Few target analytics responsibilities were found."
    add_component(components, "responsibility_fit", responsibility_points, 10, [responsibility_reason])

    if profile.get("work_authorized_us", True) and not profile.get("sponsorship_needed", False):
        auth_points, auth_reasons = 5.0, ["Profile has U.S. work authorization and does not require sponsorship."]
    else:
        sponsorship = as_bool(job.get("sponsorship_available"))
        auth_points = 5.0 if sponsorship else 0.0 if sponsorship is False else 2.0
        auth_reasons = ["Sponsorship information was evaluated against the profile."]
    if "security clearance" in job_text or "clearance required" in job_text:
        flags.append("Verify whether an active clearance is required; prior clearance history is not current access.")
    add_component(components, "authorization_fit", auth_points, 5, auth_reasons)

    completeness = {
        "title": bool(title), "company": bool(text(job.get("company"))),
        "description": len(text(job.get("description"))) >= 80,
        "remote status": remote is not None or bool(location),
        "compensation": minimum is not None or maximum is not None,
    }
    completeness_points = float(sum(completeness.values()))
    missing = [name for name, present in completeness.items() if not present]
    add_component(components, "data_completeness", completeness_points, 5, ["Core posting fields are present." if not missing else f"Missing or weak fields: {', '.join(missing)}."])

    for phrase in profile.get("hard_block_phrases", []):
        if has_phrase(job_text, phrase):
            blockers.append(f"Posting contains blocked phrase: {phrase}.")
    risk_penalty = 0.0
    for phrase in profile.get("risk_phrases", []):
        if has_phrase(job_text, phrase):
            flags.append(f"Review risk phrase before proceeding: {phrase}.")
            risk_penalty += 3
    allowed = {text(v) for v in profile.get("allowed_employment_types", [])}
    employment = text(job.get("employment_type"))
    if employment and allowed and employment not in allowed:
        flags.append(f"Employment type '{employment}' is outside the preferred set.")
        risk_penalty += 2
    risk_penalty = min(risk_penalty, 10)

    posted = job.get("posted_date")
    if not posted:
        flags.append("Posting date is missing; confirm the opportunity is still active.")
    else:
        try:
            age = (date.today() - datetime.strptime(str(posted)[:10], "%Y-%m-%d").date()).days
            if age > 30:
                flags.append(f"Posting is {age} days old; confirm it is still active.")
        except ValueError:
            flags.append("Posting date is not in YYYY-MM-DD format.")

    raw_score = sum(float(v["earned"]) for v in components.values()) - risk_penalty
    score = max(0.0, min(100.0, raw_score))
    if blockers:
        score, fit = min(score, 49.0), "blocked"
    elif score >= 85:
        fit = "strong_fit"
    elif score >= 70:
        fit = "good_fit"
    elif score >= 55:
        fit = "review"
    else:
        fit = "low_fit"

    reasons = [reason for component in components.values() for reason in component["reasons"]]
    if risk_penalty:
        reasons.append(f"Risk penalty applied: -{risk_penalty:.0f} points.")
    return {
        "id": job.get("id"), "title": job.get("title"), "company": job.get("company"),
        "score": round(score, 1), "fit": fit, "blocked": bool(blockers),
        "blockers": list(dict.fromkeys(blockers)), "review_flags": list(dict.fromkeys(flags)),
        "reasons": reasons, "component_scores": components, "source_url": job.get("source_url"),
    }


def score_jobs(jobs: Iterable[Mapping[str, Any]], profile: Mapping[str, Any]) -> list[dict[str, Any]]:
    return sorted((score_job(job, profile) for job in jobs), key=lambda r: (-float(r["score"]), text(r.get("company")), text(r.get("title"))))


def load_json(path: Path) -> Any:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"File not found: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"Invalid JSON in {path}: {exc}") from exc


def load_jobs(path: Path) -> list[dict[str, Any]]:
    if path.suffix.lower() == ".csv":
        with path.open("r", encoding="utf-8-sig", newline="") as handle:
            return [dict(row) for row in csv.DictReader(handle)]
    data = load_json(path)
    if isinstance(data, dict):
        data = data.get("jobs")
    if not isinstance(data, list) or not all(isinstance(v, dict) for v in data):
        raise ValueError("Input must be a JSON array, {'jobs': [...]}, or CSV file.")
    return data


def write_csv(path: Path, results: list[dict[str, Any]]) -> None:
    fields = ["rank", "score", "fit", "blocked", "company", "title", "blockers", "review_flags", "source_url"]
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fields)
        writer.writeheader()
        for rank, result in enumerate(results, 1):
            writer.writerow({
                "rank": rank, "score": result["score"], "fit": result["fit"], "blocked": result["blocked"],
                "company": result.get("company"), "title": result.get("title"),
                "blockers": " | ".join(result["blockers"]), "review_flags": " | ".join(result["review_flags"]),
                "source_url": result.get("source_url"),
            })


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Score remote analytics jobs against explicit criteria.")
    parser.add_argument("--profile", required=True, type=Path)
    parser.add_argument("--input", required=True, type=Path)
    parser.add_argument("--output", type=Path)
    parser.add_argument("--csv", type=Path)
    parser.add_argument("--min-score", type=float, default=0)
    args = parser.parse_args(argv)
    try:
        profile = load_json(args.profile)
        if not isinstance(profile, dict):
            raise ValueError("Profile JSON must be an object.")
        results = [r for r in score_jobs(load_jobs(args.input), profile) if r["score"] >= args.min_score]
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    payload = {"profile_version": profile.get("version"), "result_count": len(results), "results": results}
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    if args.csv:
        write_csv(args.csv, results)
    for rank, result in enumerate(results, 1):
        marker = "BLOCKED" if result["blocked"] else result["fit"].replace("_", " ").upper()
        print(f"{rank:>2}. {result['score']:>5.1f}  {marker:<11}  {result['title']} — {result['company']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
