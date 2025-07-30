# app/llm_gpt.py
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
MODEL_NAME = "gemini-2.5-flash-preview-05-20" # Usamos gemini-2.5-flash-preview-05-20 como LLM por defecto

# Esquema de respuesta esperado del LLM
# Debe coincidir con la interfaz LLMAnalysisResult en el frontend
RESPONSE_SCHEMA = {
    "type": "OBJECT",
    "properties": {
        "resumen_ejecutivo": {"type": "STRING", "description": "Resumen ejecutivo del diagnóstico."},
        "areas_oportunidad": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de áreas clave de oportunidad identificadas."
        },
        "recomendaciones_clave": {
            "type": "ARRAY",
            "items": {"type": "STRING"},
            "description": "Lista de recomendaciones accionables para la empresa."
        },
        "puntuacion_madurez_promedio": {
            "type": "NUMBER",
            "description": "Puntuación promedio de madurez basada en las respuestas Likert."
        },
        "nivel_madurez_general": {
            "type": "STRING",
            "enum": ["muy_bajo", "bajo", "medio", "alto", "muy_alto"],
            "description": "Nivel general de madurez de la empresa."
        }
    },
    "required": [
        "resumen_ejecutivo",
        "areas_oportunidad",
        "recomendaciones_clave",
        "puntuacion_madurez_promedio",
        "nivel_madurez_general"
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
            async with httpx.AsyncClient(timeout=60.0) as client: # Aumentar el timeout
                response = await client.post(url, headers=headers, json=payload)
                response.raise_for_status() # Lanza una excepción para códigos de estado HTTP 4xx/5xx
                return response.json()
        except httpx.HTTPStatusError as e:
            if e.response.status_code == 429 and attempt < max_retries - 1:
                # Too Many Requests - Implementar retroceso exponencial
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


async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial general utilizando un LLM.
    Genera un resumen, áreas de oportunidad, recomendaciones y un nivel de madurez.
    """
    # Construir el prompt para el LLM
    prompt_parts = [
        "Eres un consultor de negocios experto en diagnóstico empresarial. "
        "Analiza el siguiente diagnóstico general de una empresa. "
        "Proporciona un resumen ejecutivo, identifica las áreas de oportunidad clave, "
        "ofrece recomendaciones accionables y calcula una puntuación promedio de madurez "
        "basada en las respuestas de Likert (1-5), y un nivel de madurez general. "
        "La interpretación de la escala Likert es:\n"
        "1: Difuso, poco claro, no desarrollado; no se cumplen los objetivos; no se percibe valor.\n"
        "2: Se realiza de manera ocasional e informal; a veces se cumplen los objetivos; se percibe poco valor.\n"
        "3: Se realiza regularmente, pero sin procesos definidos y de forma perceptiva; se cumplen los objetivos; se percibe valor principalmente a nivel regional.\n"
        "4: Se realiza correctamente, con seguimiento y mediciones básicas; se cumplen los objetivos con procesos estandarizados; se reconoce su alto valor a nivel nacional.\n"
        "5: Se realiza de manera excelente, automatizada y con indicadores de desempeño; se cumplen los objetivos con altos estándares; es reconocido a nivel internacional.\n\n"
        "Los niveles de madurez general deben ser: 'muy_bajo' (1.0-1.9), 'bajo' (2.0-2.9), 'medio' (3.0-3.9), 'alto' (4.0-4.5), 'muy_alto' (4.6-5.0).\n\n"
        "Aquí están los datos del diagnóstico:\n"
    ]

    # Añadir los datos del diagnóstico al prompt
    for key, value in diagnostico_data.items():
        if key not in ["userId", "createdAt"] and value: # Excluir campos internos y vacíos
            # Formatear las claves para que sean más legibles en el prompt
            display_key = key.replace('_', ' ').replace('dg ', 'Dirección General: ').replace('fa ', 'Finanzas y Administración: ') \
                             .replace('op ', 'Operaciones: ').replace('mv ', 'Marketing y Ventas: ') \
                             .replace('rh ', 'Recursos Humanos: ').replace('lc ', 'Logística y Cadena de Suministro: ') \
                             .replace('nombreSolicitante', 'Nombre del Solicitante') \
                             .replace('puestoSolicitante', 'Puesto del Solicitante') \
                             .replace('nombreEmpresa', 'Nombre de la Empresa') \
                             .replace('rfcEmpresa', 'RFC de la Empresa') \
                             .replace('giroIndustria', 'Giro/Industria') \
                             .replace('numeroEmpleados', 'Número de Empleados') \
                             .replace('antiguedadEmpresa', 'Antigüedad de la Empresa') \
                             .replace('ubicacion', 'Ubicación') \
                             .replace('telefonoContacto', 'Teléfono de Contacto') \
                             .replace('correoElectronico', 'Correo Electrónico') \
                             .replace('sitioWebRedes', 'Sitio Web/Redes Sociales') \
                             .replace('areaMayorProblema', 'Área con Mayor Problema') \
                             .replace('problematicaEspecifica', 'Problemática Específica') \
                             .replace('principalPrioridad', 'Principal Prioridad') \
                             .strip()
            prompt_parts.append(f"- {display_key}: {value}\n")

    full_prompt = "".join(prompt_parts)

    payload = {
        "contents": [
            {
                "role": "user",
                "parts": [{"text": full_prompt}]
            }
        ],
        "generationConfig": {
            "responseMimeType": "application/json",
            "responseSchema": RESPONSE_SCHEMA
        }
    }

    try:
        response_json = await call_gemini_api_with_backoff(payload, MODEL_NAME, API_KEY)
        
        # Extraer y parsear la respuesta JSON del LLM
        if response_json and response_json.get("candidates"):
            candidate = response_json["candidates"][0]
            if candidate.get("content") and candidate["content"].get("parts"):
                text_part = candidate["content"]["parts"][0].get("text")
                if text_part:
                    parsed_result = json.loads(text_part)

                    # Calcular la puntuación promedio de madurez y el nivel de madurez
                    likert_scores = []
                    for key, value in diagnostico_data.items():
                        # Asegúrate de que las claves aquí coincidan con las claves de tus preguntas Likert en el frontend
                        if key.startswith(("dg_", "fa_", "op_", "mv_", "rh_", "lc_")) and value in ["1", "2", "3", "4", "5"]:
                            try:
                                likert_scores.append(int(value))
                            except ValueError:
                                pass # Ignorar valores no numéricos

                    if likert_scores:
                        avg_score = sum(likert_scores) / len(likert_scores)
                        parsed_result["puntuacion_madurez_promedio"] = round(avg_score, 2)

                        if avg_score >= 4.6:
                            parsed_result["nivel_madurez_general"] = "muy_alto"
                        elif avg_score >= 4.0:
                            parsed_result["nivel_madurez_general"] = "alto"
                        elif avg_score >= 3.0:
                            parsed_result["nivel_madurez_general"] = "medio"
                        elif avg_score >= 2.0:
                            parsed_result["nivel_madurez_general"] = "bajo"
                        else:
                            parsed_result["nivel_madurez_general"] = "muy_bajo"
                    else:
                        parsed_result["puntuacion_madurez_promedio"] = 0.0
                        parsed_result["nivel_madurez_general"] = "muy_bajo" # O un valor por defecto si no hay scores

                    return parsed_result
        raise Exception("Estructura de respuesta inesperada del LLM.")
    except Exception as e:
        print(f"Error al analizar el diagnóstico con LLM: {e}")
        # Retornar un resultado de error o una estructura vacía
        return {
            "resumen_ejecutivo": "No se pudo generar el resumen ejecutivo debido a un error.",
            "areas_oportunidad": ["Error en el análisis de IA."],
            "recomendaciones_clave": ["Verifica la configuración de la API o intenta de nuevo más tarde."],
            "puntuacion_madurez_promedio": 0.0,
            "nivel_madurez_general": "muy_bajo"
        }

