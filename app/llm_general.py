# app/llm_general.py
# MENTHIA - Inteligencia Consultiva para Diagnóstico General
# Modelo de calificación gradual con modificador de asesoría externa (Capa 1: Percentiles, Capa 2: Índice por sección)
import os
import json
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException
from openai import OpenAI
from dotenv import load_dotenv

# Carga variables de entorno (usa .env)
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================
# MODELO DE CALIFICACIÓN GRADUAL - MAPAS Y FÓRMULAS
# =====================================================
# Escala P1-P5: A=0, B=25, C=50, D=75. P6 (asesoría): A=0, B=5, C=10
# Puntaje sección = ((P1+P2+P3+P4+P5)/5) + P6. Máximo por sección: 85.
LETRA_A_PUNTOS_P1_5 = {"A": 0, "B": 25, "C": 50, "D": 75}
NUMERO_A_PUNTOS_P1_5 = {"1": 0, "2": 25, "3": 50, "4": 75, "5": 75}
NUMERO_A_PUNTOS_P6 = {"1": 0, "2": 5, "3": 10, "4": 10, "5": 10}

# Percentiles por sector y tamaño (LATAM). Cada tupla: (inicio, fin, clasificación)
PERCENTILES_POR_SECTOR = {
    "Servicios": {
        "Micro": [(0, 36, "Deficiente"), (37, 50, "Promedio"), (51, 70, "Bueno"), (71, 100, "Líder")],
        "Pequeña": [(0, 40, "Deficiente"), (41, 55, "Promedio"), (56, 75, "Bueno"), (76, 100, "Líder")],
        "Mediana": [(0, 45, "Deficiente"), (46, 60, "Promedio"), (61, 78, "Bueno"), (79, 100, "Líder")],
        "Grande": [(0, 50, "Deficiente"), (51, 65, "Promedio"), (66, 80, "Bueno"), (81, 100, "Líder")],
    },
    "Comercio": {
        "Micro": [(0, 34, "Deficiente"), (35, 49, "Promedio"), (50, 69, "Bueno"), (70, 100, "Líder")],
        "Pequeña": [(0, 38, "Deficiente"), (39, 52, "Promedio"), (53, 72, "Bueno"), (73, 100, "Líder")],
        "Mediana": [(0, 42, "Deficiente"), (43, 58, "Promedio"), (59, 76, "Bueno"), (77, 100, "Líder")],
        "Grande": [(0, 48, "Deficiente"), (49, 64, "Promedio"), (65, 82, "Bueno"), (83, 100, "Líder")],
    },
    "Tecnología": {
        "Micro": [(0, 40, "Deficiente"), (41, 54, "Promedio"), (55, 72, "Bueno"), (73, 100, "Líder")],
        "Pequeña": [(0, 42, "Deficiente"), (43, 56, "Promedio"), (57, 74, "Bueno"), (75, 100, "Líder")],
        "Mediana": [(0, 46, "Deficiente"), (47, 62, "Promedio"), (63, 79, "Bueno"), (80, 100, "Líder")],
        "Grande": [(0, 50, "Deficiente"), (51, 66, "Promedio"), (67, 82, "Bueno"), (83, 100, "Líder")],
    },
    "Agroindustria": {
        "Micro": [(0, 35, "Deficiente"), (36, 50, "Promedio"), (51, 70, "Bueno"), (71, 100, "Líder")],
        "Pequeña": [(0, 38, "Deficiente"), (39, 53, "Promedio"), (54, 72, "Bueno"), (73, 100, "Líder")],
        "Mediana": [(0, 42, "Deficiente"), (43, 58, "Promedio"), (59, 76, "Bueno"), (77, 100, "Líder")],
        "Grande": [(0, 48, "Deficiente"), (49, 64, "Promedio"), (65, 80, "Bueno"), (81, 100, "Líder")],
    },
    "Industria": {
        "Micro": [(0, 38, "Deficiente"), (39, 53, "Promedio"), (54, 73, "Bueno"), (74, 100, "Líder")],
        "Pequeña": [(0, 40, "Deficiente"), (41, 55, "Promedio"), (56, 74, "Bueno"), (75, 100, "Líder")],
        "Mediana": [(0, 44, "Deficiente"), (45, 60, "Promedio"), (61, 78, "Bueno"), (79, 100, "Líder")],
        "Grande": [(0, 50, "Deficiente"), (51, 65, "Promedio"), (66, 82, "Bueno"), (83, 100, "Líder")],
    },
}

SECCION_VALOR = {"Deficiente": 0, "Promedio": 1, "Bueno": 2, "Líder": 3}


def _puntaje_a_clasificacion_seccion(puntaje: float) -> str:
    """Clasificación por sección: <25 Deficiente, 25-49 Promedio, 50-74 Bueno, 75-100 Líder."""
    if puntaje < 25:
        return "Deficiente"
    if puntaje < 50:
        return "Promedio"
    if puntaje < 75:
        return "Bueno"
    return "Líder"


def diagnostico_por_percentil(puntaje: float, sector: str, tamano: str) -> str:
    """Capa 1: clasificación según percentiles LATAM por sector y tamaño."""
    sector_norm = (sector or "Servicios").strip().capitalize()
    if sector_norm not in PERCENTILES_POR_SECTOR:
        sector_norm = "Servicios"
    tabla = PERCENTILES_POR_SECTOR.get(sector_norm, {})
    percentiles = tabla.get(tamano) or tabla.get("Micro")
    if not percentiles:
        return "Sin referencia"
    for inicio, fin, clasificacion in percentiles:
        if inicio <= puntaje <= fin:
            return clasificacion
    return "Sin clasificar"


def diagnostico_por_secciones(clasificaciones: List[str]) -> Tuple[float, str]:
    """Capa 2: índice global y diagnóstico según promedios de valores por sección."""
    if not clasificaciones:
        return 0.0, "Deficiente crítico"
    valores = [SECCION_VALOR.get(c, 0) for c in clasificaciones]
    promedio = sum(valores) / len(valores)
    if promedio < 0.50:
        return round(promedio, 2), "Deficiente crítico"
    if promedio < 1.50:
        return round(promedio, 2), "En el promedio"
    if promedio < 2.50:
        return round(promedio, 2), "Por encima del promedio"
    return round(min(promedio, 3.0), 2), "Líder de segmento"


def _obtener_tamano_empresa(numero_empleados: Any) -> str:
    """Clasificación tamaño (México): Micro 1-10, Pequeña 11-50, Mediana 51-250, Grande >250."""
    if numero_empleados is None:
        return "Micro"
    if isinstance(numero_empleados, str):
        s = numero_empleados.lower()
        if "1-10" in s or "micro" in s:
            return "Micro"
        if "11-50" in s or "pequeña" in s or "pequena" in s:
            return "Pequeña"
        if "51-250" in s or "mediana" in s:
            return "Mediana"
        if "251" in s or "más de 500" in s or "grande" in s:
            return "Grande"
        try:
            n = int("".join(c for c in numero_empleados if c.isdigit())[:4] or "0")
        except Exception:
            return "Micro"
        numero_empleados = n
    n = int(numero_empleados) if isinstance(numero_empleados, (int, float)) else 0
    if n <= 10:
        return "Micro"
    if n <= 50:
        return "Pequeña"
    if n <= 250:
        return "Mediana"
    return "Grande"


def _calcular_puntajes_por_seccion(d: Dict[str, Any]) -> Tuple[List[float], List[str], float, str, str]:
    """
    Calcula puntaje por sección (6 bloques: dg, fa, op, mv, rh, lc).
    Cada sección: ((P1+P2+P3+P4+P5)/5) + P6 con escala 0/25/50/75 y P6 0/5/10.
    Retorna: (puntajes_seccion, clasificaciones_seccion, puntaje_promedio_total, diagnostico_capa1, diagnostico_capa2).
    """
    prefijos = ["dg_", "fa_", "op_", "mv_", "rh_", "lc_"]
    puntajes_seccion: List[float] = []
    clasificaciones_seccion: List[str] = []

    for pref in prefijos:
        suma_p1_5 = 0.0
        n_p1_5 = 0
        for q in range(1, 6):
            key = f"{pref}q{q}"
            val = d.get(key)
            if val is None:
                continue
            s = str(val).strip().upper()
            if s in NUMERO_A_PUNTOS_P1_5:
                suma_p1_5 += NUMERO_A_PUNTOS_P1_5[s]
                n_p1_5 += 1
            elif s in LETRA_A_PUNTOS_P1_5:
                suma_p1_5 += LETRA_A_PUNTOS_P1_5[s]
                n_p1_5 += 1
        prom_p1_5 = (suma_p1_5 / 5) if n_p1_5 else 0
        p6 = 0
        key6 = f"{pref}q6"
        if key6 in d:
            v6 = str(d[key6]).strip().upper()
            if v6 in NUMERO_A_PUNTOS_P6:
                p6 = NUMERO_A_PUNTOS_P6[v6]
            elif v6 in {"A", "1"}:
                p6 = 0
            elif v6 in {"B", "2"}:
                p6 = 5
            else:
                p6 = 10
        puntaje_sec = prom_p1_5 + p6
        puntajes_seccion.append(round(puntaje_sec, 2))
        clasificaciones_seccion.append(_puntaje_a_clasificacion_seccion(puntaje_sec))

    if not puntajes_seccion:
        return [], [], 0.0, "Sin referencia", "Deficiente crítico"

    puntaje_total = sum(puntajes_seccion) / len(puntajes_seccion)
    sector = d.get("sector") or d.get("sectorNormalizado") or "Servicios"
    tamano = _obtener_tamano_empresa(d.get("numeroEmpleados"))
    capa1 = diagnostico_por_percentil(puntaje_total, str(sector), tamano)
    indice_c2, capa2 = diagnostico_por_secciones(clasificaciones_seccion)
    return puntajes_seccion, clasificaciones_seccion, round(puntaje_total, 2), capa1, capa2


# =====================================================
# PROMPT SYSTEM - MODELO DE CALIFICACIÓN GRADUAL + MENTHIA
# =====================================================
MENTHIA_SYSTEM_PROMPT = """Eres MENTHIA, la Inteligencia Consultiva de nueva generación diseñada para diagnosticar empresas en LATAM con precisión quirúrgica. Combinas criterio de consultor senior (McKinsey, BCG, Bain), pensamiento futurista, visión emprendedora y lenguaje empresarial directo y pragmático.

## MODELO DE CALIFICACIÓN GRADUAL CON MODIFICADOR DE ASESORÍA EXTERNA

1. Escala por pregunta (P1-P5): A=0, B=25, C=50, D=75. Pregunta 6 (asesoría externa): A=0, B=5, C=10.
2. Puntaje por sección = ((P1+P2+P3+P4+P5)/5) + P6. Máximo por sección: 85.
3. Clasificación por sección: <25 pts Deficiente, 25-49 Promedio, 50-74 Bueno, 75-100 Líder.
4. Índice MentHIA (Capa 2) = promedio de valores numéricos por sección (Deficiente=0, Promedio=1, Bueno=2, Líder=3).
5. Diagnóstico Capa 2: 0.00-0.49 Deficiente crítico, 0.50-1.49 En el promedio, 1.50-2.49 Por encima del promedio, 2.50-3.00 Líder de segmento.
6. Capa 1 (Percentiles LATAM): compara el puntaje promedio total con la tabla por sector y tamaño (Micro, Pequeña, Mediana, Grande) para ubicar a la empresa en Deficiente/Promedio/Bueno/Líder.

Usa ambas capas: el percentil (Capa 1) da benchmarking real; el índice por sección (Capa 2) evita que una sola área destacada sobrevalore el diagnóstico.

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
- Integra en tu análisis los resultados de Capa 1 (percentil) y Capa 2 (índice por sección) cuando te los proporcionen.
- Crea un mini-roadmap agresivo y práctico.

### MARCO ANALÍTICO
- Análisis 360 por áreas.
- Identificación de cuellos de botella.
- Oportunidades inmediatas (quick wins) y estructurales.
- Riesgos críticos y señales de alerta.
- Nivel de madurez coherente con el modelo de calificación gradual.

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
  "puntuacion_madurez_promedio": número del 1-5 (o equivalente según escala 0-100 normalizado a 1-5),
  "nivel_madurez_general": "muy_bajo|bajo|medio|alto|muy_alto",
  "recomendaciones_innovadoras": ["ideas innovadoras o disruptivas"],
  "siguiente_paso": "el paso más importante a tomar ahora"
}

### MANEJO DE INFORMACIÓN
- Si una respuesta es débil, superficial o ambigua, interprétala, complétala y adviértelo.
- Si detectas una oportunidad transformacional, menciónala.
- Incluir ejemplos concretos si ayudan a clarificar.

Cuando recibas las respuestas y los resultados precalculados de Capa 1 y Capa 2, genera el diagnóstico completo en formato JSON válido."""

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


def _nivel_madurez_desde_puntaje_100(puntaje: float) -> str:
    """Mapea puntaje 0-100 (modelo gradual) a nivel para frontend."""
    if puntaje >= 71: return "muy_alto"
    if puntaje >= 51: return "alto"
    if puntaje >= 37: return "medio"
    if puntaje >= 25: return "bajo"
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
# Mapper: formato Mentoria (respuestas) -> formato API (dg_, fa_, etc.)
# =====================================================
BLOQUE_TO_PREFIX = {
    "estrategia": "dg_",
    "finanzas": "fa_",
    "marketing": "mv_",
    "operaciones": "op_",
    "talento": "rh_",
    "tecnologia": "lc_",
    "escalabilidad": "dg_",
}
LETRA_A_NUMERO = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}


def _convertir_formato_mentoria(data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convierte respuestas del frontend Mentoria (estrategia_1: 'A', etc.)
    al formato esperado por llm_general (dg_X: 1, fa_X: 2, etc.).
    """
    respuestas = data.get("respuestas")
    if not respuestas or not isinstance(respuestas, dict):
        return data

    result = dict(data)
    converted: Dict[str, int] = {}
    for key, val in respuestas.items():
        if not isinstance(key, str) or "_" not in key:
            continue
        bloque, num = key.split("_", 1)
        prefix = BLOQUE_TO_PREFIX.get(bloque.lower())
        if not prefix:
            continue
        num_val = LETRA_A_NUMERO.get(str(val).upper()) if isinstance(val, str) else None
        if num_val is None and str(val) in {"1", "2", "3", "4", "5"}:
            num_val = int(val)
        if num_val is not None:
            new_key = f"{prefix}q{num}"
            converted[new_key] = num_val

    for k, v in converted.items():
        result[k] = str(v)
    return result


# =====================================================
# Analizador principal
# =====================================================
async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analiza los datos de un diagnóstico empresarial general usando OpenAI (gpt-4o).
    Acepta dos formatos:
    1) API nativo: dg_X, fa_X, op_X, mv_X, rh_X, lc_X con valores 1-5
    2) Mentoria: respuestas con estrategia_N, finanzas_N, etc. y valores A-E
    """
    # Normalizar formato Mentoria si aplica
    diagnostico_data = _convertir_formato_mentoria(diagnostico_data)
    # Fallback si no hay API key
    if not OPENAI_API_KEY or not client:
        return _respuesta_fallback(diagnostico_data)

    # Modelo gradual: puntajes por sección, Capa 1 (percentil) y Capa 2 (índice por sección)
    puntajes_sec, clasif_sec, puntaje_total, capa1, capa2 = _calcular_puntajes_por_seccion(diagnostico_data)
    if puntajes_sec and puntaje_total > 0:
        avg = round((puntaje_total / 20.0), 2)
        nivel = _nivel_madurez_desde_puntaje_100(puntaje_total)
    else:
        avg, nivel = _extraer_likert(diagnostico_data)
        puntaje_total = avg * 20.0
        capa1, capa2 = "Sin referencia", "En el promedio"

    correlaciones = _analizar_correlaciones(diagnostico_data)
    datos_fmt = _formatear_datos_para_prompt(diagnostico_data)

    contexto_capa = ""
    if puntajes_sec and clasif_sec:
        nombres_seccion = list(AREA_MAPPING.values())
        contexto_capa = "\nRESULTADOS MODELO DE CALIFICACIÓN GRADUAL (precalculados):\n"
        contexto_capa += f"- Puntaje promedio total (0-100): {puntaje_total}\n"
        contexto_capa += f"- Capa 1 (Percentil LATAM): {capa1}\n"
        contexto_capa += f"- Capa 2 (Índice por sección): {capa2}\n"
        contexto_capa += "- Puntajes por sección: " + ", ".join(f"{nombres_seccion[i]}={puntajes_sec[i]}" for i in range(min(len(puntajes_sec), len(nombres_seccion)))) + "\n"
        contexto_capa += "- Clasificación por sección: " + ", ".join(clasif_sec) + "\n"

    contexto_correlaciones = ""
    if correlaciones.get("correlaciones"):
        for corr in correlaciones["correlaciones"][:2]:
            contexto_correlaciones += f"\nCORRELACIÓN DETECTADA: {corr['mensaje']}. "
    if correlaciones.get("area_mas_debil"):
        contexto_correlaciones += f"\nÁREA MÁS DÉBIL: {correlaciones['area_mas_debil']['nombre']} (score: {correlaciones['area_mas_debil']['score']})"
    if correlaciones.get("area_mas_fuerte"):
        contexto_correlaciones += f"\nÁREA MÁS FUERTE: {correlaciones['area_mas_fuerte']['nombre']} (score: {correlaciones['area_mas_fuerte']['score']})"

    user_msg = f"""Analiza este diagnóstico general empresarial.

{contexto_capa}
CONTEXTO ADICIONAL:{contexto_correlaciones}

DATOS DEL DIAGNÓSTICO:
{datos_fmt}

Genera el diagnóstico ejecutivo completo siguiendo la estructura JSON especificada.
IMPORTANTE: Tu diagnóstico debe basarse ÚNICAMENTE en las respuestas y datos proporcionados arriba. No inventes datos ni asumas información no indicada. Cada hallazgo o recomendación debe poder trazarse a una respuesta concreta del cuestionario.
Usa Capa 1 y Capa 2 en tu narrativa. Sé directo, práctico y accionable. Nada de motivación vacía."""

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
        parsed["puntuacion_madurez_promedio"] = float(parsed.get("puntuacion_madurez_promedio", avg or 0.0))
        parsed["nivel_madurez_general"] = str(parsed.get("nivel_madurez_general", nivel or "muy_bajo"))
        if puntajes_sec and clasif_sec:
            parsed["diagnostico_capa1_percentil"] = capa1
            parsed["diagnostico_capa2_indice"] = capa2
            parsed["puntaje_total_0_100"] = puntaje_total
            parsed["puntajes_por_seccion"] = puntajes_sec
            parsed["clasificacion_por_seccion"] = clasif_sec

        return parsed

    except Exception as e:
        # Fallback en caso de error
        fallback = _respuesta_fallback(diagnostico_data)
        fallback["resumen_ejecutivo"] = f"Error al analizar con OpenAI ({MODEL_NAME}): {str(e)}. " + fallback["resumen_ejecutivo"]
        return fallback
