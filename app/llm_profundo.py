# app/llm_profundo.py
import os
import json
import asyncio
import logging
from typing import Dict, Any, List, Tuple, Optional
from fastapi import HTTPException
from openai import OpenAI

logger = logging.getLogger("diag_profundo")

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
# Mantén consistencia con los otros módulos
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4.1-mini")

# Si DIAG_DEMO_ON_ERROR=1, ante error con OpenAI respondemos demo en lugar de 502
DEMO_ON_ERROR = os.getenv("DIAG_DEMO_ON_ERROR", "1") == "1"

client = OpenAI(api_key=OPENAI_API_KEY)

# ---------------------------
# Configuración de dominios
# ---------------------------
KW_FIN = ["flujo de caja", "liquidez", "morosidad", "deuda", "pérdida", "perdida", "quiebra", "sin presupuesto"]
KW_RH  = ["conflicto", "rotación", "burnout", "clima", "falta de capacitación", "ausentismo"]
KW_OP  = ["cuello de botella", "reproceso", "mermas", "retraso", "ineficiencia", "sin procesos", "sin documentación"]
KW_MV  = ["baja conversión", "sin canal", "poca demanda", "bajo reconocimiento", "sin plan de marketing"]
KW_DG  = ["sin plan", "sin objetivos", "reactivo", "falta de dirección", "sin estrategia"]
KW_LCS = ["proveedor incumple", "costos altos", "retraso entregas", "sin inventario", "faltantes"]
KW_INN = ["no innova", "miedo al cambio", "desactualizado", "sin tecnología"]

DOMAIN_CONFIG = {
    "finanzas": {
        "label": "Finanzas y Administración",
        "likert_fields": [
            "fa_margenGanancia",
            "fa_estadosFinancierosActualizados",
            "fa_presupuestosAnuales",
            "fa_liquidezCubreObligaciones",
            "fa_gastosControlados",
            "fa_indicadoresFinancieros",
            "fa_analizanEstadosFinancieros",
            "fa_herramientasSoftwareFinanciero",
            "fa_situacionFinancieraGeneral",
        ],
        "text_fields": ["fa_causaProblemasFinancieros", "fa_porQueNoSeAnalizan"],
        "keywords": KW_FIN,
    },
    "rrhh": {
        "label": "Recursos Humanos",
        "likert_fields": [
            "rh_organigramaFuncionesClaras",
            "rh_personalCapacitado",
            "rh_climaLaboralFavoreceProductividad",
            "rh_programasMotivacion",
            "rh_evaluacionesDesempeno",
            "rh_indicadoresRotacionPersonal",
            "rh_liderazgoJefesIntermedios",
        ],
        "text_fields": ["rh_causaClimaLaboralComplejo", "rh_cuantasPersonasTrabajan"],
        "keywords": KW_RH,
    },
    "operaciones": {
        "label": "Operaciones / Servicio",
        "likert_fields": [
            "op_capacidadProductivaCubreDemanda",
            "op_procesosDocumentados",
            "op_estandaresCalidadCumplen",
            "op_controlesErrores",
            "op_tiemposEntregaCumplen",
            "op_eficienciaProcesosOptima",
            "op_personalConoceProcedimientos",
            "op_indicadoresOperativos",
        ],
        "text_fields": ["op_porQueNoCubreDemanda", "op_porQueNoCumplen", "op_porQueNoConocen"],
        "keywords": KW_OP,
    },
    "marketing_ventas": {
        "label": "Marketing y Ventas",
        "likert_fields": [
            "mv_clienteIdealNecesidades",
            "mv_planEstrategiasMarketing",
            "mv_marcaReconocida",
            "mv_estudiosSatisfaccionCliente",
            "mv_indicadoresDesempenoComercial",
            "mv_equipoVentasCapacitado",
            "mv_politicasDescuentosPromociones",
        ],
        "text_fields": ["mv_impactoCanalesVenta", "mv_canalesVentaActuales", "mv_porQueNoHaceEstudios"],
        "keywords": KW_MV,
    },
    "direccion": {
        "label": "Dirección y Planeación",
        "likert_fields": [
            "dg_misionVisionValores",
            "dg_objetivosClaros",
            "dg_planEstrategicoDocumentado",
            "dg_revisionAvancePlan",
            "dg_factoresExternos",
            "dg_capacidadAdaptacion",
            "dg_colaboradoresParticipan",
        ],
        "text_fields": ["dg_impideCumplirMetas", "dg_comoSeTomanDecisiones", "dg_porQueNoParticipan"],
        "keywords": KW_DG,
    },
    "logistica": {
        "label": "Logística y Cadena de Suministro",
        "likert_fields": [
            "lcs_proveedoresCumplen",
            "lcs_entregasClientesPuntuales",
            "lcs_costosLogisticosCompetitivos",
            "lcs_poderNegociacionProveedores",
            "lcs_indicadoresLogisticos",
        ],
        "text_fields": ["lcs_problemasLogisticosPunto"],
        "keywords": KW_LCS,
    },
    "innovacion": {
        "label": "Innovación",
        "likert_fields": [
            "ci_mejoranProductosServicios",
            "ci_recogeImplementaIdeasPersonal",
            "ci_invierteTecnologiaInnovacion",
            "ci_dispuestoAsumirRiesgos",
            "ci_protegePropiedadIntelectual",
            "ci_fomentaCulturaCambio",
        ],
        "text_fields": ["ci_porQueNoInnova"],
        "keywords": KW_INN,
    },
}

# ---------------------------
# Utilidades de scoring
# ---------------------------
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
    if neg_hit: base -= 0.5
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

# ---------------------------
# DEMO / Fallback
# ---------------------------
_DEMO_TOP = {
    "analisis_detallado": "Diagnóstico generado en modo DEMO (sin clave OpenAI o por error).",
    "oportunidades_estrategicas": [
        "Estandarizar procesos críticos con tableros de control",
        "Fortalecer flujo de caja y disciplina presupuestal",
        "Profesionalizar gestión de talento y liderazgo intermedio",
    ],
    "riesgos_identificados": [
        "Dependencia de pocos clientes/proveedores",
        "Tensión de liquidez por falta de presupuesto y cobranza reactiva",
    ],
    "plan_accion_sugerido": [
        "Implementar presupuesto operativo y flujo semanal (30 días)",
        "Formalizar evaluación de desempeño y feedback trimestral (60 días)",
        "Definir KPIs y rutinas de revisión mensual (90 días)",
    ],
    "indicadores_clave_rendimiento": ["Margen bruto", "Ciclo de caja", "Rotación de personal", "NPS", "OTIF"],
}

def _quick_template_by_domain(sev: str, label: str) -> Dict[str, Any]:
    pref = "Prioridad alta" if sev in ("Crítico", "Alto") else "Prioridad media"
    return {
        "diagnostico": f"{label}: {pref}. Se observan brechas que requieren intervención inmediata para estabilizar resultados.",
        "causas_raiz": [
            "Falta de estandarización y rutinas de control",
            "Datos incompletos para decidir",
            "Roles/propietarios difusos sobre los procesos clave",
        ],
        "recomendaciones_30_60_90": {
            "30": ["Definir objetivos claros y responsables", "Establecer tablero mínimo de control"],
            "60": ["Documentar procesos críticos y capacitar al equipo", "Reuniones de seguimiento quincenal"],
            "90": ["Medir impacto y ajustar metas trimestrales", "Escalar mejores prácticas"],
        },
        "kpis": [
            {"nombre": "Cumplimiento de metas", "meta": "≥ 85% mensual"},
            {"nombre": "Tiempo de ciclo", "meta": "−20% en 90 días"},
        ],
        "riesgos": [
            {"riesgo": "Falta de adopción", "mitigacion": "Acompañamiento con responsables y quick wins tempranos"}
        ],
        "quick_wins": ["Checklist operativo semanal", "Hitos quincenales con tablero visible"],
    }

def _build_rule_based_structure(domains: Dict[str, Any]) -> Dict[str, Any]:
    tabla = []
    detail = {}
    for k, d in domains.items():
        tabla.append({
            "dominio": k,
            "nombre": d["nombre"],
            "score": d["score"],
            "severidad": d["severidad"],
            "prioridad": d["prioridad"],
        })
        detail[k] = _quick_template_by_domain(d["severidad"], d["nombre"])
        if k == "finanzas":
            detail[k]["kpis"] = [
                {"nombre": "Ciclo de caja", "meta": "≤ 45 días"},
                {"nombre": "Margen bruto", "meta": "≥ 40%"},
            ]
        if k == "rrhh":
            detail[k]["kpis"] = [
                {"nombre": "Rotación anualizada", "meta": "≤ 12%"},
                {"nombre": "eNPS", "meta": "≥ 20"},
            ]
        if k == "operaciones":
            detail[k]["kpis"] = [
                {"nombre": "OTIF", "meta": "≥ 95%"},
                {"nombre": "Productividad", "meta": "+15% en 90 días"},
            ]
    tabla.sort(key=lambda x: {"P1": 0, "P2": 1, "P3": 2}[x["prioridad"]])
    return {
        "resumen_ejecutivo": "Se priorizan los dominios con severidad Crítico/Alto. Se propone un plan 30-60-90 con KPIs claros.",
        "tabla_dominios": tabla,
        "dominios": detail,
    }

# ---------------------------
# Saneado de salida
# ---------------------------
def _sanitize_output(obj: Dict[str, Any], fallback_domains: Dict[str, Any]) -> Dict[str, Any]:
    def S(x): return x if isinstance(x, str) else ""
    def A(x): return x if isinstance(x, list) and all(isinstance(i, str) for i in x) else []

    out = {
        "analisis_detallado": S(obj.get("analisis_detallado")),
        "oportunidades_estrategicas": A(obj.get("oportunidades_estrategicas")),
        "riesgos_identificados": A(obj.get("riesgos_identificados")),
        "plan_accion_sugerido": A(obj.get("plan_accion_sugerido")),
        "indicadores_clave_rendimiento": A(obj.get("indicadores_clave_rendimiento")),
    }

    if not out["analisis_detallado"]:
        out["analisis_detallado"] = _DEMO_TOP["analisis_detallado"]
    if not out["oportunidades_estrategicas"]:
        out["oportunidades_estrategicas"] = _DEMO_TOP["oportunidades_estrategicas"]
    if not out["riesgos_identificados"]:
        out["riesgos_identificados"] = _DEMO_TOP["riesgos_identificados"]
    if not out["plan_accion_sugerido"]:
        out["plan_accion_sugerido"] = _DEMO_TOP["plan_accion_sugerido"]
    if not out["indicadores_clave_rendimiento"]:
        out["indicadores_clave_rendimiento"] = _DEMO_TOP["indicadores_clave_rendimiento"]

    ec = obj.get("estructura_consultiva")
    if isinstance(ec, dict):
        out["estructura_consultiva"] = ec
    else:
        out["estructura_consultiva"] = _build_rule_based_structure(fallback_domains)

    return out

# ---------------------------
# Prompt y llamada al LLM
# ---------------------------
def _make_llm_prompt(diagnostico_data: Dict[str, Any], domains: Dict[str, Any]) -> str:
    activos = [v for v in domains.values() if v["prioridad"] in ("P1", "P2")]
    if not activos:
        activos = sorted(domains.values(), key=lambda x: x["score"])[:2]

    resumen_tabla = [
        {
            "dominio": d["dominio"],
            "nombre": d["nombre"],
            "score": d["score"],
            "severidad": d["severidad"],
            "prioridad": d["prioridad"],
            "evidencias": d["evidencias"],
        }
        for d in activos
    ]

    campos_relevantes = set()
    for d in activos:
        cfg = DOMAIN_CONFIG[d["dominio"]]
        for k in cfg["likert_fields"] + cfg["text_fields"]:
            campos_relevantes.add(k)
    subset = {k: diagnostico_data.get(k) for k in sorted(list(campos_relevantes))}

    instrucciones = (
        "Eres un CONSULTOR SENIOR. Redacta con precisión, foco y priorización.\n"
        "Genera un JSON con las claves:\n"
        "1) analisis_detallado (string)\n"
        "2) oportunidades_estrategicas (string[])\n"
        "3) riesgos_identificados (string[])\n"
        "4) plan_accion_sugerido (string[])\n"
        "5) indicadores_clave_rendimiento (string[])\n"
        "6) estructura_consultiva (object) con:\n"
        "   - resumen_ejecutivo (string)\n"
        "   - tabla_dominios (array<{dominio,nombre,score,severidad,prioridad}>)\n"
        "   - dominios (obj por dominio activo) con: diagnostico, causas_raiz[], recomendaciones_30_60_90{30,60,90}, kpis[], riesgos[], quick_wins[]\n"
        "NO agregues texto fuera del JSON. Tono consultivo, metas concretas, 2–4 bullets por lista."
    )

    user_prompt = {
        "contexto": {
            "dominios_activados": resumen_tabla,
            "campos_relevantes": subset
        },
        "instrucciones": instrucciones
    }

    return json.dumps(user_prompt, ensure_ascii=False)

# ---------------------------
# API principal
# ---------------------------
async def analizar_diagnostico_profundo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    domains = _compute_domains(diagnostico_data)

    if not OPENAI_API_KEY:
        demo_struct = _build_rule_based_structure(domains)
        return _sanitize_output({**_DEMO_TOP, "estructura_consultiva": demo_struct}, domains)

    try:
        prompt = _make_llm_prompt(diagnostico_data, domains)

        def _call():
            comp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Responde únicamente con JSON válido siguiendo las instrucciones."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.2,
            )
            return comp

        completion = await asyncio.to_thread(_call)
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        return _sanitize_output(parsed, domains)

    except Exception as e:
        logger.exception("OpenAI error en analizar_diagnostico_profundo")
        if DEMO_ON_ERROR:
            demo_struct = _build_rule_based_structure(domains)
            demo = {
                **_DEMO_TOP,
                "analisis_detallado": f"[DEMO POR ERROR: {type(e).__name__}] " + _DEMO_TOP["analisis_detallado"],
                "estructura_consultiva": demo_struct,
            }
            return _sanitize_output(demo, domains)
        raise HTTPException(status_code=502, detail=f"Fallo con OpenAI ({MODEL_NAME}): {e}")
