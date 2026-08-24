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
class DraftConfig:
    teams: int = 10
    slot: int = 7
    rounds: int = 16
    scoring: str = "ppr"
    team_id: int = 10
    league_id: str = "810161"
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
