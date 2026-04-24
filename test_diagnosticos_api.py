#!/usr/bin/env python3
"""
Script de prueba para los 3 diagnósticos usando la API HTTP
Útil para probar el servidor completo
"""

import requests
import json
from datetime import datetime

API_BASE = "http://localhost:8000"  # Cambia si tu API está en otro puerto

# Mismos datos de prueba que test_diagnosticos.py
DATOS_EMERGENCIA = {
    "userId": "test_user_001",
    "nombreSolicitante": "Juan Pérez",
    "puestoSolicitante": "Director General",
    "nombreEmpresa": "TechSolutions MX",
    "problematicaEspecifica": "No tengo efectivo suficiente para cubrir nómina del próximo mes. Las ventas han caído 60% en los últimos 3 meses.",
    "problemaMasUrgente": "Falta de efectivo para nómina y proveedores críticos",
    "impactoDelProblema": "Afecta directamente a finanzas, operaciones y personal.",
    "continuidadNegocio": "4",
    "flujoEfectivo": "No",
    "ventasDisminuido": "Si",
    "riesgo_general": "alto"
}

DATOS_GENERAL = {
    "userId": "test_user_002",
    "nombreEmpresa": "Innovación Digital SA",
    "dg_misionVisionValores": "3",
    "dg_objetivosClaros": "3",
    "fa_margenGanancia": "4",
    "fa_liquidezSuficiente": "4",
    "op_procesosDocumentadosFacilesSeguir": "2",
    "mv_planMarketingDocumentado": "2",
    "rh_personalCapacitado": "4"
}

DATOS_PROFUNDO = {
    "userId": "test_user_003",
    "nombreEmpresa": "Manufactura Avanzada",
    "dg_misionVisionValores": "4",
    "fa_margenGanancia": "4",
    "op_procesosDocumentados": "2",
    "op_estandaresCalidadCumplen": "2",
    "rh_organigramaFuncionesClaras": "3"
}

def test_endpoint(endpoint: str, datos: dict, nombre: str):
    """Prueba un endpoint de la API"""
    print(f"\n{'='*80}")
    print(f"  🧪 PRUEBA: {nombre}")
    print(f"{'='*80}\n")
    
    try:
        url = f"{API_BASE}{endpoint}"
        print(f"📡 URL: {url}")
        print(f"📦 Datos enviados: {len(json.dumps(datos))} bytes\n")
        
        response = requests.post(url, json=datos, timeout=60)
        
        print(f"📊 Status Code: {response.status_code}")
        
        if response.status_code == 200:
            resultado = response.json()
            print(f"✅ Respuesta recibida exitosamente\n")
            
            # Mostrar campos principales
            if "diagnostico_rapido" in resultado:
                print(f"📋 Diagnóstico: {resultado['diagnostico_rapido'][:150]}...")
                print(f"🚨 Riesgo: {resultado.get('riesgo_general', 'N/A')}")
            elif "resumen_ejecutivo" in resultado:
                print(f"📋 Resumen: {resultado['resumen_ejecutivo'][:150]}...")
                print(f"📊 Madurez: {resultado.get('nivel_madurez_general', 'N/A')} ({resultado.get('puntuacion_madurez_promedio', 'N/A')}/5.0)")
            elif "analisis_detallado" in resultado:
                print(f"📋 Análisis: {resultado['analisis_detallado'][:150]}...")
                if "roadmap_inteligente" in resultado:
                    rm = resultado["roadmap_inteligente"]
                    print(f"🗺️ Roadmap: {rm.get('tiempo_estimado', 'N/A')}, Impacto: {rm.get('impacto_esperado', 'N/A')}")
            
            # Verificar campos nuevos
            campos_nuevos = []
            if "analisis_sentimiento" in resultado:
                campos_nuevos.append("✅ analisis_sentimiento")
            if "patrones_detectados" in resultado:
                campos_nuevos.append("✅ patrones_detectados")
            if "correlaciones_detectadas" in resultado:
                campos_nuevos.append("✅ correlaciones_detectadas")
            if "predicciones" in resultado:
                campos_nuevos.append("✅ predicciones")
            if "roadmap_inteligente" in resultado:
                campos_nuevos.append("✅ roadmap_inteligente")
            if "recomendaciones_innovadoras" in resultado:
                campos_nuevos.append("✅ recomendaciones_innovadoras")
            
            if campos_nuevos:
                print(f"\n💡 Campos nuevos detectados: {', '.join(campos_nuevos)}")
            
            return True
        else:
            print(f"❌ Error: {response.status_code}")
            print(f"Respuesta: {response.text[:500]}")
            return False
            
    except requests.exceptions.ConnectionError:
        print(f"❌ ERROR: No se pudo conectar a {API_BASE}")
        print("   Asegúrate de que el servidor esté corriendo (uvicorn app.main:app)")
        return False
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def main():
    """Ejecuta todas las pruebas HTTP"""
    print("\n" + "="*80)
    print("  🌐 PRUEBAS DE API HTTP - DIAGNÓSTICOS MENTHIA")
    print("="*80)
    print(f"\n⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"🔗 API Base: {API_BASE}\n")
    
    # Verificar que el servidor esté corriendo
    try:
        ping = requests.get(f"{API_BASE}/", timeout=5)
        if ping.status_code == 200:
            print("✅ Servidor está corriendo\n")
        else:
            print("⚠️ Servidor responde pero con código inesperado\n")
    except:
        print("❌ ERROR: El servidor no está corriendo")
        print("   Ejecuta: cd mentorapp_api_llm && uvicorn app.main:app --reload\n")
        return
    
    resultados = {
        "emergencia": test_endpoint("/api/diagnostico/emergencia/analyze", DATOS_EMERGENCIA, "DIAGNÓSTICO DE EMERGENCIA"),
        "general": test_endpoint("/api/diagnostico/general/analyze", DATOS_GENERAL, "DIAGNÓSTICO GENERAL"),
        "profundo": test_endpoint("/api/diagnostico/profundo/analyze", DATOS_PROFUNDO, "DIAGNÓSTICO PROFUNDO"),
    }
    
    print(f"\n{'='*80}")
    print("  📊 RESUMEN")
    print(f"{'='*80}\n")
    
    for nombre, resultado in resultados.items():
        status = "✅ PASÓ" if resultado else "❌ FALLÓ"
        print(f"{status}: {nombre.upper()}")
    
    total = sum(1 for v in resultados.values() if v)
    print(f"\n📊 Total: {total}/3 pruebas pasaron")
    
    if total == 3:
        print("\n🎉 ¡TODAS LAS PRUEBAS HTTP PASARON!")
    else:
        print("\n⚠️ Algunas pruebas fallaron")

if __name__ == "__main__":
    main()

