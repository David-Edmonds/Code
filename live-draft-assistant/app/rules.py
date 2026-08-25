from __future__ import annotations

import csv
import io
import re
from typing import Any

from .models import Keeper, StrategyProfile


def parse_custom_order(text: str, teams: int) -> list[int]:
    values = [part for part in re.split(r"[\s,;|]+", text.strip()) if part]
    order: list[int] = []
    for index, value in enumerate(values, start=1):
        try:
            owner = int(value)
        except ValueError as exc:
            raise ValueError(f"Pick {index} has an invalid owner: {value}") from exc
        if not 1 <= owner <= teams:
            raise ValueError(f"Pick {index} owner {owner} must be between 1 and {teams}")
        order.append(owner)
    return order


def parse_keepers(text: str, teams: int) -> list[dict[str, Any]]:
    if not text.strip():
        return []
    rows = csv.reader(io.StringIO(text), delimiter="|")
    keepers: list[dict[str, Any]] = []
    for line_number, row in enumerate(rows, start=1):
        row = [item.strip() for item in row]
        if not any(row) or row[0].startswith("#"):
            continue
        if len(row) < 2:
            raise ValueError(
                f"Keeper line {line_number} needs at least: player | owner slot"
            )
        try:
            owner_slot = int(row[1])
        except ValueError as exc:
            raise ValueError(f"Keeper line {line_number} has an invalid owner slot") from exc
        if not 1 <= owner_slot <= teams:
            raise ValueError(
                f"Keeper line {line_number} owner must be between 1 and {teams}"
            )
        keeper = Keeper(
            player_name=row[0],
            owner_slot=owner_slot,
            position=row[2].upper() if len(row) > 2 else "",
            nfl_team=row[3].upper() if len(row) > 3 else "",
            note=row[4] if len(row) > 4 else "",
        )
        keepers.append(keeper.to_dict())
    return keepers


def keeper_text(keepers: list[dict[str, Any]]) -> str:
    return "\n".join(
        " | ".join(
            [
                str(item.get("player_name", "")),
                str(item.get("owner_slot", "")),
                str(item.get("position", "")),
                str(item.get("nfl_team", "")),
                str(item.get("note", "")),
            ]
        ).rstrip(" |")
        for item in keepers
    )


def build_strategy(
    *,
    existing: dict[str, Any] | None,
    notes: str,
    preferred_players: list[str],
    avoid_players: list[str],
    qb_earliest_round: int,
    te_earliest_round: int,
) -> dict[str, Any]:
    base = StrategyProfile().to_dict()
    if existing:
        base.update(existing)
    base.update(
        {
            "notes": notes.strip() or StrategyProfile().notes,
            "preferred_players": clean_names(preferred_players),
            "avoid_players": clean_names(avoid_players),
            "qb_earliest_round": max(1, int(qb_earliest_round)),
            "te_earliest_round": max(1, int(te_earliest_round)),
        }
    )
    return base


def clean_names(names: list[str]) -> list[str]:
    output: list[str] = []
    seen: set[str] = set()
    for raw in names:
        for value in re.split(r"[,;\n]+", raw):
            name = value.strip()
            key = name.casefold()
            if name and key not in seen:
                output.append(name)
                seen.add(key)
    return output
