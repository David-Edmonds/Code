from __future__ import annotations

import re
import unicodedata
from collections.abc import Iterable
from typing import Any


def normalize_name(value: str) -> str:
    text = unicodedata.normalize("NFKD", value or "")
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = text.lower().replace("’", "'")
    text = re.sub(r"\b(jr|sr|ii|iii|iv)\.?\b", "", text)
    text = re.sub(r"[^a-z0-9]+", "", text)
    return text


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def find_all(node: Any, key: str) -> list[Any]:
    found: list[Any] = []
    if isinstance(node, dict):
        for current_key, value in node.items():
            if current_key == key:
                found.extend(ensure_list(value))
            found.extend(find_all(value, key))
    elif isinstance(node, list):
        for item in node:
            found.extend(find_all(item, key))
    return found


def first_scalar(value: Any, default: str = "") -> str:
    if value is None:
        return default
    if isinstance(value, dict):
        if "#text" in value:
            return str(value["#text"])
        return default
    if isinstance(value, list):
        return first_scalar(value[0], default) if value else default
    return str(value)


def safe_float(value: Any) -> float | None:
    try:
        if value in (None, ""):
            return None
        return float(value)
    except (TypeError, ValueError):
        return None


def safe_int(value: Any) -> int | None:
    try:
        if value in (None, ""):
            return None
        return int(float(value))
    except (TypeError, ValueError):
        return None


def unique_by(items: Iterable[Any], key_func) -> list[Any]:
    seen: set[Any] = set()
    result: list[Any] = []
    for item in items:
        marker = key_func(item)
        if marker in seen:
            continue
        seen.add(marker)
        result.append(item)
    return result
