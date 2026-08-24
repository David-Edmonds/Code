from __future__ import annotations

from collections import Counter
from math import inf

from .models import Player
from .rankings import canonical_name


SKILL_POSITIONS = {"QB", "RB", "WR", "TE"}
INJURY_BLOCK = {"IR", "PUP", "SUSP", "SUSPENDED", "OUT"}


def roster_counts(roster: list[Player]) -> Counter[str]:
    counts: Counter[str] = Counter()
    for player in roster:
        position = primary_position(player.position)
        counts[position] += 1
    return counts


def primary_position(position: str) -> str:
    value = (position or "").upper().replace("D/ST", "DEF")
    value = {"DST": "DEF", "PK": "K"}.get(value, value)
    if "," in value:
        value = value.split(",", 1)[0]
    if value in {"W/R/T", "FLEX"}:
        return "FLEX"
    return value


def blended_rank(player: Player) -> float:
    components: list[tuple[float, float]] = []
    if player.custom_rank is not None:
        components.append((player.custom_rank, 0.55))
    if player.yahoo_rank is not None:
        components.append((player.yahoo_rank, 0.25))
    if player.adp is not None:
        components.append((player.adp, 0.20))
    if not components:
        return inf
    total_weight = sum(weight for _, weight in components)
    return sum(value * weight for value, weight in components) / total_weight


def _need_adjustment(position: str, counts: Counter[str], round_number: int, superflex: bool) -> float:
    adjustment = 0.0
    if position in {"RB", "WR"}:
        if counts[position] == 0:
            adjustment -= 5.5
        elif counts[position] == 1 and round_number <= 5:
            adjustment -= 3.0
        elif counts[position] >= 5:
            adjustment += 7.0
    elif position == "QB":
        if superflex:
            if counts["QB"] == 0:
                adjustment -= 7.0
            elif counts["QB"] == 1 and round_number <= 8:
                adjustment -= 3.0
        else:
            if round_number <= 3:
                adjustment += 16.0
            elif round_number <= 5:
                adjustment += 7.0
            if counts["QB"] >= 1:
                adjustment += 18.0
    elif position == "TE":
        if round_number <= 2:
            adjustment += 6.0
        if counts["TE"] >= 1:
            adjustment += 14.0
    elif position in {"K", "DEF"}:
        if round_number < 14:
            adjustment += 100.0
        elif counts[position] >= 1:
            adjustment += 100.0
    return adjustment


def recommend(
    available: list[Player],
    roster: list[Player],
    *,
    overall_pick: int,
    teams: int,
    roster_slots: dict[str, int] | None = None,
    limit: int = 12,
) -> list[Player]:
    if overall_pick < 1:
        overall_pick = 1
    round_number = (overall_pick - 1) // teams + 1
    counts = roster_counts(roster)
    roster_slots = roster_slots or {}
    superflex = any(key.upper() in {"Q/W/R/T", "SUPERFLEX", "SF"} for key in roster_slots)
    drafted_names = {canonical_name(player.name) for player in roster}

    ranked: list[Player] = []
    for player in available:
        if canonical_name(player.name) in drafted_names:
            continue
        position = primary_position(player.position)
        if position not in SKILL_POSITIONS | {"K", "DEF"}:
            continue
        base = blended_rank(player)
        if base == inf:
            continue
        score = base + _need_adjustment(position, counts, round_number, superflex)

        status = (player.injury_status or "").upper()
        if any(blocked in status for blocked in INJURY_BLOCK):
            score += 60.0
        elif status in {"Q", "QUESTIONABLE", "DOUBTFUL"}:
            score += 2.5

        # Roster-shape guardrails for a standard one-flex PPR build.
        if round_number <= 7:
            if counts["RB"] + counts["WR"] < round_number - 1 and position not in {"RB", "WR"}:
                score += 7.0
            if position == "RB" and counts["RB"] < 2:
                score -= 1.5
            if position == "WR" and counts["WR"] < 3:
                score -= 1.5

        # Small value reward when a player has fallen well beyond market ADP.
        if player.adp is not None and overall_pick > player.adp + 8:
            score -= min(5.0, (overall_pick - player.adp) / 6)

        player.score = round(score, 2)
        player.reason = _reason(player, counts, round_number, overall_pick)
        ranked.append(player)

    ranked.sort(key=lambda item: (item.score if item.score is not None else inf, blended_rank(item)))
    return ranked[:limit]


def _reason(player: Player, counts: Counter[str], round_number: int, overall_pick: int) -> str:
    position = primary_position(player.position)
    if player.adp is not None and overall_pick >= player.adp + 10:
        return "value fall"
    if position in {"RB", "WR"} and counts[position] < 2:
        return f"fills {position} need"
    if player.tier is not None:
        return f"tier {player.tier}"
    if player.injury_status:
        return f"status: {player.injury_status}"
    return f"best value in round {round_number}"
