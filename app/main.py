from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse, JSONResponse
import io
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

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

# IMPORTA LAS FUNCIONES DE LOS CHATBOTS (ahora usan OpenAI)
from app.llm_grok import chat_grok
from app.llm_grok_ayuda import chat_grok_ayuda

# IMPORTA VISION PARA ANÁLISIS DE DOCUMENTOS
from app.llm_vision import analyze_document_with_vision, analyze_document_fallback

# IMPORTA VALIDACIÓN DE CONSULTORES
from app.llm_consultant_validation import validar_consultor

app = FastAPI(
    title="MentorApp LLM Backend",
    description="API para análisis y reporte de diagnósticos empresariales con OpenAI",
    version="2.0.0",
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
    openai_configured = bool(os.getenv("OPENAI_API_KEY"))
    return {
        "status": "ok",
        "msg": "MentorApp LLM backend online.",
        "openai_configured": openai_configured,
        "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini")
    }

@app.head("/")
def ping_head():
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
async def analyze_general_diagnosis(request: Request):
    """
    Analiza los datos de un diagnóstico general utilizando el LLM específico.
    """
    data = await request.json()
    if not data or (isinstance(data, dict) and not data):
        raise HTTPException(400, "Datos del diagnóstico general vacíos")
    return await analizar_diagnostico_general(data)

# Ruta legacy para compatibilidad con llamadas antiguas (con guion)
@app.post("/api/diagnostico/general-analyze")
async def analyze_general_diagnosis_legacy(request: Request):
    data = await request.json()
    if not data or (isinstance(data, dict) and not data):
        raise HTTPException(400, "Datos del diagnóstico general vacíos")
    return await analizar_diagnostico_general(data)

@app.post("/api/diagnostico/profundo/analyze")
async def analyze_profundo_diagnosis(request: Request):
    """
    Analiza los datos de un diagnóstico profundo utilizando el LLM específico.
    """
    data = await request.json()
    if not data or (isinstance(data, dict) and not data):
        raise HTTPException(400, "Datos del diagnóstico profundo vacíos")
    return await analizar_diagnostico_profundo(data)

@app.post("/api/diagnostico/emergencia/analyze")
async def analyze_emergencia_diagnosis(request: Request):
    """
    Analiza los datos de un diagnóstico de emergencia utilizando el LLM específico.
    """
    data = await request.json()
    if not data or (isinstance(data, dict) and not data):
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
    
    # Contexto adicional para mejorar las respuestas
    contexto = data.get("contexto", "")
    pregunta_actual = data.get("preguntaActual", "")
    
    # Enriquecer el mensaje con contexto si está disponible
    mensaje_enriquecido = message
    if pregunta_actual:
        mensaje_enriquecido = f"Contexto: El usuario está respondiendo la pregunta del diagnóstico: '{pregunta_actual}'. Área: {contexto}. Pregunta del usuario: {message}"
    
    try:
        reply = await chat_grok_ayuda(mensaje_enriquecido)
        return {"reply": reply}
    except Exception as e:
        print(f"Error en chatbot-ayuda: {e}")
        return {"reply": "Ocurrió un error con el asistente de ayuda. Intenta más tarde."}

# ---------------- Vision - Análisis de Documentos ----------------

@app.post("/api/documents/analyze")
async def analyze_document(request: Request):
    """
    Analiza un documento/imagen usando OpenAI Vision (GPT-4o)
    
    Body esperado:
    {
        "image_base64": "base64 de la imagen (opcional)",
        "image_url": "URL de la imagen (opcional)",
        "document_type": "financial|report|image|general",
        "mime_type": "image/jpeg|image/png|...",
        "diagnostic_context": {
            "empresa": "nombre",
            "sector": "sector",
            "areaActual": "área del diagnóstico"
        }
    }
    """
    data = await request.json()
    
    image_base64 = data.get("image_base64")
    image_url = data.get("image_url")
    document_type = data.get("document_type", "general")
    mime_type = data.get("mime_type", "image/jpeg")
    diagnostic_context = data.get("diagnostic_context")
    
    if not image_base64 and not image_url:
        raise HTTPException(400, "Se requiere image_base64 o image_url")
    
    result = await analyze_document_with_vision(
        image_base64=image_base64,
        image_url=image_url,
        document_type=document_type,
        mime_type=mime_type,
        diagnostic_context=diagnostic_context
    )
    
    if not result.get("success"):
        # Intentar fallback
        filename = data.get("filename", "documento")
        file_type = mime_type
        fallback = analyze_document_fallback(filename, file_type, diagnostic_context)
        return fallback
    
    return result

@app.post("/api/documents/analyze-batch")
async def analyze_documents_batch(request: Request):
    """
    Analiza múltiples documentos en lote
    
    Body esperado:
    {
        "documents": [
            {
                "id": "doc1",
                "image_base64": "...",
                "document_type": "financial"
            },
            ...
        ],
        "diagnostic_context": {...}
    }
    """
    data = await request.json()
    documents = data.get("documents", [])
    diagnostic_context = data.get("diagnostic_context")
    
    if not documents:
        raise HTTPException(400, "Lista de documentos vacía")
    
    results = []
    for doc in documents:
        result = await analyze_document_with_vision(
            image_base64=doc.get("image_base64"),
            image_url=doc.get("image_url"),
            document_type=doc.get("document_type", "general"),
            mime_type=doc.get("mime_type", "image/jpeg"),
            diagnostic_context=diagnostic_context
        )
    results.append({
        "id": doc.get("id"),
        "result": result
    })
    
    return {"results": results}

# ---------------- Validación de Consultores ----------------

@app.post("/api/consultants/validate")
async def validate_consultant(request: Request):
    """
    Valida un perfil de consultor usando IA según el prompt maestro de MentHIA.
    
    Body esperado:
    {
        "form_data": {
            "fullName": "...",
            "email": "...",
            "professionalName": "...",
            "languages": ["español", "inglés"],
            "linkedin": "https://linkedin.com/in/...",
            "website": "https://...",
            "professionalType": "consultor_independiente" | "ejecutivo_activo" | ...,
            "specializationAreas": ["Estrategia", "Finanzas"],
            "experienceDescription": "...",
            "totalYearsExperience": 15,
            "consultingYearsExperience": 10,
            "companyTypes": ["PYMES", "Medianas"],
            "industries": ["Servicios", "Manufactura"],
            "certifications": ["..."],
            "achievements": "...",
            "hasExecutiveRoles": true,
            "executiveRolesDetails": "...",
            "hasPublicSpeaking": true,
            "publicSpeakingDetails": "...",
            "publicReferences": ["https://..."],
            "serviceTypes": ["Diagnósticos", "Sesiones 1 a 1"],
            "motivation": "...",
            "weeklyAvailability": 10,
            "aiOpenness": "si" | "si_con_acompanamiento" | "no",
            "aiOpennessReason": "...",
            "currentTools": ["CRM", "Herramientas de análisis"]
        },
        "public_data": {
            "linkedin_info": "...",
            "website_info": "...",
            "articles": ["..."],
            "events": ["..."]
        }
    }
    
    Returns:
    {
        "resumen_ejecutivo_ia": "...",
        "trust_score": 88,
        "nivel_sugerido": "consultor_senior",
        "desglose_dimensiones": {
            "experiencia": 27,
            "especializacion": 16,
            "reputacion": 15,
            "enfoque_pyme": 13,
            "afinidad_ia": 9,
            "riesgos": 0
        },
        "riesgos_detectados": ["Ninguno"],
        "recomendacion_final": "APROBAR",
        "justificacion": "..."
    }
    """
    data = await request.json()
    
    form_data = data.get("form_data", {})
    public_data = data.get("public_data")
    
    if not form_data:
        raise HTTPException(400, "Se requiere form_data con los datos del consultor")
    
    try:
        result = await validar_consultor(form_data, public_data)
        return result
    except Exception as e:
        print(f"Error en validación de consultor: {e}")
        raise HTTPException(500, f"Error al validar consultor: {str(e)}")
