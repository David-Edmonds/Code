# Current Status

_Last updated: August 24, 2026_

This is the newest project-status snapshot. Historical context and decisions remain in `CURRENT_CONTEXT.md` and `DECISIONS.md`.

## Released and verified

### David Analytics Lab

- Portfolio foundation and Confia Solutions, LLC current-role association are merged.
- Browser-only CSV quality checker, reporting calculator, CI, privacy tests, and release automation are live.
- GitHub Pages output, main navigation, Analytics Lab, privacy wording, and resume download were verified.
- The public resume is a clean two-page Confia-inclusive PDF.

### David AI Build Lab

- Public-safe command center, project registry, decisions, templates, and agent guardrails are merged.
- No family, medical, banking, immigration, client-confidential, credential, or application-private data belongs in this repository.

### Job Opportunity Engine

- Deterministic scoring MVP is merged into `main`.
- Compile checks, seven original unit tests, and the synthetic scoring demo passed GitHub Actions.
- The engine scores remote/location fit, title, skills, compensation, responsibilities, authorization, and posting completeness.
- It explains reasons, blockers, and review flags rather than using a black-box score.
- It never submits applications.

## Private Airtable review queue

The existing private `Application Tracker` table retains its original records and fields. It now also has fields for:

- Fit Score and Fit Tier
- Apply/Hold/Skip manual review decision
- original source URL and posting date
- employment type and normalized compensation
- U.S.-residence and state-residence restrictions
- blockers, review flags, scoring reasons, and job description
- engine version and last-scored timestamp

No fake job records were added and no existing application record was changed.

## Active pull request

The Airtable export bridge is under review. It converts scored JSON into a local import-ready CSV with exact tracker headers, synthetic tests, and no network request or credential.

## Next validation gate

1. Merge the Airtable export bridge after CI passes.
2. Score 10–20 real job descriptions from an approved source.
3. Compare engine ranking with David's human decision and tune only observed errors.
4. Select one scoped intake source: a specific Gmail label, a CSV export, or manually supplied job URLs.
5. Add deduplicated private intake and exception-based reminders.
6. Keep final application preparation and submission manual.

## Tool rule

Do not add Vercel, Supabase, Zapier, Make, n8n, or another paid service until a validated feature requires it. The current stack is ChatGPT, Codex, GitHub, Airtable, and the existing portfolio deployment.
