"""POST /api/diagnostico/recupera-express/analyze — R.E.C.U.P.E.R.A.™ Express (abierto)."""

from __future__ import annotations

import json
from typing import Any

from fastapi import APIRouter
from pydantic import BaseModel, Field

from app.llm_anthropic import call_claude_json

router = APIRouter(tags=["recupera-express"])


class RecuperaExpressBody(BaseModel):
    userId: str = ""
    nombreEmpresa: str = ""
    sector: str = ""
    numeroEmpleados: int = 0
    nombreSolicitante: str = ""
    correoElectronico: str = ""
    respuestas: dict[str, str] = Field(default_factory=dict)


SYSTEM = """Eres consultor senior PyME México, método R.E.C.U.P.E.R.A.™ (Radiografía, fugas, control, utilidad, política comercial, eficiencia, reestructura, aceleración).
Tienes respuestas ABIERTAS del diagnóstico express R.E.C.U.P.E.R.A. (flujo, inventario, rentabilidad, control + datos empresa).
Responde SOLO JSON válido (sin markdown) con la MISMA forma que el diagnóstico express MentHIA:
{
  "resumen_ejecutivo": "string",
  "recomendacion_general": "string",
  "insight_critico": "string",
  "diagnostico_estrategico": "string largo",
  "indice_menthia_0_100": 0-100,
  "nivel_madurez": "muy_bajo|bajo|medio|alto|muy_alto",
  "capa1_percentil": "string",
  "capa2_indice": número,
  "capa2_diagnostico": "string",
  "detalle_secciones": [
    {"nombre": "Flujo (liquidez)", "prefijo": "FL", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Inventario", "prefijo": "INV", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Rentabilidad", "prefijo": "REN", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0},
    {"nombre": "Control", "prefijo": "CTL", "calificacion": 0-100, "clasificacion": "string", "valor_numerico": 0}
  ],
  "acciones_prioritarias": [{"titulo": "", "descripcion": "", "prioridad": "Alta|Media|Baja", "quick_win": ""}],
  "recomendaciones_por_area": [{"area": "", "calificacion": 0, "diagnostico": "", "prioridad": ""}],
  "kpi_sugerido": "string",
  "siguiente_paso": "string",
  "nivel_desorden": "ALTO|MEDIO|BAJO",
  "dinero_potencial_texto": "ej. rango o narrativa sin inventar cifras exactas si no hay números",
  "riesgos_detectados": ["flujo", "inventario", "rentabilidad"]
}
Inferir nivel_desorden y riesgos_detectados desde el texto. Si no hay montos, dinero_potencial_texto cualitativo (sin MXN inventados).
Contexto: PyMEs México; menciona contrastar con prácticas sectoriales y datos públicos (INEGI, Economía) solo como recomendación de fuente, sin cifras macro inventadas."""


def _fallback(body: RecuperaExpressBody) -> dict[str, Any]:
    r = body.respuestas
    blob = " ".join(str(v) for v in r.values())[:2000].lower()
    idx = 42
    if any(x in blob for x in ["quiebra", "crisis", "no alcanza", "no pago", "deuda"]):
        idx = 28
    elif any(x in blob for x in ["orden", "control", "kpi", "sistema"]):
        idx = 68
    nd = "ALTO" if idx < 38 else "MEDIO" if idx < 58 else "BAJO"
    risks = []
    if any(x in blob for x in ["cobrar", "flujo", "caja", "liquidez", "pagar"]):
        risks.append("flujo")
    if any(x in blob for x in ["inventario", "stock", "almacén"]):
        risks.append("inventario")
    if any(x in blob for x in ["margen", "rentab", "descuento", "cliente"]):
        risks.append("rentabilidad")
    if not risks:
        risks = ["flujo", "control"]
    return {
        "resumen_ejecutivo": f"Diagnóstico R.E.C.U.P.E.R.A.™ Express para {body.nombreEmpresa or 'la empresa'}: priorizar claridad de liquidez, inventario y márgenes.",
        "recomendacion_general": "Agenda revisión 90 min con plan 30-60-90 días en flujo, inventario y tablero de control.",
        "insight_critico": "Cuando no hay claridad semanal de caja, las decisiones suelen ser reactivas y caras.",
        "diagnostico_estrategico": json.dumps(r, ensure_ascii=False)[:4000],
        "indice_menthia_0_100": idx,
        "nivel_madurez": "bajo" if idx < 40 else "medio" if idx < 60 else "alto",
        "capa1_percentil": f"Desorden operativo percibido: {nd}",
        "capa2_indice": idx,
        "capa2_diagnostico": "Perfil express R.E.C.U.P.E.R.A. (cualitativo).",
        "detalle_secciones": [
            {"nombre": "Flujo (liquidez)", "prefijo": "FL", "calificacion": idx, "clasificacion": "Express", "valor_numerico": 0},
            {"nombre": "Inventario", "prefijo": "INV", "calificacion": idx, "clasificacion": "Express", "valor_numerico": 0},
            {"nombre": "Rentabilidad", "prefijo": "REN", "calificacion": idx, "clasificacion": "Express", "valor_numerico": 0},
            {"nombre": "Control", "prefijo": "CTL", "calificacion": idx, "clasificacion": "Express", "valor_numerico": 0},
        ],
        "acciones_prioritarias": [
            {
                "titulo": "Claridad de flujo semanal",
                "descripcion": "Proyección simple cobros vs pagos próximas 8 semanas.",
                "prioridad": "Alta",
                "quick_win": "7 días",
            }
        ],
        "recomendaciones_por_area": [
            {"area": "Flujo (liquidez)", "calificacion": idx, "diagnostico": "Ver respuestas abiertas.", "prioridad": "Alta"}
        ],
        "kpi_sugerido": "Saldo de caja proyectado a 6 semanas",
        "siguiente_paso": "Validar números con estados y bancos; repetir express en 30 días.",
        "nivel_desorden": nd,
        "dinero_potencial_texto": "Cuantificar en fase profesional con datos de cartera e inventario.",
        "riesgos_detectados": risks,
        "tipo": "recupera-express",
    }


@router.post("/analyze")
def analyze_recupera_express(body: RecuperaExpressBody) -> dict[str, Any]:
    user = json.dumps(
        {
            "empresa": body.nombreEmpresa,
            "sector": body.sector,
            "empleados": body.numeroEmpleados,
            "contacto": body.nombreSolicitante,
            "respuestas": body.respuestas,
        },
        ensure_ascii=False,
    )
    llm = call_claude_json(SYSTEM, user)
    if not llm or not (llm.get("resumen_ejecutivo") or llm.get("recomendacion_general")):
        llm = _fallback(body)
    else:
        llm = {**llm, "tipo": "recupera-express"}
    if "tipo" not in llm:
        llm["tipo"] = "recupera-express"
    return llm
