# app/llm_express.py
# MENTHIA Express — 12 preguntas cerradas + 3 textos | 7 áreas | 2 capas | Anthropic

import json
import os
from datetime import datetime
from typing import Any, Dict, List, Tuple

from anthropic import Anthropic
from dotenv import load_dotenv
from fastapi import HTTPException

from app.area_interpretations import enrich_recomendaciones_por_area

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-sonnet-4-20250514").strip().strip('"').strip("'")

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

S15 = [0, 25, 50, 75, 100]
L15 = list("ABCDE")
AREA_ORDER = ["es", "fi", "mk", "op", "ta", "te", "ec"]
AREA_NAMES = {
    "es": "Estrategia",
    "fi": "Finanzas",
    "mk": "Marketing y Ventas",
    "op": "Operaciones",
    "ta": "Talento",
    "te": "Tecnología",
    "ec": "Escalabilidad",
}

# (question_id, area) — solo cerradas
QUESTION_MC: List[Tuple[str, str]] = [
    ("q1", "es"),
    ("q2", "es"),
    ("q3", "fi"),
    ("q4", "fi"),
    ("q5", "op"),
    ("q6", "op"),
    ("q7", "mk"),
    ("q8", "mk"),
    ("q9", "ta"),
    ("q10", "ta"),
    ("q11", "te"),
    ("q12", "ec"),
]

PCTL: Dict[str, List[int]] = {
    "Servicios|Micro": [36, 50, 70],
    "Servicios|Pequeña": [40, 55, 75],
    "Servicios|Mediana": [45, 60, 78],
    "Servicios|Grande": [50, 65, 80],
    "Comercio|Micro": [34, 49, 69],
    "Comercio|Pequeña": [38, 52, 72],
    "Comercio|Mediana": [42, 58, 76],
    "Comercio|Grande": [48, 64, 82],
    "Tecnología|Micro": [40, 54, 72],
    "Tecnología|Pequeña": [42, 56, 74],
    "Tecnología|Mediana": [46, 62, 79],
    "Tecnología|Grande": [50, 66, 82],
    "Agroindustria|Micro": [35, 50, 70],
    "Agroindustria|Pequeña": [38, 53, 72],
    "Agroindustria|Mediana": [42, 58, 76],
    "Agroindustria|Grande": [48, 64, 80],
    "Industria|Micro": [38, 53, 73],
    "Industria|Pequeña": [40, 55, 74],
    "Industria|Mediana": [44, 60, 78],
    "Industria|Grande": [50, 65, 82],
}


def _tamano_empresa(n_emp: Any) -> str:
    if n_emp is None:
        return "Micro"
    try:
        n = int(n_emp)
    except (TypeError, ValueError):
        return "Micro"
    if n <= 10:
        return "Micro"
    if n <= 50:
        return "Pequeña"
    if n <= 250:
        return "Mediana"
    return "Grande"


def _clas_area(c: float) -> str:
    if c < 25:
        return "Deficiente"
    if c < 50:
        return "Promedio"
    if c < 75:
        return "Bueno"
    return "Líder"


def _valor_numerico(cl: str) -> int:
    return {"Deficiente": 0, "Promedio": 1, "Bueno": 2, "Líder": 3}.get(cl, 0)


def _mc_index(raw: Any) -> int:
    if raw is None:
        raise ValueError("respuesta faltante")
    if isinstance(raw, int):
        if 0 <= raw <= 4:
            return raw
        if 1 <= raw <= 5:
            return raw - 1
    s = str(raw).strip().upper()
    if s in ("0", "1", "2", "3", "4"):
        return int(s)
    if s in ("A", "B", "C", "D", "E"):
        return ord(s) - ord("A")
    if s in ("1", "2", "3", "4", "5") and len(s) == 1:
        return int(s) - 1
    raise ValueError(f"índice de opción inválido: {raw!r}")


def calcular_express(data: Dict[str, Any]) -> Dict[str, Any]:
    sector = str(data.get("sector") or "Servicios").strip()
    if sector not in (
        "Servicios",
        "Comercio",
        "Tecnología",
        "Agroindustria",
        "Industria",
    ):
        sector = "Servicios"

    empresa = str(data.get("nombreEmpresa") or data.get("empresa") or "Mi Empresa").strip() or "Mi Empresa"
    sol = str(data.get("nombreSolicitante") or data.get("solicitante") or "").strip()
    puesto = str(data.get("puesto") or "").strip()
    antiguedad = str(data.get("antiguedadEmpresa") or data.get("antiguedad_empresa") or "").strip()
    emps = int(data.get("numeroEmpleados") or data.get("empleados") or 1)
    tam = _tamano_empresa(emps)

    resp = data.get("respuestas") or {}
    if not isinstance(resp, dict):
        resp = {}

    by_area: Dict[str, List[float]] = {a: [] for a in AREA_ORDER}
    for qid, area in QUESTION_MC:
        if qid not in resp:
            raise HTTPException(400, f"Falta respuesta: {qid}")
        idx = _mc_index(resp.get(qid))
        by_area[area].append(float(S15[idx]))

    det: List[Dict[str, Any]] = []
    for area in AREA_ORDER:
        vals = by_area[area]
        if not vals:
            cal = 0.0
        else:
            cal = round(sum(vals) / len(vals), 2)
        cl = _clas_area(cal)
        det.append(
            {
                "nombre": AREA_NAMES[area],
                "prefijo": area.upper(),
                "calificacion": cal,
                "clasificacion": cl,
                "valor_numerico": _valor_numerico(cl),
            }
        )

    # Una sola pregunta MC en Tecnología puede dejar el área en 0; evitamos 0 por interpretabilidad del reporte.
    for i, d in enumerate(det):
        if d["nombre"] == "Tecnología" and float(d["calificacion"]) <= 0:
            cal_f = 12.5
            cl_f = _clas_area(cal_f)
            det[i] = {
                **d,
                "calificacion": cal_f,
                "clasificacion": cl_f,
                "valor_numerico": _valor_numerico(cl_f),
            }

    idx = round(sum(d["calificacion"] for d in det) / len(det), 2)
    pt = PCTL.get(f"{sector}|{tam}") or [36, 50, 70]
    if idx <= pt[0]:
        c1 = "Deficiente"
    elif idx <= pt[1]:
        c1 = "Promedio"
    elif idx <= pt[2]:
        c1 = "Bueno"
    else:
        c1 = "Líder"

    vn = [d["valor_numerico"] for d in det]
    c2i = round(sum(vn) / len(vn), 2) if vn else 0.0
    if c2i < 0.5:
        c2d = "Deficiente crítico"
    elif c2i < 1.5:
        c2d = "En el promedio"
    elif c2i < 2.5:
        c2d = "Por encima del promedio"
    else:
        c2d = "Líder de segmento"

    if idx >= 71:
        niv = "muy_alto"
    elif idx >= 51:
        niv = "alto"
    elif idx >= 37:
        niv = "medio"
    elif idx >= 25:
        niv = "bajo"
    else:
        niv = "muy_bajo"

    _meses = (
        "enero",
        "febrero",
        "marzo",
        "abril",
        "mayo",
        "junio",
        "julio",
        "agosto",
        "septiembre",
        "octubre",
        "noviembre",
        "diciembre",
    )
    _now = datetime.now()
    fecha = f"{_now.day} de {_meses[_now.month - 1]} de {_now.year}"

    textos = {
        "qt1": str(resp.get("qt1") or "").strip(),
        "qt2": str(resp.get("qt2") or "").strip(),
        "qt3": str(resp.get("qt3") or "").strip(),
    }
    for tk, tv in textos.items():
        if len(tv) < 4:
            raise HTTPException(400, f"Texto {tk} demasiado corto (mín. 4 caracteres)")

    return {
        "detalle_secciones": det,
        "indice_menthia_0_100": idx,
        "sector": sector,
        "tamano": tam,
        "empresa": empresa,
        "solicitante": sol,
        "empleados": emps,
        "capa1_percentil": c1,
        "capa2_indice": c2i,
        "capa2_diagnostico": c2d,
        "nivel_madurez": niv,
        "fecha": fecha,
        "textos_abiertos": textos,
        "respuestas_mc": {qid: _mc_index(resp[qid]) for qid, _ in QUESTION_MC},
        "puesto": puesto,
        "antiguedad_empresa": antiguedad,
    }


EXPRESS_SYSTEM = """Eres MENTHIA Express, Inteligencia Consultiva nivel McKinsey/BCG para LATAM, modo diagnóstico rápido. Recibes un diagnóstico EXPRESS basado en 12 preguntas + 3 textos abiertos cualitativos del CEO. La empresa fue evaluada algorítmicamente en 7 áreas: Estrategia, Finanzas, Marketing y Ventas, Operaciones, Talento, Tecnología, Escalabilidad. Escala 0-100. Modelo de 2 capas (Capa 1 percentil LATAM, Capa 2 índice global por sección).

Como es EXPRESS, sé MUY conciso pero CONTUNDENTE. Lee los textos abiertos del CEO con atención — ahí está el contexto real del negocio. Cruza los datos cuantitativos con lo que el CEO escribió.

Responde SOLO JSON:
{
"recomendacion_general":"5-7 líneas. El gran insight estratégico cruzando datos numéricos con los textos del CEO. Identifica EL problema central. Conecta lo que dijo el CEO con lo que muestran los datos.",
"resumen_ejecutivo":"3-4 líneas profesionales. Estado actual y mensaje al CEO.",
"insight_critico":"Una frase contundente. La verdad incómoda.",
"acciones_prioritarias":[
  {"titulo":"Acción 1","descripcion":"2-3 líneas accionables","prioridad":"Crítica/Alta/Media/Baja","quick_win":"Acción <14 días"},
  {"titulo":"Acción 2","descripcion":"...","prioridad":"...","quick_win":"..."},
  {"titulo":"Acción 3","descripcion":"...","prioridad":"...","quick_win":"..."}
],
"recomendaciones_por_area":[
  {"area":"Estrategia","calificacion":NUM,"diagnostico":"2-3 líneas ÚNICAS: qué significa el score EN ESTA empresa, citando datos o textos del CEO","recomendacion":"Acción concreta distinta al diagnóstico: qué hacer, quién, plazo 14-30 días, métrica","prioridad":"..."},
  {"area":"Finanzas",...},
  {"area":"Marketing y Ventas",...},
  {"area":"Operaciones",...},
  {"area":"Talento",...},
  {"area":"Tecnología",...},
  {"area":"Escalabilidad",...}
],
"kpi_sugerido":"Un indicador clave",
"siguiente_paso":"Una frase con el paso #1 que debe dar el CEO esta semana"
}

PROHIBIDO (respuesta inválida si aparece):
- Plantillas del tipo "ajustar prácticas y controles en [área]"
- "Define 1-2 acciones medibles..." repetido en todas las áreas
- Copiar el mismo diagnóstico en recomendación
- Frases genéricas que podrían aplicar a cualquier empresa sin mencionar sector, tamaño o textos del CEO

OBLIGATORIO:
- Cada área debe tener diagnóstico y recomendación DIFERENTES entre sí
- Menciona al menos 2 veces en todo el JSON datos concretos de los textos abiertos del CEO (reto, fortaleza, visión)
- En el área más débil, conecta explícitamente con qt1 (reto principal)
- Usa el nombre de la empresa al menos 3 veces

Las acciones_prioritarias deben ser 3, máximo 4. NO incluyas plan de 30 días detallado (esto es express). Sé directo, cero paja motivacional."""


def _build_user_context(calc: Dict[str, Any], resp: Dict[str, Any]) -> str:
    empresa = calc["empresa"]
    sol = calc["solicitante"]
    sector = calc["sector"]
    tam = calc["tamano"]
    emps = calc["empleados"]
    fecha = calc["fecha"]
    textos = calc["textos_abiertos"]

    extra_demo = ""
    if calc.get("puesto") or calc.get("antiguedad_empresa"):
        extra_demo = f"PUESTO: {calc.get('puesto') or '—'}\nANTIGÜEDAD EMPRESA: {calc.get('antiguedad_empresa') or '—'}\n"

    ctx = f"""EMPRESA: {empresa}
SOLICITANTE: {sol}
{extra_demo}SECTOR: {sector} | TAMAÑO: {tam} ({emps} empleados)
FECHA: {fecha}

=== RESULTADOS PRECALCULADOS (escala 0-100) ===
Índice Menthia Express: {calc['indice_menthia_0_100']}/100
Capa 1 (Percentil LATAM {sector}/{tam}): {calc['capa1_percentil']}
Capa 2 (Índice Global): {calc['capa2_indice']}/3.00 → {calc['capa2_diagnostico']}
Nivel de Madurez: {calc['nivel_madurez']}

CALIFICACIONES POR ÁREA:
"""
    for d in calc["detalle_secciones"]:
        ctx += f"  {d['nombre']}: {d['calificacion']}/100 → {d['clasificacion']}\n"

    deb = min(calc["detalle_secciones"], key=lambda x: x["calificacion"])
    fue = max(calc["detalle_secciones"], key=lambda x: x["calificacion"])
    ctx += f"\nÁREA MÁS DÉBIL: {deb['nombre']} ({deb['calificacion']})\n"
    ctx += f"ÁREA MÁS FUERTE: {fue['nombre']} ({fue['calificacion']})\n"

    ctx += f"""
=== CONTEXTO CUALITATIVO DEL CEO (OBLIGATORIO USAR EN CADA ÁREA RELEVANTE) ===
PRINCIPAL RETO ACTUAL (qt1): "{textos.get('qt1', '')}"
MAYOR FORTALEZA (qt2): "{textos.get('qt2', '')}"
VISIÓN A 12 MESES (qt3): "{textos.get('qt3', '')}"

=== RESPUESTAS CERRADAS (interpreta el significado, no solo la letra) ===
"""
    n = 0
    for qid, area in QUESTION_MC:
        vi = _mc_index(resp[qid])
        n += 1
        ctx += f"  {n}. [{AREA_NAMES[area]}] {L15[vi]} = {S15[vi]} pts\n"

    ctx += "\nResponde SOLO JSON válido sin ```json. Sé contundente, directo, personalizado al CEO."
    return ctx


def _ceo_from_calc(calc: Dict[str, Any]) -> Dict[str, str]:
    t = calc.get("textos_abiertos") or {}
    return {"reto": t.get("qt1", ""), "fortaleza": t.get("qt2", ""), "vision": t.get("qt3", "")}


def _fallback_ai(calc: Dict[str, Any]) -> Dict[str, Any]:
    emp = calc["empresa"]
    ceo = _ceo_from_calc(calc)
    deb = min(calc["detalle_secciones"], key=lambda x: x["calificacion"])
    reto_raw = ceo.get("reto") or ""
    reto_clause = ""
    if reto_raw:
        reto_snip = reto_raw[:80] + ("…" if len(reto_raw) > 80 else "")
        reto_clause = f" El reto que mencionaste («{reto_snip}») refuerza que {deb['nombre']} debe ser prioridad."

    recs = enrich_recomendaciones_por_area(calc["detalle_secciones"], [], ceo)

    return {
        "recomendacion_general": (
            f"{emp} obtuvo {calc['indice_menthia_0_100']}/100 en el índice express ({calc['sector']}, {calc['tamano']}). "
            f"La brecha más sensible está en {deb['nombre']} ({deb['calificacion']}/100).{reto_clause} "
            "El siguiente paso no es 'hacer de todo', sino un sprint de 14 días en esa área con una métrica visible."
        ),
        "resumen_ejecutivo": (
            f"{emp}: madurez {calc['nivel_madurez']}, percentil LATAM {calc['capa1_percentil']}, "
            f"índice global {calc['capa2_indice']}/3 ({calc['capa2_diagnostico']}). "
            f"Fortaleza relativa: {max(calc['detalle_secciones'], key=lambda x: x['calificacion'])['nombre']}."
        ),
        "insight_critico": (
            f"Con {deb['calificacion']}/100 en {deb['nombre']}, cada meta de crecimiento sin arreglar esa base "
            "multiplica el desgaste del equipo y la incertidumbre de caja."
        ),
        "acciones_prioritarias": [
            {
                "titulo": f"Sprint 14 días en {deb['nombre']}",
                "descripcion": (
                    f"Un solo entregable tangible en {deb['nombre']} (proceso, política o tablero) "
                    "con dueño único y revisión semanal."
                ),
                "prioridad": "Crítica",
                "quick_win": "Día 1: sesión 90 min de causa raíz con quien opera el día a día.",
            },
            {
                "titulo": "Tablero mínimo de KPIs",
                "descripcion": "5 métricas semanales: ventas, margen, cobranza, caja a 6 semanas, cumplimiento operativo.",
                "prioridad": "Alta",
                "quick_win": "En 7 días: plantilla compartida + responsables por métrica.",
            },
            {
                "titulo": "Alineación con visión 12 meses",
                "descripcion": "Traduce la visión del CEO en 3 prioridades trimestrales con fecha y evidencia de avance.",
                "prioridad": "Media",
                "quick_win": "Esta semana: reunión 2h con decisiones cerradas, no solo ideas.",
            },
        ],
        "recomendaciones_por_area": recs,
        "kpi_sugerido": "Margen bruto por línea + días de cobranza (DSO) + saldo de caja proyectado a 6 semanas.",
        "siguiente_paso": f"Esta semana: arrancar el sprint en {deb['nombre']} y la primera revisión con números reales.",
    }


def _parse_json_text(txt: str) -> Dict[str, Any]:
    t = (txt or "").strip()
    if t.startswith("```json"):
        t = t[7:]
    if t.startswith("```"):
        t = t[3:]
    if t.endswith("```"):
        t = t[:-3]
    return json.loads(t.strip())


async def analizar_diagnostico_express(data: Dict[str, Any]) -> Dict[str, Any]:
    if not isinstance(data, dict):
        raise HTTPException(400, "Body inválido")

    calc = calcular_express(data)
    resp = data.get("respuestas") or {}

    if not ANTHROPIC_API_KEY or not client:
        out = dict(calc)
        out.update(_fallback_ai(calc))
        out["llm_mode"] = "fallback_sin_anthropic"
        return out

    user_msg = _build_user_context(calc, resp)

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            system=EXPRESS_SYSTEM,
            max_tokens=3500,
            temperature=0.4,
            messages=[{"role": "user", "content": user_msg}],
        )
        content = (response.content[0].text or "{}").strip()
        parsed = _parse_json_text(content)
    except Exception as e:
        print(f"[llm_express] ERROR: {e}")
        out = dict(calc)
        fb = _fallback_ai(calc)
        fb["resumen_ejecutivo"] = f"(Fallback por error LLM: {e}) " + fb["resumen_ejecutivo"]
        out.update(fb)
        out["llm_mode"] = "fallback_error"
        return out

    acc = parsed.get("acciones_prioritarias") or []
    if isinstance(acc, list) and len(acc) > 4:
        parsed["acciones_prioritarias"] = acc[:4]

    recos = enrich_recomendaciones_por_area(
        calc["detalle_secciones"],
        parsed.get("recomendaciones_por_area") if isinstance(parsed.get("recomendaciones_por_area"), list) else [],
        _ceo_from_calc(calc),
    )

    out = dict(calc)
    out.update(
        {
            "recomendacion_general": parsed.get("recomendacion_general", ""),
            "resumen_ejecutivo": parsed.get("resumen_ejecutivo", ""),
            "insight_critico": parsed.get("insight_critico", ""),
            "acciones_prioritarias": parsed.get("acciones_prioritarias", []),
            "recomendaciones_por_area": recos,
            "kpi_sugerido": parsed.get("kpi_sugerido", ""),
            "siguiente_paso": parsed.get("siguiente_paso", ""),
            "llm_mode": "anthropic",
        }
    )
    return out
