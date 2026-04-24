#!/usr/bin/env python3
"""
Test del chatbot MentHIA (API local).
Usa el .env de esta carpeta (OPENAI_API_KEY o XAI_API_KEY según configuración).
Ejecutar con el servidor en marcha: uvicorn app.main:app --reload
"""
import os
import sys

# Cargar .env de la carpeta del monorepo API
from pathlib import Path
_env_path = Path(__file__).resolve().parent / ".env"
if _env_path.exists():
    from dotenv import load_dotenv
    load_dotenv(_env_path)
    print(f"[OK] .env cargado desde {_env_path}")
else:
    print(f"[AVISO] No se encontró {_env_path}")

import httpx

API_BASE = os.getenv("CHATBOT_TEST_URL", "http://127.0.0.1:8000")
CHATBOT_URL = f"{API_BASE}/api/chatbot"

def test_ping():
    """Comprueba que la API esté viva."""
    try:
        r = httpx.get(f"{API_BASE}/", timeout=5.0)
        if r.status_code == 200:
            data = r.json()
            print(f"  Ping: {data.get('msg', data)}")
            print(f"  OpenAI configurada: {data.get('openai_configured', '?')}")
            return True
    except Exception as e:
        print(f"  Error ping: {e}")
    return False

def test_chatbot(message: str):
    """Envía un mensaje al chatbot y devuelve la respuesta."""
    try:
        r = httpx.post(
            CHATBOT_URL,
            json={"message": message, "messages": []},
            timeout=20.0,
        )
        if r.status_code != 200:
            print(f"  HTTP {r.status_code}: {r.text[:200]}")
            return None
        data = r.json()
        reply = data.get("reply", "")
        return reply
    except Exception as e:
        print(f"  Error: {e}")
        return None

def main():
    print("=" * 60)
    print("Test Chatbot MentHIA (monorepo mentorapp_api_llm)")
    print("=" * 60)
    print(f"URL API: {API_BASE}")
    print()

    # Comprobar variables de entorno (no mostrar valores)
    openai_key = os.getenv("OPENAI_API_KEY", "")
    xai_key = os.getenv("XAI_API_KEY", "")
    print("Credenciales en .env:")
    print(f"  OPENAI_API_KEY: {'[OK] configurada' if openai_key else '[NO] no configurada'}")
    print(f"  XAI_API_KEY:    {'[OK] configurada' if xai_key else '[NO] no configurada'}")
    print()

    if not test_ping():
        print("\n[FALLO] La API no responde. Esta corriendo?")
        print("   Ejecuta: uvicorn app.main:app --reload")
        sys.exit(1)

    print("\n--- Mensajes de prueba ---\n")

    tests = [
        "Hola",
        "Soy empresa",
        "¿Qué es MentHIA?",
    ]
    for msg in tests:
        print(f"Usuario: {msg}")
        reply = test_chatbot(msg)
        if reply is not None:
            print(f"Asistente: {reply[:300]}{'...' if len(reply) > 300 else ''}")
            print()
        else:
            print("Asistente: (sin respuesta)")
            print()

    print("=" * 60)
    print("Test finalizado.")
    print("=" * 60)

if __name__ == "__main__":
    main()
