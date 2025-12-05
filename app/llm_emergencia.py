# app/llm_emergencia.py
import os
import json
import asyncio
import re
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Palabras clave para análisis de sentimiento
SENTIMENT_NEGATIVE = [
    "urgente", "crítico", "grave", "emergencia", "pérdida", "caída", "disminuido",
    "no", "falta", "sin", "incapaz", "imposible", "preocupado", "estresado",
    "desesperado", "colapsar", "quiebra", "fracaso", "problema", "conflicto"
]

SENTIMENT_STRESS = [
    "no sé", "no lo sé", "no estoy seguro", "preocupado", "angustiado",
    "presión", "estrés", "abrumado", "cansado", "agotado"
]

# Patrones de riesgo crítico
RISK_PATTERNS = {
    "flujo_caja_critico": ["no cubre", "no tengo", "sin efectivo", "sin liquidez", "quiebra"],
    "operaciones_paradas": ["no puedo operar", "detener", "parar operaciones", "no funciona"],
    "ventas_colapsadas": ["cero ventas", "sin ventas", "caída total", "nada de ventas"],
    "personal_perdido": ["renunciaron todos", "sin personal", "equipo perdido"]
}

def _analizar_sentimiento(texto: str) -> Dict[str, Any]:
    """Analiza el sentimiento y nivel de estrés en textos del empresario"""
    if not texto:
        return {"sentimiento": "neutral", "nivel_estres": 0, "indicadores": []}
    
    texto_lower = texto.lower()
    indicadores = []
    nivel_estres = 0
    
    # Detecta palabras de estrés
    stress_count = sum(1 for word in SENTIMENT_STRESS if word in texto_lower)
    negative_count = sum(1 for word in SENTIMENT_NEGATIVE if word in texto_lower)
    
    if stress_count > 2 or negative_count > 5:
        nivel_estres = 3  # Alto
        indicadores.append("Alto nivel de estrés detectado en respuestas")
    elif stress_count > 0 or negative_count > 2:
        nivel_estres = 2  # Moderado
        indicadores.append("Moderado nivel de estrés detectado")
    else:
        nivel_estres = 1  # Bajo
    
    sentimiento = "negativo" if negative_count > 3 else "preocupado" if stress_count > 0 else "neutral"
    
    return {
        "sentimiento": sentimiento,
        "nivel_estres": nivel_estres,
        "indicadores": indicadores
    }

def _detectar_patrones_riesgo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """Detecta patrones de riesgo crítico en los datos"""
    textos = [
        str(diagnostico_data.get("problematicaEspecifica", "")),
        str(diagnostico_data.get("problemaMasUrgente", "")),
        str(diagnostico_data.get("impactoDelProblema", "")),
        str(diagnostico_data.get("principalPrioridad", ""))
    ]
    texto_completo = " ".join(textos).lower()
    
    patrones_detectados = []
    riesgo_adicional = 0
    
    for patron_key, keywords in RISK_PATTERNS.items():
        if any(kw in texto_completo for kw in keywords):
            patrones_detectados.append(patron_key)
            riesgo_adicional += 1
    
    return {
        "patrones_criticos": patrones_detectados,
        "riesgo_adicional": riesgo_adicional,
        "alerta_temprana": riesgo_adicional >= 2
    }

def _calcular_riesgo_inteligente(diagnostico_data: Dict[str, Any], analisis_sentimiento: Dict, patrones: Dict) -> str:
    """Calcula el riesgo usando múltiples señales"""
    riesgo_base = 0
    
    # Análisis de continuidad de negocio
    continuidad = str(diagnostico_data.get("continuidadNegocio", ""))
    if continuidad in ("4", "5"):
        riesgo_base += 3
    elif continuidad == "3":
        riesgo_base += 2
    elif continuidad in ("1", "2"):
        riesgo_base += 1
    
    # Análisis de flujo de efectivo
    flujo = str(diagnostico_data.get("flujoEfectivo", "")).lower()
    if flujo == "no":
        riesgo_base += 3
    elif flujo == "parcialmente":
        riesgo_base += 1
    
    # Análisis de ventas
    ventas = str(diagnostico_data.get("ventasDisminuido", "")).lower()
    if ventas == "si":
        riesgo_base += 2
    
    # Ajuste por sentimiento
    riesgo_base += analisis_sentimiento.get("nivel_estres", 0) - 1
    
    # Ajuste por patrones
    riesgo_base += patrones.get("riesgo_adicional", 0)
    
    if riesgo_base >= 7:
        return "critico"
    elif riesgo_base >= 5:
        return "alto"
    elif riesgo_base >= 3:
        return "moderado"
    return "bajo"

def _generar_recomendaciones_contextuales(riesgo: str, sentimiento: Dict, patrones: Dict, diagnostico_data: Dict) -> List[str]:
    """Genera recomendaciones personalizadas según el contexto"""
    recomendaciones = []
    
    # Recomendaciones por nivel de riesgo
    if riesgo == "critico":
        recomendaciones.append("🚨 CONTACTA URGENTEMENTE con un consultor especializado en crisis empresariales")
        recomendaciones.append("⚡ Establece comunicación directa HOY con clientes clave, proveedores y empleados")
        recomendaciones.append("💰 Prioriza flujo de caja inmediato: cobros de 24-48h y renegociación urgente de pagos")
    
    # Recomendaciones por sentimiento
    if sentimiento.get("nivel_estres", 0) >= 3:
        recomendaciones.append("💡 IMPORTANTE: Detectamos alto estrés. Considera tomar 48h de pausa antes de decisiones críticas para evitar errores costosos")
        recomendaciones.append("🤝 Busca apoyo inmediato: mentor especializado o consultor de crisis para no tomar decisiones solo")
    
    # Recomendaciones por patrones detectados
    if "flujo_caja_critico" in patrones.get("patrones_criticos", []):
        recomendaciones.append("💰 FLUJO DE CAJA CRÍTICO: Revisa opciones de financiamiento urgente (líneas de crédito, factoring) y negocia términos con acreedores HOY")
    
    if "operaciones_paradas" in patrones.get("patrones_criticos", []):
        recomendaciones.append("🛑 OPERACIONES EN RIESGO: Elabora plan de continuidad mínimo viable de 7 días para mantener lo esencial funcionando")
    
    if patrones.get("alerta_temprana"):
        recomendaciones.append("⚠️ MÚLTIPLES SEÑALES CRÍTICAS DETECTADAS: La situación requiere intervención inmediata. Programa consultoría urgente esta semana")
    
    return recomendaciones

async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un diagnóstico de EMERGENCIA con OpenAI Chat Completions
    y devuelve el JSON EXACTO que consume el frontend, mejorado con análisis inteligente.
    """
    
    # Análisis avanzado local
    textos_analizar = [
        str(diagnostico_data.get("problematicaEspecifica", "")),
        str(diagnostico_data.get("problemaMasUrgente", "")),
        str(diagnostico_data.get("impactoDelProblema", ""))
    ]
    texto_completo = " ".join(txt for txt in textos_analizar if txt)
    
    analisis_sentimiento = _analizar_sentimiento(texto_completo)
    patrones_riesgo = _detectar_patrones_riesgo(diagnostico_data)
    
    # Fallback demo si no hay API key
    if not OPENAI_API_KEY or not client:
        riesgo = _calcular_riesgo_inteligente(diagnostico_data, analisis_sentimiento, patrones_riesgo)
        recomendaciones_contextuales = _generar_recomendaciones_contextuales(
            riesgo, analisis_sentimiento, patrones_riesgo, diagnostico_data
        )
        nombre = diagnostico_data.get("nombreSolicitante", "").split()[0] if diagnostico_data.get("nombreSolicitante") else ""
        saludo = f"{nombre}, " if nombre else ""
        
        return {
            "diagnostico_rapido": f"{saludo}primero quiero que sepas que hay solución para esto 💪 Entiendo que estás pasando por un momento difícil con la liquidez y las ventas. La buena noticia es que muchas empresas han superado situaciones similares. Juntos vamos a encontrar el camino. Respira profundo - hay pasos claros que podemos tomar ahora mismo.",
            "acciones_inmediatas": [
                "🔥 PRIMERO: Congela gastos no esenciales por 14 días - esto te dará aire para pensar",
                "💰 SEGUNDO: Contacta HOY a tus 3 mejores clientes para acelerar cobros pendientes",
                "📞 TERCERO: Comunica a proveedores clave tu situación - la mayoría prefiere negociar que perder un cliente",
            ] + recomendaciones_contextuales[:2],
            "riesgo_general": riesgo,
            "recomendaciones_clave": [
                "💪 Podrías implementar un control de flujo de caja semanal - te dará tranquilidad",
                "🎯 Te sugiero ajustar temporalmente la operación a la demanda actual",
                "✨ Una buena estrategia sería armar un plan de recuperación comercial para los próximos 30-60 días",
            ] + recomendaciones_contextuales[2:],
            "analisis_sentimiento": analisis_sentimiento,
            "patrones_detectados": patrones_riesgo,
            "recomendaciones_innovadoras": recomendaciones_contextuales,
            "siguiente_paso": "🎯 Tu siguiente paso más importante: Hoy mismo, antes de terminar el día, haz una lista de los 5 pagos más urgentes y los 5 cobros más fáciles de acelerar. ¡Esto te dará claridad inmediata!",
            "mensaje_de_apoyo": "¡No estás solo en esto! 🌟 Muchos empresarios han pasado por tormentas similares y han salido más fuertes. El simple hecho de que estés buscando soluciones demuestra que tienes lo que se necesita para superar esto. ¡Cuenta con nosotros!"
        }

    # Construir prompt mejorado con contexto
    contexto_analisis = ""
    if analisis_sentimiento.get("nivel_estres", 0) >= 3:
        contexto_analisis += "\n⚠️ ALERTA: Alto nivel de estrés detectado en las respuestas del empresario. "
    if patrones_riesgo.get("alerta_temprana"):
        contexto_analisis += f"\n🚨 MÚLTIPLES PATRONES CRÍTICOS DETECTADOS: {', '.join(patrones_riesgo.get('patrones_criticos', []))}. "
    
    riesgo_calculado = _calcular_riesgo_inteligente(diagnostico_data, analisis_sentimiento, patrones_riesgo)
    contexto_analisis += f"\nRiesgo calculado automáticamente: {riesgo_calculado} (usa esto como referencia pero valida con el análisis completo)."

    # Obtener nombre para personalizar
    nombre_usuario = diagnostico_data.get("nombreSolicitante", "").split()[0] if diagnostico_data.get("nombreSolicitante") else ""
    saludo = f"{nombre_usuario}, " if nombre_usuario else ""

    user_prompt = (
        "Eres MentHIA, un MENTOR DE CRISIS EMPRESARIAL con corazón. "
        "Tu misión es ser un FARO DE CALMA en la tormenta. El empresario está pasando por un momento difícil y necesita sentir que NO ESTÁ SOLO. "
        "Tu tono debe ser: TRANQUILIZADOR pero CLARO, EMPÁTICO pero PRÁCTICO, ESPERANZADOR pero REALISTA. "
        "Usa frases como: 'Entiendo lo difícil que es esto...', 'Juntos vamos a salir adelante...', 'Hay solución para esto...'\n\n"
        "Analiza este diagnóstico de emergencia con enfoque en:\n"
        "1. PRIMERO tranquilizar y validar los sentimientos del empresario\n"
        "2. Identificar lo MÁS URGENTE (próximas 24-72 horas)\n"
        "3. Dar acciones CLARAS y ALCANZABLES (no abrumar)\n"
        "4. Transmitir ESPERANZA realista\n\n"
        f"{contexto_analisis}\n\n"
        "Devuelve SOLO JSON con este esquema:\n"
        f"- diagnostico_rapido: Empieza con '{saludo}primero quiero que sepas que hay solución para esto 💪'. "
        "Luego resume la situación de forma CLARA pero NO alarmista. Termina con una frase de esperanza. "
        "Si detectas alto estrés, incluye: 'Es normal sentirse abrumado, pero juntos vamos a encontrar el camino'.\n"
        "- acciones_inmediatas: 4–6 acciones para las próximas 24–72 horas. "
        "Usa formato amigable: '🔥 PRIMERO: ...', '💰 SEGUNDO: ...'. "
        "Que sean ALCANZABLES para no abrumar. Si hay flujo de caja crítico, primeras acciones deben ser financieras.\n"
        "- riesgo_general: uno de ['bajo','moderado','alto','critico']. "
        f"Considera: {riesgo_calculado}\n"
        "- recomendaciones_clave: 4–6 recomendaciones para las próximas 2–4 semanas. "
        "Usa lenguaje motivador: '💪 Podrías...', '🎯 Te sugiero...', '✨ Una buena estrategia sería...'\n"
        "- recomendaciones_innovadoras: 2–3 ideas creativas o casos de éxito similares.\n"
        "- siguiente_paso: EL paso más importante ahora mismo, redactado de forma motivadora.\n"
        "- mensaje_de_apoyo: Una frase final de ánimo personalizada (ej: '¡No estás solo en esto! Muchos empresarios han pasado por situaciones similares y han salido adelante. Tú también puedes 🌟').\n\n"
        f"Datos del diagnóstico de emergencia:\n{json.dumps(diagnostico_data, ensure_ascii=False, indent=2)}\n\n"
        "Recuerda: el empresario necesita sentir APOYO y CLARIDAD. Responde SOLO con JSON válido."
    )

    try:
        def _call():
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {
                        "role": "system",
                        "content": "Eres MentHIA, un mentor de crisis empresarial con corazón. Tu misión es ser un faro de calma y esperanza. Responde solo con JSON válido. Sé claro, empático y tranquilizador. El empresario necesita sentir que hay solución y que no está solo."
                    },
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.4,  # Un poco más alto para más calidez en las respuestas
            )
            return completion.choices[0].message.content

        result = await asyncio.to_thread(_call)
        parsed = json.loads(result)
        
        # Enriquecer con análisis local
        if analisis_sentimiento.get("nivel_estres", 0) >= 2:
            parsed["analisis_sentimiento"] = analisis_sentimiento
        
        if patrones_riesgo.get("patrones_criticos"):
            parsed["patrones_detectados"] = patrones_riesgo
        
        # Agregar recomendaciones contextuales si no vienen del LLM
        if not parsed.get("recomendaciones_innovadoras"):
            parsed["recomendaciones_innovadoras"] = _generar_recomendaciones_contextuales(
                parsed.get("riesgo_general", riesgo_calculado),
                analisis_sentimiento,
                patrones_riesgo,
                diagnostico_data
            )
        
        # Validar y ajustar riesgo si es muy diferente del calculado
        riesgo_llm = parsed.get("riesgo_general", "").lower()
        if riesgo_llm not in ["bajo", "moderado", "alto", "critico"]:
            parsed["riesgo_general"] = riesgo_calculado
        elif riesgo_calculado == "critico" and riesgo_llm in ["bajo", "moderado"]:
            # Si calculamos crítico pero LLM dice bajo/moderado, usar crítico (más seguro)
            parsed["riesgo_general"] = "critico"
            parsed["diagnostico_rapido"] += " [Nota: Riesgo elevado a CRÍTICO por análisis automático de múltiples señales]"
        
        return parsed

    except Exception as e:
        # Fallback inteligente en caso de error
        riesgo = _calcular_riesgo_inteligente(diagnostico_data, analisis_sentimiento, patrones_riesgo)
        recomendaciones = _generar_recomendaciones_contextuales(riesgo, analisis_sentimiento, patrones_riesgo, diagnostico_data)
        
        return {
            "diagnostico_rapido": f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}. Análisis automático detecta riesgo {riesgo.upper()}.",
            "acciones_inmediatas": recomendaciones[:4] if len(recomendaciones) >= 4 else [
                "Contacta consultor especializado en crisis",
                "Prioriza flujo de caja inmediato",
                "Comunica situación a stakeholders clave",
                "Elabora plan de continuidad de 7 días"
            ],
            "riesgo_general": riesgo,
            "recomendaciones_clave": recomendaciones[4:] if len(recomendaciones) > 4 else [
                "Implementa monitoreo diario de indicadores críticos",
                "Establece rutinas de comunicación semanal con equipo",
                "Documenta decisiones críticas y su justificación"
            ],
            "recomendaciones_innovadoras": recomendaciones,
            "analisis_sentimiento": analisis_sentimiento,
            "patrones_detectados": patrones_riesgo,
        }
