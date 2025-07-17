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
    pdf.set_font("Arial", "", 12)
    pdf.multi_cell(0, 10, f"Resumen: {info.get('resumen', '')}")
    pdf.ln(10)

    if info.get("areas"):
        pdf.set_font("Arial", "B", 12)
        pdf.cell(60, 10, "Área", 1)
        pdf.cell(40, 10, "Semáforo", 1)
        pdf.ln()
        pdf.set_font("Arial", "", 12)
        for area in info["areas"]:
            pdf.cell(60, 10, area.get("nombre", "-"), 1)
            pdf.cell(40, 10, area.get("semaforo", "-"), 1)
            pdf.ln()
    else:
        pdf.set_font("Arial", "I", 10)
        pdf.cell(0, 10, "No se generó semáforo por áreas.", ln=1)

    # Disclaimer
    pdf.ln(10)
    pdf.set_font("Arial", "I", 9)
    pdf.multi_cell(0, 8, "Este reporte es orientativo y no constituye una asesoría personalizada. Consulta a un profesional para decisiones críticas.")

    pdf_bytes = pdf.output(dest='S').encode('latin-1')
    return pdf_bytes
