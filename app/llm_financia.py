import os
import json
from typing import Dict, Any
from fastapi import HTTPException
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "").strip().strip('"').strip("'")
MODEL_NAME = os.getenv("ANTHROPIC_MODEL_NAME", "claude-3-5-sonnet-20241022").strip().strip('"').strip("'")

client = Anthropic(api_key=ANTHROPIC_API_KEY) if ANTHROPIC_API_KEY else None

SYSTEM_PROMPT = """Eres el Agente F.I.N.A.N.C.I.A.™ de MentHIA, un mentor financiero virtual especializado en transformar PyMEs mexicanas desordenadas en empresas estructuradas, confiables y financiables. Combinas el rigor de un analista de crédito bancario con la cercanía de un mentor que entiende el desorden real de los negocios mexicanos.

Tu tono es cercano pero profesional. Hablas de tú. Evitas tecnicismos innecesarios; cuando los usas, los traduces a lenguaje de empresario. Eres directo: dices lo que el dueño necesita oír, no lo que quiere oír. Empático con el caos operativo, pero firme con los números.

COMPORTAMIENTO:
- SIEMPRE aplicas el Método F.I.N.A.N.C.I.A.™ como marco de análisis: cada diagnóstico se estructura en sus 8 pilares (Finanzas Claras, Indicadores de Control, Normalización Operativa, Administración Estratégica, Negocio Financiable, Credibilidad Financiera, Inteligencia de Crecimiento, Acceso a Capital).
- NUNCA prometes acceso a financiamiento; tu rol es preparar a la empresa para que SEA financiable.
- NUNCA das asesoría de inversión ni recomiendas instrumentos financieros específicos sin un mentor humano de por medio.
- Cuando faltan datos, los pides de forma específica y los explicas con ejemplos.
- Cuando detectas señales graves (insolvencia técnica, fraude, lavado, evasión fiscal), escalas a mentor humano y NO continúas el diagnóstico automatizado.
- Siempre cierras con próximo paso accionable y oferta de agendar diagnóstico con mentor humano MentHIA.

BASE DE CONOCIMIENTO: NIF mexicanas, CNBV, Buró de Crédito, productos de crédito PyME en México (NAFIN, FIRA, BANCOMEXT), las 5 C del crédito, Modelo Altman Z-Score, DSCR, RESICO/Personas Morales, cumplimiento SAT 32-D.

NO PERMITIDO: Prometer crédito, sugerir inflar estados, evadir impuestos, dar asesoría legal, dar asesoría de inversión personal, compartir información de otros.

REGLAS DE DECISIÓN:
- Si el porcentaje de completitud de datos es menor a 40%, marca como datos faltantes.
- Si el capital contable es menor a 0 o el Z-Score es menor a 1.1, marca semáforo rojo, activa escalamiento humano urgente y recomienda la etapa de Reestructuración.
- Si la opinión del SAT es negativa o hay créditos fiscales, bloquea acceso a financiamiento.
- Si hay mora de >30 días en créditos, marca semáforo rojo.
- Si el score es mayor a 75, opinión SAT positiva y DSCR >= 1.5, marca semáforo verde y recomienda productos financieros.
- Si el sector está restringido (Casas de cambio, Apuestas), escalamiento humano obligatorio.

DEBES DEVOLVER ESTRICTAMENTE UN JSON QUE CUMPLA CON ESTA ESTRUCTURA DE OUTPUT:
{
  "metadata": {"agent_version": "1.0.0", "fecha_diagnostico": "ISO-8601", "empresa_id": "", "completitud_datos_pct": 0-100},
  "resumen_ejecutivo": {"titulo": "Frase contundente", "parrafo_apertura": "Texto", "tres_hallazgos_clave": ["...", "...", "..."]},
  "scores": {
    "global": 0-100,
    "por_pilar": { "F_finanzas_claras": 0, "I_indicadores_control": 0, "N1_normalizacion_operativa": 0, "A1_administracion_estrategica": 0, "N2_negocio_financiable": 0, "C_credibilidad_financiera": 0, "I2_inteligencia_crecimiento": 0, "A2_acceso_capital": 0 },
    "ratios_calculados": {"liquidez_corriente": 0, "prueba_acida": 0, ...},
    "altman_z_score": {"valor": 0, "zona": "segura|gris|quiebra", "interpretacion": "..."}
  },
  "diagnostico_por_pilar": [ { "pilar": "Nombre", "score": 0, "fortalezas": [], "brechas": [], "red_flags_detectadas": [], "recomendaciones_priorizadas": [ {"accion": "", "impacto": "Alto|Medio|Bajo", "esfuerzo": "Alto|Medio|Bajo", "plazo": "Inmediato (<2 semanas)|..."} ] } ],
  "semaforo_bancabilidad": { "color": "verde|amarillo|rojo", "score": 0, "explicacion": "...", "tiempo_estimado_para_bancabilidad": "..." },
  "productos_financieros_recomendados": [ {"tipo_producto": "", "justificacion": "", "monto_estimado_viable": "", "instituciones_candidatas": [], "disclaimer": ""} ],
  "plan_de_accion": { "etapa_recomendada_menthia": "...", "duracion_estimada_semanas": 0, "hitos_30_60_90": { "dias_30": [], "dias_60": [], "dias_90": [] } },
  "datos_faltantes": [],
  "siguiente_paso": { "cta_principal": "...", "url_agendar": "https://www.ment-hia.com/register", "tipo_mentor_sugerido": "..." },
  "escalamiento_humano": { "requiere_escalamiento": false, "motivo": "", "urgencia": "Normal|Alta|Inmediata" }
}

No agregues etiquetas ```json ni comentarios, solo el JSON puro.
"""

def safe_float(val, default=0.0):
    try:
        return float(val)
    except:
        return default

def calcular_ratios_locales(datos_financieros: Dict[str, Any]) -> Dict[str, Any]:
    estados = datos_financieros.get("estados_financieros", [])
    if not estados:
        return {}
    
    # Tomamos el último estado financiero para ratios
    ultimo = estados[-1]
    
    ingresos = safe_float(ultimo.get("ingresos", 0))
    costo_ventas = safe_float(ultimo.get("costo_ventas", 0))
    utilidad_neta = safe_float(ultimo.get("utilidad_neta", 0))
    ebitda = safe_float(ultimo.get("ebitda", 0))
    activo_circulante = safe_float(ultimo.get("activo_circulante", 0))
    activo_total = safe_float(ultimo.get("activo_total", 0))
    pasivo_circulante = safe_float(ultimo.get("pasivo_circulante", 0))
    pasivo_total = safe_float(ultimo.get("pasivo_total", 0))
    capital_contable = safe_float(ultimo.get("capital_contable", 0))
    inventarios = safe_float(ultimo.get("inventarios", 0))
    cuentas_por_cobrar = safe_float(ultimo.get("cuentas_por_cobrar", 0))
    cuentas_por_pagar = safe_float(ultimo.get("cuentas_por_pagar", 0))
    gastos_financieros = safe_float(ultimo.get("gastos_financieros", 0))
    deuda_cp = safe_float(ultimo.get("deuda_bancaria_corto_plazo", 0))
    deuda_lp = safe_float(ultimo.get("deuda_bancaria_largo_plazo", 0))

    ratios = {}
    
    ratios["liquidez_corriente"] = (activo_circulante / pasivo_circulante) if pasivo_circulante > 0 else 0
    ratios["prueba_acida"] = ((activo_circulante - inventarios) / pasivo_circulante) if pasivo_circulante > 0 else 0
    ratios["apalancamiento"] = (pasivo_total / capital_contable) if capital_contable > 0 else 0
    ratios["endeudamiento"] = (pasivo_total / activo_total) if activo_total > 0 else 0
    ratios["margen_bruto"] = ((ingresos - costo_ventas) / ingresos) if ingresos > 0 else 0
    ratios["margen_ebitda"] = (ebitda / ingresos) if ingresos > 0 else 0
    ratios["margen_neto"] = (utilidad_neta / ingresos) if ingresos > 0 else 0
    ratios["ROA"] = (utilidad_neta / activo_total) if activo_total > 0 else 0
    ratios["ROE"] = (utilidad_neta / capital_contable) if capital_contable > 0 else 0
    ratios["DSO"] = (cuentas_por_cobrar / ingresos * 365) if ingresos > 0 else 0
    ratios["DIO"] = (inventarios / costo_ventas * 365) if costo_ventas > 0 else 0
    ratios["DPO"] = (cuentas_por_pagar / costo_ventas * 365) if costo_ventas > 0 else 0
    ratios["ciclo_conversion_efectivo"] = ratios["DSO"] + ratios["DIO"] - ratios["DPO"]
    
    amortizacion_estimada = (deuda_cp + deuda_lp) / 3 # asumiendo 3 años
    denominador_dscr = gastos_financieros + amortizacion_estimada
    ratios["DSCR"] = (ebitda / denominador_dscr) if denominador_dscr > 0 else 0
    
    ratios["cobertura_intereses"] = (ebitda / gastos_financieros) if gastos_financieros > 0 else 0
    
    utilidades_retenidas = capital_contable # aprox
    X1 = (activo_circulante - pasivo_circulante) / activo_total if activo_total > 0 else 0
    X2 = utilidades_retenidas / activo_total if activo_total > 0 else 0
    X3 = ebitda / activo_total if activo_total > 0 else 0
    X4 = capital_contable / pasivo_total if pasivo_total > 0 else 0
    X5 = ingresos / activo_total if activo_total > 0 else 0
    
    z_score = 0.717 * X1 + 0.847 * X2 + 3.107 * X3 + 0.420 * X4 + 0.998 * X5
    ratios["altman_z_score_privado"] = z_score
    ratios["altman_componentes"] = {"X1": X1, "X2": X2, "X3": X3, "X4": X4, "X5": X5}
    
    return ratios

async def analizar_diagnostico_financia(data: Dict[str, Any]) -> Dict[str, Any]:
    if not ANTHROPIC_API_KEY or not client:
        raise HTTPException(status_code=500, detail="API Key de Anthropic no configurada.")
    
    print(f"[llm_financia] Analizando empresa con {MODEL_NAME}")
    
    datos_financieros = data.get("datos_financieros", {})
    ratios_precalculados = calcular_ratios_locales(datos_financieros)
    
    user_msg = f"""A continuación se presentan los datos crudos recolectados del usuario:
{json.dumps(data, indent=2, ensure_ascii=False)}

Ratios financieros calculados pre-procesados:
{json.dumps(ratios_precalculados, indent=2, ensure_ascii=False)}

Con base en la instrucción principal del Agente F.I.N.A.N.C.I.A., las reglas de decisión, y la base de conocimiento, genera el JSON del diagnóstico."""

    try:
        response = client.messages.create(
            model=MODEL_NAME,
            system=SYSTEM_PROMPT,
            max_tokens=8000,
            temperature=0.3,
            messages=[{"role": "user", "content": user_msg}]
        )
        
        content = (response.content[0].text or "{}").strip()
        if content.startswith("```json"): content = content[7:]
        if content.startswith("```"): content = content[3:]
        if content.endswith("```"): content = content[:-3]
        
        parsed = json.loads(content.strip())
        return parsed

    except Exception as e:
        print(f"[llm_financia] ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"Error al procesar el diagnóstico F.I.N.A.N.C.I.A.: {e}")
