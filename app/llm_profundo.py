# app/llm_profundo.py
import os
import json
import time
import httpx
import asyncio # Necesario para asyncio.sleep
from typing import Dict, Any, List

# Define la URL base del API de Gemini
GEMINI_API_BASE_URL = "https://generativelanguage.googleapis.com/v1beta/models"
# Obtén la API Key de una variable de entorno o déjala vacía si Canvas la inyecta
API_KEY = os.getenv("GEMINI_API_KEY", "") # Deja vacío si Canvas la inyecta automáticamente
MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Modelo de Gemini para análisis

# Esquema de respuesta esperado del LLM para diagnóstico profundo
# Puedes personalizar este esquema según las necesidades de tu análisis profundo
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "analisis_detallado": {"type": "STRING", "description": "Análisis exhaustivo de los datos proporcionados."},
        "oportunidades_estrategicas": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de oportunidades estratégicas a largo plazo."
        },
        "riesgos_identificados": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de riesgos potenciales y su impacto."
        },
        "plan_accion_sugerido": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Pasos sugeridos para un plan de acción detallado."
        },
        "indicadores_clave_rendimiento": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "KPIs recomendados para monitorear el progreso."
        }
    },
    "required": [
        "analisis_detallado",
        "oportunidades_estrategicas",
        "riesgos_identificados",
        "plan_accion_sugerido",
        "indicadores_clave_rendimiento"
    ]
}

async def call_gemini_api_with_backoff(
    payload: Dict[str, Any],
    model_name: str,
    api_key: str,
    max_retries: int = 5,
    initial_delay: float = 1.0
) -> Dict[str, Any]:
    """
    Realiza una llamada al API de Gemini con reintentos y retroceso exponencial.
    """
    url = f"{GEMINI_API_BASE_URL}/{model_name}:generateContent?key={api_key}"
    headers = {'Content-Type': 'application/json'}

    for attempt in range(max_retries):
        try:
            async with httpx.AsyncClient(timeout=120.0) as client: # Aumentar el timeout para análisis profundos
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status() # Lanza una excepción para códigos de estado HTTP 4xx/5xx
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"Demasiadas solicitudes (429). Reintentando en {delay:.2f} segundos...")
                await asyncio.sleep(delay)
            else:
                print(f"Error HTTP: {e.response.status_code} - {e.response.text}")
                raise
        except httpx.RequestError as e:
            print(f"Error de solicitud: {e}")
            if attempt < max_retries - 1:
                delay = initial_delay * (2 ** attempt)
                print(f"Error de red. Reintentando en {delay:.2f} segundos...")
                await asyncio.sleep(delay)
            else:
                raise
        except Exception as e:
            print(f"Error inesperado: {e}")
            raise
    raise Exception("Fallo en la llamada al API de Gemini después de varios reintentos.")


async def analizar_diagnostico_profundo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial profundo utilizando un LLM.
    Se espera que 'diagnostico_data' contenga información más detallada que el diagnóstico general.
    """
    prompt = (
        "Eres un consultor de negocios altamente especializado en análisis estratégico y operativo. "
        "Recibes un diagnóstico empresarial con datos detallados. "
        "Realiza un análisis profundo identificando:\n"
        "1. Un análisis detallado de la situación actual.\n"
        "2. Oportunidades estratégicas a largo plazo.\n"
        "3. Riesgos potenciales y su impacto.\n"
        "4. Un plan de acción sugerido con pasos concretos.\n"
        "5. Indicadores clave de rendimiento (KPIs) recomendados para monitorear el progreso.\n\n"
        "Aquí están los datos del diagnóstico profundo:\n"
        f"{json.dumps(diagnostico_data, ensure_ascii=False, indent=2)}\n\n"
        "Por favor, devuelve la respuesta en formato JSON siguiendo el esquema proporcionado."
    )

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA
        }
    }

    try:
        response_json = await call_gemini_api_with_backoff(payload, MODEL_NAME, API_KEY)
        if response_json and response_json.get("candidates"):
            candidate = response_json["candidates"][0]
            if candidate.get("content") and candidate["content"].get("parts"):
                text_part = candidate["content"]["parts"][0].get("text")
                if text_part:
                    return json.loads(text_part)
        raise Exception("Estructura de respuesta inesperada del LLM.")
    except Exception as e:
        print(f"Error al analizar el diagnóstico profundo con LLM: {e}")
        return {
            "analisis_detallado": "No se pudo generar el análisis detallado debido a un error.",
            "oportunidades_estrategicas": ["Error en el análisis de IA."],
            "riesgos_identificados": ["Error en el análisis de IA."],
            "plan_accion_sugerido": ["Verifica la configuración de la API o intenta de nuevo más tarde."],
            "indicadores_clave_rendimiento": ["Error en el análisis de IA."]
        }

