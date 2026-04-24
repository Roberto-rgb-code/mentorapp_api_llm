# app/llm_general.py
# MENTHIA - Inteligencia Consultiva para Diagnóstico General
# Modelo v4: 7 Secciones | Escala A-E (0-100) + Q6 Asesoría (0-10)
# Máximo interno por sección: 110 → escalado a 0-100
# Capa 1: Percentiles LATAM por sector/tamaño
# Capa 2: Índice global por sección (0.00–3.00)

import os
import json
from typing import Dict, Any, List, Tuple
from fastapi import HTTPException
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-sonnet-4-20250514").strip().strip('"').strip("'")

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None


# =====================================================
# MODELO DE CALIFICACIÓN — ESCALAS Y FÓRMULAS
# =====================================================
#
# Q1-Q5: A=0, B=25, C=50, D=75, E=100
# Q6 (asesoría externa): A=0, B=5, C=10
#
# Puntaje interno = ((Q1+Q2+Q3+Q4+Q5) / 5) + Q6
# Rango interno: 0–110
#
# Calificación visible (0–100) = (puntaje_interno / 110) × 100
# Índice Menthia Global = promedio de las 7 calificaciones (0–100)

LETRA_A_PUNTOS_Q15 = {"A": 0, "B": 25, "C": 50, "D": 75, "E": 100}
NUMERO_A_PUNTOS_Q15 = {"1": 0, "2": 25, "3": 50, "4": 75, "5": 100}
NUMERO_A_PUNTOS_Q6 = {"1": 0, "2": 5, "3": 10}
MAX_INTERNO = 110  # 100 + 10

PERCENTILES_POR_SECTOR = {
    "Servicios": {
        "Micro":   [(0, 36, "Deficiente"), (37, 50, "Promedio"), (51, 70, "Bueno"), (71, 100, "Líder")],
        "Pequeña": [(0, 40, "Deficiente"), (41, 55, "Promedio"), (56, 75, "Bueno"), (76, 100, "Líder")],
        "Mediana": [(0, 45, "Deficiente"), (46, 60, "Promedio"), (61, 78, "Bueno"), (79, 100, "Líder")],
        "Grande":  [(0, 50, "Deficiente"), (51, 65, "Promedio"), (66, 80, "Bueno"), (81, 100, "Líder")],
    },
    "Comercio": {
        "Micro":   [(0, 34, "Deficiente"), (35, 49, "Promedio"), (50, 69, "Bueno"), (70, 100, "Líder")],
        "Pequeña": [(0, 38, "Deficiente"), (39, 52, "Promedio"), (53, 72, "Bueno"), (73, 100, "Líder")],
        "Mediana": [(0, 42, "Deficiente"), (43, 58, "Promedio"), (59, 76, "Bueno"), (77, 100, "Líder")],
        "Grande":  [(0, 48, "Deficiente"), (49, 64, "Promedio"), (65, 82, "Bueno"), (83, 100, "Líder")],
    },
    "Tecnología": {
        "Micro":   [(0, 40, "Deficiente"), (41, 54, "Promedio"), (55, 72, "Bueno"), (73, 100, "Líder")],
        "Pequeña": [(0, 42, "Deficiente"), (43, 56, "Promedio"), (57, 74, "Bueno"), (75, 100, "Líder")],
        "Mediana": [(0, 46, "Deficiente"), (47, 62, "Promedio"), (63, 79, "Bueno"), (80, 100, "Líder")],
        "Grande":  [(0, 50, "Deficiente"), (51, 66, "Promedio"), (67, 82, "Bueno"), (83, 100, "Líder")],
    },
    "Agroindustria": {
        "Micro":   [(0, 35, "Deficiente"), (36, 50, "Promedio"), (51, 70, "Bueno"), (71, 100, "Líder")],
        "Pequeña": [(0, 38, "Deficiente"), (39, 53, "Promedio"), (54, 72, "Bueno"), (73, 100, "Líder")],
        "Mediana": [(0, 42, "Deficiente"), (43, 58, "Promedio"), (59, 76, "Bueno"), (77, 100, "Líder")],
        "Grande":  [(0, 48, "Deficiente"), (49, 64, "Promedio"), (65, 80, "Bueno"), (81, 100, "Líder")],
    },
    "Industria": {
        "Micro":   [(0, 38, "Deficiente"), (39, 53, "Promedio"), (54, 73, "Bueno"), (74, 100, "Líder")],
        "Pequeña": [(0, 40, "Deficiente"), (41, 55, "Promedio"), (56, 74, "Bueno"), (75, 100, "Líder")],
        "Mediana": [(0, 44, "Deficiente"), (45, 60, "Promedio"), (61, 78, "Bueno"), (79, 100, "Líder")],
        "Grande":  [(0, 50, "Deficiente"), (51, 65, "Promedio"), (66, 82, "Bueno"), (83, 100, "Líder")],
    },
}

SECCION_VALOR = {"Deficiente": 0, "Promedio": 1, "Bueno": 2, "Líder": 3}

# 7 secciones con prefijos y nombres
AREA_MAPPING = {
    "es_": "Estrategia",
    "fi_": "Finanzas",
    "mk_": "Marketing y Ventas",
    "op_": "Operaciones",
    "ta_": "Talento",
    "te_": "Tecnología",
    "ec_": "Escalabilidad",
}

PREFIJOS = list(AREA_MAPPING.keys())
NOMBRES_SECCION = list(AREA_MAPPING.values())


# =====================================================
# FUNCIONES DE CÁLCULO
# =====================================================

def _clasificar_seccion(calificacion_100: float) -> str:
    if calificacion_100 < 25: return "Deficiente"
    if calificacion_100 < 50: return "Promedio"
    if calificacion_100 < 75: return "Bueno"
    return "Líder"


def _diagnostico_percentil(indice: float, sector: str, tamano: str) -> str:
    sector_n = (sector or "Servicios").strip().capitalize()
    if sector_n not in PERCENTILES_POR_SECTOR:
        sector_n = "Servicios"
    tabla = PERCENTILES_POR_SECTOR.get(sector_n, {})
    pctls = tabla.get(tamano) or tabla.get("Micro")
    if not pctls:
        return "Sin referencia"
    for inicio, fin, clasif in pctls:
        if inicio <= indice <= fin:
            return clasif
    return "Sin clasificar"


def _diagnostico_global(clasificaciones: List[str]) -> Tuple[float, str]:
    if not clasificaciones:
        return 0.0, "Deficiente crítico"
    vals = [SECCION_VALOR.get(c, 0) for c in clasificaciones]
    prom = sum(vals) / len(vals)
    if prom < 0.50: return round(prom, 2), "Deficiente crítico"
    if prom < 1.50: return round(prom, 2), "En el promedio"
    if prom < 2.50: return round(prom, 2), "Por encima del promedio"
    return round(min(prom, 3.0), 2), "Líder de segmento"


def _tamano_empresa(n_emp: Any) -> str:
    if n_emp is None: return "Micro"
    if isinstance(n_emp, str):
        s = n_emp.lower()
        if "micro" in s or "1-10" in s: return "Micro"
        if "pequeña" in s or "pequena" in s or "11-50" in s: return "Pequeña"
        if "mediana" in s or "51-250" in s: return "Mediana"
        if "grande" in s or "251" in s: return "Grande"
        try: n_emp = int("".join(c for c in n_emp if c.isdigit())[:4] or "0")
        except: return "Micro"
    n = int(n_emp) if isinstance(n_emp, (int, float)) else 0
    if n <= 10: return "Micro"
    if n <= 50: return "Pequeña"
    if n <= 250: return "Mediana"
    return "Grande"


def _nivel_madurez(indice: float) -> str:
    if indice >= 71: return "muy_alto"
    if indice >= 51: return "alto"
    if indice >= 37: return "medio"
    if indice >= 25: return "bajo"
    return "muy_bajo"


def _calcular_modelo(d: Dict[str, Any]) -> Dict[str, Any]:
    """
    Calcula el modelo completo de 2 capas para 7 secciones.
    Interno: ((Q1+Q2+Q3+Q4+Q5)/5) + Q6 → 0-110
    Visible: (interno/110)×100 → 0-100
    """
    calificaciones: List[float] = []
    clasificaciones: List[str] = []
    detalle: List[Dict[str, Any]] = []

    for i, pref in enumerate(PREFIJOS):
        suma = 0.0
        n_q = 0
        for q in range(1, 6):
            val = d.get(f"{pref}q{q}")
            if val is None: continue
            s = str(val).strip().upper()
            if s in NUMERO_A_PUNTOS_Q15:
                suma += NUMERO_A_PUNTOS_Q15[s]; n_q += 1
            elif s in LETRA_A_PUNTOS_Q15:
                suma += LETRA_A_PUNTOS_Q15[s]; n_q += 1

        prom = (suma / 5) if n_q else 0.0

        q6 = 0
        v6 = str(d.get(f"{pref}q6", "A")).strip().upper()
        if v6 in NUMERO_A_PUNTOS_Q6: q6 = NUMERO_A_PUNTOS_Q6[v6]
        elif v6 == "A": q6 = 0
        elif v6 == "B": q6 = 5
        elif v6 == "C": q6 = 10

        interno = round(prom + q6, 2)
        calif = round((interno / MAX_INTERNO) * 100, 2)
        clasif = _clasificar_seccion(calif)

        calificaciones.append(calif)
        clasificaciones.append(clasif)
        detalle.append({
            "nombre": NOMBRES_SECCION[i],
            "prefijo": pref.rstrip("_").upper(),
            "calificacion": calif,
            "calificacion_max": 100,
            "clasificacion": clasif,
            "valor_numerico": SECCION_VALOR.get(clasif, 0),
        })

    if not calificaciones:
        return {"calificaciones": [], "clasificaciones": [], "detalle_secciones": [],
                "indice_menthia_0_100": 0.0, "capa1_percentil": "Sin referencia",
                "capa2_indice": 0.0, "capa2_diagnostico": "Deficiente crítico",
                "nivel_madurez": "muy_bajo", "estado_madurez": "Deficiente (0)"}

    indice = round(sum(calificaciones) / len(calificaciones), 2)
    sector = str(d.get("sector") or d.get("sectorNormalizado") or "Servicios")
    tamano = _tamano_empresa(d.get("numeroEmpleados"))

    capa1 = _diagnostico_percentil(indice, sector, tamano)
    capa2_idx, capa2_diag = _diagnostico_global(clasificaciones)
    nivel = _nivel_madurez(indice)

    if capa2_idx < 0.5: estado = "Deficiente (0)"
    elif capa2_idx < 1.5: estado = "Promedio (1)"
    elif capa2_idx < 2.5: estado = "Bueno (2)"
    else: estado = "Líder (3)"

    return {
        "calificaciones": calificaciones,
        "clasificaciones": clasificaciones,
        "detalle_secciones": detalle,
        "indice_menthia_0_100": indice,
        "sector": sector, "tamano": tamano,
        "capa1_percentil": capa1,
        "capa2_indice": capa2_idx, "capa2_diagnostico": capa2_diag,
        "nivel_madurez": nivel, "estado_madurez": estado,
    }


def _correlaciones(d: Dict[str, Any]) -> Dict[str, Any]:
    areas_scores: Dict[str, List[int]] = {}
    for k, v in d.items():
        if k in {"userId", "createdAt"}: continue
        for pref, area in AREA_MAPPING.items():
            if k.startswith(pref) and str(v) in {"1","2","3","4","5"}:
                areas_scores.setdefault(area, []).append(int(v))

    areas_avg = {a: round(sum(s)/len(s), 2) for a, s in areas_scores.items() if s}
    orden = sorted(areas_avg.items(), key=lambda x: x[1])
    debil = orden[0] if orden else None
    fuerte = orden[-1] if orden else None

    corrs = []
    if areas_avg.get("Finanzas", 5) <= 2.5 and areas_avg.get("Operaciones", 5) <= 2.5:
        corrs.append({"tipo": "riesgo_sistemico", "areas": ["Finanzas", "Operaciones"],
                       "mensaje": "Finanzas y Operaciones débiles = riesgo sistémico alto", "impacto": "alto"})
    if areas_avg.get("Marketing y Ventas", 5) <= 2.5 and areas_avg.get("Talento", 5) <= 2.5:
        corrs.append({"tipo": "crecimiento_limitado", "areas": ["Marketing y Ventas", "Talento"],
                       "mensaje": "Marketing y Talento débiles limitan el crecimiento", "impacto": "medio"})
    if areas_avg.get("Estrategia", 5) <= 2.5:
        debiles = [a for a, s in areas_avg.items() if s <= 3.0 and a != "Estrategia"]
        if debiles:
            corrs.append({"tipo": "ejecucion_comprometida", "areas": ["Estrategia"] + debiles[:2],
                           "mensaje": "Estrategia débil compromete ejecución en otras áreas", "impacto": "alto"})
    if areas_avg.get("Tecnología", 5) <= 2.0 and areas_avg.get("Escalabilidad", 5) <= 2.5:
        corrs.append({"tipo": "escalamiento_bloqueado", "areas": ["Tecnología", "Escalabilidad"],
                       "mensaje": "Sin tecnología no hay escalabilidad posible", "impacto": "alto"})

    return {
        "areas_scores": areas_avg,
        "area_mas_debil": {"nombre": debil[0], "score": debil[1]} if debil else None,
        "area_mas_fuerte": {"nombre": fuerte[0], "score": fuerte[1]} if fuerte else None,
        "correlaciones": corrs,
        "brecha_maxima": round(fuerte[1] - debil[1], 2) if debil and fuerte else 0,
    }


# =====================================================
# SYSTEM PROMPT — MENTHIA v4 (7 Secciones)
# =====================================================

MENTHIA_SYSTEM_PROMPT = """Eres MENTHIA, la Inteligencia Consultiva de nueva generación diseñada para diagnosticar empresas en LATAM con precisión quirúrgica. Actúas al nivel de un Partner de McKinsey o BCG. Tienes visión futurista, lenguaje directivo (cero paja motivacional) y un agudo sentido de negocios.

## CONTEXTO DEL MODELO

La empresa fue evaluada en **7 áreas funcionales**. Cada área recibió una calificación de **0 a 100**. Los resultados fueron calculados algorítmicamente con un modelo de 2 capas.

### Las 7 secciones evaluadas:
1. **ES — Estrategia**: Visión, misión, planeación estratégica, toma de decisiones, innovación, gobierno corporativo.
2. **FI — Finanzas**: Planificación financiera, presupuestos, liquidez, contabilidad, control de costos, rentabilidad.
3. **MK — Marketing y Ventas**: CRM, proceso de ventas, generación de demanda, servicio al cliente, propuesta de valor, marca.
4. **OP — Operaciones**: Documentación de procesos, productividad, calidad, gestión de demanda, mejora continua.
5. **TA — Talento**: Reclutamiento, capacitación, evaluación de desempeño, retención, planeación de personal.
6. **TE — Tecnología**: Infraestructura TI, software/ERP, transformación digital, canales digitales, ciberseguridad.
7. **EC — Escalabilidad**: Planeación de crecimiento, capacidad de escalar, financiamiento, adaptación, alianzas estratégicas.

### Escala:
- Cada sección: 6 preguntas (Q1-Q5 de desempeño + Q6 de asesoría externa).
- Q1-Q5: A=0, B=25, C=50, D=75, E=100 puntos.
- Q6: A=0 (nunca), B=5 (puntual), C=10 (recurrente).
- Puntaje interno = ((Q1+Q2+Q3+Q4+Q5)/5) + Q6. Máximo: 110.
- Calificación visible = (interno/110)×100 → escala 0–100.
- Clasificación: <25=Deficiente, 25-49=Promedio, 50-74=Bueno, ≥75=Líder.
- Índice Menthia Global = promedio de las 7 calificaciones (0–100).

### Capa 1 — Percentil LATAM:
Índice Menthia × sector × tamaño → Deficiente / Promedio / Bueno / Líder.

### Capa 2 — Índice Global (0.00–3.00):
Promedio de valores numéricos (Deficiente=0, Promedio=1, Bueno=2, Líder=3).
<0.50=Deficiente crítico, 0.50-1.49=En el promedio, 1.50-2.49=Por encima del promedio, 2.50-3.00=Líder de segmento.

## TU MISIÓN

### 1. RECOMENDACIÓN GENERAL ESTRATÉGICA (campo `recomendacion_general`)
El bloque más importante. Análisis estratégico de alto nivel que:
- Identifica EL problema central que conecta debilidades entre áreas.
- Propone una estrategia integral (no acciones aisladas).
- Cruza Capa 1 con Capa 2 para dar contexto competitivo.
- Si hay discrepancia entre capas, explica qué significa.
- Contundente, directo, accionable. Mínimo 8 líneas. CERO paja.

### 2. RECOMENDACIÓN POR CADA SECCIÓN (campo `recomendaciones_por_seccion`)
Para CADA UNA de las 7 secciones:
- `diagnostico_seccion`: Lectura estratégica (3-4 líneas). No repitas números — interpreta.
- `recomendacion`: Plan de acción concreto y accionable (3-4 líneas).
- `prioridad`: "Crítica" / "Alta" / "Media" / "Baja".
- `quick_win`: Acción implementable en menos de 2 semanas.

### 3. ANÁLISIS CRUZADO
- Busca discrepancias entre áreas.
- Identifica patrones ocultos.
- Referencia las secciones por nombre.
- Personaliza con nombre de empresa, sector y tamaño.

## ESTRUCTURA JSON DE SALIDA

```json
{
  "recomendacion_general": "Análisis estratégico integral (8+ líneas). Problema central + estrategia + contexto competitivo.",
  "resumen_ejecutivo": "Mensaje impactante y profesional (4-5 líneas). Menciona empresa por nombre.",
  "diagnostico_estrategico": "Lectura profunda cruzando áreas (6-8 líneas). Cuello de botella + área que arrastra.",
  "insight_critico": "La verdad incómoda. Una oración contundente.",
  "recomendaciones_por_seccion": [
    {
      "seccion": "Estrategia",
      "calificacion": 0.0,
      "clasificacion": "Deficiente",
      "diagnostico_seccion": "Interpretación estratégica (3-4 líneas).",
      "recomendacion": "Plan de acción concreto (3-4 líneas).",
      "prioridad": "Crítica",
      "quick_win": "Acción en <2 semanas."
    }
  ],
  "riesgos_sistemicos": [
    {"riesgo": "Cruce de 2+ áreas", "urgencia": "alta/media/baja"}
  ],
  "plan_30_dias": [
    {"fase": "Días 1-15", "accion": "Acción de más alto ROI", "meta": "Métrica concreta"},
    {"fase": "Días 16-30", "accion": "Siguiente acción", "meta": "Métrica concreta"}
  ],
  "recomendaciones_innovadoras": ["2-3 ideas disruptivas para sector y tamaño"],
  "kpi_sugerido": "Indicador principal a medir desde hoy"
}
```

**REGLAS:**
- Respuesta = SOLO JSON. Sin ```json, sin comentarios.
- NO incluir `puntuacion_madurez_promedio` ni `nivel_madurez_general`.
- `recomendaciones_por_seccion` = EXACTAMENTE 7 elementos, orden: ES, FI, MK, OP, TA, TE, EC.
- Copiar `calificacion` y `clasificacion` del contexto precalculado.
- Riesgos sistémicos cruzan al menos 2 áreas.
- Plan 30 días realista para el tamaño."""


# =====================================================
# UTILIDADES
# =====================================================

def _fmt_datos(d: Dict[str, Any]) -> str:
    return "\n".join(f"- {k}: {v}" for k, v in d.items() if k not in {"userId","createdAt"} and v not in ("", None))


def _fallback(d: Dict[str, Any]) -> Dict[str, Any]:
    calc = _calcular_modelo(d)
    nombre = d.get("nombreSolicitante", "").split()[0] if d.get("nombreSolicitante") else ""
    empresa = d.get("nombreEmpresa", "tu empresa")

    recs = []
    # Descripciones contextuales por sección para el fallback
    _seccion_desc = {
        "Estrategia": {
            "debil": "La empresa carece de un rumbo estratégico claro. Las decisiones se toman de manera reactiva y no existe una visión documentada que guíe el crecimiento. Esto genera desalineación entre las áreas y limita la capacidad de adaptación al mercado.",
            "medio": "Existen bases estratégicas pero falta formalización. La visión se comunica de manera informal y el seguimiento de objetivos es esporádico. Se recomienda estructurar un proceso de planeación estratégica con revisiones trimestrales.",
            "fuerte": "La empresa demuestra claridad estratégica y alineación organizacional. Los objetivos se monitorean con indicadores y existe un proceso formal de planeación. Continúa fortaleciendo la innovación y el gobierno corporativo.",
            "rec_debil": "Definir misión, visión y 3 objetivos estratégicos prioritarios. Implementar reuniones mensuales de seguimiento con KPIs básicos. Considerar una sesión de planeación estratégica con un consultor externo.",
            "rec_medio": "Formalizar el proceso de planeación con metodología OKR o Balanced Scorecard. Establecer revisiones trimestrales y un tablero de seguimiento compartido con toda la organización.",
            "rec_fuerte": "Explorar metodologías avanzadas de innovación (Design Thinking, Blue Ocean). Fortalecer el gobierno corporativo con un consejo asesor externo.",
        },
        "Finanzas": {
            "debil": "La gestión financiera es informal y no existe control presupuestal riguroso. La empresa opera sin visibilidad sobre su flujo de caja real, lo que la expone a crisis de liquidez y limita su capacidad de inversión.",
            "medio": "Se lleva un control financiero básico pero faltan herramientas de análisis profundo. La contabilidad se cumple pero no se usa como herramienta estratégica de decisión.",
            "fuerte": "La empresa tiene una gestión financiera sólida con control presupuestal, análisis de rentabilidad y planeación fiscal. Los estados financieros guían decisiones estratégicas de manera consistente.",
            "rec_debil": "Implementar un control básico de flujo de caja semanal. Separar finanzas personales de empresariales. Definir presupuesto operativo mensual y revisarlo quincenalmente.",
            "rec_medio": "Adoptar un software contable/ERP para gestión financiera integrada. Implementar análisis de márgenes por producto/servicio y proyecciones de flujo a 90 días.",
            "rec_fuerte": "Optimizar la estructura de capital y explorar opciones de financiamiento estratégico. Implementar análisis de escenarios financieros para decisiones de inversión.",
        },
        "Marketing y Ventas": {
            "debil": "No existe un proceso comercial estructurado ni una estrategia de marketing definida. La generación de demanda es esporádica y depende principalmente del boca a boca. No se mide el retorno de las acciones comerciales.",
            "medio": "La empresa tiene presencia digital básica y un proceso de ventas informal. Se realizan acciones de marketing pero sin medición consistente del retorno ni segmentación clara del mercado.",
            "fuerte": "La empresa gestiona un proceso comercial estructurado con CRM, segmentación de mercado y estrategia de marketing multicanal. El embudo de ventas se monitorea con métricas claras.",
            "rec_debil": "Crear una base de datos de clientes y prospectos. Definir el proceso de ventas en 4-5 etapas básicas. Establecer presencia digital mínima (sitio web + 1 red social activa).",
            "rec_medio": "Implementar un CRM para gestionar el embudo de ventas. Desarrollar una estrategia de contenido digital y automatizar el seguimiento de prospectos.",
            "rec_fuerte": "Sofisticar la segmentación con análisis de datos. Implementar estrategias de fidelización y programas de referidos. Explorar nuevos canales digitales.",
        },
        "Operaciones": {
            "debil": "Los procesos no están documentados y la operación depende de personas clave. No existen estándares de calidad ni medición de productividad, lo que genera inconsistencias y limita la capacidad de escalar.",
            "medio": "Algunos procesos están documentados pero faltan estándares formales. La productividad se mide de manera general sin indicadores específicos por área o proceso.",
            "fuerte": "La empresa opera con procesos documentados, estándares de calidad claros y mejora continua. La productividad se mide con KPIs y existe capacidad para escalar la operación.",
            "rec_debil": "Documentar los 3-5 procesos más críticos del negocio. Definir estándares mínimos de calidad y crear checklists operativos. Asignar responsables claros por proceso.",
            "rec_medio": "Implementar un sistema de gestión de calidad y establecer KPIs operativos por proceso. Automatizar tareas repetitivas con herramientas digitales básicas.",
            "rec_fuerte": "Explorar certificaciones de calidad (ISO 9001). Implementar metodologías de mejora continua (Lean, Six Sigma) y automatización avanzada de procesos.",
        },
        "Talento": {
            "debil": "No existen procesos formales de reclutamiento, capacitación ni evaluación de desempeño. La retención de talento es un riesgo y no hay planeación de necesidades de personal a futuro.",
            "medio": "Se realizan procesos básicos de reclutamiento y capacitación, pero sin un plan estructurado de desarrollo. La evaluación de desempeño es informal o esporádica.",
            "fuerte": "La empresa gestiona el talento de manera estratégica con procesos formales de reclutamiento, evaluación, desarrollo y retención. Existe una cultura organizacional definida.",
            "rec_debil": "Definir perfiles de puesto y un proceso básico de reclutamiento. Implementar reuniones 1:1 quincenales. Crear un plan mínimo de capacitación para roles clave.",
            "rec_medio": "Implementar evaluaciones de desempeño semestrales con planes de desarrollo individual. Crear un programa de onboarding y un plan de capacitación anual.",
            "rec_fuerte": "Diseñar planes de carrera y sucesión. Implementar encuestas de clima laboral y fortalecer la marca empleadora.",
        },
        "Tecnología": {
            "debil": "La infraestructura tecnológica es limitada u obsoleta. Los procesos siguen siendo mayormente manuales y no se aprovechan herramientas digitales para mejorar la eficiencia operativa.",
            "medio": "Se cuenta con infraestructura tecnológica básica y algunas herramientas digitales, pero los sistemas no están integrados y la adopción digital es parcial.",
            "fuerte": "La empresa tiene una infraestructura tecnológica robusta con sistemas integrados, automatización de procesos y una estrategia de transformación digital activa.",
            "rec_debil": "Evaluar y adoptar herramientas digitales básicas (suite de oficina en la nube, almacenamiento compartido). Implementar respaldos automáticos de información crítica.",
            "rec_medio": "Integrar los sistemas existentes (ERP, CRM). Automatizar procesos repetitivos y establecer políticas básicas de ciberseguridad.",
            "rec_fuerte": "Explorar tecnologías emergentes (IA, automatización avanzada). Implementar estrategia omnicanal y fortalecer la ciberseguridad con auditorías externas.",
        },
        "Escalabilidad": {
            "debil": "La empresa no tiene un plan de crecimiento definido y carece de la infraestructura necesaria para escalar. El modelo de negocio no ha sido validado para mercados más amplios.",
            "medio": "Existen ideas de crecimiento pero sin un plan formal ni los recursos necesarios. La capacidad de escalar es limitada por falta de procesos estandarizados y financiamiento.",
            "fuerte": "La empresa está preparada para escalar con un plan de negocio formal, procesos estandarizados y acceso a financiamiento estratégico. Las alianzas impulsan el crecimiento.",
            "rec_debil": "Elaborar un plan básico de crecimiento a 12 meses con metas concretas. Identificar qué procesos deben estandarizarse antes de escalar. Explorar opciones de financiamiento.",
            "rec_medio": "Desarrollar un business plan formal con análisis de mercado. Estandarizar procesos core y preparar la estructura para duplicar operaciones.",
            "rec_fuerte": "Explorar expansión geográfica o nuevos segmentos de mercado. Desarrollar alianzas estratégicas y preparar pitch para inversionistas.",
        },
    }

    for det in calc.get("detalle_secciones", []):
        prio = "Crítica" if det["calificacion"] < 25 else ("Alta" if det["calificacion"] < 50 else ("Media" if det["calificacion"] < 75 else "Baja"))
        sec_name = det["nombre"]
        desc = _seccion_desc.get(sec_name, {})
        nivel_key = "debil" if det["calificacion"] < 40 else ("medio" if det["calificacion"] < 65 else "fuerte")
        
        recs.append({
            "seccion": sec_name, "calificacion": det["calificacion"],
            "clasificacion": det["clasificacion"],
            "diagnostico_seccion": desc.get(nivel_key, f"{sec_name} presenta nivel {det['clasificacion'].lower()}. Se recomienda evaluar las prácticas actuales y definir métricas de seguimiento para impulsar la mejora continua."),
            "recomendacion": desc.get(f"rec_{nivel_key}", "Implementar medición de KPIs y controles básicos. Definir métricas claras y revisarlas semanalmente para generar visibilidad y tomar decisiones informadas."),
            "prioridad": prio,
            "quick_win": "Definir 3 métricas clave para esta área y revisarlas semanalmente con el equipo responsable.",
        })

    return {
        "recomendacion_general": f"{empresa} necesita fortalecer áreas débiles antes de crecer.",
        "resumen_ejecutivo": f"{'Hola ' + nombre + '! ' if nombre else ''}{empresa}: Índice Menthia {calc['indice_menthia_0_100']}/100.",
        "diagnostico_estrategico": f"Nivel de madurez: {calc['nivel_madurez']}.",
        "insight_critico": "Falta visibilidad transversal de métricas.",
        "recomendaciones_por_seccion": recs,
        "riesgos_sistemicos": [{"riesgo": "Crecimiento sin procesos documentados.", "urgencia": "alta"}],
        "plan_30_dias": [
            {"fase": "Días 1-15", "accion": "Tablero de control con 3-5 KPIs", "meta": "Visibilidad en tiempo real"},
            {"fase": "Días 16-30", "accion": "Estandarizar proceso core", "meta": "Reducir dependencia del fundador"},
        ],
        "recomendaciones_innovadoras": ["Herramientas No-Code para digitalizar tareas."],
        "kpi_sugerido": "Margen Neto Operativo",
        "puntuacion_madurez_promedio": calc["indice_menthia_0_100"],
        "nivel_madurez_general": calc["nivel_madurez"],
        **calc,
    }


# =====================================================
# Mapper: formato frontend → formato motor
# =====================================================

BLOQUE_TO_PREFIX = {
    "estrategia": "es_", "finanzas": "fi_", "marketing": "mk_",
    "operaciones": "op_", "talento": "ta_", "tecnologia": "te_",
    "escalabilidad": "ec_",
}
LETRA_A_NUMERO = {"A": 1, "B": 2, "C": 3, "D": 4, "E": 5}

# Mapeo de asesoria_externa_<bloque_normalizado> → prefijo Q6
# El frontend normaliza el nombre del bloque: quita acentos, minúsculas, underscores
_ASESORIA_TO_PREFIX = {
    "estrategia": "es_",
    "finanzas": "fi_",
    "marketing_y_ventas": "mk_",
    "marketing": "mk_",
    "operaciones": "op_",
    "talento": "ta_",
    "tecnologia": "te_",
    "tecnologa": "te_",
    "escalabilidad": "ec_",
}


def _convertir_formato(data: Dict[str, Any]) -> Dict[str, Any]:
    respuestas = data.get("respuestas")
    if not respuestas or not isinstance(respuestas, dict):
        return data
    result = dict(data)
    for key, val in respuestas.items():
        if not isinstance(key, str) or "_" not in key: continue

        # Mapeo de asesoria_externa_* → Q6 (A=1, B=2, C=3)
        if key.startswith("asesoria_externa_"):
            bloque_key = key[len("asesoria_externa_"):].lower().strip()
            prefix = _ASESORIA_TO_PREFIX.get(bloque_key)
            if prefix:
                # A=0pts(1), B=5pts(2), C=10pts(3)
                letra = str(val).strip().upper()
                q6_map = {"A": "1", "B": "2", "C": "3"}
                result[f"{prefix}q6"] = q6_map.get(letra, "1")
            continue

        bloque, num = key.split("_", 1)
        prefix = BLOQUE_TO_PREFIX.get(bloque.lower())
        if not prefix: continue
        num_val = LETRA_A_NUMERO.get(str(val).upper())
        if num_val is None and str(val) in {"1","2","3","4","5"}: num_val = int(val)
        if num_val is not None:
            result[f"{prefix}q{num}"] = str(num_val)
    return result


# =====================================================
# ANALIZADOR PRINCIPAL
# =====================================================

async def analizar_diagnostico_general(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(diagnostico_data, dict):
        diagnostico_data = {}

    try: diagnostico_data = _convertir_formato(diagnostico_data)
    except: pass

    if not ANTHROPIC_API_KEY or not client:
        return _fallback(diagnostico_data)

    print(f"[llm_general] Análisis con {MODEL_NAME} (7 secciones)")

    calc = _calcular_modelo(diagnostico_data)
    try: corrs = _correlaciones(diagnostico_data)
    except: corrs = {}
    try: datos_fmt = _fmt_datos(diagnostico_data)
    except: datos_fmt = str(diagnostico_data)

    # Contexto para LLM
    ctx = f"""
=== RESULTADOS PRECALCULADOS (escala 0–100) ===
Empresa: {diagnostico_data.get('nombreEmpresa', 'N/D')}
Sector: {calc['sector']} | Tamaño: {calc['tamano']}
Índice Menthia Global: {calc['indice_menthia_0_100']}/100
Capa 1 (Percentil LATAM): {calc['capa1_percentil']}
Capa 2 (Índice Global): {calc['capa2_indice']}/3.00 → {calc['capa2_diagnostico']}
Nivel de Madurez: {calc['nivel_madurez']} | Estado: {calc['estado_madurez']}

Calificaciones por sección (0–100):"""
    for det in calc.get("detalle_secciones", []):
        ctx += f"\n  - {det['nombre']} ({det['prefijo']}): {det['calificacion']}/100 → {det['clasificacion']}"

    ctx_corr = ""
    if corrs.get("correlaciones"):
        ctx_corr += "\n\n=== CORRELACIONES DE RIESGO ===\n"
        for c in corrs["correlaciones"][:4]:
            ctx_corr += f"  ⚠ {c['mensaje']} (impacto: {c['impacto']})\n"
    if corrs.get("area_mas_debil"):
        ctx_corr += f"\nÁrea más débil: {corrs['area_mas_debil']['nombre']}"
    if corrs.get("area_mas_fuerte"):
        ctx_corr += f"\nÁrea más fuerte: {corrs['area_mas_fuerte']['nombre']}"
    if corrs.get("brecha_maxima", 0) > 0:
        ctx_corr += f"\nBrecha máxima: {corrs['brecha_maxima']}"

    user_msg = f"""Analiza este diagnóstico empresarial.
{ctx}{ctx_corr}

=== DATOS CRUDOS ===
{datos_fmt}

Genera diagnóstico completo: recomendación general potente + recomendación por cada una de las 7 secciones.
Responde SOLO con JSON."""

    try:
        response = client.messages.create(
            model=MODEL_NAME, system=MENTHIA_SYSTEM_PROMPT,
            max_tokens=6000, temperature=0.35,
            messages=[{"role": "user", "content": user_msg}],
        )
        content = (response.content[0].text or "{}").strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]

        parsed = json.loads(content.strip())

        # Validaciones
        def _lst(x): return x[:15] if isinstance(x, list) else []
        parsed["recomendaciones_por_seccion"] = _lst(parsed.get("recomendaciones_por_seccion", []))
        parsed["plan_30_dias"] = _lst(parsed.get("plan_30_dias", []))
        parsed["riesgos_sistemicos"] = _lst(parsed.get("riesgos_sistemicos", []))
        parsed["recomendaciones_innovadoras"] = _lst(parsed.get("recomendaciones_innovadoras", []))

        # Forzar datos algorítmicos en recomendaciones por sección
        recs_dict = {r.get("seccion", ""): r for r in parsed.get("recomendaciones_por_seccion", [])}
        recs_final = []
        for det in calc.get("detalle_secciones", []):
            rec = recs_dict.get(det["nombre"], {})
            rec["seccion"] = det["nombre"]
            rec["calificacion"] = det["calificacion"]
            rec["clasificacion"] = det["clasificacion"]
            rec.setdefault("diagnostico_seccion", f"Área con nivel {det['clasificacion'].lower()}.")
            rec.setdefault("recomendacion", "Implementar medición y control.")
            rec.setdefault("prioridad", "Crítica" if det["calificacion"] < 25 else ("Alta" if det["calificacion"] < 50 else "Media"))
            rec.setdefault("quick_win", "Definir 3 métricas clave.")
            recs_final.append(rec)
        parsed["recomendaciones_por_seccion"] = recs_final

        # Fusionar cálculos algorítmicos
        parsed.update({
            "puntuacion_madurez_promedio": calc["indice_menthia_0_100"],
            "nivel_madurez_general": calc["nivel_madurez"],
            "indice_menthia_0_100": calc["indice_menthia_0_100"],
            "diagnostico_capa1_percentil": calc["capa1_percentil"],
            "diagnostico_capa2_indice": calc["capa2_indice"],
            "diagnostico_capa2_diagnostico": calc["capa2_diagnostico"],
            "calificaciones_por_seccion": calc["calificaciones"],
            "clasificacion_por_seccion": calc["clasificaciones"],
            "detalle_secciones": calc["detalle_secciones"],
            "estado_madurez": calc["estado_madurez"],
            "sector": calc["sector"], "tamano": calc["tamano"],
        })
        if corrs.get("correlaciones"):
            parsed["correlaciones_detectadas"] = corrs["correlaciones"]

        return parsed

    except Exception as e:
        print(f"[llm_general] ERROR: {e}")
        fb = _fallback(diagnostico_data)
        fb["resumen_ejecutivo"] = f"Error LLM ({MODEL_NAME}): {e}. " + fb["resumen_ejecutivo"]
        return fb
