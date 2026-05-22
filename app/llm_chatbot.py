import logging
from typing import Any
from .llm_anthropic import call_claude_text

logger = logging.getLogger(__name__)

MENTHIA_CHAT_PROMPT = """Eres MentHIA, el asistente inteligente de la plataforma MentHIA (www.ment-hia.com).

TU PERSONALIDAD:
- Amigable, profesional y directo
- Experto en negocios, finanzas y emprendimiento en LATAM (especialmente México)
- Respuestas CORTAS y CONCISAS (máximo 2-3 oraciones)
- Siempre útil y orientado a la acción
- Tuteas al usuario

SERVICIOS DISPONIBLES EN LA PLATAFORMA (todos accesibles desde el Dashboard):

1. DIAGNÓSTICOS EMPRESARIALES (sección "Diagnóstico" en el menú):
   - Diagnóstico General: evaluación integral de la empresa en todas sus áreas (ventas, operaciones, finanzas, marketing, RRHH, liderazgo). Genera un índice MentHIA de 0 a 100.
   - Diagnóstico Express: versión rápida del diagnóstico general, ideal para obtener un panorama inicial en pocos minutos.
   - Diagnóstico Profundo: análisis detallado y extenso con preguntas especializadas por área funcional.
   - Diagnóstico de Emergencia: para situaciones críticas o urgentes (caída de ventas, problemas de flujo, pérdida de clientes). Prioriza acciones inmediatas.
   - Diagnóstico de Competencia / Participación de Mercado: análisis comparativo frente a competidores.
   - Agente F.I.N.A.N.C.I.A.™: diagnóstico financiero especializado que evalúa la bancabilidad de una PyME. Genera un semáforo (rojo/amarillo/verde), un score de bancabilidad, análisis por pilares financieros y un plan de acción 30-60-90 días.
   - R.E.C.U.P.E.R.A. Profesional: programa estructurado de recuperación empresarial para empresas en crisis.
   - R.E.C.U.P.E.R.A. Express: versión rápida del programa de recuperación.

2. MARKETPLACE:
   - Directorio de consultores y mentores especializados.
   - El usuario puede buscar, filtrar y agendar mentorías 1:1 con especialistas en diversas áreas (finanzas, marketing, operaciones, legal, tecnología, etc.).

3. ASESORÍA / MENTORÍA 1:1:
   - Sesiones individuales con mentores certificados.
   - Se agendan a través del marketplace o la sección de asesoría.

4. ANÁLISIS FINANCIERO:
   - Herramienta para subir y analizar estados financieros con IA.
   - Genera interpretaciones narrativas de los datos financieros.

5. ACTIVIDAD:
   - Mis Citas: gestión de citas agendadas con mentores.
   - Mi Historial: registro de diagnósticos y sesiones pasadas.
   - Cupones: cupones de descuento para servicios.

6. CUENTA:
   - Mi Perfil: datos personales y configuración.
   - Notificaciones: centro de notificaciones de la plataforma.

REGLAS:
- Cuando el usuario pregunte qué puede hacer, menciona los servicios más relevantes según su necesidad.
- Si no sabes qué recomendar, sugiere empezar con un Diagnóstico Express para tener un panorama rápido.
- Para problemas financieros o bancarios, recomienda el Agente F.I.N.A.N.C.I.A.
- Para crisis o urgencias, recomienda el Diagnóstico de Emergencia.
- Para compararse con competidores, recomienda el Diagnóstico de Competencia.
- Para empresas en problemas graves, recomienda R.E.C.U.P.E.R.A.
- Si preguntan por pagos o información comercial: responde que esa información la encuentran en la sección de FAQs o contactando al equipo.
- Si preguntan por capacitación o cursos: menciona que está "próximamente".
- No uses emojis.
- No des discursos largos; responde puntualmente.
- Siempre orienta al usuario hacia una acción concreta dentro de la plataforma."""

def get_fallback_response(message: str) -> str:
    msg = message.lower()
    if 'diagnóstico' in msg or 'diagnostico' in msg:
        return "Tenemos varios diagnósticos: General, Express (rápido), Profundo (detallado), de Emergencia (crisis), de Competencia, F.I.N.A.N.C.I.A. (bancabilidad) y R.E.C.U.P.E.R.A. (recuperación). ¿Cuál necesitas o quieres que te recomiende uno?"
    if 'financia' in msg or 'bancab' in msg or 'banco' in msg or 'crédito' in msg or 'credito' in msg:
        return "El Agente F.I.N.A.N.C.I.A. evalúa la bancabilidad de tu PyME y te da un semáforo (rojo/amarillo/verde) con un plan de acción. Lo encuentras en Diagnóstico > Agente F.I.N.A.N.C.I.A."
    if 'recupera' in msg or 'crisis' in msg or 'quiebra' in msg:
        return "El programa R.E.C.U.P.E.R.A. está diseñado para empresas en crisis. Tenemos versión Profesional (estructurada) y Express (rápida). Los encuentras en la sección de Diagnóstico."
    if 'emergencia' in msg or 'urgente' in msg or 'urgencia' in msg:
        return "Para situaciones urgentes tenemos el Diagnóstico de Emergencia que prioriza las acciones inmediatas. Ve a Diagnóstico > Emergencia desde tu dashboard."
    if 'competencia' in msg or 'competidor' in msg or 'mercado' in msg:
        return "El Diagnóstico de Competencia te permite comparar tu empresa frente a tus competidores y analizar tu participación de mercado. Lo encuentras en la sección de Diagnóstico."
    if 'mentor' in msg or 'asesor' in msg or 'consultor' in msg:
        return "Puedes encontrar y agendar mentorías 1:1 con especialistas en el Marketplace. Hay expertos en finanzas, marketing, operaciones, legal y más."
    if 'financiero' in msg or 'finanzas' in msg or 'estados financieros' in msg:
        return "En la sección de Análisis Financiero puedes subir tus estados financieros y obtener una interpretación con IA. Para un diagnóstico completo de bancabilidad, usa el Agente F.I.N.A.N.C.I.A."
    if 'marketplace' in msg or 'servicio' in msg:
        return "En el Marketplace encuentras consultores y mentores especializados. Puedes filtrar por área de expertise y agendar sesiones directamente."
    if 'cita' in msg or 'agendar' in msg or 'agenda' in msg:
        return "Puedes gestionar tus citas en la sección Mis Citas del dashboard. Para agendar una nueva, busca un mentor en el Marketplace."
    if 'curso' in msg or 'aprend' in msg or 'capacit' in msg:
        return "La capacitación digital está próximamente. Mientras tanto, puedes agendar una mentoría 1:1 con un especialista en el tema que te interese."
    if 'precio' in msg or 'costo' in msg or 'cuánto' in msg or 'cuanto' in msg:
        return "La información de precios la puedes consultar en las FAQs o contactando directamente al equipo de MentHIA."
    if 'hola' in msg or 'buenas' in msg or 'hey' in msg or 'buenos' in msg:
        return "Hola, soy el asistente de MentHIA. Puedo ayudarte con diagnósticos empresariales, análisis financiero, mentorías 1:1 y más. ¿Qué necesitas hoy?"
    if 'gracias' in msg or 'thank' in msg:
        return "De nada. ¿Hay algo más en lo que pueda orientarte?"
    if 'ayuda' in msg or 'help' in msg:
        return "Puedo orientarte sobre: diagnósticos (General, Express, Profundo, Emergencia, Competencia, F.I.N.A.N.C.I.A., R.E.C.U.P.E.R.A.), mentorías 1:1, análisis financiero y más. ¿Qué necesitas?"
    if 'express' in msg:
        return "El Diagnóstico Express es la forma más rápida de obtener un panorama de tu empresa. En pocos minutos obtienes recomendaciones accionables. Ve a Diagnóstico > Express."
    if 'profundo' in msg:
        return "El Diagnóstico Profundo es un análisis extenso por área funcional. Ideal si ya hiciste el Express y quieres mayor detalle. Ve a Diagnóstico > Profundo."
    if 'cupón' in msg or 'cupon' in msg or 'descuento' in msg:
        return "Puedes gestionar tus cupones de descuento en la sección Cupones del dashboard."
    if 'historial' in msg:
        return "En Mi Historial puedes ver todos tus diagnósticos y sesiones pasadas. Lo encuentras en la sección Actividad del menú."
    if 'perfil' in msg or 'cuenta' in msg or 'datos' in msg:
        return "Puedes actualizar tus datos personales en la sección Mi Perfil desde el menú lateral."
    return "Soy el asistente de MentHIA. Puedo orientarte sobre diagnósticos empresariales, análisis financiero, mentorías con expertos y más. ¿En qué te ayudo?"

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
