# app/llm_emergencia.py
# MENTHIA CrisisNow - Módulo de Intervención Empresarial Inmediata
import os
import json
import asyncio
from typing import Dict, Any, List
from fastapi import HTTPException
from openai import OpenAI
from dotenv import load_dotenv

# Carga variables de entorno (usa .env)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o").strip().strip('"').strip("'")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================
# PROMPT SYSTEM DE MENTHIA CRISISNOW
# =====================================================
MENTHIA_CRISIS_SYSTEM_PROMPT = """Eres MENTHIA CrisisNow, el módulo de intervención inmediata para empresas en peligro. Actúas como un consultor senior especializado en crisis operativas, financieras, comerciales y de personal. Tu misión es estabilizar el negocio hoy mismo.

### TU PERSONALIDAD
- Directo, frío cuando hay que serlo, contenedor cuando el usuario lo requiere.
- Priorización brutal: primero lo que salva la empresa, después lo demás.
- Cero bullshit. Cero teorías. Solo acciones.
- Lenguaje calmado pero firme.
- Enfocado en supervivencia del negocio.

### TU MISIÓN
1. Identificar la naturaleza de la crisis en menos de 10 minutos de preguntas.
2. Priorizar amenazas según severidad e impacto.
3. Dar instrucciones claras, tácticas y accionables para estabilizar HOY, no mañana.
4. Preparar el terreno para la sesión de 1 hora con un asesor humano.

### TIPOS DE CRISIS QUE DEBES IDENTIFICAR
- Liquidez / Flujo de Caja
- Caída abrupta de ventas
- Costos fuera de control
- Problemas de personal / conflictos internos
- Fallas operativas
- Riesgos legales
- Quejas o pérdida masiva de clientes
- Bloqueo mental del emprendedor (fatiga, burnout, decisiones reactivas)

### TU FRAMEWORK INTERNO
- Evaluación de severidad (1–5).
- Clasificación de tipo de crisis: Liquidez / Ventas / Costos / Operaciones / Legal / Personal / Clientes.
- Análisis de continuidad operativa (qué se cae primero y qué sostiene todo).
- Priorización de decisiones con impacto inmediato.

### MARCO ANALÍTICO - 3 PREGUNTAS CLAVE
1. ¿Qué está comprometiendo la continuidad inmediata del negocio?
2. ¿Qué puede detenerse sin afectar la operación crítica?
3. ¿Qué decisión, si no se toma hoy, será más cara mañana?

### ESTRUCTURA DE SALIDA OBLIGATORIA (JSON)
{
  "diagnostico_crisis": "qué está pasando en 4–6 líneas, sin adornos ni anestesia",
  "tipo_de_crisis": "clasificación principal (Liquidez/Ventas/Costos/Operaciones/Legal/Personal/Clientes)",
  "acciones_para_hoy": ["3 acciones no negociables, específicas, medibles, inmediatas"],
  "riesgos_si_no_actua": ["3 riesgos duros - advertencias claras"],
  "plan_7_dias": ["acciones secuenciales para estabilizar en la próxima semana"],
  "indicadores_inmediatos": ["qué medir hoy y cada 24 horas"],
  "diagnostico_rapido": "versión para el frontend",
  "acciones_inmediatas": ["acciones para las próximas 24-72 horas"],
  "riesgo_general": "bajo|moderado|alto|critico",
  "recomendaciones_clave": ["recomendaciones para las próximas 2-4 semanas"],
  "recomendaciones_innovadoras": ["ideas creativas o casos de éxito similares"],
  "siguiente_paso": "el paso más importante ahora mismo",
  "mensaje_de_apoyo": "frase de ánimo realista, no vacía"
}

### REGLAS
- Si la información es insuficiente, construye hipótesis y adviértelo.
- Si detectas riesgo de cierre, dilo claramente.
- Si la situación no es tan grave como el usuario cree, también dilo.
- Usa lenguaje ejecutivo y muy claro.
- Prioridad brutal: lo urgente mata lo importante.

Cuando recibas las respuestas, procede con el diagnóstico express."""

# =====================================================
# Utilidades de análisis
# =====================================================
SENTIMENT_NEGATIVE = [
    "urgente", "crítico", "grave", "emergencia", "pérdida", "caída", "disminuido",
    "no", "falta", "sin", "incapaz", "imposible", "preocupado", "estresado",
    "desesperado", "colapsar", "quiebra", "fracaso", "problema", "conflicto"
]

SENTIMENT_STRESS = [
    "no sé", "no lo sé", "no estoy seguro", "preocupado", "angustiado",
    "presión", "estrés", "abrumado", "cansado", "agotado"
]

RISK_PATTERNS = {
    "flujo_caja_critico": ["no cubre", "no tengo", "sin efectivo", "sin liquidez", "quiebra"],
    "operaciones_paradas": ["no puedo operar", "detener", "parar operaciones", "no funciona"],
    "ventas_colapsadas": ["cero ventas", "sin ventas", "caída total", "nada de ventas"],
    "personal_perdido": ["renunciaron todos", "sin personal", "equipo perdido"]
}

def _analizar_sentimiento(texto: str) -> Dict[str, Any]:
    if not texto:
        return {"sentimiento": "neutral", "nivel_estres": 0, "indicadores": []}
    
    texto_lower = texto.lower()
    indicadores = []
    
    stress_count = sum(1 for word in SENTIMENT_STRESS if word in texto_lower)
    negative_count = sum(1 for word in SENTIMENT_NEGATIVE if word in texto_lower)
    
    if stress_count > 2 or negative_count > 5:
        nivel_estres = 3
        indicadores.append("Alto nivel de estrés detectado en respuestas")
    elif stress_count > 0 or negative_count > 2:
        nivel_estres = 2
        indicadores.append("Moderado nivel de estrés detectado")
    else:
        nivel_estres = 1
    
    sentimiento = "negativo" if negative_count > 3 else "preocupado" if stress_count > 0 else "neutral"
    
    return {"sentimiento": sentimiento, "nivel_estres": nivel_estres, "indicadores": indicadores}

def _detectar_patrones_riesgo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
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

def _calcular_riesgo(diagnostico_data: Dict[str, Any], analisis_sentimiento: Dict, patrones: Dict) -> str:
    riesgo_base = 0
    
    continuidad = str(diagnostico_data.get("continuidadNegocio", ""))
    if continuidad in ("4", "5"):
        riesgo_base += 3
    elif continuidad == "3":
        riesgo_base += 2
    elif continuidad in ("1", "2"):
        riesgo_base += 1
    
    flujo = str(diagnostico_data.get("flujoEfectivo", "")).lower()
    if flujo == "no":
        riesgo_base += 3
    elif flujo == "parcialmente":
        riesgo_base += 1
    
    ventas = str(diagnostico_data.get("ventasDisminuido", "")).lower()
    if ventas == "si":
        riesgo_base += 2
    
    riesgo_base += analisis_sentimiento.get("nivel_estres", 0) - 1
    riesgo_base += patrones.get("riesgo_adicional", 0)
    
    if riesgo_base >= 7:
        return "critico"
    elif riesgo_base >= 5:
        return "alto"
    elif riesgo_base >= 3:
        return "moderado"
    return "bajo"

def _respuesta_fallback(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera respuesta de fallback sin OpenAI"""
    textos = [
        str(diagnostico_data.get("problematicaEspecifica", "")),
        str(diagnostico_data.get("problemaMasUrgente", "")),
        str(diagnostico_data.get("impactoDelProblema", ""))
    ]
    texto_completo = " ".join(txt for txt in textos if txt)
    
    analisis_sentimiento = _analizar_sentimiento(texto_completo)
    patrones_riesgo = _detectar_patrones_riesgo(diagnostico_data)
    riesgo = _calcular_riesgo(diagnostico_data, analisis_sentimiento, patrones_riesgo)
    
    nombre = diagnostico_data.get("nombreSolicitante", "").split()[0] if diagnostico_data.get("nombreSolicitante") else ""
    
    return {
        "diagnostico_crisis": f"Situación de riesgo {riesgo.upper()} detectada. Se requiere acción inmediata para estabilizar la operación.",
        "tipo_de_crisis": "Liquidez/Operaciones" if "flujo_caja_critico" in patrones_riesgo.get("patrones_criticos", []) else "General",
        "acciones_para_hoy": [
            "Congelar gastos no esenciales inmediatamente",
            "Contactar a clientes principales para acelerar cobros",
            "Comunicar situación a proveedores clave y negociar términos"
        ],
        "riesgos_si_no_actua": [
            "Deterioro acelerado de la situación",
            "Pérdida de proveedores o clientes clave",
            "Impacto en la moral del equipo"
        ],
        "plan_7_dias": [
            "Día 1-2: Estabilizar flujo de caja",
            "Día 3-4: Comunicar y negociar con stakeholders",
            "Día 5-7: Implementar controles de monitoreo"
        ],
        "indicadores_inmediatos": [
            "Saldo de caja diario",
            "Cuentas por cobrar vencidas",
            "Pedidos pendientes"
        ],
        "diagnostico_rapido": f"{nombre + ', ' if nombre else ''}hay solución para esto. Entiendo la situación y vamos a estabilizarla paso a paso.",
        "acciones_inmediatas": [
            "🔥 PRIMERO: Congela gastos no esenciales por 14 días",
            "💰 SEGUNDO: Contacta HOY a tus 3 mejores clientes para acelerar cobros",
            "📞 TERCERO: Comunica a proveedores clave tu situación"
        ],
        "riesgo_general": riesgo,
        "recomendaciones_clave": [
            "Implementar control de flujo de caja semanal",
            "Ajustar temporalmente la operación a la demanda actual",
            "Armar plan de recuperación comercial para los próximos 30-60 días"
        ],
        "recomendaciones_innovadoras": [
            "Considera factoring para acelerar liquidez",
            "Evalúa alianzas temporales con competidores complementarios"
        ],
        "siguiente_paso": "Hoy mismo, antes de terminar el día, lista los 5 pagos más urgentes y los 5 cobros más fáciles de acelerar.",
        "mensaje_de_apoyo": "Muchos empresarios han pasado por situaciones similares y han salido adelante. Estás tomando las decisiones correctas.",
        "analisis_sentimiento": analisis_sentimiento,
        "patrones_detectados": patrones_riesgo,
    }

# =====================================================
# Analizador principal
# =====================================================
async def analizar_diagnostico_emergencia(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza un diagnóstico de EMERGENCIA con OpenAI Chat Completions.
    """
    
    # Análisis local
    textos = [
        str(diagnostico_data.get("problematicaEspecifica", "")),
        str(diagnostico_data.get("problemaMasUrgente", "")),
        str(diagnostico_data.get("impactoDelProblema", ""))
    ]
    texto_completo = " ".join(txt for txt in textos if txt)
    
    analisis_sentimiento = _analizar_sentimiento(texto_completo)
    patrones_riesgo = _detectar_patrones_riesgo(diagnostico_data)
    riesgo_calculado = _calcular_riesgo(diagnostico_data, analisis_sentimiento, patrones_riesgo)
    
    # Fallback si no hay API key
    if not OPENAI_API_KEY or not client:
        return _respuesta_fallback(diagnostico_data)

    # Contexto para el LLM
    contexto_analisis = ""
    if analisis_sentimiento.get("nivel_estres", 0) >= 3:
        contexto_analisis += "\n⚠️ ALERTA: Alto nivel de estrés detectado en las respuestas del empresario. "
    if patrones_riesgo.get("alerta_temprana"):
        contexto_analisis += f"\n🚨 MÚLTIPLES PATRONES CRÍTICOS DETECTADOS: {', '.join(patrones_riesgo.get('patrones_criticos', []))}. "
    contexto_analisis += f"\nRiesgo calculado automáticamente: {riesgo_calculado}."

    user_prompt = f"""Analiza este diagnóstico de emergencia empresarial.

CONTEXTO PRE-ANALIZADO:
{contexto_analisis}

DATOS DEL DIAGNÓSTICO:
{json.dumps(diagnostico_data, ensure_ascii=False, indent=2)}

Genera el diagnóstico de crisis siguiendo la estructura JSON especificada.
Sé directo, táctico y enfocado en acciones inmediatas.
Priorización brutal: lo que salva la empresa primero."""

    try:
        def _call():
            completion = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": MENTHIA_CRISIS_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.25,
            )
            return completion.choices[0].message.content

        result = await asyncio.to_thread(_call)
        parsed = json.loads(result)
        
        # Enriquecer con análisis local
        if analisis_sentimiento.get("nivel_estres", 0) >= 2:
            parsed["analisis_sentimiento"] = analisis_sentimiento
        
        if patrones_riesgo.get("patrones_criticos"):
            parsed["patrones_detectados"] = patrones_riesgo
        
        # Validar riesgo
        riesgo_llm = parsed.get("riesgo_general", "").lower()
        if riesgo_llm not in ["bajo", "moderado", "alto", "critico"]:
            parsed["riesgo_general"] = riesgo_calculado
        elif riesgo_calculado == "critico" and riesgo_llm in ["bajo", "moderado"]:
            parsed["riesgo_general"] = "critico"
            parsed["diagnostico_rapido"] += " [Riesgo elevado a CRÍTICO por análisis automático]"
        
        return parsed

    except Exception as e:
        fallback = _respuesta_fallback(diagnostico_data)
        fallback["diagnostico_rapido"] = f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}. " + fallback["diagnostico_rapido"]
        return fallback
