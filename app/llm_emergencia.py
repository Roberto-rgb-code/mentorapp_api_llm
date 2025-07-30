# app/llm_emergencia.py
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

# Esquema de respuesta esperado del LLM para diagnóstico de emergencia
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "situacion_critica": {"type": "STRING", "description": "Descripción de la situación de emergencia identificada."},
        "acciones_inmediatas": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de acciones urgentes a tomar."
        },
        "impacto_potencial": {
            "type": "STRING",
            "description": "Descripción del impacto potencial si no se actúa rápidamente."
        },
        "recomendaciones_corto_plazo": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Recomendaciones para estabilizar la situación en el corto plazo."
        },
        "contactos_clave_sugeridos": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Tipos de profesionales o entidades a contactar en la emergencia (ej. abogado, contador, especialista en crisis)."
        }
    },
    "required": [
        "situacion_critica",
        "acciones_inmediatas",
        "impacto_potencial",
        "recomendaciones_corto_plazo",
        "contactos_clave_sugeridos"
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
            async with httpx.AsyncClient(timeout=60.0) as client:
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


async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial de emergencia utilizando un LLM.
    Se espera que 'diagnostico_data' contenga información sobre una crisis o situación urgente.
    """
    prompt = (
        "Eres un consultor de crisis empresarial. Recibes un diagnóstico de una situación de emergencia. "
        "Tu objetivo es identificar rápidamente la situación crítica, proponer acciones inmediatas, "
        "describir el impacto potencial si no se actúa, dar recomendaciones a corto plazo para estabilizar "
        "la situación y sugerir tipos de contactos clave a buscar (ej. abogado, especialista en crisis, etc.).\n\n"
        "Aquí están los datos del diagnóstico de emergencia:\n"
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
        print(f"Error al analizar el diagnóstico de emergencia con LLM: {e}")
        return {
            "situacion_critica": "No se pudo generar el análisis de emergencia debido a un error.",
            "acciones_inmediatas": ["Error en el análisis de IA."],
            "impacto_potencial": "No se pudo determinar el impacto potencial.",
            "recomendaciones_corto_plazo": ["Verifica la configuración de la API o intenta de nuevo más tarde."],
            "contactos_clave_sugeridos": ["Error en el análisis de IA."]
        }

