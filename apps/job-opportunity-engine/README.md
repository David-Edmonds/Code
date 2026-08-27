# Job Opportunity Engine

A deterministic, public-safe scoring tool for prioritizing remote analytics roles. It ranks jobs against explicit criteria and shows exactly why a role scored well, what blocked it, and what still needs human verification.

## What the first release does

- Scores jobs from JSON or CSV on a 0-100 scale
- Ranks remote/location fit, title fit, skills, compensation, responsibilities, authorization fit, and posting completeness
- Blocks clear mismatches such as non-remote roles, compensation below the configured floor, data-entry roles, and commission-only postings
- Flags U.S.-residence, state-residence, active-clearance, compensation, and cross-border payroll questions for human review
- Exports detailed JSON and a practical review CSV
- Uses no external API, tracking, AI model, or paid service

## Important boundary

“Remote” does not automatically mean “work from any country.” The engine does not make legal, tax, payroll, immigration, or employer-policy conclusions. It flags location restrictions and requires a human check before an application is treated as eligible.

The engine also never applies to jobs automatically. David reviews every opportunity and every final application.

## Run it

Requires Python 3.11 or newer.

```bash
cd apps/job-opportunity-engine
python job_engine.py \
  --profile profile.json \
  --input examples/sample_jobs.json \
  --output output/results.json \
  --csv output/results.csv
```

Run tests:

```bash
PYTHONPATH=. python -m unittest discover -s tests -v
```

## Input fields

The scorer accepts a JSON list, a `{"jobs": [...]}` object, or a CSV file. Useful fields are:

- `id`, `title`, `company`, `description`, `location`
- `remote`, `employment_type`
- `salary_min`, `salary_max`, `salary_period`, `currency`
- `sponsorship_available`
- `requires_us_residence`, `requires_specific_state`
- `posted_date`, `source`, `source_url`

Missing fields reduce confidence instead of being silently guessed.

## Privacy and truth

- `profile.json` contains only public-safe professional criteria.
- Do not commit actual applications, recruiter messages, addresses, phone numbers, account identifiers, or private job-tracker exports.
- The example companies and job postings are synthetic.
- A high score means “worth reviewing,” not “guaranteed eligible” or “guaranteed to receive an offer.”

## Next release

After the scoring logic is validated on real job descriptions, connect approved job alerts to a private Airtable or spreadsheet review queue. Keep application submission manual.
