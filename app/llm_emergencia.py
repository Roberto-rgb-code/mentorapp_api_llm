# app/llm_emergencia.py
import os
import json
import asyncio
from typing import Dict, Any
from fastapi import HTTPException
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY)

async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un diagnóstico de EMERGENCIA con OpenAI Chat Completions
    y devuelve el JSON EXACTO que consume el frontend.
    """
    # Fallback demo si no hay API key
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
                "Definir plan comercial de recuperación 30-60 días",
            ],
        }

    user_prompt = (
        "Eres un consultor de crisis empresarial. Recibes datos de un diagnóstico de EMERGENCIA.\n"
        "Tu objetivo: entregar un diagnóstico muy breve y accionable, manteniendo foco en medidas urgentes.\n\n"
        "Devuelve SOLO JSON con este esquema:\n"
        "- diagnostico_rapido: resumen ejecutivo en 4–6 líneas, tono claro y directo.\n"
        "- acciones_inmediatas: 4–8 acciones priorizadas para las próximas 24–72 horas.\n"
        "- riesgo_general: uno de ['bajo','moderado','alto','critico'].\n"
        "- recomendaciones_clave: 4–8 recomendaciones de estabilización para 2–4 semanas.\n\n"
        f"Datos del diagnóstico de emergencia:\n{json.dumps(diagnostico_data, ensure_ascii=False, indent=2)}\n\n"
        "Responde EXCLUSIVAMENTE con JSON válido."
    )

    try:
        def _call():
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Responde solo con JSON válido."},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},  # 👈 ahora sí válido
                temperature=0.2,
            )
            return completion.choices[0].message.content

        result = await asyncio.to_thread(_call)

        return json.loads(result)

    except Exception as e:
        raise HTTPException(
            status_code=502,
            detail=f"Fallo con OpenAI ({MODEL_NAME}): {str(e)}",
        )
