# Live Draft Assistant

A local-first assistant for David's Yahoo Fantasy Football drafts. It watches the live Yahoo draft board when OAuth is available, combines league-specific Yahoo rank with fresh 10-team PPR ADP, enriches player status from Sleeper, and returns three concise recommendations. Manual mode remains available if Yahoo authorization fails.

## What it does

- Polls Yahoo draft results during the live draft.
- Removes drafted players automatically.
- Tracks your roster using Yahoo team ID `10`.
- Uses current Yahoo league rank, Fantasy Football Calculator ADP, an optional personal rankings CSV, and Sleeper injury metadata.
- Applies full-PPR snake-draft roster rules and positional scarcity.
- Gives three names immediately.
- Copies a compact live-board prompt for regular ChatGPT.
- Optionally calls the OpenAI API for a second review.

## Start on Windows

1. Download or clone the repository.
2. Open the `live-draft-assistant` folder.
3. Double-click `run_windows.bat`.
4. The app opens at `http://127.0.0.1:8765`.

Manual mode works without credentials. The first run installs the required Python packages.

## Connect Yahoo

Yahoo private-league access uses OAuth; never paste your Yahoo password into this app.

1. Create or obtain a Yahoo Sports developer application.
2. Set its callback URL to exactly:

   `http://127.0.0.1:8765/auth/callback`

3. Copy `.env.example` to `.env` if the launcher has not already done it.
4. Add `YAHOO_CLIENT_ID` and `YAHOO_CLIENT_SECRET` to `.env`.
5. Start the app and click **Connect Yahoo**.

The supplied defaults correspond to the shared URL:

- League ID: `810161`
- Team ID: `10`
- League size: `10`
- Draft slot: `7` (change this if Yahoo assigns a different slot)
- Scoring: full PPR

## Rankings and accuracy

The app deliberately does not commit a copied expert ranking list to this public repository. It uses three live/personal inputs instead:

1. Yahoo's league-specific available-player order.
2. Daily 10-team PPR ADP from Fantasy Football Calculator.
3. An optional fresh rankings CSV imported in the browser.

Most CSVs work when they contain a player/name column and a rank/ECR column. A template is in `data/rankings.template.csv`.

Sleeper's public player endpoint supplies current team and injury metadata and is cached for the day. Fantasy Football Calculator ADP is also cached because it updates daily.

## Regular ChatGPT vs API review

The fastest free workflow is **Copy for ChatGPT** and paste the prompt into this conversation. It includes the roster, recent picks, top available players, rankings, ADP, and injury status.

The **AI review** button requires a separate OpenAI API key and API billing. A ChatGPT subscription does not automatically provide API credits. Put the key in `.env` as `OPENAI_API_KEY`. The default low-cost model is `gpt-5.6-luna`.

## Tests

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

## Draft-day fallback

If Yahoo API access is not ready, import a current rankings CSV and enter picks in the manual box. The app assigns each pick to the correct snake slot and continues making roster-aware recommendations.

See `docs/SUNDAY_CHECKLIST.md` before the draft.
