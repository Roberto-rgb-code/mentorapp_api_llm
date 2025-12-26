import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

SYSTEM_PROMPT_AYUDA = """Eres el asistente de ayuda de MentHIA para diagnósticos empresariales.

REGLAS:
- Respuestas CORTAS: máximo 2-3 oraciones
- Explica términos de forma simple
- Da fórmulas cuando pregunten sobre cálculos
- Incluye 1 ejemplo práctico si es relevante
- Español claro y directo

TÉRMINOS CLAVE:
- CAC = (Marketing + Ventas) / Nuevos clientes
- LTV = Ticket promedio × Frecuencia × Tiempo retención
- Margen neto = (Ingresos - Gastos) / Ingresos × 100
- KPIs = Indicadores clave de desempeño
- Buyer persona = Perfil del cliente ideal
- ROI = (Ganancia - Inversión) / Inversión × 100
- CRM = Sistema de gestión de relaciones con clientes"""

# Respuestas locales rápidas
LOCAL_RESPONSES = {
    'cac': 'CAC = (Gastos Marketing + Ventas) ÷ Nuevos Clientes. Ejemplo: $10,000 / 100 clientes = $100 CAC. Un buen CAC es menor a 1/3 del LTV.',
    'ltv': 'LTV = Ticket Promedio × Frecuencia × Tiempo Retención. Ejemplo: $50 × 12/año × 3 años = $1,800 LTV.',
    'margen': 'Margen Neto = (Ingresos - Gastos) / Ingresos × 100. Típico: Retail 2-5%, SaaS 20-40%, Consultoría 15-25%.',
    'kpi': 'KPIs son métricas que miden el éxito de tu negocio. Ejemplos: ventas mensuales, tasa de conversión, NPS, margen operativo.',
    'buyer': 'Buyer persona = perfil de tu cliente ideal. Incluye: edad, ubicación, motivaciones, problemas que resuelves.',
    'persona': 'Buyer persona = perfil de tu cliente ideal. Incluye: edad, ubicación, motivaciones, problemas que resuelves.',
    'roi': 'ROI = (Ganancia - Inversión) / Inversión × 100. Ejemplo: Ganas $15,000 de inversión de $10,000 → ROI = 50%.',
    'embudo': 'Embudo de ventas: Prospectos → Leads → Oportunidades → Clientes. Mide la conversión entre cada etapa.',
    'crm': 'CRM = software para gestionar clientes: leads, historial, pipeline. Ejemplos: HubSpot, Salesforce, Pipedrive.',
    'conversion': 'Conversión = (Clientes / Leads) × 100. Típico: E-commerce 2-4%, B2B 2-5%, Landing pages 10-20%.',
    'objetivo': 'Usa SMART: Específico, Medible, Alcanzable, Relevante, con Tiempo. Ej: "Aumentar ventas 20% en 12 meses".',
    'smart': 'SMART = Específico, Medible, Alcanzable, Relevante, con Tiempo. La mejor forma de definir objetivos claros.',
    'proceso': 'Procesos ineficientes = los que toman mucho tiempo o generan errores. Documenta paso a paso para mejorar.',
    'flujo': 'Flujo de caja = dinero entrante menos saliente. Diferente a ganancias porque considera el timing de pagos.',
}

def get_local_response(message: str) -> str | None:
    """Busca respuesta local instantánea"""
    msg = message.lower()
    for key, value in LOCAL_RESPONSES.items():
        if key in msg:
            return value
    return None

async def chat_grok_ayuda(message: str) -> str:
    """Chat de ayuda - primero local, luego OpenAI"""
    
    # 1. Intentar respuesta local (instantánea)
    local = get_local_response(message)
    if local:
        return local
    
    # 2. Intentar OpenAI
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                        "temperature": 0.5,
                        "max_tokens": 150,
                        "messages": [
                            {"role": "system", "content": SYSTEM_PROMPT_AYUDA},
                            {"role": "user", "content": message}
                        ]
                    }
                )
                if response.status_code == 200:
                    data = response.json()
                    return data["choices"][0]["message"]["content"].strip()
        except Exception as e:
            print(f"OpenAI error: {e}")
    
    # 3. Fallback
    return "Responde con honestidad para obtener recomendaciones precisas. ¿Tienes alguna duda específica sobre algún término?"