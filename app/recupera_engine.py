"""Motor numérico R.E.C.U.P.E.R.A.™ Profesional (paridad con lib/recupera-profesional-engine.ts)."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Literal, TypedDict


Semaforo = Literal["rojo", "amarillo", "verde"]


class ProfesionalInputs(TypedDict, total=False):
    ventasMensuales: float
    costoVentasMensual: float
    gastosOperativos: float
    depreciacion: float
    cuentasPorCobrar: float
    cuentasPorPagar: float
    inventarioTotal: float
    efectivoDisponible: float
    comprasMensuales: float
    controlPresupuesto: str
    controlRevision: str
    controlKpis: str
    controlFlujoProyectado: str


@dataclass
class ProfesionalMetrics:
    dias_cartera: float
    dias_inventario_flujo: float
    dias_proveedores: float
    ciclo_caja: float
    estado_flujo: Semaforo
    rotacion_inventario: float
    dias_inventario_anual: float
    inventario_ideal_60d: float
    exceso_inventario: float
    estado_inventario: Semaforo
    utilidad_operativa: float
    margen_bruto: float
    margen_operativo: float
    ebitda: float
    estado_rentabilidad: Semaforo
    score_control: float
    estado_control: Semaforo
    flujo_atrapado_estimado: float
    margen_mejora_estimado: float
    dinero_recuperable_estimado: float
    indice_salud_0_100: int
    alertas: list[str]


def _safe_div(a: float, b: float, fallback: float = 0.0) -> float:
    if b == 0 or not math.isfinite(a) or not math.isfinite(b):
        return fallback
    return a / b


def _letter_control_score(letter: str) -> float:
    ch = (letter or "C")[:1].upper()
    idx = "ABCDE".find(ch)
    if idx < 0:
        return 6.0
    return 2.0 + idx * 2.0


def _estado_flujo(ciclo: float) -> Semaforo:
    if ciclo > 90:
        return "rojo"
    if ciclo > 60:
        return "amarillo"
    return "verde"


def _estado_inv(dias: float) -> Semaforo:
    if dias > 120:
        return "rojo"
    if dias > 90:
        return "amarillo"
    return "verde"


def _estado_rent(mb: float) -> Semaforo:
    if mb < 0.2:
        return "rojo"
    if mb < 0.3:
        return "amarillo"
    return "verde"


def _estado_ctrl(score: float) -> Semaforo:
    if score < 4:
        return "rojo"
    if score < 7:
        return "amarillo"
    return "verde"


def _score_to_cal(e: Semaforo) -> int:
    if e == "rojo":
        return 28
    if e == "amarillo":
        return 55
    return 86


def compute_recupera_profesional(i: ProfesionalInputs) -> ProfesionalMetrics:
    ventas = max(float(i.get("ventasMensuales") or 0), 0.0)
    cv = max(float(i.get("costoVentasMensual") or 0), 0.0)
    compras = max(float(i.get("comprasMensuales") or 0), 0.0)
    inv = max(float(i.get("inventarioTotal") or 0), 0.0)
    vb = ventas if ventas > 0 else 1e-9
    cvb = cv if cv > 0 else 1e-9
    compras_b = compras if compras > 0 else 1e-9

    cxc = float(i.get("cuentasPorCobrar") or 0)
    cxp = float(i.get("cuentasPorPagar") or 0)
    efectivo = float(i.get("efectivoDisponible") or 0)
    dep = float(i.get("depreciacion") or 0)
    go = float(i.get("gastosOperativos") or 0)

    dias_cartera = _safe_div(cxc, vb) * 30
    dias_inventario_flujo = _safe_div(inv, cvb) * 30
    dias_proveedores = _safe_div(cxp, compras_b) * 30
    ciclo = dias_cartera + dias_inventario_flujo - dias_proveedores
    estado_flujo = _estado_flujo(ciclo)

    rot = _safe_div(cv, inv if inv > 0 else 1e-9)
    dias_inv_anual = 365 / rot if rot > 0 else 999.0
    inv_ideal = (cv / 12) * 2
    exceso = max(inv - inv_ideal, 0)
    estado_inv = _estado_inv(dias_inv_anual)

    uo = ventas - cv - go
    mb = _safe_div(ventas - cv, vb)
    mo = _safe_div(uo, vb)
    ebitda = uo + dep
    estado_rent = _estado_rent(mb)

    scores = [
        _letter_control_score(str(i.get("controlPresupuesto") or "C")),
        _letter_control_score(str(i.get("controlRevision") or "C")),
        _letter_control_score(str(i.get("controlKpis") or "C")),
        _letter_control_score(str(i.get("controlFlujoProyectado") or "C")),
    ]
    score_ctrl = sum(scores) / len(scores)
    estado_ctrl = _estado_ctrl(score_ctrl)

    flujo_atrap = vb * 0.1 if ciclo > 60 else 0.0
    margen_mej = vb * 0.05
    dinero_rec = exceso + flujo_atrap + margen_mej

    idx = round(
        (
            _score_to_cal(estado_flujo)
            + _score_to_cal(estado_inv)
            + _score_to_cal(estado_rent)
            + _score_to_cal(estado_ctrl)
        )
        / 4
    )

    alertas: list[str] = []
    if estado_flujo == "rojo":
        alertas.append(f"Ciclo de caja elevado ({round(ciclo)} días): riesgo alto de liquidez.")
    elif estado_flujo == "amarillo":
        alertas.append(f"Ciclo de caja en zona de alerta ({round(ciclo)} días).")
    if estado_inv == "rojo":
        alertas.append(
            f"Inventario con {round(dias_inv_anual)} días de cobertura: capital inmovilizado."
        )
    if estado_rent == "rojo":
        alertas.append(f"Margen bruto {mb * 100:.1f}% por debajo del umbral de referencia (20%).")
    if estado_ctrl in ("rojo", "amarillo"):
        alertas.append(
            f"Madurez de control financiero {score_ctrl:.1f}/10: decisiones y seguimiento pueden mejorar."
        )
    if efectivo <= 0 and ventas > 0:
        alertas.append("Efectivo disponible en cero o negativo: revisar liquidez inmediata.")

    return ProfesionalMetrics(
        dias_cartera=dias_cartera,
        dias_inventario_flujo=dias_inventario_flujo,
        dias_proveedores=dias_proveedores,
        ciclo_caja=ciclo,
        estado_flujo=estado_flujo,
        rotacion_inventario=rot,
        dias_inventario_anual=dias_inv_anual,
        inventario_ideal_60d=inv_ideal,
        exceso_inventario=exceso,
        estado_inventario=estado_inv,
        utilidad_operativa=uo,
        margen_bruto=mb,
        margen_operativo=mo,
        ebitda=ebitda,
        estado_rentabilidad=estado_rent,
        score_control=score_ctrl,
        estado_control=estado_ctrl,
        flujo_atrapado_estimado=flujo_atrap,
        margen_mejora_estimado=margen_mej,
        dinero_recuperable_estimado=dinero_rec,
        indice_salud_0_100=int(idx),
        alertas=alertas,
    )


def metrics_to_dict(m: ProfesionalMetrics) -> dict:
    return {
        "diasCartera": m.dias_cartera,
        "diasInventarioFlujo": m.dias_inventario_flujo,
        "diasProveedores": m.dias_proveedores,
        "cicloCaja": m.ciclo_caja,
        "estadoFlujo": m.estado_flujo,
        "rotacionInventario": m.rotacion_inventario,
        "diasInventarioAnual": m.dias_inventario_anual,
        "inventarioIdeal60d": m.inventario_ideal_60d,
        "excesoInventario": m.exceso_inventario,
        "estadoInventario": m.estado_inventario,
        "utilidadOperativa": m.utilidad_operativa,
        "margenBruto": m.margen_bruto,
        "margenOperativo": m.margen_operativo,
        "ebitda": m.ebitda,
        "estadoRentabilidad": m.estado_rentabilidad,
        "scoreControl": m.score_control,
        "estadoControl": m.estado_control,
        "flujoAtrapadoEstimado": m.flujo_atrapado_estimado,
        "margenMejoraEstimado": m.margen_mejora_estimado,
        "dineroRecuperableEstimado": m.dinero_recuperable_estimado,
        "indiceSalud0_100": m.indice_salud_0_100,
        "alertas": m.alertas,
    }
