# 🔑 Configuración de API Keys para LLMs

## 📋 Variables de Entorno Requeridas

Crea un archivo `.env` en el directorio `mentorapp_api_llm/` con las siguientes variables:

```env
# ============================================
# API Keys para LLMs
# ============================================

# OpenAI API Key (Requerida para diagnósticos)
# Obtén tu key en: https://platform.openai.com/api-keys
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Modelo de OpenAI a usar (opcional, por defecto: gpt-4o)
OPENAI_MODEL_NAME=gpt-4o

# xAI Grok API Key (Opcional, para chatbots)
# Obtén tu key en: https://console.x.ai/
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# ============================================
# Configuración adicional
# ============================================

# Habilitar modo demo en caso de error (1 = sí, 0 = no)
DIAG_DEMO_ON_ERROR=1
```

## 🚀 Pasos para Configurar

### 1. Crear el archivo `.env`

**Windows (PowerShell):**
```powershell
cd mentorapp_api_llm
New-Item -Path .env -ItemType File
```

**Linux/Mac:**
```bash
cd mentorapp_api_llm
touch .env
```

### 2. Obtener las API Keys

#### OpenAI API Key (Requerida)
1. Ve a: https://platform.openai.com/api-keys
2. Inicia sesión o crea una cuenta
3. Haz clic en "Create new secret key"
4. Copia la key (formato: `sk-...`)
5. **⚠️ IMPORTANTE:** Solo se muestra una vez, guárdala bien

#### xAI Grok API Key (Opcional - Solo para chatbots)
1. Ve a: https://console.x.ai/
2. Inicia sesión o crea una cuenta
3. Crea una nueva API key
4. Copia la key (formato: `xai-...`)

### 3. Editar el archivo `.env`

Abre el archivo `.env` y reemplaza los placeholders con tus API keys reales:

```env
OPENAI_API_KEY=sk-tu-key-real-aqui
XAI_API_KEY=xai-tu-key-real-aqui
```

### 4. Verificar la Configuración

**Windows (PowerShell):**
```powershell
# Verificar que las variables se cargan correctamente
python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', '✅ Configurada' if os.getenv('OPENAI_API_KEY') else '❌ No configurada')"
```

**Linux/Mac:**
```bash
# Verificar que las variables se cargan correctamente
python3 -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', '✅ Configurada' if os.getenv('OPENAI_API_KEY') else '❌ No configurada')"
```

## 🔍 Verificación de Uso

### Endpoints que usan OpenAI:
- ✅ `/api/diagnostico/general/analyze` - Diagnóstico General
- ✅ `/api/diagnostico/profundo/analyze` - Diagnóstico Profundo  
- ✅ `/api/diagnostico/emergencia/analyze` - Diagnóstico Emergencia
- ✅ `/api/diagnostico/analyze` - Análisis legacy
- ✅ `/api/diagnostico/historico` - Análisis histórico
- ✅ `/api/diagnostico/reporte-pdf` - Generación de PDFs

### Endpoints que usan xAI Grok:
- ✅ `/api/chatbot` - Chatbot principal (MentorIA)
- ✅ `/api/chatbot-ayuda` - Chatbot de ayuda general

## ⚠️ Notas Importantes

1. **Seguridad:**
   - ❌ **NUNCA** subas el archivo `.env` al repositorio
   - ✅ El archivo `.env` ya está en `.gitignore`
   - ✅ No compartas tus API keys públicamente

2. **Costos:**
   - OpenAI cobra por uso (tokens procesados)
   - xAI Grok también tiene costos asociados
   - Monitorea tu uso en los dashboards de cada plataforma

3. **Fallback:**
   - Si no hay API key, los módulos usan análisis fallback (sin LLM)
   - El análisis fallback es básico pero funcional

4. **Modelos:**
   - Por defecto usa `gpt-4o` (más potente pero más caro)
   - Puedes cambiar a `gpt-4o-mini` para ahorrar costos
   - Edita `OPENAI_MODEL_NAME` en el `.env`

## 🧪 Probar la Configuración

Ejecuta el servidor y prueba un endpoint:

```bash
# Activar entorno virtual
cd mentorapp_api_llm
source venv/bin/activate  # Linux/Mac
.\venv\Scripts\activate  # Windows

# Ejecutar servidor
uvicorn app.main:app --reload

# En otra terminal, probar el endpoint
curl http://localhost:8000/
```

Si todo está bien, deberías ver:
```json
{"status": "ok", "msg": "MentorApp backend online."}
```

## 📚 Recursos

- [OpenAI API Documentation](https://platform.openai.com/docs)
- [xAI Grok Documentation](https://docs.x.ai/)
- [Python-dotenv Documentation](https://pypi.org/project/python-dotenv/)

