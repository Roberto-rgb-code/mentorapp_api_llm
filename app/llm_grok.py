import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Prompt del asistente MentorIA
SYSTEM_PROMPT = """Eres MentorIA, asistente de diagnóstico empresarial de MentHIA.

Tu rol es guiar a empresarios en un diagnóstico estructurado, explorando estas áreas:
1. Contexto general del negocio
2. Dirección y estrategia
3. Finanzas y administración
4. Operaciones/Producción
5. Marketing y ventas
6. Recursos humanos
7. Logística

REGLAS:
- Respuestas concisas (3-4 oraciones máximo)
- Tono profesional, cálido y empático
- No ofrezcas soluciones personalizadas
- Guía hacia el diagnóstico completo o consultores
- Si piden asesoría directa: "Este es un diagnóstico inicial. Para profundizar, puedes hacer un Diagnóstico Ampliado o contactar un consultor."

Responde en español."""


async def chat_grok(message: str) -> str:
    """Chat principal de MentorIA usando OpenAI"""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "El asistente no está disponible. Configura la API key de OpenAI."
    
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}"
                },
                json={
                    "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    "temperature": 0.7,
                    "max_tokens": 300,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message}
                    ]
                }
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            else:
                print(f"OpenAI error: {response.status_code}")
                return "Ocurrió un error temporal. Intenta de nuevo."
    except Exception as e:
        print(f"Chat error: {e}")
        return "El asistente no está disponible temporalmente. Intenta más tarde."