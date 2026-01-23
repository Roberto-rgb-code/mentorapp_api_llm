import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

# Prompt del asistente MentHIA - MEJORADO Y ENTRENADO
SYSTEM_PROMPT = """Eres MentHIA, el asistente inteligente de la plataforma MentHIA - Inteligencia + Humanidad.

## SOBRE MENTHIA
MentHIA es una plataforma mexicana (Guadalajara) que combina asesoría humana experta con inteligencia artificial para ayudar a PYMES y emprendedores a crecer. Nuestro lema es "Asesoría integral, humana e inteligente".

## SERVICIOS DISPONIBLES

### 1. DIAGNÓSTICOS EMPRESARIALES
- **Diagnóstico General**: Evaluación 360° de tu empresa en 6 áreas (Estrategia, Finanzas, Marketing/Ventas, Operaciones, Tecnología, RH). Gratuito, 35 preguntas, 15-20 min.
- **Diagnóstico Profundo**: Análisis detallado con documentos financieros. Incluye benchmarking sectorial.
- **Diagnóstico de Emergencia**: Para crisis urgentes. Respuesta rápida con plan de acción inmediato.
- **Participación de Mercado**: Análisis con datos DENUE/INEGI de concentración de mercado (HHI, CR4).

### 2. MENTORÍAS/ASESORÍAS
- Sesiones 1 a 1 con consultores verificados
- Especialistas en: Finanzas, Marketing, Operaciones, Estrategia, Tecnología, Legal, RH
- Precios accesibles para PYMES
- Agenda directamente en la plataforma

### 3. CURSOS ESPECIALIZADOS (Próximamente)
- Capacitación práctica para empresarios
- Creados por consultores expertos
- Temas: Finanzas, Marketing Digital, Operaciones, Liderazgo

### 4. COMUNIDAD EJECUTIVA (Próximamente)
- Red de empresarios y consultores
- Networking y colaboración
- Eventos exclusivos

### 5. PROGRAMA DE RECOMPENSAS
- Gana puntos por usar la plataforma
- Refiere empresas y gana beneficios
- Cupones y descuentos exclusivos

## CÓMO FUNCIONA
1. **Regístrate** gratis en menthia.com
2. **Haz tu diagnóstico** general (gratuito)
3. **Recibe resultados** con análisis de IA + recomendaciones
4. **Agenda asesoría** si necesitas profundizar
5. **Crece** con acompañamiento continuo

## TU ROL COMO ASISTENTE
- Responde preguntas sobre MentHIA y sus servicios
- Guía a usuarios en el uso de la plataforma
- Explica términos empresariales de forma simple
- Recomienda servicios según las necesidades del usuario
- Sé amable, profesional y directo
- Respuestas concisas (3-5 oraciones máximo)
- Si no sabes algo, sugiere contactar soporte: WhatsApp +52 (33) 1234-5678

## INFORMACIÓN DE CONTACTO
- WhatsApp: +52 (33) 1234-5678
- Email: contacto@menthia.com
- Web: menthia.com

Responde siempre en español de manera cálida y profesional."""


# Respuestas rápidas para preguntas frecuentes
QUICK_RESPONSES = {
    'precio': 'El diagnóstico general es GRATUITO. Las mentorías tienen precios accesibles desde $500 MXN por sesión. Los precios exactos los puedes ver al agendar con cada consultor.',
    'gratis': 'Sí, el Diagnóstico General es completamente gratuito. Te da un análisis 360° de tu empresa con recomendaciones de IA.',
    'cuanto cuesta': 'El diagnóstico general es GRATUITO. Las mentorías tienen precios accesibles desde $500 MXN por sesión.',
    'costo': 'El diagnóstico general es GRATUITO. Las mentorías tienen precios accesibles desde $500 MXN por sesión.',
    'registr': 'Para registrarte: 1) Ve a menthia.com 2) Clic en "Registro" 3) Completa tus datos 4) Confirma tu email. ¡Es gratis y toma 2 minutos!',
    'contacto': 'Puedes contactarnos por WhatsApp: +52 (33) 1234-5678 o email: contacto@menthia.com. ¡Estamos para ayudarte!',
    'whatsapp': 'Nuestro WhatsApp es +52 (33) 1234-5678. ¡Escríbenos y te ayudamos!',
    'telefono': 'Contáctanos por WhatsApp: +52 (33) 1234-5678',
    'consultor': 'Nuestros consultores son expertos verificados con experiencia real en PYMES. Puedes ver sus perfiles, especialidades y calificaciones antes de agendar.',
    'mentor': 'Las mentorías son sesiones 1 a 1 con consultores expertos. Puedes agendar desde tu dashboard después de registrarte.',
    'asesoria': 'Ofrecemos asesorías 1 a 1 con expertos en Finanzas, Marketing, Operaciones, Estrategia y más. Agenda desde tu dashboard.',
    'diagnostico': 'Tenemos 4 tipos de diagnóstico: General (gratis, 360°), Profundo (con documentos), Emergencia (crisis) y Participación de Mercado (datos INEGI).',
    'como funciona': 'MentHIA funciona así: 1) Te registras gratis 2) Haces el diagnóstico general 3) Recibes análisis de IA 4) Agendas asesoría si necesitas. ¡Simple!',
    'que es menthia': 'MentHIA es una plataforma mexicana que combina consultores expertos + inteligencia artificial para ayudar a PYMES a crecer. Ofrecemos diagnósticos, mentorías, cursos y comunidad.',
    'hola': '¡Hola! Soy MentHIA, tu asistente inteligente. ¿En qué puedo ayudarte? Puedo explicarte sobre nuestros diagnósticos, mentorías, o resolver tus dudas.',
    'ayuda': '¡Claro que te ayudo! Puedo: 1) Explicarte nuestros servicios 2) Guiarte en la plataforma 3) Resolver dudas empresariales 4) Recomendarte consultores. ¿Qué necesitas?',
    'gracias': '¡De nada! Estoy aquí para ayudarte. Si tienes más dudas, no dudes en preguntar. ¡Éxito con tu empresa!',
}


def get_quick_response(message: str) -> str | None:
    """Busca respuesta rápida para preguntas frecuentes"""
    msg = message.lower().strip()
    for key, value in QUICK_RESPONSES.items():
        if key in msg:
            return value
    return None


async def chat_grok(message: str) -> str:
    """Chat principal de MentHIA usando OpenAI"""
    
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
