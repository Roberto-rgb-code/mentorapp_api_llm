# app/llm_vision.py
# Análisis de documentos con OpenAI Vision (GPT-4o)
import os
import json
import base64
import httpx
from typing import Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

# Prompts especializados por tipo de documento
PROMPTS = {
    "financial": """Eres un experto analista financiero. Analiza este documento financiero y extrae información relevante.

EXTRAE Y ANALIZA:
1. **Métricas clave**: ingresos, gastos, margen, utilidad, deudas, activos
2. **Indicadores**: liquidez, rentabilidad, endeudamiento
3. **Tendencias**: crecimiento, estabilidad, riesgos
4. **Alertas**: problemas financieros, señales de alerta
5. **Oportunidades**: áreas de mejora identificadas

Responde en JSON:
{
  "tipo_documento": "estado de resultados|balance general|flujo de caja|otro",
  "periodo": "periodo que cubre el documento",
  "metricas": {
    "ingresos": "valor o N/A",
    "gastos": "valor o N/A", 
    "utilidad_neta": "valor o N/A",
    "margen": "porcentaje o N/A",
    "activos": "valor o N/A",
    "pasivos": "valor o N/A",
    "patrimonio": "valor o N/A"
  },
  "indicadores": {
    "liquidez": "valor o descripción",
    "rentabilidad": "valor o descripción",
    "endeudamiento": "valor o descripción"
  },
  "alertas": ["lista de alertas o problemas detectados"],
  "oportunidades": ["lista de oportunidades de mejora"],
  "resumen": "resumen ejecutivo de 2-3 oraciones",
  "salud_financiera": "critica|debil|estable|saludable|excelente",
  "confianza": "alta|media|baja"
}""",

    "report": """Eres un consultor empresarial experto. Analiza este documento/reporte empresarial.

EXTRAE:
1. **Información clave**: datos importantes del documento
2. **Métricas**: cualquier número o KPI mencionado
3. **Problemas**: desafíos o issues identificados
4. **Recomendaciones**: sugerencias o próximos pasos

Responde en JSON:
{
  "tipo_documento": "descripción del tipo de documento",
  "informacion_clave": ["puntos importantes"],
  "metricas_encontradas": {"nombre": "valor"},
  "problemas_identificados": ["lista de problemas"],
  "recomendaciones": ["lista de recomendaciones"],
  "resumen": "resumen de 2-3 oraciones",
  "relevancia_diagnostico": "alta|media|baja",
  "confianza": "alta|media|baja"
}""",

    "image": """Eres un experto en análisis visual de documentos empresariales. Analiza esta imagen.

Si es una gráfica, tabla, dashboard o visualización:
- Describe qué muestra
- Extrae los datos visibles
- Identifica tendencias

Si es un documento escaneado:
- Extrae el texto importante
- Identifica el tipo de documento
- Resume el contenido

Responde en JSON:
{
  "tipo_contenido": "grafica|tabla|dashboard|documento|foto|otro",
  "descripcion": "qué muestra la imagen",
  "datos_extraidos": {"clave": "valor"},
  "insights": ["observaciones importantes"],
  "resumen": "resumen breve",
  "confianza": "alta|media|baja"
}""",

    "general": """Eres un asistente experto en análisis de documentos empresariales. Analiza este documento y extrae toda la información relevante para un diagnóstico empresarial.

Identifica:
1. Tipo de documento
2. Información clave
3. Métricas o datos cuantitativos
4. Problemas o alertas
5. Oportunidades

Responde en JSON:
{
  "tipo_documento": "descripción",
  "contenido_principal": "de qué trata",
  "informacion_clave": ["puntos importantes"],
  "metricas": {"nombre": "valor"},
  "alertas": ["problemas detectados"],
  "oportunidades": ["mejoras posibles"],
  "resumen": "resumen de 2-3 oraciones",
  "confianza": "alta|media|baja"
}"""
}


async def analyze_document_with_vision(
    image_base64: Optional[str] = None,
    image_url: Optional[str] = None,
    document_type: str = "general",
    mime_type: str = "image/jpeg",
    diagnostic_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """
    Analiza un documento/imagen usando OpenAI Vision (GPT-4o)
    
    Args:
        image_base64: Imagen en base64 (sin prefijo data:)
        image_url: URL de la imagen
        document_type: financial, report, image, general
        mime_type: Tipo MIME de la imagen
        diagnostic_context: Contexto del diagnóstico (empresa, sector, área)
    
    Returns:
        Dict con el análisis del documento
    """
    
    if not OPENAI_API_KEY:
        return {
            "error": "OpenAI API key no configurada",
            "success": False
        }
    
    if not image_base64 and not image_url:
        return {
            "error": "Se requiere image_base64 o image_url",
            "success": False
        }
    
    # Construir contenido de imagen
    if image_base64:
        # Limpiar base64 si tiene prefijo
        if image_base64.startswith("data:"):
            image_content = image_base64
        else:
            image_content = f"data:{mime_type};base64,{image_base64}"
    else:
        image_content = image_url
    
    # Obtener prompt según tipo
    system_prompt = PROMPTS.get(document_type, PROMPTS["general"])
    
    # Agregar contexto si está disponible
    if diagnostic_context:
        context_text = f"""

CONTEXTO DEL DIAGNÓSTICO:
- Empresa: {diagnostic_context.get('empresa', 'No especificada')}
- Sector: {diagnostic_context.get('sector', 'No especificado')}
- Área actual: {diagnostic_context.get('areaActual', 'General')}

Usa este contexto para dar análisis más relevante y específico."""
        system_prompt += context_text
    
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.openai.com/v1/chat/completions",
                headers={
                    "Content-Type": "application/json",
                    "Authorization": f"Bearer {OPENAI_API_KEY}"
                },
                json={
                    "model": "gpt-4o",
                    "messages": [
                        {
                            "role": "system",
                            "content": system_prompt
                        },
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "Analiza este documento y proporciona el análisis completo en formato JSON."
                                },
                                {
                                    "type": "image_url",
                                    "image_url": {
                                        "url": image_content,
                                        "detail": "high"
                                    }
                                }
                            ]
                        }
                    ],
                    "response_format": {"type": "json_object"},
                    "max_tokens": 2500,
                    "temperature": 0.3
                }
            )
            
            if response.status_code != 200:
                return {
                    "error": f"Error de OpenAI: {response.status_code}",
                    "detail": response.text,
                    "success": False
                }
            
            result = response.json()
            analysis_text = result["choices"][0]["message"]["content"]
            
            try:
                analysis = json.loads(analysis_text)
            except json.JSONDecodeError:
                analysis = {
                    "resumen": analysis_text,
                    "error_parsing": True,
                    "confianza": "baja"
                }
            
            # Agregar metadata
            analysis["_metadata"] = {
                "modelo": "gpt-4o",
                "tipo_documento": document_type,
                "tokens_usados": result.get("usage", {}).get("total_tokens", 0)
            }
            
            return {
                "success": True,
                "analysis": analysis
            }
            
    except httpx.TimeoutException:
        return {
            "error": "Timeout al analizar documento",
            "success": False
        }
    except Exception as e:
        return {
            "error": str(e),
            "success": False
        }


# Función de fallback sin Vision (análisis básico)
def analyze_document_fallback(
    filename: str,
    file_type: str,
    diagnostic_context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Análisis básico sin Vision API"""
    
    doc_type = "documento"
    if "financ" in filename.lower() or "balance" in filename.lower():
        doc_type = "documento financiero"
    elif "report" in filename.lower() or "informe" in filename.lower():
        doc_type = "reporte"
    
    empresa = diagnostic_context.get("empresa", "la empresa") if diagnostic_context else "la empresa"
    
    return {
        "success": True,
        "analysis": {
            "tipo_documento": doc_type,
            "resumen": f"Documento '{filename}' recibido para {empresa}. Se recomienda revisión manual para extraer métricas específicas.",
            "informacion_clave": [
                f"Archivo: {filename}",
                f"Tipo: {file_type}",
                "Análisis automático no disponible - revisar manualmente"
            ],
            "alertas": [],
            "oportunidades": ["Digitalizar y estructurar la información del documento"],
            "confianza": "baja",
            "_metadata": {
                "modelo": "fallback",
                "tipo_documento": "general"
            }
        }
    }

