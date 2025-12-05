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
MODEL_NAME = os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")

# Si DIAG_DEMO_ON_ERROR=1, ante error con OpenAI respondemos demo en lugar de 502
DEMO_ON_ERROR = os.getenv("DIAG_DEMO_ON_ERROR", "1") == "1"

client = OpenAI(api_key=OPENAI_API_KEY) if OPENAI_API_KEY else None

# Matriz de dependencias entre dominios (para roadmap inteligente)
DOMAIN_DEPENDENCIES = {
    "direccion": [],  # No depende de nada (base)
    "finanzas": ["direccion"],  # Depende de dirección
    "operaciones": ["direccion", "finanzas"],  # Depende de dirección y finanzas
    "marketing_ventas": ["direccion", "rrhh"],  # Depende de dirección y RH
    "rrhh": ["direccion"],  # Depende de dirección
    "logistica": ["operaciones", "finanzas"],  # Depende de operaciones y finanzas
    "innovacion": ["direccion", "operaciones", "rrhh"]  # Depende de múltiples áreas
}

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

# ---------------------------
# DEMO / Fallback
# ---------------------------
_DEMO_TOP = {
    "analisis_detallado": "¡Felicidades por completar este diagnóstico profundo! 🎉 Tu empresa muestra compromiso con la mejora continua, y eso ya es una gran fortaleza. Hemos identificado áreas donde ya estás haciendo un buen trabajo, y también oportunidades emocionantes para crecer aún más. Juntos vamos a trazar un camino claro hacia tus metas. ¡Vamos por ello! 💪",
    "oportunidades_estrategicas": [
        "💡 Procesos: Gran oportunidad de estandarizar y ganar eficiencia con tableros de control",
        "📊 Finanzas: Fortalecer el flujo de caja te dará tranquilidad y poder de decisión",
        "👥 Talento: Profesionalizar la gestión de tu equipo multiplicará los resultados",
    ],
    "riesgos_identificados": [
        "🛡️ Área a proteger: Diversificar base de clientes/proveedores para mayor estabilidad",
        "💰 Punto de atención: Implementar rutinas de cobranza proactiva para mejor liquidez",
    ],
    "plan_accion_sugerido": [
        "🚀 Te recomiendo empezar con un presupuesto operativo y flujo semanal (primeros 30 días)",
        "💪 Un gran paso sería formalizar evaluaciones de desempeño trimestrales (60 días)",
        "✨ Podrías definir KPIs claros y reuniones mensuales de revisión (90 días)",
    ],
    "indicadores_clave_rendimiento": ["📈 Margen bruto", "💰 Ciclo de caja", "👥 Rotación de personal", "⭐ NPS (satisfacción)", "📦 OTIF (entregas)"],
    "mensaje_motivacional": "¡Cada paso que das cuenta! El simple hecho de hacer este diagnóstico demuestra tu compromiso con el crecimiento. ¡Vas por excelente camino! 🌟"
}

def _quick_template_by_domain(sev: str, label: str) -> Dict[str, Any]:
    pref = "Alta prioridad - ¡gran oportunidad de mejora!" if sev in ("Crítico", "Alto") else "Oportunidad de crecimiento"
    return {
        "diagnostico": f"✨ {label}: {pref} Aquí hay potencial significativo para impulsar resultados. Con las acciones correctas, verás mejoras rápidas.",
        "causas_raiz": [
            "💡 Oportunidad: Estandarizar rutinas de control",
            "📊 Área de mejora: Mejorar la disponibilidad de datos para decisiones",
            "👥 Punto a trabajar: Clarificar roles y responsabilidades",
        ],
        "recomendaciones_30_60_90": {
            "30": ["🎯 Definir objetivos claros y asignar responsables", "📋 Crear un tablero mínimo de control"],
            "60": ["📚 Documentar procesos críticos y capacitar al equipo", "🤝 Establecer reuniones de seguimiento quincenal"],
            "90": ["📈 Medir impacto y ajustar metas", "🚀 Escalar las mejores prácticas a toda la organización"],
        },
        "kpis": [
            {"nombre": "✅ Cumplimiento de metas", "meta": "≥ 85% mensual"},
            {"nombre": "⏱️ Tiempo de ciclo", "meta": "−20% en 90 días"},
        ],
        "riesgos": [
            {"riesgo": "Resistencia al cambio", "mitigacion": "💪 Involucrar al equipo desde el inicio y celebrar quick wins"}
        ],
        "quick_wins": ["📋 Checklist operativo semanal", "🎯 Hitos quincenales con tablero visible"],
    }

def _generar_roadmap_inteligente(domains: Dict[str, Any]) -> Dict[str, Any]:
    """Genera un roadmap inteligente considerando dependencias entre dominios"""
    # Ordenar dominios por prioridad y dependencias
    dominios_criticos = [d for d in domains.values() if d.get("prioridad") == "P1" and d.get("severidad") in ["Crítico", "Alto"]]
    
    # Construir orden sugerido basado en dependencias
    orden_implementacion = []
    dominios_procesados = set()
    
    def puede_procesar(dom_key: str) -> bool:
        """Verifica si un dominio puede procesarse (sus dependencias ya están procesadas)"""
        deps = DOMAIN_DEPENDENCIES.get(dom_key, [])
        return all(dep in dominios_procesados for dep in deps)
    
    # Primero procesar dominios críticos
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
        
        if not encontrado:
            # Si hay un ciclo o algo no esperado, agregar el primero restante
            if dominios_restantes:
                orden_implementacion.append(dominios_restantes[0])
                dominios_procesados.add(dominios_restantes[0])
                dominios_restantes.pop(0)
            else:
                break
    
    # Generar fases del roadmap
    fases = {
        "fase_1_30_dias": [],
        "fase_2_60_dias": [],
        "fase_3_90_dias": []
    }
    
    # Distribuir dominios críticos en fases
    for i, dom_key in enumerate(orden_implementacion[:3]):
        if i == 0:
            fases["fase_1_30_dias"].append(dom_key)
        elif i == 1:
            fases["fase_2_60_dias"].append(dom_key)
        else:
            fases["fase_3_90_dias"].append(dom_key)
    
    # Calcular impacto esperado
    impacto_total = sum(d.get("score", 0) for d in domains.values() if d.get("prioridad") == "P1")
    impacto_maximo_posible = len(domains) * 5
    porcentaje_mejora_estimado = min(100, round((impacto_maximo_posible - impacto_total) / impacto_maximo_posible * 100, 1))
    
    return {
        "orden_implementacion": orden_implementacion,
        "fases": fases,
        "ruta_critica": orden_implementacion[:3],  # Primeros 3 dominios críticos
        "tiempo_estimado": f"{len(orden_implementacion) * 30} días",
        "impacto_esperado": f"{porcentaje_mejora_estimado}% de mejora en score total",
        "dominios_bloqueantes": [d for d in orden_implementacion[:2] if d in DOMAIN_DEPENDENCIES and DOMAIN_DEPENDENCIES[d]]
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
def _make_llm_prompt(diagnostico_data: Dict[str, Any], domains: Dict[str, Any], roadmap: Dict[str, Any] = None) -> str:
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

    # Contexto de roadmap si está disponible
    contexto_roadmap = ""
    if roadmap:
        ruta_critica = roadmap.get("ruta_critica", [])
        if ruta_critica:
            nombres_ruta = [domains.get(d, {}).get("nombre", d) for d in ruta_critica[:2]]
            contexto_roadmap = f"\n📈 RUTA CRÍTICA SUGERIDA (orden de implementación): {', '.join(nombres_ruta)}. "
            contexto_roadmap += f"Impacto esperado: {roadmap.get('impacto_esperado', 'N/A')}. "
        dominios_bloq = roadmap.get("dominios_bloqueantes", [])
        if dominios_bloq:
            nombres_bloq = [domains.get(d, {}).get("nombre", d) for d in dominios_bloq[:1]]
            contexto_roadmap += f"⚠️ DOMINIOS BLOQUEANTES (priorizar primero): {', '.join(nombres_bloq)}. "

    # Obtener nombre para personalizar
    nombre_usuario = diagnostico_data.get("nombreSolicitante", "").split()[0] if diagnostico_data.get("nombreSolicitante") else ""
    saludo = f"¡{nombre_usuario}! " if nombre_usuario else ""

    instrucciones = (
        "Eres MentHIA, un MENTOR EMPRESARIAL EXPERTO con corazón. "
        "Tu personalidad es CÁLIDA, PROFESIONAL y MOTIVADORA - como un mentor que genuinamente celebra los logros y guía con cariño en las áreas de mejora. "
        "SIEMPRE empieza reconociendo las FORTALEZAS antes de hablar de oportunidades. "
        "Usa emojis con moderación (1-2 por sección) para dar calidez. "
        "Las recomendaciones deben sonar como consejos de un mentor que quiere verte triunfar.\n\n"
        f"{contexto_roadmap}\n\n"
        "Genera un JSON con las claves:\n"
        f"1) analisis_detallado (string): {saludo}Empieza celebrando las fortalezas detectadas. "
        "Luego explica las oportunidades de forma constructiva (no como críticas). "
        "Usa un tono cercano: 'Tu empresa destaca en...', 'Hay una gran oportunidad en...', 'Juntos podemos mejorar...'. "
        "Termina con una frase motivadora.\n"
        "2) oportunidades_estrategicas (string[]): 3-5 oportunidades redactadas de forma POSITIVA. "
        "Usa formato: '💡 [Área]: [Oportunidad emocionante]' en lugar de señalar fallos.\n"
        "3) riesgos_identificados (string[]): 3-5 riesgos redactados como 'áreas a proteger' o 'puntos de atención'. "
        "Evita lenguaje alarmista.\n"
        "4) plan_accion_sugerido (string[]): 4-6 acciones con lenguaje motivador: "
        "'🚀 Te recomiendo...', '💪 Un gran paso sería...', '✨ Podrías explorar...'\n"
        "5) indicadores_clave_rendimiento (string[]): 4-6 KPIs explicados de forma simple y accesible.\n"
        "6) estructura_consultiva (object) con:\n"
        "   - resumen_ejecutivo (string): Celebra fortalezas, menciona oportunidades con entusiasmo. Tono: '¡Excelente trabajo en X! Hay oportunidades emocionantes en Y'.\n"
        "   - tabla_dominios (array)\n"
        "   - dominios (obj por dominio) con: diagnostico (positivo primero), causas_raiz[], recomendaciones_30_60_90{}, kpis[], riesgos[], quick_wins[]\n"
        "7) recomendaciones_innovadoras: 2-4 ideas creativas con emojis motivadores.\n"
        "8) siguiente_paso: El paso más importante, redactado de forma emocionante.\n"
        "9) mensaje_motivacional (nuevo): Frase de cierre positiva (ej: '¡Vas por excelente camino! Cada paso cuenta 🌟').\n"
        "NO agregues texto fuera del JSON. Tono AMIGABLE y MOTIVADOR siempre."
    )

    user_prompt = {
        "contexto": {
            "dominios_activados": resumen_tabla,
            "campos_relevantes": subset,
            "roadmap_sugerido": roadmap.get("orden_implementacion", [])[:3] if roadmap else []
        },
        "instrucciones": instrucciones
    }

    return json.dumps(user_prompt, ensure_ascii=False)

# ---------------------------
# API principal
# ---------------------------
async def analizar_diagnostico_profundo(diagnostico_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Entrada: diagnostico_data (dict) con las claves del formulario TSX.
    Salida: objeto con analisis_detallado, oportunidades_estrategicas[],
            riesgos_identificados[], plan_accion_sugerido[], indicadores_clave_rendimiento[],
            y estructura_consultiva (resumen_ejecutivo, tabla_dominios, dominios{...}).
    """
    domains = _compute_domains(diagnostico_data)

    # Generar roadmap inteligente
    roadmap = _generar_roadmap_inteligente(domains)
    
    # Modo DEMO si no hay API key
    if not OPENAI_API_KEY or not client:
        demo_struct = _build_rule_based_structure(domains)
        resultado = _sanitize_output({**_DEMO_TOP, "estructura_consultiva": demo_struct}, domains)
        resultado["roadmap_inteligente"] = roadmap
        return resultado

    try:
        prompt = _make_llm_prompt(diagnostico_data, domains, roadmap)

        def _call():
            comp = client.chat.completions.create(
                model=MODEL_NAME,
                messages=[
                    {"role": "system", "content": "Responde únicamente con JSON válido siguiendo las instrucciones."},
                    {"role": "user", "content": prompt},
                ],
                response_format={"type": "json_object"},
                temperature=0.3,  # Un poco más alto para más creatividad
            )
            return comp

        completion = await asyncio.to_thread(_call)
        content = completion.choices[0].message.content or "{}"
        parsed = json.loads(content)
        resultado = _sanitize_output(parsed, domains)
        
        # Enriquecer con roadmap inteligente
        resultado["roadmap_inteligente"] = roadmap
        
        # Agregar recomendaciones basadas en roadmap si no vienen del LLM
        if not resultado.get("recomendaciones_innovadoras"):
            recomendaciones_roadmap = []
            if roadmap.get("dominios_bloqueantes"):
                bloq = roadmap["dominios_bloqueantes"][0]
                nombre_bloq = domains.get(bloq, {}).get("nombre", bloq)
                recomendaciones_roadmap.append(f"🎯 PRIORIDAD MÁXIMA: {nombre_bloq} es bloqueante. Resuélvelo primero para desbloquear otras mejoras")
            
            if roadmap.get("ruta_critica"):
                rutas = ", ".join([domains.get(d, {}).get("nombre", d) for d in roadmap["ruta_critica"][:2]])
                recomendaciones_roadmap.append(f"📈 RUTA CRÍTICA: Enfócate en {rutas} para máximo impacto en {roadmap.get('tiempo_estimado', '90 días')}")
            
            if roadmap.get("impacto_esperado"):
                recomendaciones_roadmap.append(f"🚀 POTENCIAL: {roadmap['impacto_esperado']} siguiendo el roadmap sugerido")
            
            if recomendaciones_roadmap:
                resultado["recomendaciones_innovadoras"] = recomendaciones_roadmap
        
        if not resultado.get("siguiente_paso") and roadmap.get("orden_implementacion"):
            primer_dom = roadmap["orden_implementacion"][0]
            nombre_primer = domains.get(primer_dom, {}).get("nombre", primer_dom)
            resultado["siguiente_paso"] = f"Inicia con {nombre_primer} (Fase 1 - 30 días). Es la base para desbloquear otras mejoras."
        
        return resultado

    except Exception as e:
        logger.exception("OpenAI error en analizar_diagnostico_profundo")
        if DEMO_ON_ERROR:
            demo_struct = _build_rule_based_structure(domains)
            demo = {
                **_DEMO_TOP,
                "analisis_detallado": f"[DEMO POR ERROR: {type(e).__name__}] " + _DEMO_TOP["analisis_detallado"],
                "estructura_consultiva": demo_struct,
            }
            resultado = _sanitize_output(demo, domains)
            resultado["roadmap_inteligente"] = roadmap
            return resultado
        raise HTTPException(status_code=502, detail=f"Fallo con OpenAI ({MODEL_NAME}): {e}")
