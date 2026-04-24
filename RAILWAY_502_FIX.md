# Solución 502 en Railway

## Problema
- `connection refused` / `Application failed to respond`
- La URL devuelve 502

## Revisar en Railway Dashboard

### 1. Target Port (causa frecuente de 502)
Railway → tu servicio → **Settings** → **Networking** → **Public Networking**
- Si hay **"Target Port"** configurado (ej. 3000), debe coincidir con el puerto donde escucha tu app.
- La app usa la variable `PORT` que Railway inyecta (ej. 8080).
- **Solución:** deja Target Port **vacío** (para que use PORT) o pon el mismo valor (ej. 8080 si los logs muestran ese puerto).

### 2. Repo y Root Directory
- **Source:** debe ser el repo **`Roberto-rgb-code/mentorapp_api_llm`** (NO MentorIAvercel/mentoria).
- **Root Directory:** vacío (la raíz del repo es el backend).

### 3. Logs del Deploy
- **Deployments** → último deploy → **View Logs**
- Busca: `Uvicorn running on http://0.0.0.0:XXXX` (XXXX = puerto, ej. 8080).
- Si ves ese mensaje pero sigues con 502, el problema suele ser **Target Port** en Settings.

### 4. Variables de entorno
- `OPENAI_API_KEY` = tu clave (obligatorio para que el LLM funcione).
- No definas `PORT` manualmente; Railway la inyecta.

## Si creas un proyecto nuevo
1. **New Project** → **Deploy from GitHub** → repo **mentorapp_api_llm**
2. Root Directory: vacío
3. Variables: `OPENAI_API_KEY`
4. **Networking** → **Generate Domain**
5. Deja **Target Port** vacío
