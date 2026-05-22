import logging
from typing import Any
from .llm_anthropic import call_claude_text

logger = logging.getLogger(__name__)

MENTHIA_CHAT_PROMPT = """Eres MentHIA, el asistente inteligente de la plataforma.

TU PERSONALIDAD:
- Amigable, profesional y directo
- Experto en negocios y emprendimiento en LATAM
- Respuestas CORTAS y CONCISAS (máximo 2-3 oraciones)
- Siempre útil y orientado a la acción

LO QUE ES MENTHIA (según la web pública):
- Un ecosistema que combina asesores reales + tecnología (IA) para ayudar a PYMES a tomar mejores decisiones y crecer.
- Incluye diagnósticos empresariales y mentorías 1:1 con especialistas.
- Hay funcionalidades en "próximamente" (por ejemplo: comunidad y capacitación digital).

REGLAS:
- No menciones detalles comerciales ni servicios que no estén confirmados en la web pública.
- Si preguntan por pagos o información comercial: responde que esa información se consulta en las FAQs o por contacto.
- Si preguntan por capacitación: menciona que está "próximamente".
- Sugiere leer las FAQs cuando haya dudas de funcionamiento o políticas.
- No uses emojis.
- No des discursos largos; responde puntualmente."""

def get_fallback_response(message: str) -> str:
    msg = message.lower()
    if 'diagnóstico' in msg or 'diagnostico' in msg:
        return "En MentHIA puedes iniciar con un diagnóstico para entender tu empresa y recibir recomendaciones accionables. Si quieres, dime tu principal reto (ventas, finanzas, operaciones, etc.) y te guío."
    if 'mentor' in msg or 'asesor' in msg:
        return "En MentHIA puedes agendar mentorías 1:1 con especialistas (finanzas, marketing, operaciones y más). Cuéntame tu objetivo y te digo qué tipo de asesor te conviene."
    if 'curso' in msg or 'aprend' in msg:
        return "La capacitación digital está en 'próximamente'. Si me dices qué quieres aprender, te puedo orientar con pasos prácticos mientras se habilita."
    if 'precio' in msg or 'costo' in msg or 'cuánto' in msg:
        return "Esa información se consulta en las FAQs de MentHIA o con el equipo de soporte. ¿Quieres que te lleve a las FAQs o prefieres que te diga qué servicio te conviene según tu necesidad?"
    if 'hola' in msg or 'buenas' in msg or 'hey' in msg:
        return "Hola, soy el asistente de MentHIA. ¿En qué puedo ayudarte hoy: diagnóstico, mentoría 1:1 o dudas de la plataforma (FAQs)?"
    if 'gracias' in msg or 'thank' in msg:
        return "De nada. ¿Quieres que revisemos tu situación y el siguiente paso recomendado?"
    if 'ayuda' in msg or 'help' in msg:
        return "Puedo ayudarte con: diagnósticos empresariales, mentoría 1:1 y dudas de la plataforma (FAQs). ¿Qué necesitas?"
    if 'emergencia' in msg or 'crisis' in msg or 'urgente' in msg:
        return "Si es urgente, lo mejor es iniciar con un diagnóstico de emergencia para priorizar acciones. Dime qué está pasando (ventas, flujo, operación, cliente) y te ayudo a ordenar los primeros pasos."
    if 'marketplace' in msg or 'servicio' in msg:
        return "En MentHIA puedes encontrar servicios profesionales y especialistas según tu necesidad. Dime tu problema y te sugiero la mejor ruta (diagnóstico o mentoría)."
    return "Puedo ayudarte con diagnósticos, mentoría 1:1 o dudas de la plataforma (FAQs). ¿Qué te interesa explorar?"

async def handle_chatbot(data: dict[str, Any]) -> dict[str, Any]:
    message = data.get("message", "")
    messages = data.get("messages", [])
    
    if not message:
        return {"reply": "Mensaje vacío."}

    # Format messages for Anthropic
    anthropic_messages = []
    # Take last 6 messages
    recent = messages[-6:] if messages else []
    
    for m in recent:
        role = "user" if m.get("sender") == "user" else "assistant"
        content = m.get("text", "")
        if content:
            anthropic_messages.append({"role": role, "content": content})
            
    anthropic_messages.append({"role": "user", "content": message})
    
    # Try calling Anthropic API
    reply = call_claude_text(MENTHIA_CHAT_PROMPT, anthropic_messages, max_tokens=250)
    
    if reply:
        return {"reply": reply.strip()}
    else:
        # Fallback if API fails
        return {"reply": get_fallback_response(message)}
