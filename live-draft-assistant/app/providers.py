from __future__ import annotations

import json
import time
from pathlib import Path
from typing import Any

import httpx

from .models import Player
from .utils import normalize_name, safe_float, safe_int


def _fresh(path: Path, max_age_seconds: int) -> bool:
    return path.exists() and time.time() - path.stat().st_mtime < max_age_seconds


async def fetch_adp(
    cache_path: Path,
    *,
    teams: int,
    year: int = 2026,
    scoring: str = "ppr",
    force: bool = False,
) -> list[Player]:
    if not force and _fresh(cache_path, 4 * 60 * 60):
        raw = json.loads(cache_path.read_text(encoding="utf-8"))
    else:
        url = f"https://fantasyfootballcalculator.com/api/v1/adp/{scoring}"
        params = {"teams": teams, "year": year}
        async with httpx.AsyncClient(timeout=20, follow_redirects=True) as client:
            response = await client.get(
                url,
                params=params,
                headers={"User-Agent": "David-Live-Draft-Assistant/0.1"},
            )
            response.raise_for_status()
            raw = response.json()
        cache_path.write_text(json.dumps(raw), encoding="utf-8")

    if isinstance(raw, dict):
        players_raw = raw.get("players", [])
    elif isinstance(raw, list):
        players_raw = raw
    else:
        players_raw = []
    players: list[Player] = []
    for item in players_raw:
        name = str(item.get("name") or item.get("player_name") or "").strip()
        if not name:
            continue
        players.append(
            Player(
                name=name,
                position=str(item.get("position") or item.get("pos") or "").upper(),
                team=str(item.get("team") or "FA").upper(),
                adp=safe_float(item.get("adp") or item.get("overall")),
                bye_week=safe_int(item.get("bye")),
                source="Fantasy Football Calculator ADP",
            )
        )
    return players


async def fetch_sleeper_players(cache_path: Path, *, force: bool = False) -> dict[str, dict[str, Any]]:
    if not force and _fresh(cache_path, 20 * 60 * 60):
        return json.loads(cache_path.read_text(encoding="utf-8"))

    async with httpx.AsyncClient(timeout=45, follow_redirects=True) as client:
        response = await client.get(
            "https://api.sleeper.app/v1/players/nfl?active=true",
            headers={"User-Agent": "David-Live-Draft-Assistant/0.1"},
        )
        response.raise_for_status()
        raw = response.json()
    cache_path.write_text(json.dumps(raw), encoding="utf-8")
    return raw


def enrich_with_sleeper(players: list[Player], sleeper: dict[str, dict[str, Any]]) -> list[Player]:
    by_yahoo: dict[str, dict[str, Any]] = {}
    by_name: dict[str, dict[str, Any]] = {}
    for item in sleeper.values():
        yahoo_id = item.get("yahoo_id")
        if yahoo_id not in (None, ""):
            by_yahoo[str(yahoo_id)] = item
        full_name = item.get("full_name") or " ".join(
            part for part in [item.get("first_name"), item.get("last_name")] if part
        )
        if full_name:
            by_name[normalize_name(full_name)] = item

    for player in players:
        item = None
        if player.yahoo_id:
            item = by_yahoo.get(str(player.yahoo_id))
        if item is None:
            item = by_name.get(normalize_name(player.name))
        if not item:
            continue
        player.injury_status = item.get("injury_status") or item.get("status")
        player.injury_note = item.get("practice_description") or item.get("injury_body_part")
        if not player.team or player.team == "FA":
            player.team = str(item.get("team") or "FA").upper()
        if not player.position:
            positions = item.get("fantasy_positions") or []
            player.position = str(positions[0] if positions else item.get("position") or "").upper()
    return players
