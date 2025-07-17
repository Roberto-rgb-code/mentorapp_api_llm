from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
import io

# IMPORTA TUS FUNCIONES DEL LLM Y PDF
from app.llm_openai import (
    analizar_diagnostico,
    analizar_historico,
    generar_reporte_pdf,
)

# IMPORTA LA FUNCIÓN DE GROK
from app.llm_grok import chat_grok  # <-- debes crear este archivo y función

app = FastAPI(
    title="MentorApp LLM Backend",
    description="API para análisis y reporte de diagnósticos empresariales",
    version="1.0.0"
)

# Habilita CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def ping():
    return {"status": "ok", "msg": "MentorApp backend online."}

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

# NUEVO ENDPOINT PARA EL CHATBOT (GROK)
@app.post("/api/chatbot")
async def chatbot(request: Request):
    data = await request.json()
    message = data.get("message")
    if not message:
        raise HTTPException(400, "No se recibió mensaje")
    try:
        reply = await chat_grok(message)
        return {"reply": reply}
    except Exception as e:
        return {"reply": "Ocurrió un error con el asistente. Intenta más tarde."}
