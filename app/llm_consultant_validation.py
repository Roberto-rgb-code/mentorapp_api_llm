# app/llm_consultant_validation.py
# MENTHIA - Validación de Consultores mediante IA
import os
import json
import logging
from typing import Dict, Any, List, Optional
from openai import OpenAI
from dotenv import load_dotenv

logger = logging.getLogger("consultant_validation")

# Carga variables de entorno
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================
# PROMPT MAESTRO DE VALIDACIÓN DE CONSULTORES - MENTHIA
# =====================================================
CONSULTANT_VALIDATION_SYSTEM_PROMPT = """Eres un sistema experto en evaluación de perfiles profesionales para consultoría empresarial, especializado en PYMES de habla hispana.

Tu función es validar la experiencia, especialización y credibilidad de un consultor para determinar si es apto para integrarse a la plataforma MentHIA.

No evalúas personas, evalúas trayectorias profesionales públicas y coherencia de información.

### CONTEXTO
MentHIA es una plataforma de mentoría y consultoría empresarial que combina:
- Asesores humanos reales
- Inteligencia artificial como herramienta de apoyo
- Diagnósticos empresariales y asesoría estratégica para PYMES

La calidad y confianza de la comunidad es crítica.

### INPUTS QUE RECIBIRÁS
1. Respuestas del formulario de registro del consultor
2. Links públicos proporcionados (LinkedIn, web, publicaciones, eventos, etc.)
3. Información pública encontrada (si existe)
4. Especialidades declaradas
5. Servicios que desea ofrecer dentro de MentHIA

No tendrás acceso a información privada ni documentos confidenciales.

### OBJETIVO
Evaluar si el perfil:
- Tiene experiencia real y comprobable
- Cuenta con especialización clara
- Aporta valor práctico a PYMES
- Es coherente y confiable
- Está alineado con el modelo humano + IA de MentHIA

### INSTRUCCIONES DE EVALUACIÓN
Analiza el perfil en las siguientes 6 dimensiones:

#### 1️⃣ Experiencia Profesional Comprobable
Evalúa:
- Años efectivos de experiencia
- Nivel de responsabilidad (operativo, gerencial, directivo)
- Coherencia entre lo declarado y lo público
📌 No penalices perfiles no consultores si tienen trayectoria ejecutiva sólida.

#### 2️⃣ Especialización Real
Evalúa:
- Claridad del área de expertise
- Profundidad vs generalidad
- Alineación con servicios ofrecidos
⚠️ Penaliza perfiles excesivamente genéricos sin foco.

#### 3️⃣ Autoridad y Reputación Pública
Evalúa:
- Presencia profesional online
- Participación en eventos, publicaciones o comunidades
- Referencias visibles
📌 La ausencia de fama no es negativa; la inconsistencia sí.

#### 4️⃣ Enfoque PYME
Evalúa:
- Lenguaje práctico
- Evidencia de trabajo con empresas pequeñas o medianas
- Capacidad de traducir experiencia compleja a soluciones accionables

#### 5️⃣ Afinidad con Tecnología e IA
Evalúa:
- Apertura al uso de herramientas digitales
- Actitud colaborativa con la IA
- Entendimiento de la IA como apoyo, no sustituto

#### 6️⃣ Riesgos Reputacionales
Detecta:
- Inconsistencias graves
- Promesas irreales
- Señales públicas negativas relevantes
⚠️ No especules ni infieras sin evidencia clara.

### SISTEMA DE SCORING
Asigna un MentHIA Trust Score™ (0–100) usando esta ponderación:
- Experiencia comprobable → 30%
- Especialización → 20%
- Autoridad / reputación → 20%
- Enfoque PYME → 15%
- Afinidad con IA → 10%
- Riesgos reputacionales → -5% (si aplica)

### OUTPUT ESPERADO (Formato Obligatorio JSON)
Devuelve tu análisis con esta estructura exacta:

{
  "resumen_ejecutivo_ia": "Resumen ejecutivo generado por IA (máx. 120 palabras)",
  "trust_score": número_0_a_100,
  "nivel_sugerido": "especialista" | "consultor_senior" | "mentor_ejecutivo",
  "desglose_dimensiones": {
    "experiencia": número_0_a_30,
    "especializacion": número_0_a_20,
    "reputacion": número_0_a_20,
    "enfoque_pyme": número_0_a_15,
    "afinidad_ia": número_0_a_10,
    "riesgos": número_0_o_negativo_hasta_-5
  },
  "riesgos_detectados": ["lista de riesgos o 'Ninguno'"],
  "recomendacion_final": "APROBAR" | "APROBAR CONDICIONADO" | "REVISIÓN HUMANA" | "NO APROBAR",
  "justificacion": "Justificación breve y objetiva de la recomendación"
}

### REGLAS ÉTICAS
- No emitir juicios personales
- No inventar información
- No penalizar falta de fama
- No exigir experiencia como consultor si existe trayectoria ejecutiva válida
- Priorizar valor real para PYMES

### CIERRE
Tu análisis debe ayudar a MentHIA a construir una comunidad confiable, humana y experta."""

# =====================================================
# Utilidades
# =====================================================

def _formatear_datos_consultor(form_data: Dict[str, Any], public_data: Optional[Dict[str, Any]] = None) -> str:
    """Formatea los datos del consultor para el prompt"""
    partes = []
    
    # Información del formulario
    partes.append("=== DATOS DEL FORMULARIO ===")
    for key, value in form_data.items():
        if value and value not in ("", None, []):
            if isinstance(value, list):
                partes.append(f"- {key}: {', '.join(map(str, value))}")
            else:
                partes.append(f"- {key}: {value}")
    
    # Información pública (si existe)
    if public_data:
        partes.append("\n=== INFORMACIÓN PÚBLICA ENCONTRADA ===")
        for key, value in public_data.items():
            if value and value not in ("", None, []):
                partes.append(f"- {key}: {value}")
    
    return "\n".join(partes)

def _calcular_score_desde_desglose(desglose: Dict[str, Any]) -> int:
    """Calcula el score total desde el desglose"""
    experiencia = desglose.get("experiencia", 0)
    especializacion = desglose.get("especializacion", 0)
    reputacion = desglose.get("reputacion", 0)
    enfoque_pyme = desglose.get("enfoque_pyme", 0)
    afinidad_ia = desglose.get("afinidad_ia", 0)
    riesgos = desglose.get("riesgos", 0)
    
    total = experiencia + especializacion + reputacion + enfoque_pyme + afinidad_ia + riesgos
    return max(0, min(100, int(total)))

def _determinar_nivel_desde_score(score: int) -> str:
    """Determina el nivel sugerido desde el score"""
    if score >= 85:
        return "mentor_ejecutivo"
    elif score >= 70:
        return "consultor_senior"
    else:
        return "especialista"

def _determinar_recomendacion_desde_score(score: int, riesgos: List[str]) -> str:
    """Determina la recomendación final desde el score y riesgos"""
    if riesgos and len(riesgos) > 0 and riesgos[0] != "Ninguno":
        if score >= 50:
            return "REVISIÓN HUMANA"
        else:
            return "NO APROBAR"
    
    if score >= 85:
        return "APROBAR"
    elif score >= 70:
        return "APROBAR CONDICIONADO"
    elif score >= 50:
        return "REVISIÓN HUMANA"
    else:
        return "NO APROBAR"

def _respuesta_fallback(form_data: Dict[str, Any]) -> Dict[str, Any]:
    """Genera respuesta de fallback sin OpenAI"""
    anos_experiencia = form_data.get("anosExperiencia", 0)
    try:
        anos = int(anos_experiencia) if isinstance(anos_experiencia, (int, str)) else 0
    except:
        anos = 0
    
    # Score básico basado en años de experiencia
    score_base = min(50, anos * 2) if anos > 0 else 20
    
    desglose = {
        "experiencia": min(30, score_base * 0.6),
        "especializacion": min(20, score_base * 0.4),
        "reputacion": 10,
        "enfoque_pyme": 8,
        "afinidad_ia": 5,
        "riesgos": 0
    }
    
    score_total = _calcular_score_desde_desglose(desglose)
    nivel = _determinar_nivel_desde_score(score_total)
    recomendacion = _determinar_recomendacion_desde_score(score_total, [])
    
    return {
        "resumen_ejecutivo_ia": f"Perfil con {anos} años de experiencia. Requiere revisión manual para validación completa. Análisis automático básico realizado.",
        "trust_score": score_total,
        "nivel_sugerido": nivel,
        "desglose_dimensiones": {k: int(v) for k, v in desglose.items()},
        "riesgos_detectados": ["Ninguno"],
        "recomendacion_final": recomendacion,
        "justificacion": f"Análisis básico realizado. Score: {score_total}/100. Se recomienda revisión manual para validación completa."
    }

# =====================================================
# Analizador principal
# =====================================================

async def validar_consultor(
    form_data: Dict[str, Any],
    public_data: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Valida un perfil de consultor usando OpenAI según el prompt maestro de MentHIA.
    
    Args:
        form_data: Datos del formulario de registro del consultor
        public_data: Información pública encontrada (LinkedIn, web, etc.)
    
    Returns:
        Dict con el análisis completo de validación
    """
    
    # Fallback si no hay API key
    if not OPENAI_API_KEY or not client:
        logger.warning("OpenAI no configurado, usando fallback")
        return _respuesta_fallback(form_data)
    
    # Formatear datos para el prompt
    datos_fmt = _formatear_datos_consultor(form_data, public_data)
    
    user_msg = f"""Analiza este perfil de consultor para validación en MentHIA.

{datos_fmt}

Genera el análisis completo siguiendo la estructura JSON especificada.
Evalúa las 6 dimensiones y asigna el MentHIA Trust Score™ correspondiente.
Sé objetivo, justo y alineado con los valores de MentHIA."""

    try:
        completion = client.chat.completions.create(
            model=MODEL_NAME,
            messages=[
                {"role": "system", "content": CONSULTANT_VALIDATION_SYSTEM_PROMPT},
                {"role": "user", "content": user_msg}
            ],
            response_format={"type": "json_object"},
            temperature=0.3,  # Baja temperatura para análisis más objetivo
            max_tokens=2000
        )

        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        
        # Validación y normalización de la respuesta
        if not isinstance(parsed.get("resumen_ejecutivo_ia", ""), str):
            parsed["resumen_ejecutivo_ia"] = "Análisis realizado. Revisar detalles en desglose."
        
        # Asegurar que el desglose existe y tiene los campos correctos
        if "desglose_dimensiones" not in parsed:
            parsed["desglose_dimensiones"] = {
                "experiencia": 0,
                "especializacion": 0,
                "reputacion": 0,
                "enfoque_pyme": 0,
                "afinidad_ia": 0,
                "riesgos": 0
            }
        
        # Calcular score si no viene o está mal
        if "trust_score" not in parsed or not isinstance(parsed.get("trust_score"), (int, float)):
            parsed["trust_score"] = _calcular_score_desde_desglose(parsed["desglose_dimensiones"])
        else:
            parsed["trust_score"] = max(0, min(100, int(parsed["trust_score"])))
        
        # Determinar nivel si no viene
        if "nivel_sugerido" not in parsed or parsed["nivel_sugerido"] not in ["especialista", "consultor_senior", "mentor_ejecutivo"]:
            parsed["nivel_sugerido"] = _determinar_nivel_desde_score(parsed["trust_score"])
        
        # Asegurar riesgos es una lista
        if "riesgos_detectados" not in parsed:
            parsed["riesgos_detectados"] = ["Ninguno"]
        elif not isinstance(parsed["riesgos_detectados"], list):
            parsed["riesgos_detectados"] = [str(parsed["riesgos_detectados"])]
        
        # Determinar recomendación si no viene
        if "recomendacion_final" not in parsed or parsed["recomendacion_final"] not in ["APROBAR", "APROBAR CONDICIONADO", "REVISIÓN HUMANA", "NO APROBAR"]:
            parsed["recomendacion_final"] = _determinar_recomendacion_desde_score(
                parsed["trust_score"],
                parsed["riesgos_detectados"]
            )
        
        # Asegurar justificación
        if "justificacion" not in parsed or not parsed["justificacion"]:
            parsed["justificacion"] = f"Score: {parsed['trust_score']}/100. {parsed['recomendacion_final']}."
        
        # Normalizar valores numéricos del desglose
        desglose = parsed["desglose_dimensiones"]
        for key in ["experiencia", "especializacion", "reputacion", "enfoque_pyme", "afinidad_ia"]:
            if key in desglose:
                desglose[key] = max(0, min(int(desglose[key]), 30 if key == "experiencia" else 20 if key == "especializacion" or key == "reputacion" else 15 if key == "enfoque_pyme" else 10))
        
        if "riesgos" in desglose:
            desglose["riesgos"] = max(-5, min(0, int(desglose["riesgos"])))
        
        return parsed

    except json.JSONDecodeError as e:
        logger.error(f"Error parseando JSON de OpenAI: {e}")
        fallback = _respuesta_fallback(form_data)
        fallback["justificacion"] = f"Error al parsear respuesta de IA: {str(e)}. " + fallback["justificacion"]
        return fallback
    
    except Exception as e:
        logger.error(f"Error en validación de consultor: {e}")
        fallback = _respuesta_fallback(form_data)
        fallback["justificacion"] = f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}. " + fallback["justificacion"]
        return fallback
