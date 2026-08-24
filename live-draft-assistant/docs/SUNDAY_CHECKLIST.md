# Sunday, August 30, 2026 Draft Checklist

## Complete before Sunday

- [ ] Download or clone the project and run `run_windows.bat` once so Python packages install before draft day.
- [ ] Open `.env` and add the Yahoo Client ID and Client Secret if Yahoo grants API access.
- [ ] Confirm the Yahoo app callback is exactly `http://127.0.0.1:8765/auth/callback`.
- [ ] Start the dashboard and set 10 teams, your actual draft slot, full PPR, team ID 10, and league ID 810161.
- [ ] Click **Connect Yahoo** and confirm the top status says **Yahoo live**.
- [ ] Import a fresh full-PPR rankings CSV on draft day when you have one. The app also uses Yahoo rank and current ADP.
- [ ] Click **Refresh** and verify player status information appears.
- [ ] Run a Yahoo mock draft or enter at least five manual picks to practice the workflow.

## Thirty minutes before the draft

- [ ] Restart the dashboard.
- [ ] Confirm your final draft slot and Yahoo roster settings.
- [ ] Click **Refresh**.
- [ ] Keep Yahoo's draft room and the dashboard side by side.
- [ ] Keep this ChatGPT conversation open in another tab.
- [ ] Make sure the manual box and **Undo last** button work even when Yahoo live syncing is connected.

## During the draft

- Use the dashboard's first recommendation as the fast default.
- Use **Copy for ChatGPT** when the top choices are close, surprising, or affected by recent news.
- Paste the copied context here. ChatGPT is instructed to return exactly three names with no explanation.
- Do not wait on an AI response when the clock is nearly expired.
- If Yahoo syncing stops, enter each new pick in **Manual backup**. You only need the player name; position and NFL team are filled from the ranking data when possible.
- Use **Undo last** immediately after a typo.

## Rules built into the app

- Avoid kicker and defense until the closing rounds.
- Avoid a second quarterback in a normal one-QB build unless late value is extreme.
- Prioritize RB/WR roster construction through the early and middle rounds.
- Penalize Out, IR, PUP, and suspended players.
- Reward players falling beyond current ADP.
- Alert visually and audibly when your slot is on the clock.
