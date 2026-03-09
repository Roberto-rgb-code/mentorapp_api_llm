---

# MentorApp Backend API

API de FastAPI para MentorApp — Análisis y asistencia LLM.

---

## 🚀 Requisitos Previos

* [Docker](https://www.docker.com/get-started) instalado y funcionando en tu equipo.
* (Opcional, para desarrollo local) Python 3.9+ y `pip` (si NO usas Docker).

---

## 📥 Clonar el Proyecto

```sh
git clone https://github.com/TU_USUARIO/mentorapp-backend.git
cd mentorapp-backend
```

---

## 🛡️ Variables de Entorno

La API requiere un archivo `.env` en la raíz del proyecto para funcionar.
Copia el ejemplo y personalízalo:

```sh
cp .env.example .env
```

### Ejemplo de `.env`

```env
# Clave de OpenAI (requerida)
OPENAI_API_KEY=sk-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx

# Clave de xAI Grok (si usas Grok)
XAI_API_KEY=xai-xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
```

**Nota:**
¡Nunca subas tu `.env` real al repo! (está ignorado por `.gitignore`).

---

## 🐳 Dockerización

### 1. Construir la imagen

```sh
docker build -t mentorapp-backend .
```

### 2. Ejecutar el contenedor

```sh
docker run --env-file .env -p 8000:8000 mentorapp-backend
```

Esto dejará la API disponible en [http://127.0.0.1:8000](http://127.0.0.1:8000)

---

## 🧪 Probar la API

Puedes probar que está viva con:

```sh
curl http://127.0.0.1:8000/
```

Respuesta esperada:

```json
{ "status": "ok", "msg": "MentorApp backend online." }
```

### Endpoints principales

* **POST `/api/chatbot`** — Chat LLM (Grok/xAI si XAI_API_KEY, si no OpenAI)
* **POST `/api/diagnostico/analyze`** — Analiza un diagnóstico (OpenAI)
* **POST `/api/diagnostico/historico`** — Análisis histórico de diagnósticos
* **POST `/api/diagnostico/reporte-pdf`** — Genera un reporte PDF
* **POST `/api/consultants/validate`** — Valida un perfil de consultor mediante IA (ver [CONSULTANT_VALIDATION_README.md](./CONSULTANT_VALIDATION_README.md))

---

## 📝 Desarrollo Local (opcional, sin Docker)

1. Instala un entorno virtual:

   ```sh
   python -m venv venv
   source venv/bin/activate  # Linux/macOS
   .\venv\Scripts\activate   # Windows
   ```
2. Instala las dependencias:

   ```sh
   pip install -r requirements.txt
   ```
3. Copia tu `.env` (si no lo tienes):

   ```sh
   cp .env.example .env
   ```
4. Ejecuta FastAPI:

   ```sh
   uvicorn app.main:app --reload
   ```

---

## 💡 Notas útiles

* Actualiza tu `.env` cada vez que cambies las claves.
* Si usas otra ruta o puerto, actualízalo en tu frontend.
* Para desplegar en producción, asegúrate de no exponer tus claves en logs ni en el repo.

---

## 📂 Archivos importantes

* `.env.example` — Ejemplo de variables de entorno.
* `.gitignore` — Ignora `venv/`, `__pycache__/`, `.env` y archivos temporales.
* `Dockerfile` — Contenedor listo para producción o desarrollo.
* `requirements.txt` — Dependencias Python.
* `CONSULTANT_VALIDATION_README.md` — Documentación del sistema de validación de consultores.

---


