from __future__ import annotations

import json

from .models import Player


async def ai_review(
    *,
    api_key: str,
    model: str,
    league_context: dict,
    roster: list[Player],
    candidates: list[Player],
) -> str:
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY is not configured")
    try:
        from openai import AsyncOpenAI
    except ImportError as exc:
        raise RuntimeError("Install the OpenAI Python package to use AI review") from exc
    client = AsyncOpenAI(api_key=api_key)
    payload = {
        "league": league_context,
        "my_roster": [player.to_dict() for player in roster],
        "best_available": [player.to_dict() for player in candidates[:12]],
    }
    response = await client.responses.create(
        model=model,
        reasoning={"effort": "low"},
        input=[
            {
                "role": "system",
                "content": (
                    "You are an elite redraft fantasy-football draft analyst. "
                    "Use the supplied live board, full-PPR roster construction, "
                    "positional scarcity, and market value. Return exactly three "
                    "player names in order, one per line. No explanation. Never "
                    "name a drafted player."
                ),
            },
            {"role": "user", "content": json.dumps(payload, ensure_ascii=False)},
        ],
        max_output_tokens=80,
    )
    return response.output_text.strip()
