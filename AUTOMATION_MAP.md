# Automation Map

| Workflow | Trigger | Automated work | Human decision | System of record |
|---|---|---|---|---|
| Portfolio quality | Pull request or push | Install, lint, build, rendered-page tests | Review claims and preview | GitHub |
| Job opportunity review | Weekday schedule | Find, normalize, and score roles | Approve applications | Airtable or spreadsheet |
| Social content | Approved item due | Format channel version and schedule | Approve content and image | Airtable + Buffer |
| Weekly project review | Weekly schedule | Summarize issues, PRs, failures, and next tasks | Reprioritize backlog | GitHub |
| Site health | Daily/weekly schedule | Check broken links, deploy status, and form health | Approve fixes | GitHub |

## Guardrails

- No automatic job applications without final human review.
- No automatic public post unless the item has an explicit approved status.
- No confidential dataset processing in public tools.
- No paid service or broad permission change without David's approval.
- Notifications should be exception-based, not constant summaries with no action.
