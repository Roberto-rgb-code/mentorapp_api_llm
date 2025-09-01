# app/llm_emergencia.py
import os
import json
import asyncio
from typing import Dict, Any
from fastapi import HTTPException

# OpenAI SDK (pip install openai>=1.40.0)
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")

# === Esquema EXACTO que espera tu frontend de emergencia ===
# {
#   diagnostico_rapido: string,
#   acciones_inmediatas: string[],
#   riesgo_general: "bajo" | "moderado" | "alto" | "critico",
#   recomendaciones_clave: string[]
# }
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

async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un diagnóstico de EMERGENCIA con OpenAI (Responses + Structured Outputs)
    y devuelve el JSON EXACTO que consume el frontend.
    """
    # Fallback DEMO si no hay API key (útil en local)
    if not OPENAI_API_KEY:
        return {
            "diagnostico_rapido": "Demo local sin OPENAI_API_KEY. Empresa en estrés de liquidez y caída de ventas.",
            "acciones_inmediatas": [
                "Congelar gastos no esenciales 14 días",
                "Priorizar cobros críticos y renegociar pagos",
                "Comunicar a clientes clave un plan de continuidad",
            ],
            "riesgo_general": "alto",
            "recomendaciones_clave": [
                "Proteger flujo de caja semanal",
                "Ajustar capacidad operativa a demanda actual",
                "Definir plan comercial de recuperación 30-60 días"
            ]
        }

    user_prompt = (
        "Eres un consultor de crisis empresarial. Recibes datos de un diagnóstico de EMERGENCIA.\n"
        "Tu objetivo: entregar un diagnóstico muy breve y accionable, manteniendo foco en medidas urgentes.\n\n"
        "Devuelve SOLO JSON cumpliendo estrictamente el esquema:\n"
        "- diagnostico_rapido: resumen ejecutivo en 4–6 líneas, tono claro y directo.\n"
        "- acciones_inmediatas: 4–8 acciones priorizadas para las próximas 24–72 horas.\n"
        "- riesgo_general: uno de ['bajo','moderado','alto','critico'].\n"
        "- recomendaciones_clave: 4–8 recomendaciones de estabilización para 2–4 semanas.\n\n"
        "Datos del diagnóstico de emergencia:\n"
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

        if isinstance(resp, dict):
            return resp

        if isinstance(resp, str):
            return json.loads(resp)

        text = str(resp)
        return json.loads(text)

    except Exception as e:
        # No dejes reventar el flujo del frontend; entrega un payload útil.
        raise HTTPException(
            status_code=502,
            detail=f"Fallo con OpenAI ({MODEL_NAME}): {str(e)}"
        )

# —— Helpers (idéntico enfoque al módulo 'profundo') ——
async def _create_response_async(model: str, messages, json_schema: dict):
    """
    Llama al Responses API con response_format=json_schema.
    Nota: el SDK Python de OpenAI no es nativamente async; usamos hilo con asyncio.to_thread.
    """
    def _call():
        try:
            if hasattr(client, "responses"):
                r = client.responses.create(
                    model=model,
                    input=messages,
                    response_format={
                        "type": "json_schema",
                        "json_schema": {
                            "name": "DiagnosticoEmergenciaSchema",
                            "schema": json_schema,
                            "strict": True
                        }
                    },
                )
                # Intentar parseo estructurado directo:
                try:
                    return r.output_parsed
                except Exception:
                    # Fallback: extraer texto
                    if getattr(r, "output", None) and getattr(r.output, "content", None):
                        c0 = r.output.content[0]
                        text = getattr(c0, "text", None)
                        return text if text is not None else getattr(r, "output_text", None)
                    return getattr(r, "output_text", None)

            # Fallback a Chat Completions en JSON mode (menos estricto)
            completion = client.chat.completions.create(
                model=model,
                messages=messages,
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return completion.choices[0].message.content

        except Exception as e:
            raise e

    return await asyncio.to_thread(_call)
