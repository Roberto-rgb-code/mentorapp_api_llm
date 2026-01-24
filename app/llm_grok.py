import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Prompt del asistente Platia - basado en vistas públicas
SYSTEM_PROMPT = """Eres Platia, el asistente inteligente de la plataforma.

## QUÉ ES PLATIA
Platia es un ecosistema que combina asesores humanos reales e inteligencia artificial para ayudar a PYMES y emprendedores a tomar mejores decisiones y crecer con estrategias accionables.

## SERVICIOS PRINCIPALES

### 1) DIAGNÓSTICOS EMPRESARIALES
- Ayudan a entender la situación de la empresa y priorizar acciones.

### 2) MENTORÍA 1 A 1
- Sesiones con especialistas en áreas como finanzas, marketing, operaciones, estrategia, tecnología y más.

### 3) PRÓXIMAMENTE
- Comunidad empresarial
- Capacitación digital

## REGLAS DE RESPUESTA (MUY IMPORTANTES)
- Responde en español, cálido y profesional.
- Sé conciso (3-5 oraciones máximo).
- No menciones detalles comerciales ni servicios que no estén confirmados en la web pública.
- Si te preguntan por pagos o información comercial: indica que esa información se consulta en las FAQs o con soporte.
- Si te preguntan por capacitación: indica que está “próximamente”.
- Cuando el usuario tenga dudas de funcionamiento/políticas, refuerza que revise las FAQs.

## CONTACTO
- WhatsApp: +52 (33) 1234-5678
- Email: contacto@menthia.com

Responde siempre de manera útil y orientada a la acción."""


# Respuestas rápidas para preguntas frecuentes
QUICK_RESPONSES = {
    'precio': 'Esa información se consulta en las FAQs o con soporte (WhatsApp: +52 (33) 1234-5678).',
    'cuanto cuesta': 'Esa información se consulta en las FAQs o con soporte (WhatsApp: +52 (33) 1234-5678).',
    'costo': 'Esa información se consulta en las FAQs o con soporte (WhatsApp: +52 (33) 1234-5678).',
    'registr': 'Para registrarte: 1) Entra a la web 2) Clic en "Registro" 3) Completa tus datos 4) Confirma tu email. Si tienes dudas, revisa las FAQs.',
    'contacto': 'Puedes contactarnos por WhatsApp: +52 (33) 1234-5678 o email: contacto@menthia.com.',
    'whatsapp': 'Nuestro WhatsApp es +52 (33) 1234-5678. ¡Escríbenos y te ayudamos!',
    'telefono': 'Contáctanos por WhatsApp: +52 (33) 1234-5678',
    'consultor': 'Nuestra red reúne especialistas verificados en áreas clave para PYMES. Si me dices tu reto, te ayudo a ubicar el perfil adecuado.',
    'mentor': 'La mentoría 1 a 1 te conecta con un especialista para resolver un reto concreto. Si me dices tu objetivo, te sugiero el mejor enfoque.',
    'asesoria': 'Ofrecemos mentoría 1 a 1 con especialistas en finanzas, marketing, operaciones, estrategia y más. Si tienes dudas del proceso, revisa las FAQs.',
    'diagnostico': 'El diagnóstico te ayuda a entender tu situación y priorizar acciones. Si me dices tu principal reto, te guío con el siguiente paso.',
    'como funciona': 'Platia funciona así: inicias con un diagnóstico y, si necesitas profundizar, avanzas con mentoría 1 a 1. Para dudas de uso y políticas, revisa las FAQs.',
    'que es platia': 'Platia es una plataforma que combina asesores reales e inteligencia artificial para ayudar a PYMES a crecer con decisiones basadas en datos y acciones claras.',
    'hola': 'Hola, soy Platia. ¿Qué necesitas hoy: diagnóstico, mentoría 1 a 1 o dudas de la plataforma (FAQs)?',
    'ayuda': '¡Claro que te ayudo! Puedo: 1) Explicarte nuestros servicios 2) Guiarte en la plataforma 3) Resolver dudas empresariales 4) Recomendarte consultores. ¿Qué necesitas?',
    'gracias': '¡De nada! Estoy aquí para ayudarte. Si tienes más dudas, no dudes en preguntar. ¡Éxito con tu empresa!',
    'curso': 'La capacitación digital está en “próximamente”. Si me dices qué quieres aprender, te doy una guía práctica para empezar.',
}


def get_quick_response(message: str) -> str | None:
    """Busca respuesta rápida para preguntas frecuentes"""
    msg = message.lower().strip()
    for key, value in QUICK_RESPONSES.items():
        if key in msg:
            return value
    return None


async def chat_grok(message: str) -> str:
    """Chat principal de Platia usando OpenAI"""
    
    # 1. Intentar respuesta rápida (instantánea)
    quick = get_quick_response(message)
    if quick:
        return quick
    
    # 2. Usar OpenAI para respuestas más complejas
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return "El asistente no está disponible. Por favor contacta a soporte: WhatsApp +52 (33) 1234-5678"
    
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
                    "max_tokens": 400,
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
                return "Ocurrió un error temporal. Intenta de nuevo o contáctanos por WhatsApp: +52 (33) 1234-5678"
    except Exception as e:
        print(f"Chat error: {e}")
        return "El asistente no está disponible temporalmente. Contáctanos por WhatsApp: +52 (33) 1234-5678"
