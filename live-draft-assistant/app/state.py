from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import DraftConfig, DraftPick


class ManualDraftStore:
    def __init__(self, path: Path, config: DraftConfig) -> None:
        self.path = path
        self.default_config = config

    def load(self) -> tuple[DraftConfig, list[DraftPick]]:
        if not self.path.exists():
            return self.default_config, []
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
            config_raw = raw.get("config", {})
            config = DraftConfig(**{**asdict(self.default_config), **config_raw})
            picks = [DraftPick(**item) for item in raw.get("picks", [])]
            picks.sort(key=lambda item: item.pick)
            return config, picks
        except (OSError, json.JSONDecodeError, TypeError, ValueError):
            return self.default_config, []

    def save(self, config: DraftConfig, picks: list[DraftPick]) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        payload = {
            "config": config.to_dict(),
            "picks": [pick.to_dict() for pick in sorted(picks, key=lambda item: item.pick)],
        }
        self.path.write_text(json.dumps(payload, indent=2), encoding="utf-8")

    def add_pick(self, pick: DraftPick) -> list[DraftPick]:
        config, picks = self.load()
        picks = [existing for existing in picks if existing.pick != pick.pick]
        picks.append(pick)
        picks.sort(key=lambda item: item.pick)
        self.save(config, picks)
        return picks

    def delete_pick(self, overall_pick: int) -> list[DraftPick]:
        config, picks = self.load()
        picks = [pick for pick in picks if pick.pick != overall_pick]
        self.save(config, picks)
        return picks

    def update_config(self, config: DraftConfig) -> None:
        _, picks = self.load()
        self.save(config, picks)
