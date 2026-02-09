# Desplegar mentorapp_api_llm en Railway

Guía paso a paso para migrar el backend de Render a Railway.

---

## Requisitos previos

- Cuenta en [Railway](https://railway.app/) (con GitHub o email).
- Repositorio con `mentorapp_api_llm` en GitHub (o el repo de mentoria con esta carpeta).
- API Key de OpenAI para las variables de entorno.

**Importante:** En el repo de mentoria, la carpeta `mentorapp_api_llm` está en `.gitignore`. Para desplegar en Railway desde el mismo repo tienes que **quitar** `mentorapp_api_llm` del `.gitignore`, hacer commit y push de esa carpeta. O bien crear un **repositorio aparte** solo para mentorapp_api_llm y conectar ese repo en Railway.

---

## Paso 1: Crear proyecto en Railway

1. Entra a [railway.app](https://railway.app/) e inicia sesión.
2. Clic en **"New Project"**.
3. Elige **"Deploy from GitHub repo"**.
4. Conecta tu cuenta de GitHub si aún no está conectada.
5. Selecciona el repositorio donde está el código (ej. el repo de mentoria).
6. Railway creará un proyecto y detectará el servicio. Si pregunta **"What is the root directory?"**, indica: **`mentorapp_api_llm`** (carpeta raíz del backend).

---

## Paso 2: Configurar raíz del servicio

Si el repo es el de mentoria (raíz = mentoria) y el backend está en una subcarpeta:

1. En el proyecto, abre el **servicio** que creó Railway.
2. Ve a **Settings**.
3. En **"Root Directory"** (o **"Source"** → **Root Directory**) escribe:
   ```
   mentorapp_api_llm
   ```
4. Guarda.

Así Railway construye y despliega solo la carpeta `mentorapp_api_llm`.

---

## Paso 3: Variables de entorno

1. En el servicio, ve a la pestaña **Variables** (o **"Variables"** en el menú).
2. Añade estas variables (clic en **"+ New Variable"** o **"Raw Editor"**):

| Variable | Valor | Obligatorio |
|----------|--------|-------------|
| `OPENAI_API_KEY` | `sk-...` (tu API key de OpenAI) | Sí |
| `OPENAI_MODEL_NAME` | `gpt-4o` (o `gpt-4o-mini`) | No (default: gpt-4o-mini) |

3. Guarda. Railway redeployará solo si hace falta; si no, haz un **Redeploy** manual.

---

## Paso 4: Comando de inicio (si no usa railway.toml)

Si Railway no toma el comando del `railway.toml`:

1. En el servicio → **Settings**.
2. Busca **"Start Command"** o **"Custom Start Command"**.
3. Pon:
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port $PORT
   ```
4. Guarda.

Con el `railway.toml` incluido en el repo, normalmente no hace falta este paso.

---

## Paso 5: Generar dominio público

1. En el servicio, ve a **Settings** (o pestaña **"Networking"**).
2. En **"Public Networking"** / **"Generate Domain"** clic en **"Generate Domain"**.
3. Railway te dará una URL como:  
   `https://mentorapp-api-llm-production-xxxx.up.railway.app`
4. Copia esa URL; será tu **NEXT_PUBLIC_BACKEND_URL** en el frontend.

---

## Paso 6: Deploy

1. Si no se ha desplegado solo, en el servicio clic en **"Deploy"** o **"Redeploy"**.
2. Espera a que el **build** y el **deploy** terminen (Estado: **Success** / **Active**).
3. Abre la URL del dominio en el navegador. Deberías ver algo como:
   ```json
   {"status":"ok","msg":"MentorApp LLM backend online.","openai_configured":true,"model":"gpt-4o"}
   ```

---

## Paso 7: Probar el diagnóstico general

Desde tu máquina (o Postman):

```bash
curl -X POST https://TU-DOMINIO.up.railway.app/api/diagnostico/general/analyze \
  -H "Content-Type: application/json" \
  -d '{"userId":"test","nombreEmpresa":"Test SA","respuestas":{"estrategia_1":"C","finanzas_1":"D"}}'
```

O desde la raíz del repo:

```bash
cd mentorapp_api_llm
BACKEND_URL=https://TU-DOMINIO.up.railway.app node test_produccion_api.js
```

Sustituye `TU-DOMINIO` por el dominio que te dio Railway.

---

## Paso 8: Actualizar el frontend (mentoria)

1. En el repo de mentoria, en **production** (Vercel o donde esté):
   - Añade o edita la variable de entorno:
   - **Nombre:** `NEXT_PUBLIC_BACKEND_URL`
   - **Valor:** `https://TU-DOMINIO.up.railway.app` (sin barra final)
2. En local, en tu `.env` o `.env.local`:
   ```
   NEXT_PUBLIC_BACKEND_URL=https://TU-DOMINIO.up.railway.app
   ```
3. Redespliega el frontend para que tome la nueva URL.

---

## Resumen de archivos para Railway

- **`railway.toml`** – Comando de inicio y política de reinicio.
- **`nixpacks.toml`** – Build con Python 3.10 y comando de start (por si Nixpacks se usa en lugar de Dockerfile).
- **`Dockerfile`** – Opcional; si existe, Railway puede usarlo y aplica `PORT` con `CMD`.
- **`requirements.txt`** – Dependencias Python (ya existía).

---

## Problemas frecuentes

| Problema | Qué hacer |
|----------|-----------|
| Build falla | Revisa que **Root Directory** sea `mentorapp_api_llm` y que `requirements.txt` esté en esa carpeta. |
| "Application failed to respond" | Comprueba que el **Start Command** use `$PORT` y `--host 0.0.0.0`. |
| 502 / timeout | Espera 1–2 min tras el deploy; si sigue, revisa logs del servicio en Railway. |
| OpenAI errors | Verifica que `OPENAI_API_KEY` esté bien en Variables y sin espacios. |

---

## Dejar de usar Render

Cuando Railway funcione bien:

1. En Render, puedes pausar o eliminar el servicio antiguo.
2. Deja solo `NEXT_PUBLIC_BACKEND_URL` apuntando a la URL de Railway en producción.
