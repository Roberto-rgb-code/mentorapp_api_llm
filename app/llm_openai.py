import os
import json
from dotenv import load_dotenv
from openai import OpenAI, OpenAIError
from fpdf import FPDF
import io

# Carga variables de entorno (usa .env)
load_dotenv()

# Inicializa cliente OpenAI
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
client = OpenAI(api_key=OPENAI_API_KEY)

# ----------- FUNCIÓN: ANALIZAR DIAGNÓSTICO -----------
async def analizar_diagnostico(data):
    prompt = (
        "Eres un consultor experto. Analiza este diagnóstico empresarial recibido en formato JSON.\n"
        f"Diagnóstico:\n{json.dumps(data, ensure_ascii=False)}\n"
        "Entrega un JSON con: fortalezas, areas_oportunidad, score (1-100), recomendaciones (3).\n"
        "Ejemplo de respuesta: {'fortalezas':[], 'areas_oportunidad':[], 'score':0, 'recomendaciones':[]}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": prompt}]
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"OpenAI error: {e}")
        return {"error": "No se pudo analizar el diagnóstico", "details": str(e)}

# ----------- FUNCIÓN: ANALIZAR HISTÓRICO -----------
async def analizar_historico(diagnosticos):
    prompt = (
        "Recibiste la siguiente evolución de diagnósticos empresariales (JSON array):\n"
        f"{json.dumps(diagnosticos, ensure_ascii=False)}\n"
        "Detecta patrones, progreso, retrocesos y haz un resumen de evolución (máx 200 palabras). "
        "Agrega 3 consejos para continuar avanzando y una calificación histórica (1-100). "
        "Responde en formato JSON: {'resumen':'', 'consejos':[], 'score_historico':0}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": prompt}]
        )
        content = resp.choices[0].message.content
        return json.loads(content)
    except Exception as e:
        print(f"OpenAI error: {e}")
        return {"error": "No se pudo analizar el histórico", "details": str(e)}

# ----------- FUNCIÓN: GENERAR REPORTE PDF -----------
async def generar_reporte_pdf(diagnostico):
    # Consulta LLM para resumen y semáforo por área
    prompt = (
        "Analiza este diagnóstico empresarial y asigna un color de semáforo (rojo, amarillo, verde) "
        "para cada área clave (estrategia, finanzas, marketing, operaciones, tecnología, legal, RH). "
        "Entrega resumen y tabla de áreas con semáforo.\n"
        f"Diagnóstico:\n{json.dumps(diagnostico, ensure_ascii=False)}\n"
        "Formato de respuesta JSON: {'areas':[{'nombre':'', 'semaforo':''}], 'resumen':''}"
    )
    try:
        resp = client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[{"role": "system", "content": prompt}]
        )
        info = json.loads(resp.choices[0].message.content)
    except Exception as e:
        print(f"OpenAI error (PDF): {e}")
        info = {
            "resumen": "No se pudo analizar el diagnóstico por un error del modelo.",
            "areas": []
        }

    # Generar PDF
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", "B", 16)
    pdf.cell(0, 10, "Reporte Diagnóstico Empresarial", ln=1)
    
    # Información de la empresa
    empresa = diagnostico.get("nombreEmpresa", "Empresa")
    sector = diagnostico.get("sector", "No especificado")
    pdf.set_font("Arial", "", 10)
    pdf.cell(0, 8, f"Empresa: {empresa} | Sector: {sector}", ln=1)
    pdf.cell(0, 8, f"Fecha: {diagnostico.get('createdAt', 'N/A')}", ln=1)
    pdf.ln(5)
    
    # Resumen
    pdf.set_font("Arial", "B", 12)
    pdf.cell(0, 10, "Resumen Ejecutivo", ln=1)
    pdf.set_font("Arial", "", 11)
    pdf.multi_cell(0, 8, info.get('resumen', 'No disponible'))
    pdf.ln(5)

    # Áreas con semáforo
    if info.get("areas"):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Evaluación por Áreas", ln=1)
        pdf.set_font("Arial", "B", 11)
        pdf.cell(80, 10, "Área", 1)
        pdf.cell(40, 10, "Semáforo", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 10)
        for area in info["areas"]:
            pdf.cell(80, 10, area.get("nombre", "-"), 1)
            pdf.cell(40, 10, area.get("semaforo", "-"), 1)
            pdf.ln()
        pdf.ln(5)
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "No se generó semáforo por áreas.", ln=1)
        pdf.ln(5)

    # Documentos analizados (si existen)
    documentos_analizados = diagnostico.get("documentosAnalizados", [])
    if documentos_analizados:
        pdf.set_font("Arial", "B", 12)
        pdf.cell(0, 10, "Documentos Analizados con IA", ln=1)
        pdf.set_font("Arial", "", 10)
        for idx, doc in enumerate(documentos_analizados, 1):
            pdf.set_font("Arial", "B", 10)
            pdf.cell(0, 8, f"Documento {idx}: {doc.get('documento', {}).get('name', 'Sin nombre')}", ln=1)
            pdf.set_font("Arial", "", 9)
            
            analisis = doc.get("analisis", {})
            if analisis.get("resumen"):
                pdf.multi_cell(0, 6, f"Resumen: {analisis['resumen']}")
            
            if analisis.get("metricas"):
                pdf.cell(0, 6, "Métricas extraídas:", ln=1)
                for key, value in analisis["metricas"].items():
                    pdf.cell(0, 5, f"  • {key}: {value}", ln=1)
            
            if analisis.get("alertas"):
                pdf.cell(0, 6, "Alertas:", ln=1)
                for alerta in analisis["alertas"]:
                    pdf.multi_cell(0, 5, f"  ⚠ {alerta}")
            
            if analisis.get("recomendaciones"):
                pdf.cell(0, 6, "Recomendaciones:", ln=1)
                for rec in analisis["recomendaciones"]:
                    pdf.multi_cell(0, 5, f"  • {rec}")
            
            pdf.ln(3)
    
    # Resultado del diagnóstico (si está disponible)
    resultado = diagnostico.get("resultado", {})
    if resultado:
        if resultado.get("resumen_ejecutivo"):
            pdf.add_page()
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Análisis Completo con IA", ln=1)
            pdf.set_font("Arial", "", 10)
            pdf.multi_cell(0, 8, resultado.get("resumen_ejecutivo", ""))
            pdf.ln(5)
        
        if resultado.get("acciones_recomendadas"):
            pdf.set_font("Arial", "B", 12)
            pdf.cell(0, 10, "Acciones Recomendadas", ln=1)
            pdf.set_font("Arial", "", 10)
            for accion in resultado["acciones_recomendadas"][:10]:  # Máximo 10
                plazo = accion.get("plazo", "N/A")
                texto = accion.get("accion", "")
                pdf.multi_cell(0, 6, f"[{plazo.upper()}] {texto}")
                pdf.ln(2)

    # Disclaimer
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 8, "Este reporte es orientativo y no constituye una asesoría personalizada. Consulta a un profesional para decisiones críticas.")
    pdf.multi_cell(0, 8, f"Documentos analizados: {len(documentos_analizados)} | Generado con IA (OpenAI GPT-4o)")

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes
