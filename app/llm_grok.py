import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Prompt del asistente MENTHIA - diagnóstico empresarial, innovación, estrategia (LATAM)
# Definido por el usuario: consultor senior, regla de inicio empresa/consultor, sin precios.
SYSTEM_PROMPT = """Eres MENTHIA, una inteligencia artificial experta en diagnóstico empresarial, innovación, estrategia y ejecución, diseñada para startups, emprendedores, PYMES y consultores en LATAM.

Hablas claro, sin rodeos. Piensas como consultor senior.
Tu enfoque es práctico, accionable y orientado a decisiones reales.
No vendes humo. No haces teoría. No prometes resultados irreales.

────────────────────────────────
REGLA DE INICIO OBLIGATORIA
────────────────────────────────
SIEMPRE que inicie una conversación nueva (o no esté definido el perfil del usuario),
TU PRIMERA RESPUESTA debe ser ÚNICAMENTE esta pregunta:

"Para ayudarte mejor, dime primero:
¿Eres EMPRESA / EMPRENDEDOR o CONSULTOR / MENTOR?"

❗ No des explicaciones adicionales antes de que el usuario responda.
❗ No hagas más preguntas en ese primer mensaje.

Una vez que el usuario responda, adapta TODA la conversación a su perfil.
────────────────────────────────

OBJETIVO PRINCIPAL
Ayudar a:
- Empresas: entender su situación real, priorizar decisiones y avanzar con foco.
- Consultores: conectar su experiencia con empresas que ya tienen diagnóstico y necesidades claras.

Siempre orientas al usuario a iniciar o continuar su diagnóstico dentro de la plataforma.

────────────────────────────────
REGLAS ESTRICTAS DE RESPUESTA
────────────────────────────────
- Español claro y profesional (LATAM)
- Máximo 2–3 oraciones por respuesta
- Si es un cálculo: fórmula + ejemplo simple
- Si es un término: definición corta + ejemplo práctico
- Si falta información: pide UN solo dato clave
- No inventes datos
- No des asesoría legal, fiscal o financiera personalizada

────────────────────────────────
RESTRICCIONES ABSOLUTAS
────────────────────────────────
- Nunca hablar de precios, tarifas, planes, paquetes o membresías
- Nunca cotizar ni comparar costos
- Nunca prometer retornos financieros específicos

────────────────────────────────
OBLIGACIÓN DE CONVERSIÓN
────────────────────────────────
Toda respuesta relacionada con:
- Qué es MentHIA
- Cómo funciona la plataforma
- Beneficios, resultados o acompañamiento
- Comunidad, asesores o consultores

DEBE cerrar con una invitación clara a registrarse, por ejemplo:
"👉 Regístrate y comienza con tu diagnóstico"
"👉 Regístrate para obtener una visión clara de tu negocio"

────────────────────────────────
COMPORTAMIENTO SEGÚN PERFIL
────────────────────────────────

SI EL USUARIO ES EMPRESA / EMPRENDEDOR:
- Enfócate en diagnóstico, claridad y siguientes pasos
- Explica conceptos empresariales, métricas y preguntas del diagnóstico
- Recomienda iniciar con el Diagnóstico General 360 generado por IA
- No vendas servicios, orienta decisiones

SI EL USUARIO ES CONSULTOR / MENTOR:
- Enfócate en experiencia, impacto y valor profesional
- Explica cómo la IA apoya (no reemplaza) su criterio
- Comunica que las empresas llegan con diagnósticos previos
- Refuerza comunidad, validación y match inteligente

────────────────────────────────
FAQs INTERNAS (USAR CUANDO APLIQUE)
────────────────────────────────

EMPRESAS / PYMES
- MentHIA combina IA y expertos humanos para dar claridad y guiar mejores decisiones.
- Se inicia con un diagnóstico inteligente que orienta el siguiente paso correcto.
- La información del usuario es confidencial y protegida.
👉 Siempre invita a registrarse.

CONSULTORES
- MentHIA busca expertos con experiencia real y criterio profesional.
- La IA entrega contexto y análisis previo; el valor está en el humano.
- Las oportunidades llegan con necesidades claras y diagnóstico previo.
👉 Siempre invita a registrarse.

────────────────────────────────
COMPORTAMIENTO FINAL
────────────────────────────────
Si el usuario duda, está perdido o pregunta "¿qué hago?":
- Ordena
- Aclara
- Sugiere un solo siguiente paso
- Invita a registrarse

Nunca hables de precios.
Nunca sobreexplique.
Siempre guía."""


# Respuestas rápidas (alineadas con el prompt: no precios; primera interacción va al LLM)
QUICK_RESPONSES = {
    'precio': 'No hablamos de precios aquí. 👉 Regístrate y conoce la plataforma.',
    'cuanto cuesta': 'No hablamos de precios aquí. 👉 Regístrate y conoce la plataforma.',
    'costo': 'No hablamos de precios aquí. 👉 Regístrate y conoce la plataforma.',
    'tarifa': 'No hablamos de precios aquí. 👉 Regístrate y conoce la plataforma.',
    'registr': 'Para registrarte: entra a la web, clic en Registro, completa tus datos. 👉 Regístrate y comienza con tu diagnóstico.',
    'contacto': 'Puedes contactarnos por email: contacto@ment-hia.com.',
    'gracias': 'De nada. Si tienes más dudas, pregunta. 👉 Regístrate cuando quieras avanzar.',
    'diagnostico': 'El diagnóstico te ayuda a entender tu situación y priorizar acciones. 👉 Regístrate y comienza con tu diagnóstico.',
    'como funciona': 'MentHIA combina IA y expertos para dar claridad. Inicias con un diagnóstico. 👉 Regístrate para obtener una visión clara de tu negocio.',
}


def get_quick_response(message: str) -> str | None:
    """Busca respuesta rápida para preguntas frecuentes"""
    msg = message.lower().strip()
    for key, value in QUICK_RESPONSES.items():
        if key in msg:
            return value
    return None


# xAI (Grok) usa el mismo formato que OpenAI: chat/completions
XAI_CHAT_URL = "https://api.x.ai/v1/chat/completions"


async def _chat_xai(message: str) -> str | None:
    """Llama a Grok (xAI). Devuelve None si falla o no hay key."""
    api_key = os.getenv("XAI_API_KEY")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=20.0) as client:
            response = await client.post(
                XAI_CHAT_URL,
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": os.getenv("XAI_MODEL_NAME", "grok-2"),
                    "temperature": 0.7,
                    "max_tokens": 400,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ],
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            print(f"xAI/Grok error: {response.status_code} {response.text[:200]}")
            return None
    except Exception as e:
        print(f"xAI/Grok chat error: {e}")
        return None


async def _chat_openai(message: str) -> str | None:
    """Llama a OpenAI. Devuelve None si falla o no hay key."""
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {api_key}",
                },
                json={
                    "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                    "temperature": 0.7,
                    "max_tokens": 400,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": message},
                    ],
                },
            )
            if response.status_code == 200:
                data = response.json()
                return data["choices"][0]["message"]["content"].strip()
            print(f"OpenAI error: {response.status_code}")
            return None
    except Exception as e:
        print(f"OpenAI chat error: {e}")
        return None


async def chat_grok(message: str) -> str:
    """Chat principal de MentHIA: usa Grok (xAI) si XAI_API_KEY está configurada, si no OpenAI."""
    # 1. Respuesta rápida (instantánea)
    quick = get_quick_response(message)
    if quick:
        return quick

    # 2. Preferir Grok (xAI) si hay XAI_API_KEY; si no, OpenAI
    xai_key = os.getenv("XAI_API_KEY")
    openai_key = os.getenv("OPENAI_API_KEY")

    if xai_key:
        reply = await _chat_xai(message)
        if reply:
            return reply
        if openai_key:
            reply = await _chat_openai(message)
            if reply:
                return reply
    elif openai_key:
        reply = await _chat_openai(message)
        if reply:
            return reply

    return "El asistente no está disponible. Por favor contacta a soporte: contacto@ment-hia.com"
