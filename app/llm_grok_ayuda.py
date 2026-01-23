import os
import httpx
from dotenv import load_dotenv

# Carga variables de entorno
load_dotenv()

SYSTEM_PROMPT_AYUDA = """Eres el asistente de ayuda de MentHIA para diagnósticos empresariales.

## TU ROL
Ayudas a empresarios durante el diagnóstico a:
- Entender términos empresariales
- Calcular métricas y KPIs
- Responder preguntas sobre su negocio
- Dar contexto sobre las preguntas del diagnóstico

## REGLAS ESTRICTAS
- Respuestas CORTAS: máximo 2-3 oraciones
- Explica términos de forma simple con ejemplos
- Da fórmulas cuando pregunten sobre cálculos
- Incluye 1 ejemplo práctico si es relevante
- Español claro y directo
- Si no entiendes, pide que reformulen

## FÓRMULAS CLAVE

### FINANCIERAS
- CAC (Costo Adquisición Cliente) = (Gastos Marketing + Ventas) ÷ Nuevos Clientes
- LTV (Valor de Vida del Cliente) = Ticket Promedio × Frecuencia Compra × Tiempo Retención
- Margen Neto = (Ingresos - Gastos Totales) ÷ Ingresos × 100
- Margen Bruto = (Ingresos - Costo de Ventas) ÷ Ingresos × 100
- ROI = (Ganancia - Inversión) ÷ Inversión × 100
- Punto de Equilibrio = Costos Fijos ÷ (Precio - Costo Variable)
- EBITDA = Utilidad Operativa + Depreciación + Amortización
- Capital de Trabajo = Activo Circulante - Pasivo Circulante
- Razón Corriente = Activo Circulante ÷ Pasivo Circulante

### VENTAS Y MARKETING
- Tasa de Conversión = (Clientes ÷ Leads) × 100
- Ticket Promedio = Ventas Totales ÷ Número de Transacciones
- Churn Rate = Clientes Perdidos ÷ Clientes Iniciales × 100
- NPS = % Promotores - % Detractores
- CTR = (Clics ÷ Impresiones) × 100
- CPC = Inversión ÷ Clics Totales

### OPERACIONES
- Rotación de Inventario = Costo de Ventas ÷ Inventario Promedio
- Eficiencia Operativa = Output ÷ Input × 100
- Takt Time = Tiempo Disponible ÷ Demanda del Cliente
- OEE = Disponibilidad × Rendimiento × Calidad

### RECURSOS HUMANOS
- Rotación de Personal = (Salidas ÷ Promedio Empleados) × 100
- Costo por Contratación = Gastos Reclutamiento ÷ Contrataciones

## TÉRMINOS EMPRESARIALES CLAVE
- PYME: Pequeña y Mediana Empresa
- B2B: Business to Business (venta a empresas)
- B2C: Business to Consumer (venta al público)
- KPI: Key Performance Indicator (indicador clave)
- CRM: Sistema de gestión de clientes
- ERP: Sistema de planificación empresarial
- Lean: Metodología de eficiencia sin desperdicios
- Scrum/Agile: Metodologías de gestión de proyectos
- MVP: Producto Mínimo Viable
- Pivot: Cambio de modelo de negocio
- Stakeholders: Partes interesadas
- Due Diligence: Investigación antes de inversión
- Break-even: Punto de equilibrio
- Bootstrapping: Crecer sin inversión externa
- Scale-up: Empresa en crecimiento acelerado

## EJEMPLOS DE RESPUESTAS

Usuario: "¿Qué es el CAC?"
Respuesta: "CAC = (Gastos Marketing + Ventas) ÷ Nuevos Clientes. Ejemplo: Si gastas $10,000 en marketing y consigues 100 clientes, tu CAC es $100. Un buen CAC debe ser menor a 1/3 del LTV."

Usuario: "No sé cómo calcular mi margen"
Respuesta: "Margen Neto = (Ingresos - Gastos) ÷ Ingresos × 100. Ejemplo: Ingresos $100,000, gastos $70,000 → Margen = 30%. Típico: Retail 2-5%, SaaS 20-40%, Consultoría 15-25%."

Responde siempre de forma práctica y con ejemplos cuando sea posible."""

# Respuestas locales EXPANDIDAS para términos empresariales
LOCAL_RESPONSES = {
    # FINANCIERAS
    'cac': 'CAC = (Gastos Marketing + Ventas) ÷ Nuevos Clientes. Ejemplo: $10,000 / 100 clientes = $100 CAC. Un buen CAC es menor a 1/3 del LTV.',
    'ltv': 'LTV = Ticket Promedio × Frecuencia × Tiempo Retención. Ejemplo: $50 × 12/año × 3 años = $1,800 LTV. Busca que LTV sea al menos 3x tu CAC.',
    'margen': 'Margen Neto = (Ingresos - Gastos) / Ingresos × 100. Típico: Retail 2-5%, SaaS 20-40%, Servicios 15-30%, Manufactura 5-15%.',
    'margen bruto': 'Margen Bruto = (Ingresos - Costo de Ventas) / Ingresos × 100. No incluye gastos operativos. Típico: 40-60% es saludable.',
    'roi': 'ROI = (Ganancia - Inversión) / Inversión × 100. Ejemplo: Inviertes $10,000, ganas $15,000 → ROI = 50%.',
    'ebitda': 'EBITDA = Utilidad Operativa + Depreciación + Amortización. Mide la capacidad de generar efectivo antes de impuestos e intereses.',
    'punto de equilibrio': 'Punto de Equilibrio = Costos Fijos ÷ (Precio - Costo Variable). Es el punto donde no ganas ni pierdes.',
    'break even': 'Break Even = Costos Fijos ÷ (Precio - Costo Variable). Ejemplo: Fijos $50,000, Precio $100, Variable $40 → Necesitas 833 unidades.',
    'capital de trabajo': 'Capital de Trabajo = Activo Circulante - Pasivo Circulante. Mide tu liquidez operativa. Positivo = bueno.',
    'razon corriente': 'Razón Corriente = Activo Circulante ÷ Pasivo Circulante. Ideal > 1.5. Mide si puedes pagar deudas a corto plazo.',
    'liquidez': 'Liquidez mide tu capacidad de pagar deudas inmediatas. Razón Corriente = Activo Circulante ÷ Pasivo Circulante. Ideal > 1.5.',
    
    # VENTAS Y MARKETING
    'kpi': 'KPIs son métricas que miden el éxito de tu negocio. Ejemplos: ventas mensuales, tasa de conversión, NPS, margen operativo, CAC, LTV.',
    'buyer persona': 'Buyer Persona = perfil de tu cliente ideal. Incluye: edad, ubicación, cargo, motivaciones, problemas que resuelves, comportamiento de compra.',
    'persona': 'Buyer Persona = perfil de tu cliente ideal. Incluye: edad, ubicación, cargo, motivaciones, problemas que resuelves.',
    'embudo': 'Embudo de ventas: Prospectos → Leads → Oportunidades → Clientes. Mide la conversión entre cada etapa para optimizar.',
    'funnel': 'Funnel de ventas: Awareness → Interés → Consideración → Decisión → Compra. Identifica dónde pierdes más clientes.',
    'crm': 'CRM = software para gestionar clientes y ventas. Ejemplos: HubSpot, Salesforce, Pipedrive, Zoho. Ayuda a dar seguimiento a leads.',
    'conversion': 'Conversión = (Clientes ÷ Leads) × 100. Típico: E-commerce 2-4%, B2B 2-5%, Landing pages 10-20%.',
    'tasa de conversion': 'Tasa de Conversión = (Clientes ÷ Leads) × 100. Si de 100 leads cierras 5, tu conversión es 5%.',
    'churn': 'Churn Rate = Clientes Perdidos ÷ Clientes Iniciales × 100. Ejemplo: Pierdes 5 de 100 clientes → Churn = 5%. Ideal < 5% mensual.',
    'nps': 'NPS (Net Promoter Score) = % Promotores - % Detractores. Escala -100 a +100. > 50 es excelente, > 70 es de clase mundial.',
    'ticket promedio': 'Ticket Promedio = Ventas Totales ÷ Número de Transacciones. Ayuda a medir el valor por cliente.',
    'ctr': 'CTR (Click Through Rate) = (Clics ÷ Impresiones) × 100. Típico en Google Ads: 2-5%, Email: 2-3%.',
    'cpc': 'CPC (Costo por Clic) = Inversión ÷ Clics. Ejemplo: $1,000 en ads, 500 clics → CPC = $2.',
    
    # ESTRATEGIA
    'objetivo': 'Usa SMART: Específico, Medible, Alcanzable, Relevante, con Tiempo. Ej: "Aumentar ventas 20% en 12 meses".',
    'smart': 'SMART = Específico, Medible, Alcanzable, Relevante, con Tiempo. La mejor forma de definir objetivos claros.',
    'foda': 'FODA = Fortalezas, Oportunidades, Debilidades, Amenazas. Análisis interno (F, D) y externo (O, A) de tu empresa.',
    'swot': 'SWOT/FODA = Strengths, Weaknesses, Opportunities, Threats. Herramienta de análisis estratégico.',
    'propuesta de valor': 'Propuesta de Valor = beneficio único que ofreces. Responde: ¿Por qué elegirte a ti? ¿Qué problema resuelves mejor?',
    'diferenciador': 'Diferenciador = lo que te hace único vs competencia. Puede ser precio, calidad, servicio, tecnología, experiencia.',
    'ventaja competitiva': 'Ventaja Competitiva = capacidad difícil de copiar. Ejemplos: marca, tecnología propia, relaciones, ubicación, know-how.',
    'modelo de negocio': 'Modelo de Negocio define cómo generas dinero: qué vendes, a quién, cómo entregas, cómo cobras. Usa Business Model Canvas.',
    'canvas': 'Business Model Canvas = lienzo con 9 bloques: Segmentos, Propuesta de Valor, Canales, Relaciones, Ingresos, Recursos, Actividades, Socios, Costos.',
    'okr': 'OKR = Objectives and Key Results. Objetivo ambicioso + 3-5 resultados medibles. Google, Intel lo usan.',
    
    # OPERACIONES
    'proceso': 'Proceso = secuencia de pasos para lograr un resultado. Documenta: entrada, actividades, responsables, salida.',
    'eficiencia': 'Eficiencia = hacer más con menos. Mide: Output ÷ Input. Busca eliminar desperdicios y automatizar.',
    'productividad': 'Productividad = Output ÷ Horas Trabajadas. Mide cuánto produces por unidad de tiempo o recurso.',
    'inventario': 'Rotación de Inventario = Costo de Ventas ÷ Inventario Promedio. Alta rotación = vendes rápido.',
    'flujo de caja': 'Flujo de Caja = dinero entrante - dinero saliente. Diferente a utilidad porque considera timing de pagos.',
    'cash flow': 'Cash Flow = Ingresos Cobrados - Pagos Realizados. Es el efectivo real disponible, no la utilidad contable.',
    'lead time': 'Lead Time = tiempo desde pedido hasta entrega. Menor lead time = mejor servicio y competitividad.',
    'lean': 'Lean = metodología de eficiencia. Elimina desperdicios: sobreproducción, esperas, transporte, inventario, movimientos, defectos.',
    'six sigma': 'Six Sigma = metodología de calidad. Reduce defectos a 3.4 por millón. Usa DMAIC: Definir, Medir, Analizar, Mejorar, Controlar.',
    
    # RECURSOS HUMANOS
    'rotacion de personal': 'Rotación = (Salidas ÷ Promedio Empleados) × 100. Alta rotación es costosa. Típico: 10-15% anual es aceptable.',
    'cultura organizacional': 'Cultura = valores, creencias y comportamientos de la empresa. Define cómo trabajan y se relacionan las personas.',
    'engagement': 'Engagement = compromiso de empleados. Mide satisfacción, motivación, lealtad. Empleados engaged son 21% más productivos.',
    'onboarding': 'Onboarding = proceso de integración de nuevos empleados. Bueno = menor rotación y más rápida productividad.',
    
    # TECNOLOGÍA
    'erp': 'ERP = sistema que integra operaciones: finanzas, inventario, compras, ventas, RH. Ejemplos: SAP, Oracle, Odoo.',
    'saas': 'SaaS = Software as a Service. Software en la nube, pagas suscripción. Ejemplos: Office 365, Salesforce, Slack.',
    'automatizacion': 'Automatización = usar tecnología para tareas repetitivas. Reduce errores y tiempo. Ejemplos: emails, reportes, facturación.',
    'transformacion digital': 'Transformación Digital = integrar tecnología en todas las áreas del negocio para mejorar operaciones y valor al cliente.',
    'mvp': 'MVP (Producto Mínimo Viable) = versión básica para validar idea rápido y barato antes de invertir más.',
    
    # GENERALES
    'pyme': 'PYME = Pequeña y Mediana Empresa. En México: Micro (hasta 10 empleados), Pequeña (11-50), Mediana (51-250).',
    'b2b': 'B2B = Business to Business. Vendes a otras empresas. Ciclos de venta más largos, tickets más altos.',
    'b2c': 'B2C = Business to Consumer. Vendes al público general. Mayor volumen, menor ticket.',
    'stakeholders': 'Stakeholders = partes interesadas: clientes, empleados, inversionistas, proveedores, comunidad.',
    'startup': 'Startup = empresa nueva con modelo escalable y alto potencial de crecimiento. Busca product-market fit.',
    'scale up': 'Scale-up = startup que ya validó su modelo y está en crecimiento acelerado (20%+ anual).',
    'bootstrapping': 'Bootstrapping = crecer tu empresa sin inversión externa, solo con tus recursos y reinvirtiendo ganancias.',
    'pivot': 'Pivot = cambio significativo en tu modelo de negocio cuando el actual no funciona.',
    'due diligence': 'Due Diligence = investigación detallada antes de inversión o compra. Revisa finanzas, legal, operaciones.',
}


def get_local_response(message: str) -> str | None:
    """Busca respuesta local instantánea"""
    msg = message.lower().strip()
    
    # Buscar coincidencias exactas primero
    for key in sorted(LOCAL_RESPONSES.keys(), key=len, reverse=True):
        if key in msg:
            return LOCAL_RESPONSES[key]
    
    return None


async def chat_grok_ayuda(message: str) -> str:
    """Chat de ayuda - primero local, luego OpenAI"""
    
    # 1. Intentar respuesta local (instantánea)
    local = get_local_response(message)
    if local:
        return local
    
    # 2. Intentar OpenAI para respuestas más complejas
    api_key = os.getenv("OPENAI_API_KEY")
    if api_key:
        try:
            async with httpx.AsyncClient(timeout=12.0) as client:
                response = await client.post(
                    "https://api.openai.com/v1/chat/completions",
                    headers={
                        "Content-Type": "application/json",
                        "Authorization": f"Bearer {api_key}"
                    },
                    json={
                        "model": os.getenv("OPENAI_MODEL_NAME", "gpt-4o-mini"),
                        "temperature": 0.5,
                        "max_tokens": 200,
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
    
    # 3. Fallback inteligente
    return "Responde con honestidad para obtener recomendaciones precisas. Si tienes dudas sobre algún término específico, pregúntame y te explico con un ejemplo práctico."
