import json

import pytest

from app.models import Player
from app.providers import enrich_with_sleeper, fetch_adp


def test_sleeper_enrichment_matches_yahoo_id() -> None:
    players = [Player(name="Player Name", position="", yahoo_id="123")]
    sleeper = {
        "sleeper-id": {
            "full_name": "Different Display Name",
            "yahoo_id": 123,
            "fantasy_positions": ["WR"],
            "team": "DAL",
            "injury_status": "Questionable",
        }
    }
    enriched = enrich_with_sleeper(players, sleeper)
    assert enriched[0].position == "WR"
    assert enriched[0].team == "DAL"
    assert enriched[0].injury_status == "Questionable"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "cached_payload",
    [
        {"players": [{"name": "Player One", "position": "RB", "team": "DAL", "adp": 12.3}]},
        [{"name": "Player One", "position": "RB", "team": "DAL", "adp": 12.3}],
    ],
)
async def test_fetch_adp_accepts_dict_or_list_cache(tmp_path, cached_payload) -> None:
    cache_path = tmp_path / "adp.json"
    cache_path.write_text(json.dumps(cached_payload), encoding="utf-8")
    players = await fetch_adp(cache_path, teams=10)
    assert players[0].name == "Player One"
    assert players[0].adp == 12.3
