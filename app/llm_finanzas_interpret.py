# app/llm_finanzas_interpret.py
# Interpretación narrativa del módulo Análisis financiero (MentHIA web) — Anthropic, misma credencial que express/general.

import json
import os
from typing import Any, Dict

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import HTTPException

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-sonnet-4-20250514").strip().strip('"').strip("'")

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM = """Eres un analista financiero senior para PYME en español (México/LATAM), integrado en MentHIA.

REGLAS ESTRICTAS:
- Solo interpreta y prioriza con base en los números y ratios que recibes en el JSON. No inventes datos ni completes campos vacíos.
- Si falta información para un tema (DCF, beta, etc.), dilo en una frase breve sin suponer cifras.
- Tono: profesional, claro, sin jerga innecesaria. Sin emojis.
- Estructura la respuesta en: (1) Resumen ejecutivo 4-6 bullets cortos. (2) Fortalezas. (3) Riesgos u omisiones. (4) 3 acciones concretas para los próximos 30 días.
- Incluye una línea final: "Esta interpretación es orientativa y no sustituye asesoría fiscal, legal ni de inversión."
"""


async def interpretar_finanzas_narrativa(payload: Dict[str, Any]) -> Dict[str, Any]:
    """
    Recibe el JSON compacto armado por la app Next (estados, ratios, escenarios, etc.).
    Devuelve dict con ok, interpretacion, modelo, fallback (compatible con /pages/api/finanzas/interpretar).
    """
    if not isinstance(payload, dict):
        raise HTTPException(400, "payload debe ser un objeto")

    raw = json.dumps(payload, ensure_ascii=False)
    if len(raw) > 48_000:
        raise HTTPException(400, "payload demasiado grande")

    if not client:
        return {
            "ok": True,
            "interpretacion": (
                "La interpretación con IA no está disponible: falta ANTHROPIC_API_KEY en mentorapp_api_llm (.env). "
                "Los números del informe en la web siguen siendo válidos."
            ),
            "modelo": "none",
            "fallback": True,
        }

    user_msg = f"Datos calculados en la app (JSON). Interpreta:\n\n{raw}"

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            system=SYSTEM,
            max_tokens=2048,
            temperature=0.35,
            messages=[{"role": "user", "content": user_msg}],
        )
        block = response.content[0]
        text = (getattr(block, "text", None) or "").strip()
        if not text:
            return {
                "ok": True,
                "interpretacion": "Claude devolvió una respuesta vacía. Intenta de nuevo más tarde.",
                "modelo": MODEL_NAME,
                "fallback": True,
            }
        return {
            "ok": True,
            "interpretacion": text,
            "modelo": MODEL_NAME,
            "fallback": False,
        }
    except Exception as e:
        print(f"[llm_finanzas_interpret] ERROR: {e}")
        return {
            "ok": True,
            "interpretacion": (
                f"No se pudo generar la interpretación con Claude. Revisa ANTHROPIC_API_KEY, modelo y cuotas. "
                f"Detalle: {e}"
            ),
            "modelo": MODEL_NAME,
            "fallback": True,
        }
