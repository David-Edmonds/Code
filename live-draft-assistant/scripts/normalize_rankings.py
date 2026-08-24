from __future__ import annotations

import argparse
import csv
from pathlib import Path


def first(row: dict[str, str], names: list[str]) -> str:
    lowered = {key.strip().lower(): (value or "").strip() for key, value in row.items() if key}
    return next((lowered[name] for name in names if lowered.get(name)), "")


def main() -> None:
    parser = argparse.ArgumentParser(description="Normalize an expert rankings CSV for the draft assistant")
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()

    with args.input.open("r", encoding="utf-8-sig", newline="") as source:
        reader = csv.DictReader(source)
        rows = list(reader)

    output_rows = []
    for index, row in enumerate(rows, start=1):
        name = first(row, ["player", "player name", "name", "player_name"])
        if not name:
            continue
        output_rows.append(
            {
                "rank": first(row, ["rank", "overall rank", "ecr", "rk"]) or index,
                "player": name,
                "position": first(row, ["position", "pos", "position rank"]),
                "team": first(row, ["team", "tm"]),
                "tier": first(row, ["tier"]),
                "adp": first(row, ["adp"]),
                "source": args.input.stem,
            }
        )

    args.output.parent.mkdir(parents=True, exist_ok=True)
    with args.output.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=["rank", "player", "position", "team", "tier", "adp", "source"])
        writer.writeheader()
        writer.writerows(output_rows)
    print(f"Wrote {len(output_rows)} players to {args.output}")


if __name__ == "__main__":
    main()
