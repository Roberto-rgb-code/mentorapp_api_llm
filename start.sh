#!/bin/sh
# Script de arranque para Railway/Docker - evita que $PORT no se expanda
PORT=${PORT:-8000}
exec uvicorn app.main:app --host 0.0.0.0 --port "$PORT"
