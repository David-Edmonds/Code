# Current Status

_Last updated: August 27, 2026_

This is the newest public project-status snapshot. Historical context and decisions remain in `CURRENT_CONTEXT.md` and `DECISIONS.md`.

## Released and verified

### David Analytics Lab

- Portfolio foundation and Confia Solutions, LLC current-role association are merged.
- Browser-only CSV quality checker, reporting calculator, CI, privacy tests, and release automation are live.
- GitHub Pages output, main navigation, Analytics Lab, privacy wording, and resume download were verified.
- Independent public-data projects remain clearly separated from Confia client work.

### David AI Build Lab

- Public-safe command center, project registry, decisions, templates, and agent guardrails are merged.
- Automated repository integrity checks protect required files, internal links, formatting, privacy boundaries, and common credential patterns.
- Safe environment templates such as `.env.example` are permitted; real environment and key files remain blocked.
- No family, medical, banking, immigration, client-confidential, credential, or application-private data belongs in this repository.

### Job Opportunity Engine

- Deterministic scoring MVP is merged into `main`.
- Compile checks, unit tests, repository validation, and the synthetic scoring demo pass GitHub Actions.
- The engine scores remote/location fit, title, skills, compensation, responsibilities, authorization, and posting completeness.
- It explains reasons, blockers, and review flags rather than using a black-box score.
- A high score never proves physical-work-location, payroll, tax, employer-policy, clearance, or offer eligibility.
- It never submits applications.

## Private Airtable review queue

The private review system remains outside this public repository. Its structured fields support fit score and tier, manual Apply/Hold/Skip decisions, source and compensation details, residence restrictions, blockers, review flags, scoring reasons, engine version, and scoring timestamp.

No actual applications, recruiter messages, private account identifiers, or Airtable credentials are committed here.

## Active pull request

The Airtable export bridge is under review on a clean branch based on the released scoring engine. It converts scored JSON into a local import-ready CSV with exact tracker headers, synthetic tests, and no network request or credential.

## Next validation gate

1. Merge the Airtable export bridge after both Job Opportunity Engine workflows pass.
2. Continue comparing private scoring results with human decisions and tune only observed errors.
3. Keep intake scoped to approved sources and deduplicate before creating private review records.
4. Keep final application preparation and submission manual.
5. Monitor Airtable Free-plan API and automation usage before adding any recurring intake process.

## Tool rule

Do not add Vercel, Supabase, Zapier, Make, n8n, Metricool, or another paid service until a validated feature requires it. The current stack is ChatGPT, Codex, GitHub, Airtable, Google Workspace, and the existing portfolio and publishing services.
