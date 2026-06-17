"""Cliente Anthropic: JSON estricto para diagnósticos."""

from __future__ import annotations

import json
import logging
import os
import re
from typing import Any

import anthropic

logger = logging.getLogger(__name__)

_DEFAULT_SONNET = "claude-sonnet-4-5"
# Modelos con fecha que Anthropic deprecó → alias vigentes
_MODEL_ALIASES: dict[str, str] = {
    "claude-sonnet-4-20250514": "claude-sonnet-4-5",
    "claude-sonnet-4-5-20250917": "claude-sonnet-4-5",
    "claude-sonnet-4-6-20260217": "claude-sonnet-4-6",
    "claude-3-5-sonnet-20241022": "claude-sonnet-4-5",
    "claude-3-5-sonnet-latest": "claude-sonnet-4-5",
}


def _resolve_model() -> str:
    raw = (
        os.environ.get("ANTHROPIC_MODEL_NAME")
        or os.environ.get("ANTHROPIC_MODEL")
        or _DEFAULT_SONNET
    )
    model = str(raw).strip().strip('"').strip("'")
    return _MODEL_ALIASES.get(model, model)


def _models_to_try() -> list[str]:
    primary = _resolve_model()
    fallbacks = ["claude-sonnet-4-5", "claude-sonnet-4-6"]
    ordered = [primary]
    for m in fallbacks:
        if m not in ordered:
            ordered.append(m)
    return ordered


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
    client = anthropic.Anthropic(api_key=key)
    for model in _models_to_try():
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=[{"role": "user", "content": user}],
            )
        except Exception as e:  # noqa: BLE001
            logger.warning("Anthropic messages.create falló (%s): %s", model, e)
            continue
        parts: list[str] = []
        for b in msg.content:
            if b.type == "text":
                parts.append(b.text)
        raw = "\n".join(parts)
        parsed = extract_json_object(raw)
        if parsed is None and raw:
            logger.warning(
                "Anthropic devolvió texto sin JSON parseable (primeros 120 chars): %s",
                raw[:120],
            )
        return parsed
    return None

def call_claude_text(system: str, messages: list[dict[str, str]], max_tokens: int = 1000) -> str | None:
    key = os.environ.get("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        return None
    client = anthropic.Anthropic(api_key=key)
    for model in _models_to_try():
        try:
            msg = client.messages.create(
                model=model,
                max_tokens=max_tokens,
                system=system,
                messages=messages,
            )
        except Exception as e:
            logger.warning("Anthropic text messages.create falló (%s): %s", model, e)
            continue
        parts: list[str] = []
        for b in msg.content:
            if b.type == "text":
                parts.append(b.text)
        return "\n".join(parts)
    return None
