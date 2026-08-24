from __future__ import annotations


def slot_for_pick(overall_pick: int, teams: int) -> int:
    if overall_pick < 1:
        raise ValueError("overall_pick must be at least 1")
    if teams < 2:
        raise ValueError("teams must be at least 2")
    round_number = (overall_pick - 1) // teams + 1
    position_in_round = (overall_pick - 1) % teams + 1
    return position_in_round if round_number % 2 == 1 else teams + 1 - position_in_round


def picks_for_slot(slot: int, teams: int, rounds: int) -> list[int]:
    if not 1 <= slot <= teams:
        raise ValueError("slot must be within the league size")
    picks: list[int] = []
    for round_number in range(1, rounds + 1):
        in_round = slot if round_number % 2 == 1 else teams + 1 - slot
        picks.append((round_number - 1) * teams + in_round)
    return picks


def next_pick_for_slot(completed_picks: int, slot: int, teams: int, rounds: int) -> int | None:
    for pick in picks_for_slot(slot, teams, rounds):
        if pick > completed_picks:
            return pick
    return None


def picks_until_turn(completed_picks: int, slot: int, teams: int, rounds: int) -> int | None:
    next_pick = next_pick_for_slot(completed_picks, slot, teams, rounds)
    if next_pick is None:
        return None
    return max(0, next_pick - completed_picks - 1)
