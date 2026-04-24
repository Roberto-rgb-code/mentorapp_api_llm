"""Cliente Anthropic: JSON estricto para diagnósticos."""

from __future__ import annotations

import json
import os
import re
from typing import Any

import anthropic

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-3-5-sonnet-20241022")


def extract_json_object(text: str) -> dict[str, Any] | None:
    t = text.strip()
    m = re.search(r"\{[\s\S]*\}\s*$", t)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass
    fence = re.search(r"```(?:json)?\s*([\s\S]*?)```", t, re.IGNORECASE)
    if fence:
        try:
            return json.loads(fence.group(1).strip())
        except json.JSONDecodeError:
            return None
    try:
        return json.loads(t)
    except json.JSONDecodeError:
        return None


def call_claude_json(system: str, user: str, max_tokens: int = 6000) -> dict[str, Any] | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip()
    if not key:
        return None
    client = anthropic.Anthropic(api_key=key)
    msg = client.messages.create(
        model=DEFAULT_MODEL,
        max_tokens=max_tokens,
        system=system,
        messages=[{"role": "user", "content": user}],
    )
    parts = []
    for b in msg.content:
        if b.type == "text":
            parts.append(b.text)
    raw = "\n".join(parts)
    return extract_json_object(raw)
