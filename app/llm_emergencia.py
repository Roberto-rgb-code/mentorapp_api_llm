# app/llm_emergencia.py
import os
import json
import asyncio
from typing import Dict, Any, List, Literal
from fastapi import HTTPException

# OpenAI SDK (pip install openai>=1.40.0)
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")

Riesgo = Literal["bajo", "moderado", "alto", "critico"]

# Esquema EXACTO esperado por el frontend
RESPONSE_SCHEMA = {
    "type": "object",
    "properties": {
        "diagnostico_rapido": {
            "type": "string",
            "description": "Resumen ejecutivo y directo de la situación de emergencia detectada."
        },
        "acciones_inmediatas": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Lista priorizada de acciones urgentes (hoy/mañana)."
        },
        "riesgo_general": {
            "type": "string",
            "enum": ["bajo", "moderado", "alto", "critico"],
            "description": "Nivel de riesgo global estimado."
        },
        "recomendaciones_clave": {
            "type": "array",
            "items": {"type": "string"},
            "description": "Recomendaciones clave para estabilizar en el corto plazo."
        }
    },
    "required": [
        "diagnostico_rapido",
        "acciones_inmediatas",
        "riesgo_general",
        "recomendaciones_clave"
    ],
    "additionalProperties": False
}

client = OpenAI(api_key=OPENAI_API_KEY)

def _demo_payload() -> Dict[str, Any]:
  return {
      "diagnostico_rapido": (
          "Demo local sin OPENAI_API_KEY.\n"
          "Se observan señales de estrés de liquidez y caída de ventas. "
          "Riesgo operativo moderado-alto por retrasos en entregas y presión de costos."
      ),
      "acciones_inmediatas": [
          "Congelar gastos no esenciales por 14 días",
          "Priorizar cobros críticos y renegociar cuentas por pagar",
          "Contactar a clientes clave con plan de continuidad",
          "Revisar inventario y programar compras mínimas"
      ],
      "riesgo_general": "alto",
      "recomendaciones_clave": [
          "Proteger flujo de caja con proyección semanal",
          "Ajustar capacidad operativa a la demanda vigente",
          "Iniciar plan comercial de recuperación 30–60 días",
          "Definir tableros de métricas diarias (ventas, caja, servicio)"
      ]
  }

async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza diagnóstico de EMERGENCIA con OpenAI (Responses + Structured Outputs)
    y devuelve el JSON EXACTO que consume el frontend.
    """
    # Fallback DEMO si no hay API key
    if not OPENAI_API_KEY:
        return _demo_payload()

    user_prompt = (
        "Eres un consultor de crisis empresarial. Recibes datos de un diagnóstico de EMERGENCIA.\n"
        "Objetivo: diagnóstico breve y MUY accionable, enfocado en medidas urgentes.\n\n"
        "Devuelve SOLO JSON cumpliendo estrictamente el esquema:\n"
        "- diagnostico_rapido: 4–6 líneas, claro y directo.\n"
        "- acciones_inmediatas: 4–8 acciones para 24–72 horas.\n"
        "- riesgo_general: uno de ['bajo','moderado','alto','critico'].\n"
        "- recomendaciones_clave: 4–8 acciones para 2–4 semanas.\n\n"
        "Datos:\n"
        f"{json.dumps(diagnostico_data, ensure_ascii=False, indent=2)}\n\n"
        "Responde EXCLUSIVAMENTE con JSON válido que cumpla el esquema."
    )

    try:
        resp = await _create_response_async(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": "Responde solo con JSON válido que cumpla el esquema."},
                {"role": "user", "content": user_prompt},
            ],
            json_schema=RESPONSE_SCHEMA,
        )

        # Normalizar salida
        if isinstance(resp, dict):
            return _coerce_types(resp)

        if isinstance(resp, str):
            parsed = json.loads(resp)
            return _coerce_types(parsed)

        text = str(resp)
        parsed = json.loads(text)
        return _coerce_types(parsed)

    except Exception as e:
        # Devuelve error con detalle para que el frontend pueda mostrarlo
        raise HTTPException(
            status_code=502,
            detail=f"Fallo con OpenAI ({MODEL_NAME}): {str(e)}"
        )

def _coerce_types(obj: Dict[str, Any]) -> Dict[str, Any]:
    """Asegura tipos mínimos del esquema y recorta campos imprevistos."""
    out: Dict[str, Any] = {}

    # diagnostico_rapido
    dr = obj.get("diagnostico_rapido")
    out["diagnostico_rapido"] = str(dr) if dr is not None else ""

    # acciones_inmediatas
    ai = obj.get("acciones_inmediatas") or []
    out["acciones_inmediatas"] = [str(x) for x in ai if isinstance(x, (str, int, float))][:12]

    # riesgo_general
    rg = str(obj.get("riesgo_general", "")).lower()
    if rg not in ("bajo", "moderado", "alto", "critico"):
        rg = "moderado"
    out["riesgo_general"] = rg

    # recomendaciones_clave
    rc = obj.get("recomendaciones_clave") or []
    out["recomendaciones_clave"] = [str(x) for x in rc if isinstance(x, (str, int, float))][:12]

    return out

# —— Helper para Responses con json_schema —— #
async def _create_response_async(model: str, messages, json_schema: dict):
    """
    Llama al Responses API con response_format=json_schema.
    El SDK es sync; encapsulamos en hilo usando asyncio.to_thread.
    """
    def _call():
        if hasattr(client, "responses"):
            r = client.responses.create(
                model=model,
                input=messages,
                response_format={
                    "type": "json_schema",
                    "json_schema": {
                        "name": "DiagnosticoEmergenciaSchema",
                        "schema": json_schema,
                        "strict": True,
                    }
                },
            )
            # Intentar parseo estructurado directo
            try:
                return r.output_parsed
            except Exception:
                pass
            # Fallback: texto
            if getattr(r, "output", None) and getattr(r.output, "content", None):
                c0 = r.output.content[0]
                text = getattr(c0, "text", None)
                return text if text is not None else getattr(r, "output_text", None)
            return getattr(r, "output_text", None)

        # Fallback a chat.completions con JSON mode
        completion = client.chat.completions.create(
            model=model,
            messages=messages,
            response_format={"type": "json_object"},
            temperature=0.2,
        )
        return completion.choices[0].message.content

    return await asyncio.to_thread(_call)
