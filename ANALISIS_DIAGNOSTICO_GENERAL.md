# Análisis del Diagnóstico General - mentorapp_api_llm

**Fecha:** 31 enero 2025  
**Estado:** ✅ Todos los tests pasan | Diagnóstico general operativo

---

## Resumen Ejecutivo

El módulo **mentorapp_api_llm** es un backend Python (FastAPI) para análisis de diagnósticos empresariales con IA (OpenAI GPT-4o). El diagnóstico general (`llm_general.py`) analiza respuestas de empresas, calcula nivel de madurez y genera recomendaciones ejecutivas.

**Resultado de pruebas:** 4/4 pruebas pasaron (emergencia, general API, general Mentoria, profundo).

---

## Arquitectura

### mentorapp_api_llm (Python FastAPI)
- **Ubicación:** `mentorapp_api_llm/`
- **Endpoints:**
  - `POST /api/diagnostico/general/analyze` - Diagnóstico General
  - `POST /api/diagnostico/general-analyze` - Legacy (mismo handler)
  - `POST /api/diagnostico/emergencia/analyze`
  - `POST /api/diagnostico/profundo/analyze`
- **Modelo:** OpenAI GPT-4o (configurable vía `OPENAI_MODEL_NAME`)

### mentoria (Next.js) - Frontend
- **Diagnóstico General:** `pages/dashboard/diagnostico/general.tsx`
- **API local:** `pages/api/diagnostico/general/analyze.ts` (implementación propia en TypeScript)
- **Cuestionario:** `lib/diagnostico-questions.ts` (estrategia, finanzas, marketing, operaciones, talento, tecnología, escalabilidad)

**Nota:** El frontend mentoria usa su propia API Next.js; no llama a mentorapp_api_llm por defecto. mentorapp_api_llm es un backend alternativo/paralelo que **ahora acepta ambos formatos**.

---

## Formatos de Datos Soportados

### 1. Formato API nativo (dg_, fa_, op_, mv_, rh_, lc_)
```json
{
  "userId": "...",
  "nombreEmpresa": "Innovación Digital SA",
  "nombreSolicitante": "María González",
  "dg_misionVisionValores": "3",
  "fa_margenGanancia": "4",
  "op_procesosDocumentadosFacilesSeguir": "2",
  "mv_planMarketingDocumentado": "2",
  "rh_personalCapacitado": "4",
  "lc_proveedoresCumplenTiempoForma": "4"
}
```
Valores: "1" a "5" (escala Likert).

### 2. Formato Mentoria (respuestas A-E)
```json
{
  "userId": "...",
  "nombreEmpresa": "Consultoría SA",
  "respuestas": {
    "estrategia_1": "C",
    "estrategia_2": "B",
    "finanzas_1": "D",
    "marketing_1": "C",
    "operaciones_1": "D",
    "talento_1": "D",
    "tecnologia_1": "C",
    "escalabilidad_1": "B"
  }
}
```
Valores: A=1, B=2, C=3, D=4, E=5. Se convierte automáticamente al formato interno.

---

## Mapeo de Áreas

| Bloque Mentoria | Prefijo API | Área |
|-----------------|-------------|------|
| estrategia | dg_ | Dirección General |
| finanzas | fa_ | Finanzas |
| marketing | mv_ | Marketing/Ventas |
| operaciones | op_ | Operaciones |
| talento | rh_ | Recursos Humanos |
| tecnologia | lc_ | Logística |
| escalabilidad | dg_ | Dirección General |

---

## Estructura de Salida (JSON)

```json
{
  "resumen_ejecutivo": "5-7 líneas de lectura estratégica",
  "hallazgos_clave": ["hallazgos importantes"],
  "oportunidades": ["máx 5, accionables"],
  "riesgos": ["máx 3, críticos"],
  "prioridades_30_dias": ["acciones próximos 30 días"],
  "nivel_madurez": "valor 1-5 con explicación",
  "comentarios_adicionales": "insights o alertas",
  "areas_oportunidad": ["áreas con oportunidad"],
  "recomendaciones_clave": ["recomendaciones principales"],
  "puntuacion_madurez_promedio": 3.18,
  "nivel_madurez_general": "medio",
  "recomendaciones_innovadoras": ["ideas innovadoras"],
  "siguiente_paso": "próximo paso más importante",
  "correlaciones_detectadas": []
}
```

Niveles de madurez: `muy_bajo`, `bajo`, `medio`, `alto`, `muy_alto`.

---

## Flujo de Análisis (llm_general.py)

1. **Normalización:** Si hay `respuestas` (formato Mentoria), se convierte a dg_/fa_/op_/mv_/rh_/lc_ con valores 1-5.
2. **Fallback sin API key:** Si no hay OPENAI_API_KEY, se genera respuesta basada en promedios y correlaciones locales.
3. **Análisis local:** Se extraen puntuaciones Likert, se calcula promedio, nivel de madurez y correlaciones (área más débil/fuerte, riesgos sistémicos).
4. **LLM:** Se envía prompt con datos formateados y contexto pre-analizado a GPT-4o.
5. **Validación:** Se valida y enriquece la respuesta (resumen_ejecutivo, puntuacion_madurez_promedio, nivel_madurez_general).

---

## Correlaciones Detectadas

- **riesgo_sistemico:** Finanzas y Operaciones débiles simultáneamente.
- **crecimiento_limitado:** Marketing y RH débiles.
- **ejecucion_comprometida:** Dirección débil + otras áreas débiles.

---

## Cómo Ejecutar Tests

```bash
cd mentorapp_api_llm
pip install -r requirements.txt

# Windows: usar UTF-8 para emojis
set PYTHONIOENCODING=utf-8
python test_diagnosticos.py

# O con py:
py -3.13 test_diagnosticos.py
```

Tests incluidos:
- Diagnóstico de Emergencia
- Diagnóstico General (formato API)
- **Diagnóstico General (formato Mentoria)** ← Nuevo
- Diagnóstico Profundo

---

## Variables de Entorno

| Variable | Descripción | Default |
|----------|-------------|---------|
| OPENAI_API_KEY | API key de OpenAI | (requerida para LLM) |
| OPENAI_MODEL_NAME | Modelo a usar | gpt-4o |

---

## Integración con mentoria Frontend

Para que el frontend mentoria use mentorapp_api_llm en lugar de la API Next.js:

1. Configurar `NEXT_PUBLIC_MENTORAPP_API_URL` apuntando al servidor FastAPI (ej. `https://api-menthia.railway.app`).
2. Modificar `pages/api/diagnostico/general/analyze.ts` para hacer proxy a `{MENTORAPP_API_URL}/api/diagnostico/general/analyze` cuando esté configurado.
3. El formato `respuestas` (estrategia_1, finanzas_1, etc.) ya es soportado por mentorapp_api_llm.

---

## Conclusión

- ✅ El diagnóstico general analiza correctamente las respuestas.
- ✅ Acepta formato API nativo (dg_, fa_, etc.) y formato Mentoria (respuestas A-E).
- ✅ Genera resumen ejecutivo, áreas de oportunidad, recomendaciones y nivel de madurez.
- ✅ Fallback robusto cuando no hay API key o falla OpenAI.
- ✅ Tests automatizados pasan para ambos formatos.
