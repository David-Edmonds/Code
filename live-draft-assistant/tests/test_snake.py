from app.snake import next_pick_for_slot, picks_for_slot, picks_until_turn, slot_for_pick


def test_ten_team_slot_seven_schedule() -> None:
    assert picks_for_slot(7, 10, 6) == [7, 14, 27, 34, 47, 54]


def test_slot_for_pick_reverses_even_rounds() -> None:
    assert slot_for_pick(1, 10) == 1
    assert slot_for_pick(10, 10) == 10
    assert slot_for_pick(11, 10) == 10
    assert slot_for_pick(14, 10) == 7


def test_next_pick_and_wait() -> None:
    assert next_pick_for_slot(7, 7, 10, 16) == 14
    assert picks_until_turn(7, 7, 10, 16) == 6
