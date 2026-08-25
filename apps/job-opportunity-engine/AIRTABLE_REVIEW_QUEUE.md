# Private Airtable Review Queue

The Job Opportunity Engine can prepare an import-ready CSV for the existing **Application Tracker** table. The repository does not contain the Airtable base ID, API keys, actual applications, recruiter messages, or private account data.

## Private table fields

The existing tracker keeps its original application fields and now also supports:

- Fit Score
- Fit Tier
- Review Decision
- Source URL and Posted Date
- Employment Type
- Salary Min, Salary Max, Salary Period, and Currency
- Requires U.S. Residence
- Requires Specific State
- Blockers
- Review Flags
- Scoring Reasons
- Description and Source
- Engine Version
- Last Scored

These fields separate a role's analytical fit from unresolved eligibility questions.

## Create the scored files

From the repository root:

```bash
python apps/job-opportunity-engine/job_engine.py \
  --profile apps/job-opportunity-engine/profile.json \
  --input jobs.json \
  --output output/results.json \
  --csv output/results.csv
```

Create the Airtable import CSV:

```bash
python apps/job-opportunity-engine/airtable_export.py \
  --jobs jobs.json \
  --results output/results.json \
  --output output/airtable-import.csv \
  --engine-version job-opportunity-engine-v1
```

The exporter makes no network request. It only writes a local CSV.

## Safe import procedure

1. Open the private **Application Tracker** table.
2. Check the `ID` and `Source URL` columns for existing records before importing.
3. Import `output/airtable-import.csv` and map columns by their matching names.
4. Do not overwrite application status, notes, or dates on an existing record without reviewing the match.
5. Review Blockers and Review Flags before changing Review Decision from `Unreviewed`.
6. Use `Apply`, `Hold`, or `Skip` only after checking the original posting.
7. Keep final application submission manual.

## Decision meanings

| Review Decision | Meaning |
|---|---|
| Unreviewed | Newly scored; no human decision yet |
| Apply | Posting and eligibility were reviewed and the application is worth preparing |
| Hold | Potentially useful, but an important detail is unresolved |
| Skip | Do not invest more application time |

## Fit-tier meanings

| Fit Tier | Meaning |
|---|---|
| Strong Fit | High analytical alignment; still requires eligibility review |
| Good Fit | Worth reviewing soon |
| Review | Important information is missing or the match is mixed |
| Low Fit | Weak alignment and usually low priority |
| Blocked | A configured hard requirement is not met |

## Non-negotiable checks

A high fit score does not establish:

- permission to work from a particular country or state
- employer payroll or tax support for the physical work location
- active security clearance or current access
- compensation details that the employer did not publish
- authenticity of the employer or recruiter
- likelihood of receiving an interview or offer

Those remain human checks. The system never applies automatically.

## Duplicate rule

Use the original posting's stable ID when available. Otherwise, compare Source URL plus Company, Job Title, and Location. Never assume two similar titles are the same opening.

## Next integration gate

After the scorer is calibrated on 10–20 real postings, an approved source such as a specific Gmail job-alert label, a CSV export, or manually supplied URLs can feed the private queue. Intake should remain scoped, deduplicated, and exception-based.
