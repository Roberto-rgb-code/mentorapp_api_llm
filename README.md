# mentorapp_api_llm

API **FastAPI** para MentHIA: diagnósticos (general, express, emergencia, profundo), análisis financiero narrativo y **R.E.C.U.P.E.R.A.™** (profesional + express abierto).  
En el monorepo vive en `mentoria/mentorapp_api_llm` (ya no está en `.gitignore`).

## Endpoints principales

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/` | Ping |
| GET | `/health` | Estado |
| POST | `/api/diagnostico/general/analyze` | Diagnóstico general (Anthropic) |
| POST | `/api/diagnostico/express/analyze` | Diagnóstico express (Anthropic) |
| POST | `/api/diagnostico/emergencia/analyze` | Emergencia (OpenAI) |
| POST | `/api/diagnostico/profundo/analyze` | Profundo (OpenAI) |
| POST | `/api/finanzas/interpretar` | Narrativa análisis financiero (`body.payload`) |
| POST | `/api/diagnostico/recupera-profesional/analyze` | **R.E.C.U.P.E.R.A.™ Profesional** (motor + Claude) |
| POST | `/api/diagnostico/recupera-express/analyze` | **R.E.C.U.P.E.R.A.™ Express** (abierto + Claude) |

## Variables de entorno

- `ANTHROPIC_API_KEY` — general, express, finanzas interpret, R.E.C.U.P.E.R.A.
- `ANTHROPIC_MODEL_NAME` o `ANTHROPIC_MODEL` — modelo Claude (según módulo).
- `OPENAI_API_KEY` — emergencia y profundo.

Ver también `CONFIGURAR_API_KEYS.md` y `DEPLOY_RAILWAY.md`.

## Ejecutar en local

```bash
cd mentorapp_api_llm
python -m venv .venv
.venv\Scripts\activate   # Windows
pip install -r requirements.txt
uvicorn app.main:app --reload --host 0.0.0.0 --port 8787
```

En Next.js: `MENTORAPP_LLM_API_URL=http://localhost:8787`

## Repo solo backend (`mentorapp_api_llm` en GitHub)

Desde la raíz del monorepo **mentoria**:

```bash
git subtree split --prefix=mentorapp_api_llm -b mentorapp-api-llm-split
git push https://github.com/Roberto-rgb-code/mentorapp_api_llm.git mentorapp-api-llm-split:main
```

Ajusta URL y rama (`main` / `master`) según el remoto.
