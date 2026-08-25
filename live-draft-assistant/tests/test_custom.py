import pytest

from app.models import Player
from app.recommender import recommend
from app.rules import parse_custom_order, parse_keepers
from app.snake import next_pick_for_slot, picks_for_slot, slot_for_pick, total_picks


def test_custom_order_supports_traded_and_extra_picks() -> None:
    order = [1, 2, 3, 4, 5, 5, 2, 1, 3]
    assert slot_for_pick(6, 5, order) == 5
    assert picks_for_slot(5, 5, 2, order) == [5, 6]
    assert next_pick_for_slot(5, 5, 5, 2, order) == 6
    assert total_picks(5, 2, order) == 9


def test_parse_custom_order() -> None:
    assert parse_custom_order("1, 2 3\n2;1", 3) == [1, 2, 3, 2, 1]
    with pytest.raises(ValueError):
        parse_custom_order("1,4", 3)


def test_parse_keepers() -> None:
    keepers = parse_keepers("CeeDee Lamb | 7 | WR | DAL | Round 3", 10)
    assert keepers[0]["player_name"] == "CeeDee Lamb"
    assert keepers[0]["owner_slot"] == 7
    assert keepers[0]["note"] == "Round 3"


def test_strategy_targets_and_avoids_change_order() -> None:
    available = [
        Player(name="Neutral", position="WR", custom_rank=10),
        Player(name="Target", position="WR", custom_rank=13),
        Player(name="Avoid", position="WR", custom_rank=1),
    ]
    choices = recommend(
        available,
        [],
        overall_pick=10,
        teams=10,
        strategy={
            "preferred_players": ["Target"],
            "avoid_players": ["Avoid"],
            "preferred_bonus": 8,
            "avoid_penalty": 100,
        },
    )
    assert choices[0].name == "Target"
    assert choices[-1].name == "Avoid"
