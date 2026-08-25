# Automation Map

| Workflow | Trigger | Automated work | Human decision | System of record |
|---|---|---|---|---|
| Portfolio quality | Pull request or push | Restore approved résumé, install, lint, build, test, generate and verify deployable output | Review claims and visual changes | GitHub |
| Portfolio publication | Successful reviewed merge to `main` | Rebuild `docs/`, verify links/privacy/résumé checksum, commit generated release | Approve source PR before merge | GitHub |
| Site health | Daily or weekly schedule | Check key pages, downloads, internal links, and failed workflows | Approve fixes | GitHub |
| Job opportunity review | Weekday schedule | Find, normalize, deduplicate, and score roles | Approve applications and answers | GitHub plus Airtable or spreadsheet |
| Social content | Approved item due | Format channel version and schedule | Approve content and image | Airtable + Buffer |
| Weekly project review | Weekly schedule | Summarize issues, PRs, failures, and next tasks | Reprioritize backlog | GitHub |

## Guardrails

- No automatic job applications without final human review.
- No automatic public post unless the item has an explicit approved status.
- No confidential dataset processing in public tools.
- No paid service or broad permission change without David's approval.
- Failed releases and scheduling errors must be surfaced; do not silently retry into duplicates.
- Notifications should be exception-based, not constant summaries with no action.
