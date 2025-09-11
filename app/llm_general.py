# app/llm_general.py
import os
import json
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException

# OpenAI SDK (pip install openai>=1.40.0)
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# ---- Utilidades ----
def _respuesta_vacia(mensaje_error: str = "No se pudo generar el análisis.") -> Dict[str, Any]:
    return {
        "resumen_ejecutivo": f"{mensaje_error}",
        "areas_oportunidad": ["Error en el análisis con IA."],
        "recomendaciones_clave": ["Verifica la configuración de la API o intenta de nuevo más tarde."],
        "puntuacion_madurez_promedio": 0.0,
        "nivel_madurez_general": "muy_bajo",
    }

def _nivel_madurez_desde_promedio(avg: float) -> str:
    if avg >= 4.6:
        return "muy_alto"
    if avg >= 4.0:
        return "alto"
    if avg >= 3.0:
        return "medio"
    if avg >= 2.0:
        return "bajo"
    return "muy_bajo"

def _extraer_likert(d: Dict[str, Any]) -> Tuple[float, str]:
    """Calcula el promedio de todas las respuestas tipo Likert (claves que inician con dg_, fa_, op_, mv_, rh_, lc_)."""
    scores: List[int] = []
    for k, v in d.items():
        if k.startswith(("dg_", "fa_", "op_", "mv_", "rh_", "lc_")) and str(v) in {"1", "2", "3", "4", "5"}:
            scores.append(int(v))
    if not scores:
        return 0.0, "muy_bajo"
    avg = round(sum(scores) / len(scores), 2)
    return avg, _nivel_madurez_desde_promedio(avg)

def _formatear_datos_para_prompt(d: Dict[str, Any]) -> str:
    """Convierte el dict de respuestas en líneas legibles para el prompt, excluyendo campos internos vacíos."""
    partes: List[str] = []
    for key, value in d.items():
        if key in {"userId", "createdAt"} or value in ("", None):
            continue
        partes.append(f"- {key}: {value}")
    return "\n".join(partes)

# ---- Analizador principal ----
async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial general usando OpenAI (gpt-4.1-mini),
    devolviendo el JSON EXACTO que consume el frontend:
    {
      resumen_ejecutivo: string,
      areas_oportunidad: string[],
      recomendaciones_clave: string[],
      puntuacion_madurez_promedio: number,
      nivel_madurez_general: "muy_bajo"|"bajo"|"medio"|"alto"|"muy_alto"
    }
    """

    # Fallback DEMO si no hay API key (útil en local)
    if not OPENAI_API_KEY:
        avg, nivel = _extraer_likert(diagnostico_data)
        return {
            "resumen_ejecutivo": "Demo local sin OPENAI_API_KEY. Se detectan oportunidades en planeación, finanzas y marketing.",
            "areas_oportunidad": [
                "Definición y seguimiento de objetivos (OKR)",
                "Control y proyección de flujo de caja",
                "Estandarización de procesos operativos",
                "Definición de ICP y canal comercial",
            ],
            "recomendaciones_clave": [
                "Implantar tablero semanal con KPIs",
                "Auditar gastos y renegociar costos",
                "Documentar procesos críticos (SOPs)",
                "Campañas con propuesta de valor segmentada",
            ],
            "puntuacion_madurez_promedio": avg,
            "nivel_madurez_general": nivel,
        }

    # Construcción del prompt
    datos_fmt = _formatear_datos_para_prompt(diagnostico_data)
    avg, nivel = _extraer_likert(diagnostico_data)

    system_msg = {
        "role": "system",
        "content": (
            "Eres un consultor de negocios experto. Responde EXCLUSIVAMENTE con JSON válido. "
            "El JSON debe cumplir el siguiente contrato:\n"
            "{\n"
            '  "resumen_ejecutivo": string,\n'
            '  "areas_oportunidad": string[],\n'
            '  "recomendaciones_clave": string[],\n'
            '  "puntuacion_madurez_promedio": number,\n'
            '  "nivel_madurez_general": "muy_bajo"|"bajo"|"medio"|"alto"|"muy_alto"\n'
            "}\n"
            "Nada de texto fuera de JSON."
        ),
    }

    user_msg = {
        "role": "user",
        "content": (
            "Analiza el siguiente diagnóstico general. Devuelve SOLO el JSON con:\n"
            "- resumen_ejecutivo: breve, claro y accionable.\n"
            "- areas_oportunidad: 4–8 puntos concretos.\n"
            "- recomendaciones_clave: 4–8 acciones prácticas (0-90 días).\n"
            "- puntuacion_madurez_promedio: número (puedes usar el cálculo sugerido si aplica).\n"
            "- nivel_madurez_general: muy_bajo | bajo | medio | alto | muy_alto.\n\n"
            "Interpretación Likert:\n"
            "1: Difuso; 2: Ocasional; 3: Regular sin procesos; 4: Correcto y estandarizado; 5: Excelente y automatizado.\n\n"
            f"Sugerencia de cálculo (opcional) basada en las respuestas: promedio={avg}, nivel={nivel}.\n\n"
            "Datos:\n"
            f"{datos_fmt}\n\n"
            "Recuerda: responde SOLO con JSON válido."
        ),
    }

    try:
        # Usamos chat.completions con JSON mode (json_object) para evitar problemas con Responses API
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[system_msg, user_msg],
            response_format={"type": "json_object"},
            temperature=0.2,
        )

        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)

        # Validación mínima y saneo de tipos/valores
        if not isinstance(parsed.get("resumen_ejecutivo", ""), str):
            parsed["resumen_ejecutivo"] = "No se pudo generar el resumen."

        def _as_list_str(x):
            if isinstance(x, list):
                return [str(i) for i in x][:12]
            return []

        parsed["areas_oportunidad"] = _as_list_str(parsed.get("areas_oportunidad", []))
        parsed["recomendaciones_clave"] = _as_list_str(parsed.get("recomendaciones_clave", []))

        # Recalcular con datos reales del usuario (tiene prioridad)
        avg_usr, nivel_usr = _extraer_likert(diagnostico_data)
        parsed["puntuacion_madurez_promedio"] = float(parsed.get("puntuacion_madurez_promedio", avg_usr or 0.0))
        parsed["nivel_madurez_general"] = str(parsed.get("nivel_madurez_general", nivel_usr or "muy_bajo"))

        # Asegurar consistencia si el modelo devolvió algo fuera de rango
        if parsed["nivel_madurez_general"] not in {"muy_bajo", "bajo", "medio", "alto", "muy_alto"}:
            parsed["nivel_madurez_general"] = nivel_usr

        # Si el promedio no tiene sentido, aplicamos nuestro cálculo
        if parsed["puntuacion_madurez_promedio"] <= 0.0 and avg_usr > 0.0:
            parsed["puntuacion_madurez_promedio"] = avg_usr
            parsed["nivel_madurez_general"] = nivel_usr

        return parsed

    except Exception as e:
        # No reventar al frontend: retornar payload útil con mensaje de error (+ cálculo propio si aplica)
        avg2, nivel2 = _extraer_likert(diagnostico_data)
        return {
            "resumen_ejecutivo": f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}",
            "areas_oportunidad": ["No fue posible generar áreas de oportunidad."],
            "recomendaciones_clave": ["Intenta nuevamente en unos minutos o verifica tu API Key."],
            "puntuacion_madurez_promedio": avg2,
            "nivel_madurez_general": nivel2,
        }
