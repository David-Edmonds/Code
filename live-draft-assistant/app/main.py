from __future__ import annotations

import asyncio
import csv
import io
import time
from datetime import datetime, timezone
from typing import Any

from fastapi import FastAPI, File, HTTPException, Request, UploadFile
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from .ai import ai_review
from .config import BASE_DIR, settings
from .models import DraftConfig, DraftPick, Player
from .providers import enrich_with_sleeper, fetch_adp, fetch_sleeper_players
from .rankings import canonical_name, load_custom_rankings, merge_rankings
from .recommender import recommend
from .snake import next_pick_for_slot, picks_until_turn, slot_for_pick
from .state import ManualDraftStore
from .yahoo import YahooClient, YahooError


app = FastAPI(title="Live Draft Assistant", version="0.2.0")
app.mount("/static", StaticFiles(directory=BASE_DIR / "app" / "static"), name="static")
templates = Jinja2Templates(directory=BASE_DIR / "app" / "templates")

initial_config = DraftConfig(
    teams=settings.league_teams,
    slot=settings.draft_slot,
    rounds=settings.draft_rounds,
    scoring=settings.scoring_format,
    team_id=settings.yahoo_team_id,
    league_id=settings.yahoo_league_id,
)
store = ManualDraftStore(settings.manual_state_path, initial_config)
yahoo = YahooClient(
    client_id=settings.yahoo_client_id,
    client_secret=settings.yahoo_client_secret,
    redirect_uri=settings.yahoo_redirect_uri,
    token_path=settings.token_path,
)

SOURCE_REFRESH_SECONDS = 60
YAHOO_AVAILABLE_REFRESH_SECONDS = 60
refresh_lock = asyncio.Lock()

RUNTIME_CACHE: dict[str, Any] = {
    "league_key": None,
    "available": [],
    "adp": [],
    "sleeper": {},
    "player_details": {},
    "last_refresh": 0.0,
    "last_source_refresh": 0.0,
    "last_yahoo_available_refresh": 0.0,
    "errors": [],
}


class ConfigPayload(BaseModel):
    teams: int = Field(ge=4, le=20)
    slot: int = Field(ge=1, le=20)
    rounds: int = Field(ge=1, le=40)
    scoring: str = "ppr"
    team_id: int = Field(ge=1, le=50)
    league_id: str


class PickPayload(BaseModel):
    player_name: str
    position: str = ""
    nfl_team: str = ""
    team_slot: int | None = None


@app.get("/", response_class=HTMLResponse)
async def index(request: Request) -> HTMLResponse:
    return templates.TemplateResponse(
        request=request,
        name="index.html",
        context={"poll_seconds": settings.poll_seconds},
    )


@app.get("/auth/yahoo")
async def auth_yahoo(request: Request) -> RedirectResponse:
    try:
        url, state = yahoo.authorization_url()
    except YahooError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = RedirectResponse(url)
    response.set_cookie(
        "yahoo_oauth_state",
        state,
        httponly=True,
        secure=False,
        samesite="lax",
        max_age=600,
    )
    return response


@app.get("/auth/callback")
async def auth_callback(request: Request, code: str = "", state: str = "") -> RedirectResponse:
    expected = request.cookies.get("yahoo_oauth_state")
    if not code or not state or not expected or state != expected:
        raise HTTPException(status_code=400, detail="Yahoo OAuth state validation failed")
    try:
        await yahoo.exchange_code(code)
        config, _ = store.load()
        RUNTIME_CACHE["league_key"] = await yahoo.discover_league_key(config.league_id)
        RUNTIME_CACHE["last_source_refresh"] = 0.0
    except YahooError as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    response = RedirectResponse("/?connected=1")
    response.delete_cookie("yahoo_oauth_state")
    return response


@app.get("/api/status")
async def api_status() -> dict[str, Any]:
    config, picks = store.load()
    return {
        "yahoo_configured": yahoo.configured,
        "yahoo_authenticated": yahoo.authenticated,
        "league_key": RUNTIME_CACHE.get("league_key"),
        "openai_configured": bool(settings.openai_api_key),
        "manual_pick_count": len(picks),
        "config": config.to_dict(),
        "last_refresh": RUNTIME_CACHE.get("last_refresh"),
        "errors": RUNTIME_CACHE.get("errors", [])[-3:],
    }


@app.post("/api/config")
async def update_config(payload: ConfigPayload) -> dict[str, Any]:
    if payload.slot > payload.teams:
        raise HTTPException(status_code=400, detail="Draft slot cannot exceed league size")
    config, _ = store.load()
    config.teams = payload.teams
    config.slot = payload.slot
    config.rounds = payload.rounds
    config.scoring = payload.scoring.lower()
    config.team_id = payload.team_id
    config.league_id = payload.league_id.strip()
    store.update_config(config)
    RUNTIME_CACHE.update(
        {
            "league_key": None,
            "available": [],
            "player_details": {},
            "last_refresh": 0.0,
            "last_source_refresh": 0.0,
            "last_yahoo_available_refresh": 0.0,
        }
    )
    return {"ok": True, "config": config.to_dict()}


@app.post("/api/refresh")
async def refresh(force: bool = True) -> dict[str, Any]:
    await refresh_sources(force=force)
    return {"ok": True, "last_refresh": RUNTIME_CACHE["last_refresh"]}


@app.post("/api/manual/pick")
async def manual_pick(payload: PickPayload) -> dict[str, Any]:
    await refresh_sources(force=False)
    config, picks = store.load()
    player_name = payload.player_name.strip()
    if not player_name:
        raise HTTPException(status_code=400, detail="Player name is required")
    if len(picks) >= config.teams * config.rounds:
        raise HTTPException(status_code=400, detail="The configured draft is already complete")
    if any(canonical_name(pick.player_name) == canonical_name(player_name) for pick in picks):
        raise HTTPException(status_code=400, detail=f"{player_name} is already on the draft board")

    overall_pick = len(picks) + 1
    slot = payload.team_slot or slot_for_pick(overall_pick, config.teams)
    if not 1 <= slot <= config.teams:
        raise HTTPException(status_code=400, detail="Team slot is outside the league size")

    matched = find_cached_player(player_name)
    position = payload.position.strip().upper() or (matched.position if matched else "")
    nfl_team = payload.nfl_team.strip().upper() or (matched.team if matched else "")
    canonical_display_name = matched.name if matched else player_name

    pick = DraftPick(
        pick=overall_pick,
        round=(overall_pick - 1) // config.teams + 1,
        team_key=f"manual.t.{slot}",
        player_name=canonical_display_name,
        position=position,
        nfl_team=nfl_team,
        player_id=matched.yahoo_id if matched else None,
    )
    store.add_pick(pick)
    RUNTIME_CACHE["last_refresh"] = time.time()
    return {"ok": True, "pick": pick.to_dict()}


@app.post("/api/manual/undo")
async def undo_manual_pick() -> dict[str, Any]:
    config, picks = store.load()
    if not picks:
        raise HTTPException(status_code=400, detail="There are no manual picks to undo")
    removed = max(picks, key=lambda item: item.pick)
    remaining = [pick for pick in picks if pick.pick != removed.pick]
    store.save(config, remaining)
    RUNTIME_CACHE["last_refresh"] = time.time()
    return {"ok": True, "removed": removed.to_dict()}


@app.delete("/api/manual/pick/{overall_pick}")
async def delete_manual_pick(overall_pick: int) -> dict[str, Any]:
    picks = store.delete_pick(overall_pick)
    config, _ = store.load()
    for index, pick in enumerate(picks, start=1):
        pick.pick = index
        pick.round = (index - 1) // config.teams + 1
        if pick.team_key.startswith("manual.t."):
            pick.team_key = f"manual.t.{slot_for_pick(index, config.teams)}"
    store.save(config, picks)
    RUNTIME_CACHE["last_refresh"] = time.time()
    return {"ok": True}


@app.post("/api/rankings/upload")
async def upload_rankings(file: UploadFile = File(...)) -> dict[str, Any]:
    content = await file.read()
    try:
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        rows = list(reader)
        if not rows:
            raise ValueError("CSV contains no rows")
        settings.custom_rankings_path.parent.mkdir(parents=True, exist_ok=True)
        settings.custom_rankings_path.write_text(text, encoding="utf-8")
        parsed = load_custom_rankings(settings.custom_rankings_path)
        if not parsed:
            raise ValueError("No player/name column was detected")
    except (UnicodeDecodeError, csv.Error, ValueError) as exc:
        raise HTTPException(status_code=400, detail=f"Could not read rankings CSV: {exc}") from exc
    return {"ok": True, "players": len(parsed), "filename": file.filename}


@app.get("/api/state")
async def draft_state() -> dict[str, Any]:
    await refresh_sources(force=False)
    config, manual_picks = store.load()
    errors: list[str] = []
    live_mode = yahoo.authenticated
    picks = manual_picks
    yahoo_available: list[Player] = []

    if live_mode:
        try:
            league_key = await ensure_league_key(config)
            picks = await yahoo.draft_results(league_key)
            details_cache: dict[str, Player] = RUNTIME_CACHE.setdefault("player_details", {})
            player_ids = list(dict.fromkeys(pick.player_id for pick in picks if pick.player_id))
            missing_ids = [player_id for player_id in player_ids if player_id not in details_cache]
            if missing_ids:
                details_cache.update(await yahoo.player_details(league_key, missing_ids))
            for pick in picks:
                player = details_cache.get(pick.player_id or "")
                if player:
                    pick.player_name = player.name
                    pick.position = player.position
                    pick.nfl_team = player.team
            yahoo_available = list(RUNTIME_CACHE.get("available") or [])
            RUNTIME_CACHE["last_refresh"] = time.time()
        except Exception as exc:  # Live mode must fail safe during a timed draft.
            errors.append(f"Yahoo live mode failed; using manual mode: {exc}")
            live_mode = False
            picks = manual_picks

    available = combined_player_pool(yahoo_available=yahoo_available)
    drafted_names = {canonical_name(pick.player_name) for pick in picks if pick.player_name}
    available = [player for player in available if canonical_name(player.name) not in drafted_names]

    team_suffix = f".t.{config.team_id}"
    my_picks = [pick for pick in picks if pick.team_key.endswith(team_suffix)]
    if not live_mode:
        manual_key = f"manual.t.{config.slot}"
        my_picks = [pick for pick in picks if pick.team_key == manual_key]

    roster = [
        Player(
            name=pick.player_name,
            position=pick.position,
            team=pick.nfl_team,
            yahoo_id=pick.player_id,
        )
        for pick in my_picks
        if pick.player_name
    ]
    next_overall = len(picks) + 1
    ranked_available = recommend(
        available,
        roster,
        overall_pick=next_overall,
        teams=config.teams,
        roster_slots=config.roster_slots,
        limit=80,
    )
    next_mine = next_pick_for_slot(len(picks), config.slot, config.teams, config.rounds)
    until_turn = picks_until_turn(len(picks), config.slot, config.teams, config.rounds)
    draft_complete = len(picks) >= config.teams * config.rounds
    current_slot = None if draft_complete else slot_for_pick(next_overall, config.teams)

    prompt = build_chatgpt_prompt(
        config=config,
        picks=picks,
        roster=roster,
        recommendations=ranked_available,
        next_overall=next_overall,
        next_mine=next_mine,
    )

    return {
        "mode": "yahoo-live" if live_mode else "manual",
        "config": config.to_dict(),
        "draft": {
            "completed": len(picks),
            "complete": draft_complete,
            "next_overall": None if draft_complete else next_overall,
            "current_slot": current_slot,
            "is_my_turn": current_slot == config.slot,
            "next_my_pick": next_mine,
            "picks_until_turn": until_turn,
        },
        "recommendations": [player.to_dict() for player in ranked_available[:3]],
        "available": [player.to_dict() for player in ranked_available[:50]],
        "roster": [player.to_dict() for player in roster],
        "recent_picks": [pick.to_dict() for pick in picks[-12:]][::-1],
        "chatgpt_prompt": prompt,
        "last_refresh": datetime.fromtimestamp(
            RUNTIME_CACHE.get("last_refresh") or time.time(), tz=timezone.utc
        ).isoformat(),
        "errors": errors + list(RUNTIME_CACHE.get("errors") or [])[-2:],
        "attribution": [
            "Yahoo Fantasy Sports API",
            "Fantasy Football Calculator ADP",
            "Sleeper player metadata",
        ],
    }


@app.post("/api/ai-review")
async def run_ai_review() -> dict[str, str]:
    state = await draft_state()
    candidates = [Player(**item) for item in state["available"]]
    roster = [Player(**item) for item in state["roster"]]
    try:
        answer = await ai_review(
            api_key=settings.openai_api_key,
            model=settings.openai_model,
            league_context={"config": state["config"], "draft": state["draft"]},
            roster=roster,
            candidates=candidates,
        )
    except Exception as exc:
        raise HTTPException(status_code=400, detail=str(exc)) from exc
    return {"answer": answer}


async def ensure_league_key(config: DraftConfig) -> str:
    league_key = RUNTIME_CACHE.get("league_key")
    if league_key:
        return str(league_key)
    league_key = await yahoo.discover_league_key(config.league_id)
    RUNTIME_CACHE["league_key"] = league_key
    return league_key


def combined_player_pool(*, yahoo_available: list[Player] | None = None) -> list[Player]:
    yahoo_players = yahoo_available
    if yahoo_players is None:
        yahoo_players = list(RUNTIME_CACHE.get("available") or [])
    custom = load_custom_rankings(settings.custom_rankings_path)
    adp_players: list[Player] = list(RUNTIME_CACHE.get("adp") or [])
    players = merge_rankings(custom, yahoo_players, adp_players)
    return enrich_with_sleeper(players, RUNTIME_CACHE.get("sleeper") or {})


def find_cached_player(name: str) -> Player | None:
    wanted = canonical_name(name)
    return next(
        (player for player in combined_player_pool() if canonical_name(player.name) == wanted),
        None,
    )


async def refresh_sources(*, force: bool) -> None:
    now = time.time()
    last_source_refresh = float(RUNTIME_CACHE.get("last_source_refresh") or 0)
    if not force and now - last_source_refresh < SOURCE_REFRESH_SECONDS:
        return

    async with refresh_lock:
        now = time.time()
        last_source_refresh = float(RUNTIME_CACHE.get("last_source_refresh") or 0)
        if not force and now - last_source_refresh < SOURCE_REFRESH_SECONDS:
            return

        config, _ = store.load()
        errors: list[str] = []

        async def load_adp() -> None:
            try:
                RUNTIME_CACHE["adp"] = await fetch_adp(
                    settings.adp_cache_path,
                    teams=config.teams,
                    year=settings.season_year,
                    scoring=config.scoring,
                    force=False,
                )
            except Exception as exc:
                errors.append(f"ADP refresh: {exc}")

        async def load_sleeper() -> None:
            try:
                RUNTIME_CACHE["sleeper"] = await fetch_sleeper_players(
                    settings.sleeper_cache_path,
                    force=False,
                )
            except Exception as exc:
                errors.append(f"Sleeper refresh: {exc}")

        async def load_yahoo() -> None:
            if not yahoo.authenticated:
                return
            last_yahoo_refresh = float(
                RUNTIME_CACHE.get("last_yahoo_available_refresh") or 0
            )
            should_refresh = (
                force
                or not RUNTIME_CACHE.get("available")
                or now - last_yahoo_refresh >= YAHOO_AVAILABLE_REFRESH_SECONDS
            )
            if not should_refresh:
                return
            try:
                league_key = await ensure_league_key(config)
                RUNTIME_CACHE["available"] = await yahoo.available_players(
                    league_key,
                    limit=250,
                )
                RUNTIME_CACHE["last_yahoo_available_refresh"] = time.time()
            except Exception as exc:
                errors.append(f"Yahoo available players: {exc}")

        await asyncio.gather(load_adp(), load_sleeper(), load_yahoo())
        refreshed_at = time.time()
        RUNTIME_CACHE["last_source_refresh"] = refreshed_at
        RUNTIME_CACHE["last_refresh"] = refreshed_at
        RUNTIME_CACHE["errors"] = errors


def build_chatgpt_prompt(
    *,
    config: DraftConfig,
    picks: list[DraftPick],
    roster: list[Player],
    recommendations: list[Player],
    next_overall: int,
    next_mine: int | None,
) -> str:
    roster_text = ", ".join(f"{player.name} ({player.position})" for player in roster) or "None"
    recent_text = ", ".join(
        f"{pick.pick}. {pick.player_name or pick.player_id}" for pick in picks[-10:]
    ) or "No picks yet"
    available_text = "; ".join(
        (
            f"{player.name} ({player.position}, {player.team}, "
            f"rank {first_rank(player)}, ADP {player.adp}, "
            f"injury {player.injury_status or 'none'})"
        )
        for player in recommendations[:12]
    )
    scoring_label = {
        "ppr": "full PPR",
        "half-ppr": "half PPR",
        "standard": "standard",
    }.get(config.scoring, config.scoring)
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    return (
        f"Live Yahoo fantasy draft as of {timestamp}. "
        f"{config.teams}-team {scoring_label} snake, my slot is {config.slot}. "
        f"Next overall pick is {next_overall}; my next pick is {next_mine}. "
        f"My roster: {roster_text}. Recent picks: {recent_text}. "
        f"Best available: {available_text}. "
        "Use current injury, suspension, depth-chart, and role news when it materially changes the pick. "
        "Return exactly the best 3 player names in order. No explanation. "
        "Do not include anyone already drafted."
    )


def first_rank(player: Player) -> float | None:
    for value in (player.custom_rank, player.yahoo_rank, player.adp):
        if value is not None:
            return value
    return None
