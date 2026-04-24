"""
Pruebas HTTP del endpoint /api/finanzas/interpretar (sin llamar a Anthropic real).

Requisito: dependencias instaladas en este entorno, p. ej.:
  pip install -r requirements.txt

Ejecutar desde la carpeta mentorapp_api_llm:
  python test_finanzas_interpret_api.py
"""
import unittest
from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from app.main import app


class TestFinanzasInterpretAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.client = TestClient(app)

    def test_get_returns_405(self):
        r = self.client.get("/api/finanzas/interpretar")
        self.assertEqual(r.status_code, 405)

    def test_missing_payload_400(self):
        r = self.client.post("/api/finanzas/interpretar", json={})
        self.assertEqual(r.status_code, 400)

    def test_payload_not_object_400(self):
        r = self.client.post("/api/finanzas/interpretar", json={"payload": "x"})
        self.assertEqual(r.status_code, 400)

    def test_success_with_mocked_llm(self):
        want = {
            "ok": True,
            "interpretacion": "Texto simulado del LLM.",
            "modelo": "claude-mock",
            "fallback": False,
        }
        with patch(
            "app.main.interpretar_finanzas_narrativa",
            new=AsyncMock(return_value=want),
        ):
            r = self.client.post(
                "/api/finanzas/interpretar",
                json={"payload": {"moneda": "MXN", "periodo_reciente": "2024"}},
            )
        self.assertEqual(r.status_code, 200, r.text)
        data = r.json()
        self.assertTrue(data.get("ok"))
        self.assertEqual(data.get("interpretacion"), "Texto simulado del LLM.")
        self.assertEqual(data.get("modelo"), "claude-mock")


if __name__ == "__main__":
    unittest.main()
