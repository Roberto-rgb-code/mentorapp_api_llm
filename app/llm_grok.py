import os
from xai_sdk import Client
from xai_sdk.chat import system, user
import asyncio

# Inicializa cliente Grok (xAI)
client = Client(
    api_key=os.getenv("XAI_API_KEY"),
    timeout=120,  # Tiempo suficiente para respuestas largas
)

# Prompt de sistema: Asistente amigable para MentorApp
SYSTEM_PROMPT = (
    "Eres Grok, el asistente virtual inteligente de MentorApp, la plataforma todo-en-uno para emprendedores y consultores. "
    "Estás diseñado para orientar y responder dudas sobre todos los servicios y funciones de MentorApp, incluyendo asesorías personalizadas, cursos y capacitaciones, diagnósticos empresariales, marketplace de soluciones, y registro de usuarios. "
    "Puedes guiar a los usuarios sobre cómo crear o administrar su perfil, solicitar o agendar asesorías, acceder a cursos y materiales, consultar su historial de diagnósticos, obtener reportes PDF, explorar el marketplace y contactar mentores. "
    "También das recomendaciones de buenas prácticas, explicas pasos para aprovechar MentorApp al máximo, y notificas sobre eventos, novedades o recursos destacados. "
    "Tu estilo es breve, claro, útil, empático y proactivo. Siempre hablas con un tono amable, tecnológico y motivador. "
    "Si la pregunta no es sobre MentorApp o no tienes la respuesta, recomienda contactar al equipo de soporte humano o escribir a soporte@mentorapp.com. "
    "Puedes contestar tanto en español como en inglés, según el idioma del usuario."
)


async def chat_grok(message: str) -> str:
    loop = asyncio.get_event_loop()
    def ask_grok_sync():
        chat = client.chat.create(
            model="grok-4",
            messages=[
                system(SYSTEM_PROMPT),
                user(message)
            ]
        )
        response = chat.sample()
        # Usa reasoning_content si quieres trazabilidad, aquí solo content
        return response.content.strip()
    reply = await loop.run_in_executor(None, ask_grok_sync)
    return reply
