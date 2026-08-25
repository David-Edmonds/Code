# Live Draft Assistant

A local Yahoo Fantasy Football draft companion built for David's league—not a generic expert-rankings widget.

It supports:

- Keeper leagues
- Traded draft positions
- Bonus or extra picks
- Any non-standard pick order
- David's target list, avoid list, QB/TE timing, and strategy notes
- Yahoo live draft syncing through OAuth
- A Chrome side-panel widget beside the Yahoo draft room
- Manual backup mode if Yahoo access fails
- One-click context copying for a final decision in regular ChatGPT

## The simple setup

1. Double-click `run_windows.bat`.
2. In the dashboard, confirm the league size, scoring, Yahoo team ID, and your normal draft slot.
3. Open **Keepers, traded picks, and your style**.
4. Paste the full owner sequence if the draft is not a normal snake.
5. Add keeper lines.
6. Save the rules.
7. Load the `extension` folder as an unpacked Chrome extension.
8. Open Yahoo's draft room and click the extension icon.

The widget stays beside Yahoo and shows the top three choices, your roster, whose pick it is, and when you pick next.

## How to represent special picks

The custom order is a list of the owner slot for every overall pick.

Example normal 4-team snake:

```text
1,2,3,4,4,3,2,1
```

If slot 2 won a bonus pick after pick 4:

```text
1,2,3,4,2,4,3,2,1
```

If slot 3 traded pick 7 to slot 1, put `1` in the seventh position.

Use the owner's original draft-slot number—not Yahoo's team ID—in this list. Your Yahoo team ID is only used to identify your roster from the live Yahoo API.

## Keeper format

Enter one player per line:

```text
Player | owner slot | position | NFL team | note
CeeDee Lamb | 7 | WR | DAL | costs Round 3
```

Keepers are removed from the available-player pool and appear on the correct owner's roster. The custom order should match how Yahoo actually handles any picks consumed by keepers.

## Chrome widget

1. Open `chrome://extensions`.
2. Turn on **Developer mode**.
3. Click **Load unpacked**.
4. Select the project's `extension` folder.
5. Pin **David's Live Draft Widget**.
6. Keep `run_windows.bat` running.
7. Open Yahoo and click the widget icon.

The Chrome Side Panel API keeps the assistant alongside the Yahoo page. The extension only talks to the local app at `127.0.0.1:8765`; it does not contain Yahoo or OpenAI credentials.

## Yahoo live connection

Manual mode works immediately. For automatic live picks, create a Yahoo Sports developer application with this exact callback:

```text
http://127.0.0.1:8765/auth/callback
```

Copy `.env.example` to `.env`, add your Yahoo Client ID and Client Secret, restart the app, and click **Connect Yahoo**.

Defaults from the shared league URL:

- League ID: `810161`
- Yahoo team ID: `10`
- Full PPR
- 10 teams

The draft slot is not assumed permanently because keeper/trade leagues can change it.

## Data and decisions

The assistant combines:

1. Yahoo's live league board and available-player order.
2. Current PPR ADP from Fantasy Football Calculator.
3. Sleeper player and injury metadata.
4. An optional fresh rankings CSV.
5. Your keepers, custom pick ownership, targets, avoids, and roster strategy.

The local engine gives a fast default. For difficult picks, press **Copy for ChatGPT** and paste the result into the regular ChatGPT conversation. The prompt includes the exact board, keepers, custom order, your roster, your strategy, and how long until your next owned pick.

## Windows start

Double-click:

```text
run_windows.bat
```

The first launch installs Python packages and opens `http://127.0.0.1:8765`.

## Validation

```powershell
.\.venv\Scripts\python.exe -m ruff check .
.\.venv\Scripts\python.exe -m pytest
```

See `docs/SUNDAY_CHECKLIST.md` before draft day.
