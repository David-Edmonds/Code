#!/usr/bin/env python3
"""Validate the public-safe David AI Build Lab repository."""

from __future__ import annotations

import csv
import hashlib
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

REQUIRED_FILES = {
    "README.md",
    "AGENTS.md",
    "CURRENT_CONTEXT.md",
    "DECISIONS.md",
    "BACKLOG.md",
    "AUTOMATION_MAP.md",
    "project-registry.json",
    "projects/david-analytics-lab.md",
    "projects/job-opportunity-engine.md",
    "projects/social-content-os.md",
    "job-engine/README.md",
    "job-engine/PRIVACY.md",
    "templates/app-brief.md",
    "templates/codex-task.md",
    "templates/content-operations.csv",
    "templates/decision-log.md",
    "templates/product-backlog.csv",
    "templates/release-checklist.md",
}

FORBIDDEN_FILE_PATTERNS = (
    # Allow documentation-only templates such as .env.example, while blocking
    # real environment files such as .env, .env.local, and .env.production.
    re.compile(
        r"(^|/)\.env(?:$|\.(?!example$|sample$|template$)[^/]+$)",
        re.IGNORECASE,
    ),
    re.compile(r"\.(pem|key|p12|pfx|pbix)$", re.IGNORECASE),
)

SECRET_PATTERNS = {
    "AWS access key": re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    "GitHub token": re.compile(r"\bgh[pousr]_[A-Za-z0-9]{20,}\b"),
    "OpenAI-style secret": re.compile(r"\bsk-[A-Za-z0-9_-]{20,}\b"),
    "private key": re.compile(
        r"-----BEGIN (?:RSA |OPENSSH |EC |DSA )?PRIVATE KEY-----"
    ),
}

REQUIRED_CONFIA_TEXT = "Confia Solutions, LLC"
REQUIRED_JOB_PRIVACY_TEXT = "private"


def fail(message: str, errors: list[str]) -> None:
    errors.append(message)


def repository_files() -> list[Path]:
    excluded = {".git", "__pycache__"}
    return sorted(
        path
        for path in ROOT.rglob("*")
        if path.is_file() and not any(part in excluded for part in path.parts)
    )


def validate_required_files(errors: list[str]) -> None:
    for relative in sorted(REQUIRED_FILES):
        if not (ROOT / relative).is_file():
            fail(f"Missing required file: {relative}", errors)


def validate_registry(errors: list[str]) -> None:
    path = ROOT / "project-registry.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        fail(f"project-registry.json is invalid: {exc}", errors)
        return

    if payload.get("version") != 1:
        fail("project-registry.json must use version 1", errors)

    projects = payload.get("projects")
    if not isinstance(projects, list) or not projects:
        fail("project-registry.json must contain a non-empty projects list", errors)
        return

    ids: set[str] = set()
    priorities: set[int] = set()
    for index, project in enumerate(projects, start=1):
        if not isinstance(project, dict):
            fail(f"Project #{index} must be an object", errors)
            continue
        for field in ("id", "name", "status", "priority", "next_action"):
            if project.get(field) in (None, ""):
                fail(f"Project #{index} is missing {field}", errors)
        project_id = project.get("id")
        if isinstance(project_id, str):
            if project_id in ids:
                fail(f"Duplicate project id: {project_id}", errors)
            ids.add(project_id)
        priority = project.get("priority")
        if isinstance(priority, int):
            if priority in priorities:
                fail(f"Duplicate project priority: {priority}", errors)
            priorities.add(priority)
        else:
            fail(f"Project #{index} priority must be an integer", errors)


def validate_csv_templates(errors: list[str]) -> None:
    for path in sorted((ROOT / "templates").glob("*.csv")):
        try:
            with path.open(newline="", encoding="utf-8") as handle:
                rows = list(csv.reader(handle))
        except (OSError, csv.Error) as exc:
            fail(f"Invalid CSV template {path.relative_to(ROOT)}: {exc}", errors)
            continue

        if len(rows) != 1:
            fail(
                f"CSV template {path.relative_to(ROOT)} should contain one header row",
                errors,
            )
            continue

        headers = [header.strip() for header in rows[0]]
        if not headers or any(not header for header in headers):
            fail(f"CSV template {path.relative_to(ROOT)} has an empty header", errors)
        if len(headers) != len(set(headers)):
            fail(f"CSV template {path.relative_to(ROOT)} has duplicate headers", errors)


def validate_paths(files: list[Path], errors: list[str]) -> None:
    for path in files:
        relative = path.relative_to(ROOT).as_posix()
        for pattern in FORBIDDEN_FILE_PATTERNS:
            if pattern.search(relative):
                fail(f"Forbidden public file type or path: {relative}", errors)


def validate_text(files: list[Path], errors: list[str]) -> None:
    text_extensions = {
        ".md",
        ".txt",
        ".json",
        ".yml",
        ".yaml",
        ".csv",
        ".py",
        ".js",
        ".mjs",
        ".ts",
        ".tsx",
        ".html",
        ".css",
        ".toml",
        ".ini",
        ".cfg",
        ".sh",
        ".example",
        ".sample",
        ".template",
    }
    for path in files:
        if path.suffix.lower() not in text_extensions:
            continue
        relative = path.relative_to(ROOT).as_posix()
        try:
            raw = path.read_bytes()
            text = raw.decode("utf-8")
        except OSError as exc:
            fail(f"Unable to read text file {relative}: {exc}", errors)
            continue
        except UnicodeDecodeError:
            fail(f"Text file is not valid UTF-8: {relative}", errors)
            continue

        if b"\r\n" in raw:
            fail(f"Text file uses CRLF line endings: {relative}", errors)
        for name, pattern in SECRET_PATTERNS.items():
            if pattern.search(text):
                fail(f"Possible {name} found in {relative}", errors)
        for number, line in enumerate(text.splitlines(), start=1):
            if line.rstrip() != line:
                fail(f"Trailing whitespace in {relative}:{number}", errors)


def validate_truth_and_privacy(errors: list[str]) -> None:
    context = (ROOT / "CURRENT_CONTEXT.md").read_text(encoding="utf-8")
    decisions = (ROOT / "DECISIONS.md").read_text(encoding="utf-8")
    agents = (ROOT / "AGENTS.md").read_text(encoding="utf-8")
    job_privacy = (ROOT / "job-engine/PRIVACY.md").read_text(encoding="utf-8")

    for relative, text in (
        ("CURRENT_CONTEXT.md", context),
        ("DECISIONS.md", decisions),
        ("AGENTS.md", agents),
    ):
        if REQUIRED_CONFIA_TEXT not in text:
            fail(f"Approved Confia association missing from {relative}", errors)

    if REQUIRED_JOB_PRIVACY_TEXT not in job_privacy.lower():
        fail("Job Opportunity Engine privacy boundary is missing", errors)
    if "never submit" not in job_privacy.lower():
        fail("Job Opportunity Engine no-auto-application guardrail is missing", errors)


def validate_internal_markdown_links(files: list[Path], errors: list[str]) -> None:
    link_pattern = re.compile(r"\[[^\]]+\]\(([^)]+)\)")
    for path in files:
        if path.suffix.lower() != ".md":
            continue
        text = path.read_text(encoding="utf-8")
        for target in link_pattern.findall(text):
            target = target.strip()
            if not target or target.startswith(("http://", "https://", "mailto:", "#")):
                continue
            clean_target = target.split("#", 1)[0]
            if not clean_target:
                continue
            resolved = (path.parent / clean_target).resolve()
            try:
                resolved.relative_to(ROOT.resolve())
            except ValueError:
                fail(
                    f"Markdown link escapes repository in {path.relative_to(ROOT)}: {target}",
                    errors,
                )
                continue
            if not resolved.exists():
                fail(
                    f"Broken Markdown link in {path.relative_to(ROOT)}: {target}",
                    errors,
                )


def main() -> int:
    errors: list[str] = []
    files = repository_files()

    validate_required_files(errors)
    validate_registry(errors)
    validate_csv_templates(errors)
    validate_paths(files, errors)
    validate_text(files, errors)
    validate_truth_and_privacy(errors)
    validate_internal_markdown_links(files, errors)

    if errors:
        print("Build Lab validation failed:", file=sys.stderr)
        for error in errors:
            print(f"- {error}", file=sys.stderr)
        return 1

    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(ROOT).as_posix().encode("utf-8"))
        digest.update(path.read_bytes())

    print(f"Build Lab validation passed for {len(files)} files.")
    print(f"Repository content digest: {digest.hexdigest()[:16]}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
