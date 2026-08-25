from __future__ import annotations


def slot_for_pick(overall_pick: int, teams: int, custom_order: list[int] | None = None) -> int:
    if overall_pick < 1:
        raise ValueError("overall_pick must be at least 1")
    if teams < 2:
        raise ValueError("teams must be at least 2")
    if custom_order:
        if overall_pick > len(custom_order):
            raise ValueError("overall_pick exceeds the custom draft order")
        slot = int(custom_order[overall_pick - 1])
        if not 1 <= slot <= teams:
            raise ValueError("custom draft owner is outside the league size")
        return slot
    round_number = (overall_pick - 1) // teams + 1
    position_in_round = (overall_pick - 1) % teams + 1
    return position_in_round if round_number % 2 == 1 else teams + 1 - position_in_round


def picks_for_slot(
    slot: int,
    teams: int,
    rounds: int,
    custom_order: list[int] | None = None,
) -> list[int]:
    if not 1 <= slot <= teams:
        raise ValueError("slot must be within the league size")
    if custom_order:
        return [index for index, owner in enumerate(custom_order, start=1) if int(owner) == slot]
    picks: list[int] = []
    for round_number in range(1, rounds + 1):
        in_round = slot if round_number % 2 == 1 else teams + 1 - slot
        picks.append((round_number - 1) * teams + in_round)
    return picks


def next_pick_for_slot(
    completed_picks: int,
    slot: int,
    teams: int,
    rounds: int,
    custom_order: list[int] | None = None,
) -> int | None:
    for pick in picks_for_slot(slot, teams, rounds, custom_order):
        if pick > completed_picks:
            return pick
    return None


def picks_until_turn(
    completed_picks: int,
    slot: int,
    teams: int,
    rounds: int,
    custom_order: list[int] | None = None,
) -> int | None:
    next_pick = next_pick_for_slot(completed_picks, slot, teams, rounds, custom_order)
    if next_pick is None:
        return None
    return max(0, next_pick - completed_picks - 1)


def total_picks(teams: int, rounds: int, custom_order: list[int] | None = None) -> int:
    return len(custom_order) if custom_order else teams * rounds
