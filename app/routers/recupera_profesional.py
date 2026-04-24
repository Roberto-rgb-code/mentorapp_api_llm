"""POST /api/diagnostico/recupera-profesional/analyze"""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm_anthropic import call_claude_json
from app.recupera_engine import ProfesionalInputs, compute_recupera_profesional, metrics_to_dict

router = APIRouter(tags=["recupera-profesional"])


class ProfesionalBody(BaseModel):
    userId: str = ""
    nombreEmpresa: str = ""
    sector: str = ""
    numeroEmpleados: int = 0
    nombreSolicitante: str = ""
    correoElectronico: str = ""
    inputs: dict[str, Any] = Field(default_factory=dict)


SYSTEM = """Eres consultor senior en rescate financiero de PyMEs en México (comercio y distribución).
Recibes métricas ya calculadas del método R.E.C.U.P.E.R.A.™ Profesional.
Debes responder SOLO un JSON válido (sin markdown) con esta forma exacta:
{
  "resumen_ejecutivo": "string 3-6 frases, tono directo, impacto en dinero",
  "recomendacion_general": "string con prioridades para consultor y cliente",
  "insight_critico": "una verdad incómoda breve",
  "diagnostico_estrategico": "string más largo: flujo, inventario, rentabilidad, control",
  "indice_menthia_0_100": número entero 0-100 alineado al riesgo global,
  "nivel_madurez": "muy_bajo|bajo|medio|alto|muy_alto",
  "capa1_percentil": "string corta tipo percentil o banda",
  "capa2_indice": número,
  "capa2_diagnostico": "string",
  "detalle_secciones": [
    {"nombre": "Flujo de efectivo", "prefijo": "FL", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Inventarios", "prefijo": "INV", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Rentabilidad", "prefijo": "REN", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Control financiero", "prefijo": "CTL", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0}
  ],
  "acciones_prioritarias": [
    {"titulo": "string", "descripcion": "string", "prioridad": "Alta|Media|Baja", "quick_win": "string"}
  ],
  "recomendaciones_por_area": [
    {"area": "Flujo de efectivo", "calificacion": 0-100, "diagnostico": "string", "prioridad": "Alta|Media|Baja"}
  ],
  "kpi_sugerido": "string",
  "siguiente_paso": "string"
}
Usa los estados rojo/amarillo/verde de las métricas para calificaciones (rojo≈20-35, amarillo≈45-60, verde≈75-90).
Contexto país México: cita de forma genérica riesgos típicos de PyME (liquidez, cartera, inventario) sin inventar cifras macro; puedes mencionar que conviene contrastar con fuentes oficiales (INEGI, Secretaría de Economía) para el sector.
No inventes números que contradigan el JSON de métricas entrante."""


def _fallback_llm_payload(metrics: dict, body: ProfesionalBody) -> dict[str, Any]:
    m = metrics
    sev = m.get("estadoFlujo", "verde")
    cal_fl = 30 if sev == "rojo" else 52 if sev == "amarillo" else 82
    sev_i = m.get("estadoInventario", "verde")
    cal_i = 30 if sev_i == "rojo" else 52 if sev_i == "amarillo" else 82
    sev_r = m.get("estadoRentabilidad", "verde")
    cal_r = 30 if sev_r == "rojo" else 52 if sev_r == "amarillo" else 82
    sev_c = m.get("estadoControl", "verde")
    cal_c = 30 if sev_c == "rojo" else 52 if sev_c == "amarillo" else 82
    idx = int(m.get("indiceSalud0_100") or 50)
    dr = float(m.get("dineroRecuperableEstimado") or 0)
    resumen = (
        f"Radiografía R.E.C.U.P.E.R.A.™: ciclo de caja aprox. {m.get('cicloCaja', 0):.0f} días; "
        f"dinero recuperable estimado ${dr:,.0f} (orden de magnitud operativa). "
        "Los semáforos indican dónde actuar primero."
    )
    return {
        "resumen_ejecutivo": resumen,
        "recomendacion_general": "Prioriza liberar efectivo (cartera, inventario, términos de pago) y refuerza control con KPIs mensuales.",
        "insight_critico": "Sin datos de flujo e inventario alineados, el crecimiento suele consumir caja aunque suban las ventas.",
        "diagnostico_estrategico": json.dumps(metrics, ensure_ascii=False)[:3500],
        "indice_menthia_0_100": idx,
        "nivel_madurez": "bajo" if idx < 45 else "medio" if idx < 70 else "alto",
        "capa1_percentil": f"Salud sintética ~{idx}/100",
        "capa2_indice": idx,
        "capa2_diagnostico": "Mapa operativo de fugas y capital atrapado.",
        "detalle_secciones": [
            {
                "nombre": "Flujo de efectivo",
                "prefijo": "FL",
                "calificacion": cal_fl,
                "clasificacion": "Crítico" if sev == "rojo" else "Atención" if sev == "amarillo" else "Controlado",
                "valor_numerico": float(m.get("cicloCaja") or 0),
            },
            {
                "nombre": "Inventarios",
                "prefijo": "INV",
                "calificacion": cal_i,
                "clasificacion": "Crítico" if sev_i == "rojo" else "Atención" if sev_i == "amarillo" else "Controlado",
                "valor_numerico": float(m.get("diasInventarioAnual") or 0),
            },
            {
                "nombre": "Rentabilidad",
                "prefijo": "REN",
                "calificacion": cal_r,
                "clasificacion": "Crítico" if sev_r == "rojo" else "Atención" if sev_r == "amarillo" else "Controlado",
                "valor_numerico": float(m.get("margenBruto") or 0),
            },
            {
                "nombre": "Control financiero",
                "prefijo": "CTL",
                "calificacion": cal_c,
                "clasificacion": "Crítico" if sev_c == "rojo" else "Atención" if sev_c == "amarillo" else "Controlado",
                "valor_numerico": float(m.get("scoreControl") or 0),
            },
        ],
        "acciones_prioritarias": [
            {
                "titulo": "Acortar ciclo de caja",
                "descripcion": "Cartera, inventario y días de proveedor: negociar términos y depurar stock lento.",
                "prioridad": "Alta",
                "quick_win": "0-30 días",
            },
            {
                "titulo": "Tablero semanal de liquidez",
                "descripcion": "Proyección 8-13 semanas con cobros, pagos e inventario.",
                "prioridad": "Alta",
                "quick_win": "7 días",
            },
        ],
        "recomendaciones_por_area": [
            {
                "area": "Flujo de efectivo",
                "calificacion": cal_fl,
                "diagnostico": f"Ciclo de caja {m.get('cicloCaja', 0):.0f} días; estado {sev}.",
                "prioridad": "Alta" if sev == "rojo" else "Media",
            },
            {
                "area": "Inventarios",
                "calificacion": cal_i,
                "diagnostico": f"Días inventario ~{m.get('diasInventarioAnual', 0):.0f}; exceso estimado ${float(m.get('excesoInventario') or 0):,.0f}.",
                "prioridad": "Alta" if sev_i == "rojo" else "Media",
            },
        ],
        "kpi_sugerido": "Días de inventario y ciclo de caja (semanal)",
        "siguiente_paso": "Reunión de 90 minutos para validar datos y cerrar plan 30-60-90 días.",
    }


@router.post("/analyze")
def analyze_recupera_profesional(body: ProfesionalBody) -> dict[str, Any]:
    inputs_cast: ProfesionalInputs = body.inputs  # type: ignore[assignment]
    met = compute_recupera_profesional(inputs_cast)
    metrics = metrics_to_dict(met)

    user = json.dumps(
        {
            "empresa": body.nombreEmpresa,
            "sector": body.sector,
            "empleados": body.numeroEmpleados,
            "metricas": metrics,
        },
        ensure_ascii=False,
    )

    llm = call_claude_json(SYSTEM, user)
    if not llm or not (llm.get("resumen_ejecutivo") or llm.get("recomendacion_general")):
        llm = _fallback_llm_payload(metrics, body)

    out = {**llm, "recupera_metricas": metrics, "tipo": "recupera-profesional"}
    return out
