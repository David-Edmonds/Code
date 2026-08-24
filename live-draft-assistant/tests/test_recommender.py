from app.models import Player
from app.recommender import recommend


def test_avoids_early_kicker_and_defense() -> None:
    available = [
        Player(name="Wide Receiver", position="WR", custom_rank=20),
        Player(name="Kicker", position="K", custom_rank=1),
        Player(name="Defense", position="DEF", custom_rank=2),
    ]
    choices = recommend(available, [], overall_pick=20, teams=10)
    assert choices[0].name == "Wide Receiver"


def test_does_not_push_second_qb_in_one_qb_league() -> None:
    roster = [Player(name="QB One", position="QB")]
    available = [
        Player(name="QB Two", position="QB", custom_rank=30),
        Player(name="RB One", position="RB", custom_rank=35),
    ]
    choices = recommend(available, roster, overall_pick=60, teams=10)
    assert choices[0].name == "RB One"


def test_penalizes_out_player() -> None:
    available = [
        Player(name="Healthy", position="WR", custom_rank=25),
        Player(name="Out", position="WR", custom_rank=20, injury_status="Out"),
    ]
    choices = recommend(available, [], overall_pick=25, teams=10)
    assert choices[0].name == "Healthy"
