# app/llm_general.py
import os
import json
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException

# OpenAI SDK (pip install openai>=1.40.0)
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Mapeo de áreas por prefijos
AREA_MAPPING = {
    "dg_": "Dirección General",
    "fa_": "Finanzas",
    "op_": "Operaciones",
    "mv_": "Marketing/Ventas",
    "rh_": "Recursos Humanos",
    "lc_": "Logística"
}

# ---- Utilidades ----
def _respuesta_vacia(mensaje_error: str = "No se pudo generar el análisis.") -> Dict[str, Any]:
    return {
        "resumen_ejecutivo": f"{mensaje_error}",
        "areas_oportunidad": ["Error en el análisis con IA."],
        "recomendaciones_clave": ["Verifica la configuración de la API o intenta de nuevo más tarde."],
        "puntuacion_madurez_promedio": 0.0,
        "nivel_madurez_general": "muy_bajo",
    }

def _nivel_madurez_desde_promedio(avg: float) -> str:
    if avg >= 4.6:
        return "muy_alto"
    if avg >= 4.0:
        return "alto"
    if avg >= 3.0:
        return "medio"
    if avg >= 2.0:
        return "bajo"
    return "muy_bajo"

def _extraer_likert(d: Dict[str, Any]) -> Tuple[float, str]:
    """Calcula el promedio de todas las respuestas tipo Likert (claves que inician con dg_, fa_, op_, mv_, rh_, lc_)."""
    scores: List[int] = []
    for k, v in d.items():
        if k.startswith(("dg_", "fa_", "op_", "mv_", "rh_", "lc_")) and str(v) in {"1", "2", "3", "4", "5"}:
            scores.append(int(v))
    if not scores:
        return 0.0, "muy_bajo"
    avg = round(sum(scores) / len(scores), 2)
    return avg, _nivel_madurez_desde_promedio(avg)

def _formatear_datos_para_prompt(d: Dict[str, Any]) -> str:
    """Convierte el dict de respuestas en líneas legibles para el prompt, excluyendo campos internos vacíos."""
    partes: List[str] = []
    for key, value in d.items():
        if key in {"userId", "createdAt"} or value in ("", None):
            continue
        partes.append(f"- {key}: {value}")
    return "\n".join(partes)

def _analizar_correlaciones(d: Dict[str, Any]) -> Dict[str, Any]:
    """Detecta correlaciones y patrones entre diferentes áreas del diagnóstico"""
    areas_scores: Dict[str, List[int]] = {}
    
    # Agrupar scores por área
    for k, v in d.items():
        if k in {"userId", "createdAt"}:
            continue
        for prefix, area_name in AREA_MAPPING.items():
            if k.startswith(prefix) and str(v) in {"1", "2", "3", "4", "5"}:
                if area_name not in areas_scores:
                    areas_scores[area_name] = []
                areas_scores[area_name].append(int(v))
    
    # Calcular promedios por área
    areas_avg: Dict[str, float] = {}
    for area, scores in areas_scores.items():
        if scores:
            areas_avg[area] = round(sum(scores) / len(scores), 2)
    
    # Detectar áreas débiles y fuertes
    areas_ordenadas = sorted(areas_avg.items(), key=lambda x: x[1])
    area_mas_debil = areas_ordenadas[0] if areas_ordenadas else None
    area_mas_fuerte = areas_ordenadas[-1] if areas_ordenadas else None
    
    # Detectar correlaciones problemáticas conocidas
    correlaciones_detectadas = []
    
    # Finanzas baja + Operaciones baja = riesgo sistémico
    if areas_avg.get("Finanzas", 5) <= 2.5 and areas_avg.get("Operaciones", 5) <= 2.5:
        correlaciones_detectadas.append({
            "tipo": "riesgo_sistemico",
            "areas": ["Finanzas", "Operaciones"],
            "mensaje": "Finanzas y Operaciones débiles simultáneamente indican riesgo sistémico alto",
            "impacto": "alto"
        })
    
    # Marketing bajo + RH bajo = problemas de crecimiento
    if areas_avg.get("Marketing/Ventas", 5) <= 2.5 and areas_avg.get("Recursos Humanos", 5) <= 2.5:
        correlaciones_detectadas.append({
            "tipo": "crecimiento_limitado",
            "areas": ["Marketing/Ventas", "Recursos Humanos"],
            "mensaje": "Marketing y RH débiles limitan significativamente el crecimiento",
            "impacto": "medio"
        })
    
    # Dirección débil + cualquier área débil = problemas de ejecución
    if areas_avg.get("Dirección General", 5) <= 2.5:
        areas_debiles = [a for a, score in areas_avg.items() if score <= 3.0 and a != "Dirección General"]
        if areas_debiles:
            correlaciones_detectadas.append({
                "tipo": "ejecucion_comprometida",
                "areas": ["Dirección General"] + areas_debiles[:2],
                "mensaje": "Dirección débil compromete la ejecución efectiva en otras áreas",
                "impacto": "alto"
            })
    
    return {
        "areas_scores": areas_avg,
        "area_mas_debil": {"nombre": area_mas_debil[0], "score": area_mas_debil[1]} if area_mas_debil else None,
        "area_mas_fuerte": {"nombre": area_mas_fuerte[0], "score": area_mas_fuerte[1]} if area_mas_fuerte else None,
        "correlaciones": correlaciones_detectadas,
        "brecha_maxima": round(area_mas_fuerte[1] - area_mas_debil[1], 2) if area_mas_debil and area_mas_fuerte else 0
    }

def _predecir_tendencias(d: Dict[str, Any], correlaciones: Dict, avg: float, nivel: str) -> Dict[str, Any]:
    """Predice tendencias futuras basadas en patrones detectados"""
    predicciones = []
    
    # Predicción basada en nivel general
    if nivel in ["muy_bajo", "bajo"]:
        if correlaciones.get("correlaciones"):
            for corr in correlaciones["correlaciones"]:
                if corr.get("impacto") == "alto":
                    predicciones.append({
                        "escenario": "pesimista",
                        "probabilidad": "60-75%",
                        "descripcion": f"Sin intervención, {corr['mensaje']}. Impacto en 3-6 meses.",
                        "tiempo": "3-6 meses"
                    })
        
        # Predicción de mejora si toman acción
        predicciones.append({
            "escenario": "optimista",
            "probabilidad": "65-80%",
            "descripcion": "Con acciones correctas en áreas prioritarias, mejora de 0.8-1.2 puntos en 90 días",
            "tiempo": "90 días",
            "requisito": "Implementar recomendaciones prioritarias"
        })
    elif nivel == "medio":
        predicciones.append({
            "escenario": "base",
            "probabilidad": "50-60%",
            "descripcion": "Mantener status quo requiere atención constante. Mejora moderada (0.5-0.8 puntos) posible en 120 días con enfoque estratégico",
            "tiempo": "120 días"
        })
    
    # Predicción basada en área más débil
    area_debil = correlaciones.get("area_mas_debil")
    if area_debil and area_debil.get("score", 5) <= 2.0:
        predicciones.append({
            "escenario": "riesgo_especifico",
            "probabilidad": "70-85%",
            "descripcion": f"{area_debil['nombre']} crítica. Sin acción, puede arrastrar otras áreas en 2-4 meses",
            "tiempo": "2-4 meses",
            "area_critica": area_debil["nombre"]
        })
    
    return {
        "predicciones": predicciones[:3],  # Máximo 3 predicciones
        "recomendacion_prioritaria": area_debil["nombre"] if area_debil else None
    }

def _generar_recomendaciones_inteligentes(correlaciones: Dict, predicciones: Dict, d: Dict[str, Any]) -> List[str]:
    """Genera recomendaciones basadas en correlaciones y predicciones"""
    recomendaciones = []
    
    # Recomendación basada en área más débil
    area_debil = correlaciones.get("area_mas_debil")
    if area_debil:
        if area_debil["nombre"] == "Finanzas":
            recomendaciones.append("💰 PRIORIDAD MÁXIMA: Finanzas débil. Implementa control de flujo de caja semanal inmediatamente. Sin esto, otras mejoras no serán sostenibles")
        elif area_debil["nombre"] == "Dirección General":
            recomendaciones.append("🎯 PRIORIDAD ALTA: Dirección débil compromete todo. Establece misión/visión y objetivos claros antes de otras iniciativas")
        elif area_debil["nombre"] == "Operaciones":
            recomendaciones.append("⚙️ PRIORIDAD ALTA: Operaciones débil. Documenta procesos críticos primero, luego mejora calidad")
    
    # Recomendación basada en correlaciones
    for corr in correlaciones.get("correlaciones", []):
        if corr.get("impacto") == "alto":
            recomendaciones.append(f"🚨 RIESGO SISTÉMICO: {corr['mensaje']}. Aborda ambas áreas simultáneamente con plan integrado")
            break
    
    # Recomendación basada en brecha
    if correlaciones.get("brecha_maxima", 0) >= 2.0:
        recomendaciones.append("📊 BRECHA SIGNIFICATIVA: Diferencia de más de 2 puntos entre áreas. Enfócate primero en la más débil para evitar arrastre sistémico")
    
    # Recomendación basada en predicción
    if predicciones.get("predicciones"):
        pred_alta_prob = [p for p in predicciones["predicciones"] if "70" in str(p.get("probabilidad", ""))]
        if pred_alta_prob:
            rec = pred_alta_prob[0]
            recomendaciones.append(f"⏱️ URGENCIA: {rec.get('descripcion', '')}. Acción recomendada en los próximos 30 días")
    
    return recomendaciones[:3]  # Máximo 3 recomendaciones inteligentes

# ---- Analizador principal ----
async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial general usando OpenAI (gpt-4.1-mini),
    devolviendo el JSON EXACTO que consume el frontend:
    {
      resumen_ejecutivo: string,
      areas_oportunidad: string[],
      recomendaciones_clave: string[],
      puntuacion_madurez_promedio: number,
      nivel_madurez_general: "muy_bajo"|"bajo"|"medio"|"alto"|"muy_alto"
    }
    """

    # Fallback DEMO si no hay API key (útil en local)
    if not OPENAI_API_KEY or not client:
        avg, nivel = _extraer_likert(diagnostico_data)
        correlaciones = _analizar_correlaciones(diagnostico_data)
        predicciones = _predecir_tendencias(diagnostico_data, correlaciones, avg, nivel)
        recomendaciones_inteligentes = _generar_recomendaciones_inteligentes(correlaciones, predicciones, diagnostico_data)
        
        return {
            "resumen_ejecutivo": "Demo local sin OPENAI_API_KEY. Se detectan oportunidades en planeación, finanzas y marketing.",
            "areas_oportunidad": [
                "Definición y seguimiento de objetivos (OKR)",
                "Control y proyección de flujo de caja",
                "Estandarización de procesos operativos",
                "Definición de ICP y canal comercial",
            ],
            "recomendaciones_clave": [
                "Implantar tablero semanal con KPIs",
                "Auditar gastos y renegociar costos",
                "Documentar procesos críticos (SOPs)",
                "Campañas con propuesta de valor segmentada",
            ],
            "puntuacion_madurez_promedio": avg,
            "nivel_madurez_general": nivel,
            "recomendaciones_innovadoras": recomendaciones_inteligentes,
            "correlaciones_detectadas": correlaciones.get("correlaciones", []),
            "predicciones": predicciones.get("predicciones", []),
            "siguiente_paso": predicciones.get("recomendacion_prioritaria") and f"Prioriza acciones en {predicciones['recomendacion_prioritaria']}"
        }

    # Análisis inteligente local
    avg, nivel = _extraer_likert(diagnostico_data)
    correlaciones = _analizar_correlaciones(diagnostico_data)
    predicciones = _predecir_tendencias(diagnostico_data, correlaciones, avg, nivel)
    recomendaciones_inteligentes = _generar_recomendaciones_inteligentes(correlaciones, predicciones, diagnostico_data)
    
    # Construcción del prompt mejorado
    datos_fmt = _formatear_datos_para_prompt(diagnostico_data)
    
    # Contexto adicional para el LLM
    contexto_inteligente = ""
    if correlaciones.get("correlaciones"):
        for corr in correlaciones["correlaciones"][:2]:  # Máximo 2 correlaciones
            contexto_inteligente += f"\n⚠️ CORRELACIÓN DETECTADA: {corr['mensaje']}. "
    if predicciones.get("predicciones"):
        pred_importante = predicciones["predicciones"][0] if predicciones["predicciones"] else None
        if pred_importante and pred_importante.get("impacto") != "bajo":
            contexto_inteligente += f"\n📊 PREDICCIÓN: {pred_importante.get('descripcion', '')}. "

    system_msg = {
        "role": "system",
        "content": (
            "Eres un CONSULTOR DE NEGOCIOS EXPERTO con experiencia en análisis predictivo y detección de patrones. "
            "Responde EXCLUSIVAMENTE con JSON válido. "
            "El JSON debe cumplir el siguiente contrato:\n"
            "{\n"
            '  "resumen_ejecutivo": string,\n'
            '  "areas_oportunidad": string[],\n'
            '  "recomendaciones_clave": string[],\n'
            '  "puntuacion_madurez_promedio": number,\n'
            '  "nivel_madurez_general": "muy_bajo"|"bajo"|"medio"|"alto"|"muy_alto",\n'
            '  "recomendaciones_innovadoras" (opcional): string[],\n'
            '  "siguiente_paso" (opcional): string\n'
            "}\n"
            "Nada de texto fuera de JSON."
        ),
    }

    user_msg = {
        "role": "user",
        "content": (
            "Analiza este diagnóstico general empresarial. Considera:\n"
            "1. Identificar áreas más débiles y su impacto en otras áreas (efecto cascada)\n"
            "2. Detectar correlaciones entre problemas en diferentes áreas\n"
            "3. Priorizar recomendaciones por impacto y velocidad de implementación\n\n"
            f"{contexto_inteligente}\n\n"
            "Devuelve SOLO el JSON con:\n"
            "- resumen_ejecutivo: breve, claro y accionable. Menciona correlaciones si las detectas.\n"
            "- areas_oportunidad: 4–8 puntos concretos. Prioriza las que tienen mayor impacto sistémico.\n"
            "- recomendaciones_clave: 4–8 acciones prácticas (0-90 días). Primera recomendación debe ser la de mayor prioridad.\n"
            "- puntuacion_madurez_promedio: número. Usa el cálculo sugerido: {avg}\n"
            "- nivel_madurez_general: {nivel}\n"
            "- recomendaciones_innovadoras (opcional): 2–4 recomendaciones adicionales basadas en patrones detectados.\n"
            "- siguiente_paso (opcional): Próximo paso más importante según el análisis.\n\n"
            "Interpretación Likert:\n"
            "1: Difuso; 2: Ocasional; 3: Regular sin procesos; 4: Correcto y estandarizado; 5: Excelente y automatizado.\n\n"
            f"Área más débil detectada: {correlaciones.get('area_mas_debil', {}).get('nombre', 'N/A')} "
            f"(score: {correlaciones.get('area_mas_debil', {}).get('score', 'N/A')})\n"
            f"Área más fuerte: {correlaciones.get('area_mas_fuerte', {}).get('nombre', 'N/A')} "
            f"(score: {correlaciones.get('area_mas_fuerte', {}).get('score', 'N/A')})\n\n"
            "Datos completos:\n"
            f"{datos_fmt}\n\n"
            "Recuerda: responde SOLO con JSON válido."
        ).format(avg=avg, nivel=nivel),
    }

    try:
        # Usamos chat.completions con JSON mode (json_object) para evitar problemas con Responses API
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[system_msg, user_msg],
            response_format={"type": "json_object"},
            temperature=0.3,  # Un poco más alto para más creatividad en recomendaciones
        )

        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)

        # Validación mínima y saneo de tipos/valores
        if not isinstance(parsed.get("resumen_ejecutivo", ""), str):
            parsed["resumen_ejecutivo"] = "No se pudo generar el resumen."

        def _as_list_str(x):
            if isinstance(x, list):
                return [str(i) for i in x][:12]
            return []

        parsed["areas_oportunidad"] = _as_list_str(parsed.get("areas_oportunidad", []))
        parsed["recomendaciones_clave"] = _as_list_str(parsed.get("recomendaciones_clave", []))

        # Recalcular con datos reales del usuario (tiene prioridad)
        avg_usr, nivel_usr = _extraer_likert(diagnostico_data)
        parsed["puntuacion_madurez_promedio"] = float(parsed.get("puntuacion_madurez_promedio", avg_usr or 0.0))
        parsed["nivel_madurez_general"] = str(parsed.get("nivel_madurez_general", nivel_usr or "muy_bajo"))

        # Asegurar consistencia si el modelo devolvió algo fuera de rango
        if parsed["nivel_madurez_general"] not in {"muy_bajo", "bajo", "medio", "alto", "muy_alto"}:
            parsed["nivel_madurez_general"] = nivel_usr

        # Si el promedio no tiene sentido, aplicamos nuestro cálculo
        if parsed["puntuacion_madurez_promedio"] <= 0.0 and avg_usr > 0.0:
            parsed["puntuacion_madurez_promedio"] = avg_usr
            parsed["nivel_madurez_general"] = nivel_usr
        
        # Enriquecer con análisis inteligente
        if correlaciones.get("correlaciones"):
            parsed["correlaciones_detectadas"] = correlaciones["correlaciones"]
        
        if predicciones.get("predicciones"):
            parsed["predicciones"] = predicciones["predicciones"]
        
        # Agregar recomendaciones inteligentes si no vienen del LLM
        if not parsed.get("recomendaciones_innovadoras"):
            parsed["recomendaciones_innovadoras"] = recomendaciones_inteligentes
        
        # Agregar siguiente paso si hay predicción importante
        if not parsed.get("siguiente_paso") and predicciones.get("recomendacion_prioritaria"):
            parsed["siguiente_paso"] = f"Prioriza acciones en {predicciones['recomendacion_prioritaria']} para mayor impacto sistémico"

        return parsed

    except Exception as e:
        # No reventar al frontend: retornar payload útil con mensaje de error (+ cálculo propio si aplica)
        avg2, nivel2 = _extraer_likert(diagnostico_data)
        return {
            "resumen_ejecutivo": f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}",
            "areas_oportunidad": ["No fue posible generar áreas de oportunidad."],
            "recomendaciones_clave": ["Intenta nuevamente en unos minutos o verifica tu API Key."],
            "puntuacion_madurez_promedio": avg2,
            "nivel_madurez_general": nivel2,
        }
