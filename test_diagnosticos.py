#!/usr/bin/env python3
"""
Script de prueba para los 3 diagnósticos empresariales
Prueba: emergencia, general y profundo
"""

import asyncio
import json
import sys
import os
from datetime import datetime

# Agregar el directorio app al path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

from app.llm_emergencia import analizar_diagnostico_emergencia
from app.llm_general import analizar_diagnostico_general
from app.llm_profundo import analizar_diagnostico_profundo

# ===== DATOS DE PRUEBA =====

# Datos de prueba para Diagnóstico de Emergencia
DATOS_EMERGENCIA = {
    "userId": "test_user_001",
    "nombreSolicitante": "Juan Pérez",
    "puestoSolicitante": "Director General",
    "nombreEmpresa": "TechSolutions MX",
    "rfcEmpresa": "TSM123456ABC",
    "giroIndustria": "Tecnología y Software",
    "numeroEmpleados": "15",
    "antiguedadEmpresa": "5",
    "ubicacion": "Ciudad de México, CDMX",
    "telefonoContacto": "5551234567",
    "correoElectronico": "juan@techsolutions.mx",
    "sitioWebRedes": "www.techsolutions.mx",
    "areaMayorProblema": "Finanzas y flujo de caja",
    "problematicaEspecifica": "No tengo efectivo suficiente para cubrir nómina del próximo mes. Las ventas han caído 60% en los últimos 3 meses y tengo deudas pendientes con proveedores. Estoy muy preocupado porque no sé cómo voy a pagar.",
    "principalPrioridad": "Conseguir liquidez inmediata para mantener operaciones",
    "problemaMasUrgente": "Falta de efectivo para nómina y proveedores críticos",
    "impactoDelProblema": "Afecta directamente a finanzas, operaciones y personal. Si no pago nómina, el equipo se irá.",
    "continuidadNegocio": "4",
    "flujoEfectivo": "No",
    "ventasDisminuido": "Si",
    "personalAfectado": "Si",
    "operacionesCalidadTiempo": "Parcialmente",
    "suministroMateriales": "No",
    "capacidadAdaptarse": "2",
    "apoyoExterno": "Estoy buscando",
    "createdAt": datetime.now().isoformat()
}

# Datos de prueba para Diagnóstico General
DATOS_GENERAL = {
    "userId": "test_user_002",
    "nombreSolicitante": "María González",
    "puestoSolicitante": "CEO",
    "nombreEmpresa": "Innovación Digital SA",
    "rfcEmpresa": "IDS789012XYZ",
    "giroIndustria": "Consultoría Digital",
    "numeroEmpleados": "25",
    "antiguedadEmpresa": "8",
    "ubicacion": "Guadalajara, Jalisco",
    "telefonoContacto": "3339876543",
    "correoElectronico": "maria@innovaciondigital.mx",
    "sitioWebRedes": "www.innovaciondigital.mx",
    "areaMayorProblema": "Marketing y ventas",
    "problematicaEspecifica": "Necesitamos aumentar ventas pero no tenemos un plan claro de marketing",
    "principalPrioridad": "Crear estrategia de marketing digital efectiva",
    
    # Dirección General
    "dg_misionVisionValores": "3",
    "dg_objetivosClaros": "3",
    "dg_analisisFoda": "2",
    "dg_situacionGeneralEmpresa": "Empresa en crecimiento pero con falta de estructura",
    "dg_principalProblemaActual": "Falta de estrategia clara y procesos definidos",
    
    # Finanzas
    "fa_margenGanancia": "4",
    "fa_estadosFinancierosActualizados": "3",
    "fa_liquidezSuficiente": "4",
    "fa_razonBajaLiquidez": "",
    "fa_gastosIdentificadosControlados": "3",
    
    # Operaciones
    "op_capacidadCubreDemanda": "4",
    "op_procesosDocumentadosFacilesSeguir": "2",
    "op_calidadProductosServicios": "4",
    "op_factorBajaCalidad": "",
    "op_inventariosControladosRotacionAdecuada": "3",
    
    # Marketing/Ventas
    "mv_clienteIdealValora": "2",
    "mv_planMarketingDocumentado": "2",
    "mv_canalesVentaAdecuados": "3",
    "mv_canalExplorar": "Marketing digital y redes sociales",
    "mv_marcaReconocidaValorada": "3",
    
    # RH
    "rh_organigramaClaroFuncionesDefinidas": "3",
    "rh_personalCapacitado": "4",
    "rh_climaLaboralProductividad": "4",
    "rh_factorAfectaClimaLaboral": "",
    "rh_sistemaRemuneracionCompetitivoJusto": "4",
    
    # Logística
    "lc_proveedoresCumplenTiempoForma": "4",
    "lc_procesosAseguranEntregasTiempo": "3",
    "lc_costosLogisticosControladosCompetitivos": "3",
    "lc_principalObstaculoCadenaSuministro": "Falta de coordinación entre áreas",
    "lc_areaMayorAtencionOperacion": "Mejorar comunicación entre equipos",
    
    "createdAt": datetime.now().isoformat()
}

# Datos de prueba para Diagnóstico Profundo (simplificado pero completo)
DATOS_PROFUNDO = {
    "userId": "test_user_003",
    "nombreSolicitante": "Carlos Ramírez",
    "puestoSolicitante": "Fundador y Director",
    "nombreEmpresa": "Manufactura Avanzada",
    "rfcEmpresa": "MA456789DEF",
    "giroIndustria": "Manufactura",
    "numeroEmpleados": "50",
    "antiguedadEmpresa": "12",
    "ubicacion": "Monterrey, Nuevo León",
    "telefonoContacto": "8187654321",
    "correoElectronico": "carlos@manufacturaavanzada.mx",
    "sitioWebRedes": "www.manufacturaavanzada.mx",
    "areaMayorProblema": "Operaciones y calidad",
    "problematicaEspecifica": "Tenemos problemas de calidad que están afectando nuestra reputación y tenemos procesos poco documentados",
    "principalPrioridad": "Mejorar calidad y estandarizar procesos",
    
    # Dirección General
    "dg_misionVisionValores": "4",
    "dg_objetivosClaros": "4",
    "dg_planEstrategicoDocumentado": "3",
    "dg_revisionAvancePlan": "3",
    "dg_factoresExternos": "3",
    "dg_impideCumplirMetas": "Falta de seguimiento y métricas claras",
    "dg_capacidadAdaptacion": "3",
    "dg_comoSeTomanDecisiones": "Principalmente por el director, con poca participación del equipo",
    "dg_colaboradoresParticipan": "2",
    "dg_porQueNoParticipan": "Falta de comunicación y estructura para involucrarlos",
    
    # Finanzas
    "fa_margenGanancia": "4",
    "fa_estadosFinancierosActualizados": "4",
    "fa_presupuestosAnuales": "3",
    "fa_liquidezCubreObligaciones": "4",
    "fa_gastosControlados": "3",
    "fa_causaProblemasFinancieros": "",
    "fa_indicadoresFinancieros": "3",
    "fa_analizanEstadosFinancieros": "3",
    "fa_porQueNoSeAnalizan": "",
    "fa_herramientasSoftwareFinanciero": "3",
    "fa_situacionFinancieraGeneral": "3",
    
    # Operaciones
    "op_capacidadProductivaCubreDemanda": "3",
    "op_porQueNoCubreDemanda": "Cuellos de botella en producción",
    "op_procesosDocumentados": "2",
    "op_estandaresCalidadCumplen": "2",
    "op_controlesErrores": "2",
    "op_tiemposEntregaCumplen": "3",
    "op_porQueNoCumplen": "Procesos ineficientes y falta de control",
    "op_eficienciaProcesosOptima": "2",
    "op_personalConoceProcedimientos": "2",
    "op_porQueNoConocen": "No hay documentación clara",
    "op_indicadoresOperativos": "2",
    
    # Marketing y Ventas
    "mv_clienteIdealNecesidades": "3",
    "mv_planEstrategiasMarketing": "3",
    "mv_impactoCanalesVenta": "Ventas directas funcionan bien, pero queremos expandir",
    "mv_canalesVentaActuales": "Ventas directas, algunos distribuidores",
    "mv_marcaReconocida": "3",
    "mv_estudiosSatisfaccionCliente": "2",
    "mv_porQueNoHaceEstudios": "No hemos priorizado esto",
    "mv_indicadoresDesempenoComercial": "3",
    "mv_equipoVentasCapacitado": "3",
    "mv_politicasDescuentosPromociones": "2",
    
    # Recursos Humanos
    "rh_organigramaFuncionesClaras": "3",
    "rh_personalCapacitado": "3",
    "rh_climaLaboralFavoreceProductividad": "3",
    "rh_programasMotivacion": "2",
    "rh_causaClimaLaboralComplejo": "",
    "rh_evaluacionesDesempeno": "2",
    "rh_indicadoresRotacionPersonal": "2",
    "rh_liderazgoJefesIntermedios": "3",
    "rh_cuantasPersonasTrabajan": "50",
    
    # Logística y Cadena de Suministro
    "lcs_proveedoresCumplen": "3",
    "lcs_entregasClientesPuntuales": "3",
    "lcs_costosLogisticosCompetitivos": "3",
    "lcs_problemasLogisticosPunto": "Algunos retrasos en entregas",
    "lcs_poderNegociacionProveedores": "3",
    "lcs_indicadoresLogisticos": "2",
    
    # Habilidades del Empresario
    "he_liderInspiraEquipo": "3",
    "he_tomaDecisionesDatos": "3",
    "he_resilienteDificultades": "4",
    "he_invierteDesarrolloPropio": "3",
    "he_porQueNoInvierte": "",
    "he_visionNegocioClara": "4",
    "he_apoyoAsesoresMentores": "2",
    
    # Cultura de Innovación
    "ci_mejoranProductosServicios": "3",
    "ci_recogeImplementaIdeasPersonal": "2",
    "ci_invierteTecnologiaInnovacion": "2",
    "ci_dispuestoAsumirRiesgos": "3",
    "ci_porQueNoInnova": "Falta de recursos y tiempo",
    "ci_protegePropiedadIntelectual": "2",
    "ci_fomentaCulturaCambio": "2",
    
    # Retos y Aspiraciones
    "ra_mayorReto": "Mejorar calidad y procesos para crecer",
    "ra_queMotiva": "Ver la empresa crecer y ser reconocida",
    "ra_cambiosPersonalesNecesarios": "Mejorar comunicación y delegación",
    "ra_lograrEn5Anos": "Ser líder en el mercado regional",
    "ra_queEnorgullece": "El equipo y la calidad de algunos productos",
    "ra_quePreocupa": "La competencia y mantener calidad",
    "ra_principalProblematica": "Calidad y procesos",
    "ra_habilidadesFortalecer": "Liderazgo y gestión de procesos",
    "ra_tanSatisfechoRolActual": "3",
    "ra_referenteParaEquipo": "3",
    "ra_situacionFinancieraGeneral": "3",
    
    "createdAt": datetime.now().isoformat()
}

# ===== FUNCIONES DE PRUEBA =====

def print_section(title: str):
    """Imprime un separador visual"""
    print("\n" + "="*80)
    print(f"  {title}")
    print("="*80 + "\n")

def print_result(tipo: str, resultado: dict):
    """Imprime el resultado de forma legible"""
    print(f"\n✅ DIAGNÓSTICO {tipo.upper()} - RESULTADO:")
    print("-" * 80)
    
    # Campos principales según el tipo
    if tipo == "emergencia":
        print(f"📋 Diagnóstico Rápido:")
        print(f"   {resultado.get('diagnostico_rapido', 'N/A')[:200]}...")
        print(f"\n⚡ Acciones Inmediatas ({len(resultado.get('acciones_inmediatas', []))}):")
        for i, accion in enumerate(resultado.get('acciones_inmediatas', [])[:5], 1):
            print(f"   {i}. {accion}")
        print(f"\n🚨 Riesgo General: {resultado.get('riesgo_general', 'N/A').upper()}")
        print(f"\n💡 Recomendaciones Clave ({len(resultado.get('recomendaciones_clave', []))}):")
        for i, rec in enumerate(resultado.get('recomendaciones_clave', [])[:5], 1):
            print(f"   {i}. {rec}")
        
        # Nuevos campos
        if 'analisis_sentimiento' in resultado:
            sent = resultado['analisis_sentimiento']
            print(f"\n😊 Análisis de Sentimiento:")
            print(f"   - Sentimiento: {sent.get('sentimiento', 'N/A')}")
            print(f"   - Nivel de estrés: {sent.get('nivel_estres', 'N/A')}/3")
        
        if 'patrones_detectados' in resultado:
            patrones = resultado['patrones_detectados']
            print(f"\n🔍 Patrones Detectados:")
            print(f"   - Patrones críticos: {', '.join(patrones.get('patrones_criticos', []))}")
            print(f"   - Alerta temprana: {'SÍ' if patrones.get('alerta_temprana') else 'NO'}")
        
        if 'recomendaciones_innovadoras' in resultado:
            print(f"\n💡 Recomendaciones Innovadoras ({len(resultado.get('recomendaciones_innovadoras', []))}):")
            for i, rec in enumerate(resultado.get('recomendaciones_innovadoras', [])[:3], 1):
                print(f"   {i}. {rec}")
        
        if 'siguiente_paso' in resultado:
            print(f"\n🎯 Siguiente Paso:")
            print(f"   {resultado.get('siguiente_paso', 'N/A')}")
    
    elif tipo == "general":
        print(f"📋 Resumen Ejecutivo:")
        print(f"   {resultado.get('resumen_ejecutivo', 'N/A')[:200]}...")
        print(f"\n📊 Puntuación de Madurez: {resultado.get('puntuacion_madurez_promedio', 'N/A')}/5.0")
        print(f"📈 Nivel de Madurez: {resultado.get('nivel_madurez_general', 'N/A').upper().replace('_', ' ')}")
        print(f"\n🎯 Áreas de Oportunidad ({len(resultado.get('areas_oportunidad', []))}):")
        for i, area in enumerate(resultado.get('areas_oportunidad', [])[:5], 1):
            print(f"   {i}. {area}")
        print(f"\n💡 Recomendaciones Clave ({len(resultado.get('recomendaciones_clave', []))}):")
        for i, rec in enumerate(resultado.get('recomendaciones_clave', [])[:5], 1):
            print(f"   {i}. {rec}")
        
        # Nuevos campos
        if 'correlaciones_detectadas' in resultado:
            print(f"\n🔗 Correlaciones Detectadas ({len(resultado.get('correlaciones_detectadas', []))}):")
            for corr in resultado.get('correlaciones_detectadas', [])[:2]:
                print(f"   - {corr.get('mensaje', 'N/A')} (Impacto: {corr.get('impacto', 'N/A')})")
        
        if 'predicciones' in resultado:
            print(f"\n📊 Predicciones ({len(resultado.get('predicciones', []))}):")
            for pred in resultado.get('predicciones', [])[:2]:
                print(f"   - {pred.get('escenario', 'N/A').upper()}: {pred.get('descripcion', 'N/A')[:100]}...")
                print(f"     Probabilidad: {pred.get('probabilidad', 'N/A')}, Tiempo: {pred.get('tiempo', 'N/A')}")
        
        if 'recomendaciones_innovadoras' in resultado:
            print(f"\n💡 Recomendaciones Innovadoras ({len(resultado.get('recomendaciones_innovadoras', []))}):")
            for i, rec in enumerate(resultado.get('recomendaciones_innovadoras', [])[:3], 1):
                print(f"   {i}. {rec}")
        
        if 'siguiente_paso' in resultado:
            print(f"\n🎯 Siguiente Paso:")
            print(f"   {resultado.get('siguiente_paso', 'N/A')}")
    
    elif tipo == "profundo":
        print(f"📋 Análisis Detallado:")
        print(f"   {resultado.get('analisis_detallado', 'N/A')[:200]}...")
        print(f"\n🌟 Oportunidades Estratégicas ({len(resultado.get('oportunidades_estrategicas', []))}):")
        for i, opp in enumerate(resultado.get('oportunidades_estrategicas', [])[:3], 1):
            print(f"   {i}. {opp}")
        print(f"\n⚠️ Riesgos Identificados ({len(resultado.get('riesgos_identificados', []))}):")
        for i, riesgo in enumerate(resultado.get('riesgos_identificados', [])[:3], 1):
            print(f"   {i}. {riesgo}")
        print(f"\n📋 Plan de Acción ({len(resultado.get('plan_accion_sugerido', []))}):")
        for i, accion in enumerate(resultado.get('plan_accion_sugerido', [])[:3], 1):
            print(f"   {i}. {accion}")
        
        # Estructura consultiva
        if 'estructura_consultiva' in resultado:
            ec = resultado['estructura_consultiva']
            print(f"\n📊 Estructura Consultiva:")
            print(f"   - Resumen: {ec.get('resumen_ejecutivo', 'N/A')[:150]}...")
            print(f"   - Dominios analizados: {len(ec.get('tabla_dominios', []))}")
            if ec.get('tabla_dominios'):
                print(f"   - Top 3 dominios críticos:")
                for dom in ec.get('tabla_dominios', [])[:3]:
                    print(f"     • {dom.get('nombre', 'N/A')}: {dom.get('severidad', 'N/A')} (Prioridad: {dom.get('prioridad', 'N/A')})")
        
        # Roadmap inteligente
        if 'roadmap_inteligente' in resultado:
            rm = resultado['roadmap_inteligente']
            print(f"\n🗺️ Roadmap Inteligente:")
            print(f"   - Orden de implementación: {', '.join(rm.get('orden_implementacion', [])[:5])}")
            print(f"   - Ruta crítica: {', '.join(rm.get('ruta_critica', [])[:3])}")
            print(f"   - Tiempo estimado: {rm.get('tiempo_estimado', 'N/A')}")
            print(f"   - Impacto esperado: {rm.get('impacto_esperado', 'N/A')}")
            if rm.get('dominios_bloqueantes'):
                print(f"   - Dominios bloqueantes: {', '.join(rm.get('dominios_bloqueantes', [])[:2])}")
        
        if 'recomendaciones_innovadoras' in resultado:
            print(f"\n💡 Recomendaciones Innovadoras ({len(resultado.get('recomendaciones_innovadoras', []))}):")
            for i, rec in enumerate(resultado.get('recomendaciones_innovadoras', [])[:3], 1):
                print(f"   {i}. {rec}")
        
        if 'siguiente_paso' in resultado:
            print(f"\n🎯 Siguiente Paso:")
            print(f"   {resultado.get('siguiente_paso', 'N/A')}")
    
    print("\n" + "-" * 80)

async def test_emergencia():
    """Prueba el diagnóstico de emergencia"""
    print_section("PRUEBA: DIAGNÓSTICO DE EMERGENCIA")
    try:
        resultado = await analizar_diagnostico_emergencia(DATOS_EMERGENCIA)
        print_result("emergencia", resultado)
        
        # Validaciones
        assert "diagnostico_rapido" in resultado, "❌ Falta 'diagnostico_rapido'"
        assert "acciones_inmediatas" in resultado, "❌ Falta 'acciones_inmediatas'"
        assert "riesgo_general" in resultado, "❌ Falta 'riesgo_general'"
        assert resultado["riesgo_general"] in ["bajo", "moderado", "alto", "critico"], "❌ Riesgo inválido"
        
        print("✅ Validación: Estructura correcta")
        return True
    except Exception as e:
        print(f"❌ ERROR en diagnóstico de emergencia: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_general():
    """Prueba el diagnóstico general"""
    print_section("PRUEBA: DIAGNÓSTICO GENERAL")
    try:
        resultado = await analizar_diagnostico_general(DATOS_GENERAL)
        print_result("general", resultado)
        
        # Validaciones
        assert "resumen_ejecutivo" in resultado, "❌ Falta 'resumen_ejecutivo'"
        assert "areas_oportunidad" in resultado, "❌ Falta 'areas_oportunidad'"
        assert "recomendaciones_clave" in resultado, "❌ Falta 'recomendaciones_clave'"
        assert "puntuacion_madurez_promedio" in resultado, "❌ Falta 'puntuacion_madurez_promedio'"
        assert "nivel_madurez_general" in resultado, "❌ Falta 'nivel_madurez_general'"
        assert resultado["nivel_madurez_general"] in ["muy_bajo", "bajo", "medio", "alto", "muy_alto"], "❌ Nivel inválido"
        
        print("✅ Validación: Estructura correcta")
        return True
    except Exception as e:
        print(f"❌ ERROR en diagnóstico general: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def test_profundo():
    """Prueba el diagnóstico profundo"""
    print_section("PRUEBA: DIAGNÓSTICO PROFUNDO")
    try:
        resultado = await analizar_diagnostico_profundo(DATOS_PROFUNDO)
        print_result("profundo", resultado)
        
        # Validaciones
        assert "analisis_detallado" in resultado, "❌ Falta 'analisis_detallado'"
        assert "oportunidades_estrategicas" in resultado, "❌ Falta 'oportunidades_estrategicas'"
        assert "riesgos_identificados" in resultado, "❌ Falta 'riesgos_identificados'"
        assert "plan_accion_sugerido" in resultado, "❌ Falta 'plan_accion_sugerido'"
        assert "estructura_consultiva" in resultado, "❌ Falta 'estructura_consultiva'"
        
        print("✅ Validación: Estructura correcta")
        return True
    except Exception as e:
        print(f"❌ ERROR en diagnóstico profundo: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Ejecuta todas las pruebas"""
    print("\n" + "="*80)
    print("  🧪 PRUEBAS DE DIAGNÓSTICOS EMPRESARIALES - MENTHIA")
    print("="*80)
    print(f"\n⏰ Inicio: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    resultados = {
        "emergencia": False,
        "general": False,
        "profundo": False
    }
    
    # Prueba 1: Emergencia
    resultados["emergencia"] = await test_emergencia()
    await asyncio.sleep(1)  # Pausa entre pruebas
    
    # Prueba 2: General
    resultados["general"] = await test_general()
    await asyncio.sleep(1)
    
    # Prueba 3: Profundo
    resultados["profundo"] = await test_profundo()
    
    # Resumen final
    print_section("RESUMEN DE PRUEBAS")
    print(f"✅ Emergencia: {'PASÓ' if resultados['emergencia'] else 'FALLÓ'}")
    print(f"✅ General: {'PASÓ' if resultados['general'] else 'FALLÓ'}")
    print(f"✅ Profundo: {'PASÓ' if resultados['profundo'] else 'FALLÓ'}")
    
    total_pasados = sum(1 for v in resultados.values() if v)
    print(f"\n📊 Total: {total_pasados}/3 pruebas pasaron")
    
    if total_pasados == 3:
        print("\n🎉 ¡TODAS LAS PRUEBAS PASARON EXITOSAMENTE!")
    else:
        print("\n⚠️ Algunas pruebas fallaron. Revisa los errores arriba.")
    
    print(f"\n⏰ Fin: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
    
    return total_pasados == 3

if __name__ == "__main__":
    try:
        exit_code = 0 if asyncio.run(main()) else 1
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\n⚠️ Pruebas interrumpidas por el usuario")
        sys.exit(1)
    except Exception as e:
        print(f"\n\n❌ ERROR FATAL: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

