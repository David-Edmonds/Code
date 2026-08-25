import json

from app.models import DraftConfig
from app.state import ManualDraftStore


def test_old_state_gets_new_keeper_defaults(tmp_path) -> None:
    path = tmp_path / "draft.json"
    path.write_text(
        json.dumps({"config": {"teams": 10, "slot": 7}, "picks": []}),
        encoding="utf-8",
    )
    config, picks = ManualDraftStore(path, DraftConfig()).load()
    assert not picks
    assert config.keeper_league is False
    assert config.custom_pick_order == []
    assert config.strategy["qb_earliest_round"] == 6
