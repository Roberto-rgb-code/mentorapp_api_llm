"""
mentorapp_api_llm — FastAPI: diagnósticos MentHIA + R.E.C.U.P.E.R.A.™
"""

from __future__ import annotations

from typing import Any

from fastapi import Body, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from app.llm_emergencia import analizar_diagnostico_emergencia
from app.llm_express import analizar_diagnostico_express
from app.llm_finanzas_interpret import interpretar_finanzas_narrativa
from app.llm_general import analizar_diagnostico_general
from app.llm_profundo import analizar_diagnostico_profundo
from app.routers import recupera_express, recupera_profesional

app = FastAPI(title="mentorapp_api_llm", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(
    recupera_profesional.router,
    prefix="/api/diagnostico/recupera-profesional",
)
app.include_router(
    recupera_express.router,
    prefix="/api/diagnostico/recupera-express",
)


@app.get("/")
def root() -> dict[str, Any]:
    return {"ok": True, "service": "mentorapp_api_llm"}


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "mentorapp_api_llm"}


@app.post("/api/diagnostico/general/analyze")
async def diagnostico_general_analyze(data: dict = Body(...)) -> dict[str, Any]:
    return await analizar_diagnostico_general(data)


@app.post("/api/diagnostico/express/analyze")
async def diagnostico_express_analyze(data: dict = Body(...)) -> dict[str, Any]:
    return await analizar_diagnostico_express(data)


@app.post("/api/diagnostico/emergencia/analyze")
async def diagnostico_emergencia_analyze(data: dict = Body(...)) -> dict[str, Any]:
    return await analizar_diagnostico_emergencia(data)


@app.post("/api/diagnostico/profundo/analyze")
async def diagnostico_profundo_analyze(data: dict = Body(...)) -> dict[str, Any]:
    return await analizar_diagnostico_profundo(data)


@app.post("/api/finanzas/interpretar")
async def finanzas_interpretar(body: dict = Body(...)) -> dict[str, Any]:
    payload = body.get("payload")
    if payload is None or not isinstance(payload, dict):
        raise HTTPException(status_code=400, detail="payload (objeto) es requerido")
    return await interpretar_finanzas_narrativa(payload)
