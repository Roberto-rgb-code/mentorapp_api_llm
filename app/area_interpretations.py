"""Interpretaciones por área para diagnósticos express / general (evita plantillas genéricas)."""

from __future__ import annotations

from typing import Any, Dict, List, Optional

GENERIC_PATTERNS = (
    "ajustar prácticas y controles",
    "define 1-2 acciones medibles",
    "prioriza el indicador más sensible",
    "acción sugerida: prioriza en",
    "acción concreta: prioriza una mejora medible",
    "nivel bueno: ajustar",
    "nivel promedio: ajustar",
)

SECCION_DESC: Dict[str, Dict[str, str]] = {
    "Estrategia": {
        "debil": "La empresa carece de un rumbo estratégico claro. Las decisiones se toman de manera reactiva y no existe una visión documentada que guíe el crecimiento, lo que genera desalineación entre áreas.",
        "medio": "Hay dirección general, pero la estrategia no está formalizada ni se traduce en metas medibles. El seguimiento de objetivos es esporádico y depende de pocas personas.",
        "fuerte": "La empresa muestra claridad estratégica y alineación. Los objetivos se monitorean y existe un proceso de planeación que orienta decisiones de inversión y crecimiento.",
        "rec_debil": "Documenta misión, visión y 3 objetivos trimestrales. Instala una reunión mensual de 60 minutos solo para revisar avance vs. metas y responsables.",
        "rec_medio": "Formaliza OKRs o un tablero trimestral compartido con el equipo. Define un dueño por objetivo y evidencia mínima de avance cada mes.",
        "rec_fuerte": "Profundiza en innovación y gobierno: evalúa un consejo asesor externo o una sesión de planeación anual con escenarios (optimista/base/conservador).",
    },
    "Finanzas": {
        "debil": "La gestión financiera es informal: no hay visibilidad confiable de utilidad, flujo o márgenes. Esto expone a crisis de liquidez y dificulta cualquier conversación con bancos o inversionistas.",
        "medio": "Existe control básico (ingresos vs. gastos), pero faltan presupuesto, proyección de caja y análisis de rentabilidad por producto o línea de negocio.",
        "fuerte": "Hay disciplina financiera: presupuesto, reportes periódicos y uso de estados para decidir. La empresa puede sostener crecimiento con menor riesgo de sorpresas de caja.",
        "rec_debil": "Separa finanzas personales y del negocio. Implementa flujo de caja semanal (cobros, pagos, saldo a 6 semanas) y presupuesto mensual revisado quincenalmente.",
        "rec_medio": "Calcula margen por producto/servicio principal y DSO (días de cobranza). Proyecta caja a 90 días y define un tope de gasto discrecional.",
        "rec_fuerte": "Optimiza estructura de capital y prepara un paquete bancario (EEFF, flujo, explicación de uso de recursos). Simula escenarios de inversión antes de comprometer deuda.",
    },
    "Marketing y Ventas": {
        "debil": "No hay proceso comercial estructurado ni medición del embudo. La demanda depende del boca a boca y no se sabe qué canal o mensaje realmente convierte.",
        "medio": "Hay acciones comerciales y presencia básica, pero falta CRM, segmentación y seguimiento sistemático de prospectos y ticket promedio.",
        "fuerte": "El embudo comercial está definido, se mide conversión por etapa y hay estrategia multicanal con foco en clientes rentables.",
        "rec_debil": "Mapea el proceso de venta en 4 etapas, registra prospectos en una hoja/CRM y define 1 canal prioritario (referidos, digital o visitas) con meta semanal.",
        "rec_medio": "Implementa CRM, mide conversión por etapa y costo de adquisición aproximado. Ajusta descuentos/precios según margen real, no solo volumen.",
        "rec_fuerte": "Escala con segmentación avanzada, programa de referidos y playbooks de venta por tipo de cliente. Prueba nuevos canales con experimentos acotados de 30 días.",
    },
    "Operaciones": {
        "debil": "Los procesos no están documentados y la operación depende de personas clave. La inconsistencia en entregas limita calidad, márgenes y capacidad de escalar.",
        "medio": "Algunos procesos están claros informalmente, pero faltan estándares, checklists y KPIs operativos por área.",
        "fuerte": "Operación documentada con estándares de calidad y medición de productividad. Hay base para replicar o crecer sin colapsar el servicio.",
        "rec_debil": "Documenta los 3 procesos que más impactan al cliente. Crea checklists y tiempos estándar; asigna un responsable por proceso.",
        "rec_medio": "Define KPIs operativos (tiempo de entrega, retrabajo, % cumplimiento) y revisa semanalmente. Automatiza tareas repetitivas con herramientas simples.",
        "rec_fuerte": "Formaliza mejora continua (Lean básico) y capacidad instalada vs. demanda. Prepara la operación para duplicar volumen sin duplicar caos.",
    },
    "Talento": {
        "debil": "No hay procesos formales de reclutamiento, capacitación ni evaluación. La retención es frágil y el crecimiento depende demasiado del fundador.",
        "medio": "Existen prácticas básicas de contratación y capacitación, pero sin plan de desarrollo ni evaluación periódica estructurada.",
        "fuerte": "El talento se gestiona con roles claros, desarrollo y cultura definida. La empresa puede delegar sin perder calidad.",
        "rec_debil": "Define perfiles de puesto para roles críticos, reuniones 1:1 quincenales y un plan mínimo de capacitación de 90 días.",
        "rec_medio": "Implementa evaluaciones semestrales con plan de desarrollo individual y onboarding estandarizado para nuevas contrataciones.",
        "rec_fuerte": "Diseña planes de carrera, sucesión en puestos clave y encuestas de clima para anticipar rotación.",
    },
    "Tecnología": {
        "debil": "La operación es mayormente manual; sistemas desconectados o inexistentes. Se pierde tiempo en retrabajo y no hay respaldo confiable de información crítica.",
        "medio": "Hay herramientas digitales básicas, pero no integradas. La adopción es parcial y los datos viven en silos.",
        "fuerte": "Infraestructura y herramientas alineadas al negocio, con automatización de procesos repetitivos y foco en datos para decidir.",
        "rec_debil": "Migra a suite en la nube, respaldos automáticos y un inventario de sistemas (qué usa cada área y para qué).",
        "rec_medio": "Integra ventas/contabilidad/operación donde sea posible. Automatiza reportes recurrentes y define políticas básicas de accesos.",
        "rec_fuerte": "Evalúa automatización avanzada e IA aplicada a tareas concretas (cobranza, inventario, atención). Refuerza ciberseguridad y continuidad operativa.",
    },
    "Escalabilidad": {
        "debil": "No hay plan de crecimiento ni procesos estandarizados que permitan escalar. El modelo actual depende del esfuerzo heroico del dueño.",
        "medio": "Hay ambición de crecer, pero faltan business plan, financiamiento alineado y procesos replicables antes de acelerar.",
        "fuerte": "La empresa tiene plan formal, procesos estandarizados y capacidad de acceder a capital o alianzas para crecer con orden.",
        "rec_debil": "Construye un plan de 12 meses con 3 metas concretas, identifica cuellos de botella antes de vender más y valida unit economics.",
        "rec_medio": "Desarrolla business plan con escenarios de ingresos y necesidad de capital. Estandariza procesos core antes de abrir nuevos mercados.",
        "rec_fuerte": "Explora expansión geográfica o nuevos segmentos con pilotos acotados. Prepara pitch y métricas para inversionistas o banca.",
    },
}


def is_generic_text(text: str) -> bool:
    t = (text or "").strip().lower()
    if len(t) < 20:
        return True
    return any(p in t for p in GENERIC_PATTERNS)


def prioridad_from_score(score: float) -> str:
    if score < 25:
        return "Crítica"
    if score < 50:
        return "Alta"
    if score < 75:
        return "Media"
    return "Baja"


def _nivel_key(score: float) -> str:
    if score < 40:
        return "debil"
    if score < 65:
        return "medio"
    return "fuerte"


def _ceo_context(ceo: Optional[Dict[str, str]]) -> Dict[str, str]:
    if not ceo:
        return {}
    return {
        "reto": (ceo.get("reto") or ceo.get("qt1") or "").strip(),
        "fortaleza": (ceo.get("fortaleza") or ceo.get("qt2") or "").strip(),
        "vision": (ceo.get("vision") or ceo.get("qt3") or "").strip(),
    }


def build_area_interpretation(
    area: str,
    score: float,
    clasificacion: str = "",
    ceo: Optional[Dict[str, str]] = None,
    *,
    is_weakest: bool = False,
    is_strongest: bool = False,
) -> Dict[str, str]:
    desc = SECCION_DESC.get(area, {})
    nk = _nivel_key(score)
    diag = desc.get(nk) or (
        f"{area} se ubica en nivel {clasificacion or nk} ({score}/100). "
        f"Conviene traducir el puntaje en 1-2 decisiones concretas esta semana."
    )
    reco = desc.get(f"rec_{nk}") or (
        f"En {area}, elige una métrica única (ej. cumplimiento, margen o conversión) "
        "y revísala cada viernes con el responsable asignado."
    )

    ctx = _ceo_context(ceo)
    if is_weakest and ctx.get("reto"):
        snippet = ctx["reto"][:110] + ("…" if len(ctx["reto"]) > 110 else "")
        diag = (
            f"{diag} Lo que compartiste como reto principal («{snippet}») encaja con una brecha "
            f"en {area}; atacar esta área primero suele destrabar el resto."
        )
    elif is_strongest and ctx.get("fortaleza"):
        snippet = ctx["fortaleza"][:90] + ("…" if len(ctx["fortaleza"]) > 90 else "")
        diag = (
            f"{diag} Tu fortaleza declarada («{snippet}») puede usarse como palanca "
            f"para mejorar otras áreas sin empezar desde cero."
        )
    elif ctx.get("vision") and area == "Estrategia":
        snippet = ctx["vision"][:90] + ("…" if len(ctx["vision"]) > 90 else "")
        diag = f"{diag} Tu visión a 12 meses («{snippet}») debe convertirse en 3 prioridades trimestrales medibles."

    return {
        "diagnostico": diag,
        "recomendacion": reco,
        "prioridad": prioridad_from_score(score),
    }


def enrich_recomendaciones_por_area(
    detalle_secciones: List[Dict[str, Any]],
    recos: Optional[List[Dict[str, Any]]],
    ceo: Optional[Dict[str, str]] = None,
) -> List[Dict[str, Any]]:
    """Reemplaza textos genéricos o vacíos con interpretaciones contextuales por score."""
    det_by_name = {str(d.get("nombre") or ""): d for d in detalle_secciones}
    reco_by_area = {
        str(r.get("area") or ""): r for r in (recos or []) if isinstance(r, dict)
    }

    if detalle_secciones:
        weakest = min(detalle_secciones, key=lambda x: float(x.get("calificacion") or 0))
        strongest = max(detalle_secciones, key=lambda x: float(x.get("calificacion") or 0))
        weak_name = str(weakest.get("nombre") or "")
        strong_name = str(strongest.get("nombre") or "")
    else:
        weak_name = strong_name = ""

    out: List[Dict[str, Any]] = []
    areas_order = [str(d.get("nombre") or "") for d in detalle_secciones]
    if not areas_order:
        areas_order = list(SECCION_DESC.keys())

    for area in areas_order:
        det = det_by_name.get(area, {})
        score = float(reco_by_area.get(area, {}).get("calificacion") or det.get("calificacion") or 0)
        clasif = str(det.get("clasificacion") or "")
        existing = reco_by_area.get(area, {})

        diag = str(existing.get("diagnostico") or "").strip()
        rec = str(existing.get("recomendacion") or "").strip()

        if is_generic_text(diag) or is_generic_text(rec) or not diag or not rec or rec == diag:
            built = build_area_interpretation(
                area,
                score,
                clasif,
                ceo,
                is_weakest=(area == weak_name),
                is_strongest=(area == strong_name),
            )
            diag = built["diagnostico"]
            rec = built["recomendacion"]
            prio = built["prioridad"]
        else:
            prio = str(existing.get("prioridad") or prioridad_from_score(score))

        out.append(
            {
                "area": area,
                "calificacion": score,
                "diagnostico": diag,
                "recomendacion": rec,
                "prioridad": prio,
            }
        )

    return out
