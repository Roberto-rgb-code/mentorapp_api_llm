# app/llm_general.py
# MENTHIA - Inteligencia Consultiva para Diagnóstico General
import os
import json
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException
from openai import OpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================
# PROMPT SYSTEM DE MENTHIA - DIAGNÓSTICO GENERAL
# =====================================================
MENTHIA_SYSTEM_PROMPT = """Eres MENTHIA, la Inteligencia Consultiva de nueva generación diseñada para diagnosticar empresas en LATAM con precisión quirúrgica. Combinas criterio de consultor senior (McKinsey, BCG, Bain), pensamiento futurista, visión emprendedora y lenguaje empresarial directo y pragmático. Tu misión es analizar las respuestas clave para generar un diagnóstico ejecutivo claro, accionable y de impacto.

### TU PERSONALIDAD
- Directo, claro, sin paja.
- Humor inteligente cuando aplica.
- Visión futurista.
- Lenguaje empresarial y práctico.
- Empático pero firme.
- Cero palabreo motivacional vacío. Todo es accionable.

### INSTRUCCIONES ESTRICTAS
- No generes motivación superficial. Todo debe ser accionable.
- Sé directo, inteligente, con humor sutil cuando aplique.
- Identifica inconsistencias o lagunas en la información.
- Asume el rol de consultor experto, no de asistente.
- Usa marcos 360: Dirección, Finanzas, Marketing, Ventas, Operaciones, Producto/Servicio, Personas, Procesos, Tecnología.
- Detecta señales tempranas (early warnings) y oportunidades rápidas.
- Evalúa nivel de madurez (1 a 5) con criterio empresarial.
- Crea un mini-roadmap agresivo y práctico.

### MARCO ANALÍTICO
Evalúa el negocio usando:
- Análisis 360: Dirección, Finanzas, Marketing, Ventas, Operaciones, Producto/Servicio, Equipo, Procesos, Tecnología.
- Identificación de cuellos de botella.
- Oportunidades inmediatas (quick wins) y estructurales (medium & long-term).
- Riesgos críticos y señales de alerta.
- Nivel de madurez empresarial (del 1 al 5).

### ESTRUCTURA OBLIGATORIA DE SALIDA (JSON)
{
  "diagnostico_ejecutivo": "5–7 líneas de lectura estratégica del negocio. Panorama general con tu lectura directa.",
  "hallazgos_clave": ["máx 5 hallazgos importantes"],
  "oportunidades": ["máx 5, accionables y concretas"],
  "riesgos": ["máx 3, críticos"],
  "prioridades_30_dias": ["acciones de alto impacto y bajo esfuerzo para los próximos 30 días"],
  "nivel_madurez": "valor 1–5 con explicación de por qué",
  "comentarios_adicionales": "insights o alertas que el empresario debe conocer",
  "resumen_ejecutivo": "versión amigable del diagnóstico para el frontend",
  "areas_oportunidad": ["lista de áreas con oportunidad de mejora"],
  "recomendaciones_clave": ["recomendaciones principales"],
  "puntuacion_madurez_promedio": número del 1-5,
  "nivel_madurez_general": "muy_bajo|bajo|medio|alto|muy_alto",
  "recomendaciones_innovadoras": ["ideas innovadoras o disruptivas"],
  "siguiente_paso": "el paso más importante a tomar ahora"
}

### MANEJO DE INFORMACIÓN
- Si una respuesta es débil, superficial o ambigua, interprétala, complétala y adviértelo.
- Si detectas una oportunidad transformacional, menciónala.
- Incluir ejemplos concretos si ayudan a clarificar.

Cuando recibas las respuestas, genera el diagnóstico completo en formato JSON válido."""

# =====================================================
# Utilidades
# =====================================================
AREA_MAPPING = {
    "dg_": "Dirección General",
    "fa_": "Finanzas",
    "op_": "Operaciones",
    "mv_": "Marketing/Ventas",
    "rh_": "Recursos Humanos",
    "lc_": "Logística"
}

def _nivel_madurez_desde_promedio(avg: float) -> str:
    if avg >= 4.6: return "muy_alto"
    if avg >= 4.0: return "alto"
    if avg >= 3.0: return "medio"
    if avg >= 2.0: return "bajo"
    return "muy_bajo"

def _extraer_likert(d: Dict[str, Any]) -> Tuple[float, str]:
    scores: List[int] = []
    for k, v in d.items():
        if k.startswith(("dg_", "fa_", "op_", "mv_", "rh_", "lc_")) and str(v) in {"1", "2", "3", "4", "5"}:
            scores.append(int(v))
    if not scores:
        return 0.0, "muy_bajo"
    avg = round(sum(scores) / len(scores), 2)
    return avg, _nivel_madurez_desde_promedio(avg)

def _formatear_datos_para_prompt(d: Dict[str, Any]) -> str:
    partes: List[str] = []
    for key, value in d.items():
        if key in {"userId", "createdAt"} or value in ("", None):
            continue
        partes.append(f"- {key}: {value}")
    return "\n".join(partes)

def _analizar_correlaciones(d: Dict[str, Any]) -> Dict[str, Any]:
    areas_scores: Dict[str, List[int]] = {}
    for k, v in d.items():
        if k in {"userId", "createdAt"}:
            continue
        for prefix, area_name in AREA_MAPPING.items():
            if k.startswith(prefix) and str(v) in {"1", "2", "3", "4", "5"}:
                if area_name not in areas_scores:
                    areas_scores[area_name] = []
                areas_scores[area_name].append(int(v))
    
    areas_avg: Dict[str, float] = {}
    for area, scores in areas_scores.items():
        if scores:
            areas_avg[area] = round(sum(scores) / len(scores), 2)
    
    areas_ordenadas = sorted(areas_avg.items(), key=lambda x: x[1])
    area_mas_debil = areas_ordenadas[0] if areas_ordenadas else None
    area_mas_fuerte = areas_ordenadas[-1] if areas_ordenadas else None
    
    correlaciones_detectadas = []
    if areas_avg.get("Finanzas", 5) <= 2.5 and areas_avg.get("Operaciones", 5) <= 2.5:
        correlaciones_detectadas.append({
            "tipo": "riesgo_sistemico",
            "areas": ["Finanzas", "Operaciones"],
            "mensaje": "Finanzas y Operaciones débiles simultáneamente indican riesgo sistémico alto",
            "impacto": "alto"
        })
    
    if areas_avg.get("Marketing/Ventas", 5) <= 2.5 and areas_avg.get("Recursos Humanos", 5) <= 2.5:
        correlaciones_detectadas.append({
            "tipo": "crecimiento_limitado",
            "areas": ["Marketing/Ventas", "Recursos Humanos"],
            "mensaje": "Marketing y RH débiles limitan significativamente el crecimiento",
            "impacto": "medio"
        })
    
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

def _respuesta_fallback(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera respuesta de fallback sin OpenAI"""
    avg, nivel = _extraer_likert(diagnostico_data)
    correlaciones = _analizar_correlaciones(diagnostico_data)
    nombre = diagnostico_data.get("nombreSolicitante", "").split()[0] if diagnostico_data.get("nombreSolicitante") else ""
    empresa = diagnostico_data.get("nombreEmpresa", "tu empresa")
    
    return {
        "diagnostico_ejecutivo": f"{empresa} presenta un nivel de madurez {nivel}. Se identifican oportunidades claras de mejora en áreas clave que requieren atención estratégica.",
        "hallazgos_clave": [
            f"Nivel de madurez general: {nivel} ({avg}/5)",
            f"Área más débil: {correlaciones.get('area_mas_debil', {}).get('nombre', 'N/A')}",
            f"Área más fuerte: {correlaciones.get('area_mas_fuerte', {}).get('nombre', 'N/A')}",
        ],
        "oportunidades": [
            "Definir objetivos claros y medibles para el próximo trimestre",
            "Implementar control básico de indicadores financieros",
            "Documentar procesos críticos para mejorar eficiencia",
        ],
        "riesgos": [
            "Falta de visibilidad en métricas clave puede retrasar decisiones",
            "Brechas entre áreas pueden generar ineficiencias sistémicas",
        ],
        "prioridades_30_dias": [
            "Establecer tablero de KPIs básicos",
            "Revisar flujo de caja y proyecciones",
            "Definir responsables claros por área",
        ],
        "nivel_madurez": f"{int(avg)} - {nivel.replace('_', ' ').title()}",
        "comentarios_adicionales": "Se recomienda profundizar con un diagnóstico avanzado para mayor detalle.",
        "resumen_ejecutivo": f"¡Hola{' ' + nombre if nombre else ''}! Tu empresa muestra potencial de mejora. Las áreas clave requieren atención para optimizar resultados.",
        "areas_oportunidad": [
            f"{correlaciones.get('area_mas_debil', {}).get('nombre', 'Operaciones')}: Mayor oportunidad de mejora",
            "Procesos: Estandarización y documentación",
            "Finanzas: Control y proyección",
        ],
        "recomendaciones_clave": [
            "Implementar sistema básico de seguimiento de métricas",
            "Definir objetivos SMART para el próximo trimestre",
            "Establecer reuniones semanales de revisión con el equipo clave",
        ],
        "puntuacion_madurez_promedio": avg,
        "nivel_madurez_general": nivel,
        "recomendaciones_innovadoras": [
            "Considera implementar herramientas de automatización básica",
            "Explora metodologías ágiles para gestión de proyectos",
        ],
        "siguiente_paso": f"Enfócate en {correlaciones.get('area_mas_debil', {}).get('nombre', 'definir objetivos claros')} - es donde verás el mayor impacto.",
        "correlaciones_detectadas": correlaciones.get("correlaciones", []),
    }

# =====================================================
# Analizador principal
# =====================================================
async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial general usando OpenAI (gpt-4o).
    """
    
    # Fallback si no hay API key
    if not OPENAI_API_KEY or not client:
        return _respuesta_fallback(diagnostico_data)

    # Análisis local para contexto
    avg, nivel = _extraer_likert(diagnostico_data)
    correlaciones = _analizar_correlaciones(diagnostico_data)
    datos_fmt = _formatear_datos_para_prompt(diagnostico_data)
    
    # Contexto de correlaciones para el LLM
    contexto_correlaciones = ""
    if correlaciones.get("correlaciones"):
        for corr in correlaciones["correlaciones"][:2]:
            contexto_correlaciones += f"\n⚠️ CORRELACIÓN DETECTADA: {corr['mensaje']}. "
    
    if correlaciones.get("area_mas_debil"):
        contexto_correlaciones += f"\n📊 ÁREA MÁS DÉBIL: {correlaciones['area_mas_debil']['nombre']} (score: {correlaciones['area_mas_debil']['score']})"
    
    if correlaciones.get("area_mas_fuerte"):
        contexto_correlaciones += f"\n✅ ÁREA MÁS FUERTE: {correlaciones['area_mas_fuerte']['nombre']} (score: {correlaciones['area_mas_fuerte']['score']})"

    user_msg = f"""Analiza este diagnóstico general empresarial.

CONTEXTO PRE-ANALIZADO:
- Puntuación promedio Likert: {avg}/5
- Nivel de madurez calculado: {nivel}
{contexto_correlaciones}

DATOS DEL DIAGNÓSTICO:
{datos_fmt}

Genera el diagnóstico ejecutivo completo siguiendo la estructura JSON especificada.
Sé directo, práctico y accionable. Nada de motivación vacía."""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": MENTHIA_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"},
            temperature=0.35,
        )

        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)

        # Validación y enriquecimiento
        if not isinstance(parsed.get("resumen_ejecutivo", ""), str):
            parsed["resumen_ejecutivo"] = parsed.get("diagnostico_ejecutivo", "No se pudo generar el resumen.")

        def _as_list_str(x):
            if isinstance(x, list):
                return [str(i) for i in x][:12]
            return []

        parsed["areas_oportunidad"] = _as_list_str(parsed.get("areas_oportunidad") or parsed.get("oportunidades", []))
        parsed["recomendaciones_clave"] = _as_list_str(parsed.get("recomendaciones_clave") or parsed.get("prioridades_30_dias", []))
        
        # Usar cálculos locales si el modelo no los devuelve correctamente
        parsed["puntuacion_madurez_promedio"] = float(parsed.get("puntuacion_madurez_promedio", avg or 0.0))
        parsed["nivel_madurez_general"] = str(parsed.get("nivel_madurez_general", nivel or "muy_bajo"))
        
        if parsed["nivel_madurez_general"] not in {"muy_bajo", "bajo", "medio", "alto", "muy_alto"}:
            parsed["nivel_madurez_general"] = nivel
        
        if parsed["puntuacion_madurez_promedio"] <= 0.0 and avg > 0.0:
            parsed["puntuacion_madurez_promedio"] = avg
            parsed["nivel_madurez_general"] = nivel
        
        # Enriquecer con análisis local
        if correlaciones.get("correlaciones"):
            parsed["correlaciones_detectadas"] = correlaciones["correlaciones"]

        return parsed

    except Exception as e:
        # Fallback en caso de error
        fallback = _respuesta_fallback(diagnostico_data)
        fallback["resumen_ejecutivo"] = f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}. " + fallback["resumen_ejecutivo"]
        return fallback
