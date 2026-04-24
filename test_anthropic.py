import asyncio
from app.llm_general import analizar_diagnostico_general
import json

dummy_data = {
    "sector": "Tecnología",
    "numeroEmpleados": "20",
    "respuestas": {
        "estrategia_1": "C",
        "estrategia_2": "C",
        "estrategia_3": "C",
        "estrategia_4": "B",
        "estrategia_5": "D",
        "finanzas_1": "A",
        "finanzas_2": "B"
    }
}

async def main():
    print("Enviando petición a Claude...")
    res = await analizar_diagnostico_general(dummy_data)
    print("\nRespuesta obtenida:\n")
    print(json.dumps(res, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    asyncio.run(main())
