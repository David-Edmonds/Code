from __future__ import annotations

import csv
from pathlib import Path

from .models import Player
from .utils import normalize_name, safe_float, safe_int, unique_by


PLAYER_ALIASES = {
    "jamescookiii": "jamescook",
    "kennethwalkeriii": "kennethwalker",
    "marquisebrown": "hollywoodbrown",
}


def canonical_name(name: str) -> str:
    normalized = normalize_name(name)
    return PLAYER_ALIASES.get(normalized, normalized)


def load_custom_rankings(path: Path) -> list[Player]:
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as handle:
        reader = csv.DictReader(handle)
        players: list[Player] = []
        for index, row in enumerate(reader, start=1):
            lowered = {str(key).strip().lower(): value for key, value in row.items() if key}
            name = (
                lowered.get("player")
                or lowered.get("player name")
                or lowered.get("name")
                or lowered.get("player_name")
                or ""
            ).strip()
            if not name:
                continue
            rank = safe_float(
                lowered.get("rank")
                or lowered.get("overall rank")
                or lowered.get("ecr")
                or lowered.get("rk")
            )
            position = (
                lowered.get("position") or lowered.get("pos") or lowered.get("position rank") or ""
            ).upper()
            if position and any(ch.isdigit() for ch in position):
                position = "".join(ch for ch in position if ch.isalpha())
            players.append(
                Player(
                    name=name,
                    position=position,
                    team=(lowered.get("team") or lowered.get("tm") or "FA").upper(),
                    custom_rank=rank or float(index),
                    adp=safe_float(lowered.get("adp")),
                    tier=safe_int(lowered.get("tier")),
                    source=lowered.get("source") or "Custom rankings",
                )
            )
    return players


def merge_rankings(*collections: list[Player]) -> list[Player]:
    merged: dict[str, Player] = {}
    order: list[str] = []
    for collection in collections:
        for incoming in collection:
            key = canonical_name(incoming.name)
            if not key:
                continue
            if key not in merged:
                merged[key] = Player(
                    name=incoming.name,
                    position=incoming.position,
                    team=incoming.team,
                )
                order.append(key)
            target = merged[key]
            for field_name in (
                "position",
                "team",
                "yahoo_id",
                "yahoo_rank",
                "adp",
                "custom_rank",
                "tier",
                "injury_status",
                "injury_note",
                "bye_week",
            ):
                value = getattr(incoming, field_name)
                if value not in (None, "", "FA") or getattr(target, field_name) in (None, "", "FA"):
                    if value not in (None, ""):
                        setattr(target, field_name, value)
            if incoming.source:
                sources = [part.strip() for part in target.source.split("+") if part.strip()]
                if incoming.source not in sources:
                    sources.append(incoming.source)
                target.source = " + ".join(sources)
    return unique_by((merged[key] for key in order), lambda player: canonical_name(player.name))
