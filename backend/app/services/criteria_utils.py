# -*- coding: utf-8 -*-
"""Utilities for parsing and formatting position evaluation criteria.

The criteria are stored as a JSON string in Position.preferences with the schema:
[
  {"name": "dimension_name", "description": "details", "weight": "high|medium|low"},
  ...
]

For backward compatibility, if preferences is plain text (not valid JSON array),
it is treated as a single free-text note.
"""

from __future__ import annotations

import json

WEIGHT_LABELS: dict[str, str] = {
    "high": "\u9ad8",
    "medium": "\u4e2d",
    "low": "\u4f4e",
}
WEIGHT_ORDER: dict[str, int] = {"high": 0, "medium": 1, "low": 2}


def parse_criteria(preferences: str) -> list[dict]:
    """Parse the preferences field into a list of criteria dicts.

    Returns an empty list if the field is empty or not valid JSON array.
    """
    if not preferences or not preferences.strip():
        return []
    try:
        data = json.loads(preferences)
        if isinstance(data, list):
            return [
                c for c in data
                if isinstance(c, dict) and c.get("name")
            ]
    except (json.JSONDecodeError, TypeError):
        pass
    return []


def format_criteria_for_prompt(preferences: str) -> str:
    """Convert stored preferences into prompt-ready text.

    Structured criteria are sorted by weight and formatted as a numbered list.
    Plain-text preferences are returned as-is for backward compatibility.
    """
    criteria = parse_criteria(preferences)
    if criteria:
        sorted_criteria = sorted(
            criteria, key=lambda c: WEIGHT_ORDER.get(c.get("weight", "medium"), 1)
        )
        lines = []
        for i, c in enumerate(sorted_criteria, 1):
            weight = WEIGHT_LABELS.get(c.get("weight", "medium"), "\u4e2d")
            desc = "\uff1a" + c["description"] if c.get("description") else ""
            lines.append(f"{i}. [{weight}\u4f18\u5148] {c['name']}{desc}")
        return "\n".join(lines)

    if preferences and preferences.strip():
        return preferences.strip()

    return ""


def format_criteria_section(preferences: str, section_title: str, instruction: str) -> str:
    """Build a complete prompt section from criteria, or return empty string."""
    text = format_criteria_for_prompt(preferences)
    if not text:
        return ""
    return f"\n\n## {section_title}\n{text}\n{instruction}"
