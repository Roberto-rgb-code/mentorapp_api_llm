"""Cliente Anthropic: JSON estricto para diagnósticos."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_DEFAULT_SONNET = "claude-sonnet-4-20250514"


def _resolve_model() -> str:
    raw = (
        os.environ.get("ANTHROPIC_MODEL_NAME")
        or os.environ.get("ANTHROPIC_MODEL")
        or _DEFAULT_SONNET
    )
    return str(raw).strip().strip('"').strip("'")


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
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        return None
    model = _resolve_model()
    try:
        client = anthropic.Anthropic(api_key=key)
        msg = client.messages.create(
            model=model,
            max_tokens=max_tokens,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
    except Exception as e:  # noqa: BLE001 — devolver None y usar fallback en routers
        logger.warning("Anthropic messages.create falló (%s): %s", model, e)
        return None
    parts: list[str] = []
    for b in msg.content:
        if b.type == "text":
            parts.append(b.text)
    raw = "\n".join(parts)
    parsed = extract_json_object(raw)
    if parsed is None and raw:
        logger.warning("Anthropic devolvió texto sin JSON parseable (primeros 120 chars): %s", raw[:120])
    return parsed
