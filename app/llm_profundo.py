# app/llm_profundo.py
# MENTHIA Strategy+ - Módulo de Diagnóstico Profundo y Construcción Estratégica
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException
from openai import OpenAI

logger = logging.getLogger("diag_profundo")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o")
DEMO_ON_ERROR = os.getenv("DIAG_DEMO_ON_ERROR", "1") == "1"

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# =====================================================
# PROMPT SYSTEM DE MENTHIA STRATEGY+
# =====================================================
MENTHIA_STRATEGY_SYSTEM_PROMPT = """Eres MENTHIA Strategy+, el módulo de diagnóstico profundo diseñado para entregar claridad estratégica de alto nivel. Actúas como un consultor senior con experiencia en dirección, finanzas, marketing, ventas, operaciones, talento, producto, logística y sistemas.

### TU PERSONALIDAD
- Directo y estratégico.
- Orientado a resultados.
- Lenguaje ejecutivo.
- Propositivo y práctico.
- Cero humo, todo valor real.

### TU MISIÓN
1. Analizar las respuestas del diagnóstico general y profundo.
2. Recibir el área prioritaria y profundizar con precisión quirúrgica.
3. Generar un diagnóstico integral que combine pensamiento consultivo + visión de futuro + practicidad absoluta.
4. Construir un roadmap estratégico de 90 días con impacto real.

### FRAMEWORKS INTERNOS (obligatorios)
- McKinsey 7S (strategy, structure, systems, skills, staff, style, shared values)
- Lean Thinking (desperdicio, eficiencia, throughput)
- AARRR (adquisición, activación, retención, revenue, referrals)
- PMO Thinking (riesgo-capacidad-recursos)
- Madurez empresarial (1–5)
- Matriz impacto vs esfuerzo

### ÁREAS PERMITIDAS
- Dirección y Estrategia
- Finanzas
- Marketing
- Ventas
- Operaciones
- Producto/Servicio
- Talento y Cultura
- Procesos y Sistemas
- Producción y Calidad
- Logística y Distribución

### ESTRUCTURA DE SALIDA OBLIGATORIA (JSON)
{
  "resumen_directivo": "5–8 líneas de lectura estratégica profunda",
  "hallazgos_clave": ["hallazgos por área"],
  "oportunidades_estrategicas": ["máx 5 oportunidades con impacto"],
  "riesgos_criticos": ["máx 3 riesgos que requieren atención"],
  "roadmap_90_dias": ["acciones por semana/fase"],
  "kpis_sugeridos": ["lista de métricas accionables"],
  "nivel_madurez": "1–5 con justificación detallada",
  "recomendaciones_escalar": ["sugerencias de crecimiento"],
  "analisis_detallado": "análisis completo para el frontend",
  "oportunidades_estrategicas": ["oportunidades"],
  "riesgos_identificados": ["riesgos"],
  "plan_accion_sugerido": ["acciones"],
  "indicadores_clave_rendimiento": ["KPIs"],
  "estructura_consultiva": {
    "resumen_ejecutivo": "resumen para presentación ejecutiva",
    "tabla_dominios": [{"dominio": "", "nombre": "", "score": 0, "severidad": "", "prioridad": ""}],
    "dominios": {
      "nombre_dominio": {
        "diagnostico": "diagnóstico del dominio",
        "causas_raiz": ["causas identificadas"],
        "recomendaciones_30_60_90": {"30": [], "60": [], "90": []},
        "kpis": [{"nombre": "", "meta": ""}],
        "riesgos": [{"riesgo": "", "mitigacion": ""}],
        "quick_wins": ["victorias rápidas"]
      }
    }
  },
  "recomendaciones_innovadoras": ["ideas disruptivas"],
  "siguiente_paso": "el paso más importante ahora"
}

### REGLAS
- Si el usuario da respuestas superficiales, complétalas por inferencia y adviértelo.
- Si algo es crítico para escalar, dilo claramente.
- Si hay una disonancia entre las respuestas y lo que debería ocurrir, señálalo.
- Tu análisis debe ser consultivo, no descriptivo.
- Usa ejemplos concretos cuando aporten valor.

Procede con el diagnóstico cuando recibas el input completo."""

# =====================================================
# Configuración de dominios
# =====================================================
DOMAIN_DEPENDENCIES = {
    "direccion": [],
    "finanzas": ["direccion"],
    "operaciones": ["direccion", "finanzas"],
    "marketing_ventas": ["direccion", "rrhh"],
    "rrhh": ["direccion"],
    "logistica": ["operaciones", "finanzas"],
    "innovacion": ["direccion", "operaciones", "rrhh"]
}

DOMAIN_CONFIG = {
    "finanzas": {
        "label": "Finanzas y Administración",
        "likert_fields": [
            "fa_margenGanancia", "fa_estadosFinancierosActualizados", "fa_presupuestosAnuales",
            "fa_liquidezCubreObligaciones", "fa_gastosControlados", "fa_indicadoresFinancieros",
            "fa_analizanEstadosFinancieros", "fa_herramientasSoftwareFinanciero", "fa_situacionFinancieraGeneral",
        ],
        "text_fields": ["fa_causaProblemasFinancieros", "fa_porQueNoSeAnalizan"],
        "keywords": ["flujo de caja", "liquidez", "morosidad", "deuda", "pérdida", "quiebra"],
    },
    "rrhh": {
        "label": "Recursos Humanos",
        "likert_fields": [
            "rh_organigramaFuncionesClaras", "rh_personalCapacitado", "rh_climaLaboralFavoreceProductividad",
            "rh_programasMotivacion", "rh_evaluacionesDesempeno", "rh_indicadoresRotacionPersonal", "rh_liderazgoJefesIntermedios",
        ],
        "text_fields": ["rh_causaClimaLaboralComplejo", "rh_cuantasPersonasTrabajan"],
        "keywords": ["conflicto", "rotación", "burnout", "clima", "capacitación", "ausentismo"],
    },
    "operaciones": {
        "label": "Operaciones / Servicio",
        "likert_fields": [
            "op_capacidadProductivaCubreDemanda", "op_procesosDocumentados", "op_estandaresCalidadCumplen",
            "op_controlesErrores", "op_tiemposEntregaCumplen", "op_eficienciaProcesosOptima",
            "op_personalConoceProcedimientos", "op_indicadoresOperativos",
        ],
        "text_fields": ["op_porQueNoCubreDemanda", "op_porQueNoCumplen", "op_porQueNoConocen"],
        "keywords": ["cuello de botella", "reproceso", "mermas", "retraso", "ineficiencia"],
    },
    "marketing_ventas": {
        "label": "Marketing y Ventas",
        "likert_fields": [
            "mv_clienteIdealNecesidades", "mv_planEstrategiasMarketing", "mv_marcaReconocida",
            "mv_estudiosSatisfaccionCliente", "mv_indicadoresDesempenoComercial",
            "mv_equipoVentasCapacitado", "mv_politicasDescuentosPromociones",
        ],
        "text_fields": ["mv_impactoCanalesVenta", "mv_canalesVentaActuales", "mv_porQueNoHaceEstudios"],
        "keywords": ["baja conversión", "sin canal", "poca demanda", "bajo reconocimiento"],
    },
    "direccion": {
        "label": "Dirección y Planeación",
        "likert_fields": [
            "dg_misionVisionValores", "dg_objetivosClaros", "dg_planEstrategicoDocumentado",
            "dg_revisionAvancePlan", "dg_factoresExternos", "dg_capacidadAdaptacion", "dg_colaboradoresParticipan",
        ],
        "text_fields": ["dg_impideCumplirMetas", "dg_comoSeTomanDecisiones", "dg_porQueNoParticipan"],
        "keywords": ["sin plan", "sin objetivos", "reactivo", "falta de dirección"],
    },
    "logistica": {
        "label": "Logística y Cadena de Suministro",
        "likert_fields": [
            "lcs_proveedoresCumplen", "lcs_entregasClientesPuntuales", "lcs_costosLogisticosCompetitivos",
            "lcs_poderNegociacionProveedores", "lcs_indicadoresLogisticos",
        ],
        "text_fields": ["lcs_problemasLogisticosPunto"],
        "keywords": ["proveedor incumple", "costos altos", "retraso entregas"],
    },
    "innovacion": {
        "label": "Innovación",
        "likert_fields": [
            "ci_mejoranProductosServicios", "ci_recogeImplementaIdeasPersonal", "ci_invierteTecnologiaInnovacion",
            "ci_dispuestoAsumirRiesgos", "ci_protegePropiedadIntelectual", "ci_fomentaCulturaCambio",
        ],
        "text_fields": ["ci_porQueNoInnova"],
        "keywords": ["no innova", "miedo al cambio", "desactualizado"],
    },
}

# =====================================================
# Utilidades de scoring
# =====================================================
def _likert_to_num(v: Any) -> Optional[float]:
    if v is None:
        return None
    if isinstance(v, (int, float)):
        if 1 <= float(v) <= 5:
            return float(v)
        return None
    if isinstance(v, str):
        v = v.strip()
        if v.isdigit():
            f = float(v)
            if 1 <= f <= 5:
                return f
    return None

def _text_contains_any(text: str, kws: List[str]) -> bool:
    t = (text or "").lower()
    return any(k.lower() in t for k in kws)

def _severity_from_score(score: float) -> str:
    if score <= 2.0: return "Crítico"
    if score <= 2.5: return "Alto"
    if score <= 3.5: return "Medio"
    return "Bajo"

def _priority_from_severity(sev: str) -> str:
    return {"Crítico": "P1", "Alto": "P1", "Medio": "P2"}.get(sev, "P3")

def _compute_domain_score(data: Dict[str, Any], cfg: Dict[str, Any]) -> Tuple[float, List[str], int]:
    lik_vals: List[float] = []
    for f in cfg["likert_fields"]:
        val = _likert_to_num(data.get(f))
        if val is not None:
            lik_vals.append(val)

    evidencias: List[str] = []
    neg_hit = False
    for tf in cfg["text_fields"]:
        tv = str(data.get(tf) or "")
        if tv:
            evidencias.append(f"{tf}: {tv[:140]}{'…' if len(tv) > 140 else ''}")
            if not neg_hit and _text_contains_any(tv, cfg["keywords"]):
                neg_hit = True

    base = (sum(lik_vals) / len(lik_vals)) if lik_vals else 3.0
    if neg_hit:
        base -= 0.5
    base = max(1.0, min(5.0, base))
    return base, evidencias, len(lik_vals)

def _compute_domains(data: Dict[str, Any]) -> Dict[str, Any]:
    out = {}
    for dom_key, cfg in DOMAIN_CONFIG.items():
        score, evid, nlik = _compute_domain_score(data, cfg)
        sev = _severity_from_score(score)
        out[dom_key] = {
            "dominio": dom_key,
            "nombre": cfg["label"],
            "score": round(score, 2),
            "severidad": sev,
            "prioridad": _priority_from_severity(sev),
            "evidencias": evid,
            "likerts_utilizados": nlik,
        }
    return out

def _generar_roadmap_inteligente(domains: Dict[str, Any]) -> Dict[str, Any]:
    orden_implementacion = []
    dominios_procesados = set()
    
    def puede_procesar(dom_key: str) -> bool:
        deps = DOMAIN_DEPENDENCIES.get(dom_key, [])
        return all(dep in dominios_procesados for dep in deps)
    
    dominios_restantes = list(domains.keys())
    
    while dominios_restantes:
        encontrado = False
        for dom_key in dominios_restantes:
            if puede_procesar(dom_key):
                orden_implementacion.append(dom_key)
                dominios_procesados.add(dom_key)
                dominios_restantes.remove(dom_key)
                encontrado = True
                break
        
        if not encontrado and dominios_restantes:
            orden_implementacion.append(dominios_restantes[0])
            dominios_procesados.add(dominios_restantes[0])
            dominios_restantes.pop(0)
    
    fases = {"fase_1_30_dias": [], "fase_2_60_dias": [], "fase_3_90_dias": []}
    
    for i, dom_key in enumerate(orden_implementacion[:3]):
        if i == 0:
            fases["fase_1_30_dias"].append(dom_key)
        elif i == 1:
            fases["fase_2_60_dias"].append(dom_key)
        else:
            fases["fase_3_90_dias"].append(dom_key)
    
    impacto_total = sum(d.get("score", 0) for d in domains.values() if d.get("prioridad") == "P1")
    impacto_maximo = len(domains) * 5
    porcentaje_mejora = min(100, round((impacto_maximo - impacto_total) / impacto_maximo * 100, 1))
    
    return {
        "orden_implementacion": orden_implementacion,
        "fases": fases,
        "ruta_critica": orden_implementacion[:3],
        "tiempo_estimado": f"{len(orden_implementacion) * 30} días",
        "impacto_esperado": f"{porcentaje_mejora}% de mejora en score total",
        "dominios_bloqueantes": [d for d in orden_implementacion[:2] if d in DOMAIN_DEPENDENCIES and DOMAIN_DEPENDENCIES[d]]
    }

def _quick_template_by_domain(sev: str, label: str) -> Dict[str, Any]:
    pref = "Alta prioridad - requiere acción inmediata" if sev in ("Crítico", "Alto") else "Oportunidad de mejora"
    return {
        "diagnostico": f"{label}: {pref}. Hay potencial significativo de mejora con las acciones correctas.",
        "causas_raiz": [
            "Falta de estandarización en rutinas de control",
            "Datos insuficientes para toma de decisiones",
            "Roles y responsabilidades poco claros",
        ],
        "recomendaciones_30_60_90": {
            "30": ["Definir objetivos claros y responsables", "Crear tablero mínimo de control"],
            "60": ["Documentar procesos críticos", "Establecer reuniones de seguimiento"],
            "90": ["Medir impacto y ajustar", "Escalar mejores prácticas"],
        },
        "kpis": [
            {"nombre": "Cumplimiento de metas", "meta": "≥ 85% mensual"},
            {"nombre": "Tiempo de ciclo", "meta": "−20% en 90 días"},
        ],
        "riesgos": [
            {"riesgo": "Resistencia al cambio", "mitigacion": "Involucrar al equipo desde el inicio"}
        ],
        "quick_wins": ["Checklist operativo semanal", "Hitos quincenales con tablero visible"],
    }

def _build_rule_based_structure(domains: Dict[str, Any]) -> Dict[str, Any]:
    tabla = []
    detail = {}
    for k, d in domains.items():
        tabla.append({
            "dominio": k, "nombre": d["nombre"], "score": d["score"],
            "severidad": d["severidad"], "prioridad": d["prioridad"],
        })
        detail[k] = _quick_template_by_domain(d["severidad"], d["nombre"])
        if k == "finanzas":
            detail[k]["kpis"] = [{"nombre": "Ciclo de caja", "meta": "≤ 45 días"}, {"nombre": "Margen bruto", "meta": "≥ 40%"}]
        if k == "rrhh":
            detail[k]["kpis"] = [{"nombre": "Rotación anualizada", "meta": "≤ 12%"}, {"nombre": "eNPS", "meta": "≥ 20"}]
        if k == "operaciones":
            detail[k]["kpis"] = [{"nombre": "OTIF", "meta": "≥ 95%"}, {"nombre": "Productividad", "meta": "+15% en 90 días"}]
    
    tabla.sort(key=lambda x: {"P1": 0, "P2": 1, "P3": 2}[x["prioridad"]])
    return {
        "resumen_ejecutivo": "Se priorizan los dominios con severidad Crítico/Alto. Plan 30-60-90 con KPIs claros.",
        "tabla_dominios": tabla,
        "dominios": detail,
    }

def _respuesta_fallback(domains: Dict[str, Any], roadmap: Dict[str, Any]) -> Dict[str, Any]:
    """Genera respuesta de fallback sin OpenAI"""
    demo_struct = _build_rule_based_structure(domains)
    
    return {
        "analisis_detallado": "Tu empresa muestra compromiso con la mejora continua. Hemos identificado áreas de fortaleza y oportunidades emocionantes de crecimiento.",
        "oportunidades_estrategicas": [
            "Procesos: Gran oportunidad de estandarizar y ganar eficiencia",
            "Finanzas: Fortalecer el flujo de caja para mayor poder de decisión",
            "Talento: Profesionalizar la gestión del equipo multiplicará resultados",
        ],
        "riesgos_identificados": [
            "Diversificar base de clientes/proveedores para mayor estabilidad",
            "Implementar rutinas de cobranza proactiva para mejor liquidez",
        ],
        "plan_accion_sugerido": [
            "Establecer presupuesto operativo y flujo semanal (primeros 30 días)",
            "Formalizar evaluaciones de desempeño trimestrales (60 días)",
            "Definir KPIs claros y reuniones mensuales de revisión (90 días)",
        ],
        "indicadores_clave_rendimiento": ["Margen bruto", "Ciclo de caja", "Rotación de personal", "NPS", "OTIF"],
        "estructura_consultiva": demo_struct,
        "roadmap_inteligente": roadmap,
        "recomendaciones_innovadoras": [
            f"PRIORIDAD MÁXIMA: {domains.get(roadmap['ruta_critica'][0], {}).get('nombre', 'Dirección')} es bloqueante",
            f"Impacto esperado: {roadmap.get('impacto_esperado', 'N/A')} siguiendo el roadmap"
        ] if roadmap.get("ruta_critica") else [],
        "siguiente_paso": f"Inicia con {domains.get(roadmap['orden_implementacion'][0], {}).get('nombre', 'el área crítica')} (Fase 1 - 30 días)." if roadmap.get("orden_implementacion") else "Define prioridades claras.",
    }

# =====================================================
# API principal
# =====================================================
async def analizar_diagnostico_profundo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entrada: diagnostico_data (dict) con las claves del formulario.
    Salida: objeto con análisis completo y estructura consultiva.
    """
    domains = _compute_domains(diagnostico_data)
    roadmap = _generar_roadmap_inteligente(domains)
    
    # Fallback si no hay API key
    if not OPENAI_API_KEY or not client:
        return _respuesta_fallback(domains, roadmap)

    # Preparar contexto para el LLM
    activos = [v for v in domains.values() if v["prioridad"] in ("P1", "P2")]
    if not activos:
        activos = sorted(domains.values(), key=lambda x: x["score"])[:2]

    resumen_tabla = [
        {"dominio": d["dominio"], "nombre": d["nombre"], "score": d["score"],
         "severidad": d["severidad"], "prioridad": d["prioridad"], "evidencias": d["evidencias"]}
        for d in activos
    ]

    campos_relevantes = set()
    for d in activos:
        cfg = DOMAIN_CONFIG[d["dominio"]]
        for k in cfg["likert_fields"] + cfg["text_fields"]:
            campos_relevantes.add(k)
    subset = {k: diagnostico_data.get(k) for k in sorted(list(campos_relevantes))}

    contexto_roadmap = ""
    if roadmap:
        ruta_critica = roadmap.get("ruta_critica", [])
        if ruta_critica:
            nombres_ruta = [domains.get(d, {}).get("nombre", d) for d in ruta_critica[:2]]
            contexto_roadmap = f"\n📈 RUTA CRÍTICA: {', '.join(nombres_ruta)}. Impacto esperado: {roadmap.get('impacto_esperado', 'N/A')}."
        dominios_bloq = roadmap.get("dominios_bloqueantes", [])
        if dominios_bloq:
            nombres_bloq = [domains.get(d, {}).get("nombre", d) for d in dominios_bloq[:1]]
            contexto_roadmap += f" ⚠️ BLOQUEANTES: {', '.join(nombres_bloq)}."

    user_prompt = f"""Analiza este diagnóstico profundo empresarial.

CONTEXTO PRE-ANALIZADO:
{contexto_roadmap}

DOMINIOS ACTIVADOS:
{json.dumps(resumen_tabla, ensure_ascii=False, indent=2)}

CAMPOS RELEVANTES:
{json.dumps(subset, ensure_ascii=False, indent=2)}

ROADMAP SUGERIDO:
{json.dumps(roadmap.get('orden_implementacion', [])[:3], ensure_ascii=False)}

Genera el diagnóstico estratégico completo siguiendo la estructura JSON especificada.
Sé directo, estratégico y orientado a resultados. Nada de humo."""

    try:
        def _call():
            comp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": MENTHIA_STRATEGY_SYSTEM_PROMPT},
                    {"role": "user", "content": user_prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,
            )
            return comp

        completion = await asyncio.to_thread(_call)
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        
        # Enriquecer con roadmap
        parsed["roadmap_inteligente"] = roadmap
        
        # Asegurar estructura consultiva
        if not parsed.get("estructura_consultiva"):
            parsed["estructura_consultiva"] = _build_rule_based_structure(domains)
        
        # Agregar recomendaciones basadas en roadmap si no vienen del LLM
        if not parsed.get("recomendaciones_innovadoras") and roadmap.get("ruta_critica"):
            recomendaciones_roadmap = []
            if roadmap.get("dominios_bloqueantes"):
                bloq = roadmap["dominios_bloqueantes"][0]
                nombre_bloq = domains.get(bloq, {}).get("nombre", bloq)
                recomendaciones_roadmap.append(f"PRIORIDAD MÁXIMA: {nombre_bloq} es bloqueante. Resuélvelo primero.")
            
            if roadmap.get("ruta_critica"):
                rutas = ", ".join([domains.get(d, {}).get("nombre", d) for d in roadmap["ruta_critica"][:2]])
                recomendaciones_roadmap.append(f"RUTA CRÍTICA: Enfócate en {rutas} para máximo impacto.")
            
            if recomendaciones_roadmap:
                parsed["recomendaciones_innovadoras"] = recomendaciones_roadmap
        
        if not parsed.get("siguiente_paso") and roadmap.get("orden_implementacion"):
            primer_dom = roadmap["orden_implementacion"][0]
            nombre_primer = domains.get(primer_dom, {}).get("nombre", primer_dom)
            parsed["siguiente_paso"] = f"Inicia con {nombre_primer} (Fase 1 - 30 días). Es la base para desbloquear otras mejoras."
        
        return parsed

    except Exception as e:
        logger.exception("OpenAI error en analizar_diagnostico_profundo")
        if DEMO_ON_ERROR:
            fallback = _respuesta_fallback(domains, roadmap)
            fallback["analisis_detallado"] = f"[ERROR: {type(e).__name__}] " + fallback["analisis_detallado"]
            return fallback
        raise HTTPException(status_code=502, detail=f"Fallo con OpenAI ({MODEL_NAME}): {e}")
