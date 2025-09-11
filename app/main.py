from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import io

# IMPORTA TUS FUNCIONES DEL LLM Y PDF
from app.llm_openai import (
    analizar_diagnostico,
    analizar_historico,
    generar_reporte_pdf,
)

# IMPORTA LAS NUEVAS FUNCIONES DE ANÁLISIS DE DIAGNÓSTICO
from app.llm_general import analizar_diagnostico_general
from app.llm_profundo import analizar_diagnostico_profundo
from app.llm_emergencia import analizar_diagnostico_emergencia

# IMPORTA LAS FUNCIONES DE LOS CHATBOTS
from app.llm_grok import chat_grok
from app.llm_grok_ayuda import chat_grok_ayuda  # <-- nuevo import

app = FastAPI(
    title="MentorApp LLM Backend",
    description="API para análisis y reporte de diagnósticos empresariales",
    version="1.0.0",
)

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Ajusta a tus dominios en producción
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def ping():
    return {"status": "ok", "msg": "MentorApp backend online."}

@app.head("/")
def ping_head():
    # Útil para plataformas que hacen HEAD health-checks
    return JSONResponse(content=None, status_code=200)

# ---------------- Diagnóstico "simple" (histórico / pdf) ----------------

@app.post("/api/diagnostico/analyze")
async def analyze_one(data: dict):
    return await analizar_diagnostico(data)

@app.post("/api/diagnostico/historico")
async def analyze_historico(payload: dict):
    """
    Recibe: {"diagnosticos": [ ... ]}
    """
    diagnosticos = payload.get("diagnosticos")
    if not diagnosticos:
        raise HTTPException(400, "Lista de diagnósticos vacía")
    return await analizar_historico(diagnosticos)

@app.post("/api/diagnostico/reporte-pdf")
async def report_pdf(payload: dict):
    """
    Recibe: {"diagnostico": {...}}
    Devuelve: PDF binario
    """
    diagnostico = payload.get("diagnostico")
    if not diagnostico:
        raise HTTPException(400, "Falta diagnóstico")
    pdf_bytes = await generar_reporte_pdf(diagnostico)
    return StreamingResponse(io.BytesIO(pdf_bytes), media_type="application/pdf")

# ---------------- Nuevos diagnósticos ----------------

@app.post("/api/diagnostico/general/analyze")
async def analyze_general_diagnosis(data: dict):
    """
    Analiza los datos de un diagnóstico general utilizando el LLM específico.
    """
    if not data:
        raise HTTPException(400, "Datos del diagnóstico general vacíos")
    return await analizar_diagnostico_general(data)

# Ruta legacy para compatibilidad con llamadas antiguas (con guion)
@app.post("/api/diagnostico/general-analyze")
async def analyze_general_diagnosis_legacy(data: dict):
    if not data:
        raise HTTPException(400, "Datos del diagnóstico general vacíos")
    return await analizar_diagnostico_general(data)

@app.post("/api/diagnostico/profundo/analyze")
async def analyze_profundo_diagnosis(data: dict):
    """
    Analiza los datos de un diagnóstico profundo utilizando el LLM específico.
    """
    if not data:
        raise HTTPException(400, "Datos del diagnóstico profundo vacíos")
    return await analizar_diagnostico_profundo(data)

@app.post("/api/diagnostico/emergencia/analyze")
async def analyze_emergencia_diagnosis(data: dict):
    """
    Analiza los datos de un diagnóstico de emergencia utilizando el LLM específico.
    """
    if not data:
        raise HTTPException(400, "Datos del diagnóstico de emergencia vacíos")
    return await analizar_diagnostico_emergencia(data)

# ---------------- Chatbots ----------------

@app.post("/api/chatbot")
async def chatbot(request: Request):
    data = await request.json()
    message = data.get("message")
    if not message:
        raise HTTPException(400, "No se recibió mensaje")
    try:
        reply = await chat_grok(message)
        return {"reply": reply}
    except Exception:
        return {"reply": "Ocurrió un error con el asistente. Intenta más tarde."}

@app.post("/api/chatbot-ayuda")
async def chatbot_ayuda(request: Request):
    data = await request.json()
    message = data.get("message")
    if not message:
        raise HTTPException(400, "No se recibió mensaje")
    try:
        reply = await chat_grok_ayuda(message)
        return {"reply": reply}
    except Exception:
        return {"reply": "Ocurrió un error con el asistente de ayuda. Intenta más tarde."}
