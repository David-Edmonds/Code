from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any


@dataclass(slots=True)
class Player:
    name: str
    position: str
    team: str = "FA"
    yahoo_id: str | None = None
    yahoo_rank: float | None = None
    adp: float | None = None
    custom_rank: float | None = None
    tier: int | None = None
    injury_status: str | None = None
    injury_note: str | None = None
    bye_week: int | None = None
    source: str = ""
    score: float | None = None
    reason: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DraftPick:
    pick: int
    round: int
    team_key: str
    player_name: str
    position: str = ""
    nfl_team: str = ""
    player_id: str | None = None

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class Keeper:
    player_name: str
    owner_slot: int
    position: str = ""
    nfl_team: str = ""
    note: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class StrategyProfile:
    name: str = "David aggressive PPR value"
    notes: str = (
        "Play to win. Prioritize elite PPR volume, league-winning upside, and falling value. "
        "Build strong RB/WR depth before taking replaceable QB/TE options."
    )
    preferred_players: list[str] = field(default_factory=list)
    avoid_players: list[str] = field(default_factory=list)
    qb_earliest_round: int = 6
    te_earliest_round: int = 5
    preferred_bonus: float = 8.0
    avoid_penalty: float = 100.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


@dataclass(slots=True)
class DraftConfig:
    teams: int = 10
    slot: int = 7
    rounds: int = 16
    scoring: str = "ppr"
    team_id: int = 10
    league_id: str = "810161"
    keeper_league: bool = False
    custom_pick_order: list[int] = field(default_factory=list)
    keepers: list[dict[str, Any]] = field(default_factory=list)
    strategy: dict[str, Any] = field(default_factory=lambda: StrategyProfile().to_dict())
    roster_slots: dict[str, int] = field(
        default_factory=lambda: {
            "QB": 1,
            "RB": 2,
            "WR": 2,
            "TE": 1,
            "FLEX": 1,
            "K": 1,
            "DEF": 1,
            "BN": 7,
        }
    )

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)
