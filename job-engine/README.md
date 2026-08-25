# Job Opportunity Engine v1

A review-first system for finding and prioritizing high-fit remote analytics roles without submitting applications automatically.

## Public repository scope

This folder documents the product design, public-safe scoring framework, synthetic test cases, and reusable code patterns. Private preferences, saved-role results, application history, tailored answers, credentials, and digests belong in a private implementation.

## Workflow

1. Read only approved public job feeds or APIs.
2. Normalize company, title, salary, location, posting date, source, and URL.
3. Deduplicate by canonical company, title, location, and source URL.
4. Apply hard eligibility gates before scoring.
5. Score role fit and provide a short evidence-based explanation.
6. Deliver a private review digest.
7. Require David's approval before resume tailoring or application preparation.
8. Never submit an application, accept legal attestations, or contact an employer automatically.

## Hard gates

- Remote eligibility must be compatible with a U.S. citizen applying for U.S. remote work while temporarily abroad.
- The role must be relevant to data analytics, BI, operations analytics, sales operations analytics, reporting, or a closely related area.
- Any salary information must meet the configured private floor unless the role is explicitly marked for manual review.
- Clearance, residency, timezone, travel, sponsorship, and location restrictions must be surfaced rather than guessed.

## Private implementation requirement

The scheduled workflow should be created only after a private repository or private system of record is connected. GitHub Actions logs, artifacts, issues, and generated reports in a public repository are public and are not an acceptable delivery channel for the user's private job search.
