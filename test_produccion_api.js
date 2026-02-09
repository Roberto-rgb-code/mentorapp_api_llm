#!/usr/bin/env node
/**
 * Test de la API productiva mentorapp_api_llm en Render
 * URL: https://mentorapp-api-llm-1.onrender.com
 */

// URL productiva (NEXT_PUBLIC_BACKEND_URL en production.env)
const API_BASE = process.env.NEXT_PUBLIC_BACKEND_URL || process.env.BACKEND_URL || 'https://mentorapp-api-llm-1.onrender.com';

// URLs alternativas a probar si la principal falla
const URLS_ALTERNATIVAS = ['https://mentorapp-api-llm-1.onrender.com', 'https://mentorapp-api-llm.onrender.com'];

const DATOS_GENERAL = {
  userId: 'test_prod_001',
  nombreSolicitante: 'María Test',
  nombreEmpresa: 'Innovación Digital SA',
  sector: 'Tecnología',
  numeroEmpleados: '25',
  respuestas: {
    estrategia_1: 'C',
    estrategia_2: 'B',
    estrategia_3: 'C',
    finanzas_1: 'D',
    finanzas_2: 'C',
    marketing_1: 'C',
    operaciones_1: 'D',
    talento_1: 'D',
    tecnologia_1: 'C',
  },
};

async function testPing(base = API_BASE) {
  console.log('\n=== 1. PING ===');
  try {
    const res = await fetch(`${base}/`, { method: 'GET' });
    const text = await res.text();
    console.log('Status:', res.status);
    try {
      const data = JSON.parse(text);
      console.log('Response:', JSON.stringify(data, null, 2));
    } catch (_) {
      console.log('Response (raw):', text.substring(0, 300));
    }
    return res.ok;
  } catch (e) {
    console.error('Error:', e.message);
    return false;
  }
}

async function testDiagnosticoGeneral(base = API_BASE) {
  console.log('\n=== 2. DIAGNÓSTICO GENERAL (formato Mentoria) ===');
  try {
    const res = await fetch(`${base}/api/diagnostico/general/analyze`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(DATOS_GENERAL),
    });
    const text = await res.text();
    let data = {};
    try {
      data = JSON.parse(text);
    } catch (_) {
      console.log('Status:', res.status);
      console.log('Response (raw):', text.substring(0, 400));
      return false;
    }
    console.log('Status:', res.status);
    if (res.ok) {
      console.log('resumen_ejecutivo:', (data.resumen_ejecutivo || '').substring(0, 150) + '...');
      console.log('nivel_madurez_general:', data.nivel_madurez_general);
      console.log('puntuacion_madurez_promedio:', data.puntuacion_madurez_promedio);
      console.log('areas_oportunidad:', data.areas_oportunidad?.length || 0);
    } else {
      console.log('Error response:', JSON.stringify(data, null, 2));
    }
    return res.ok;
  } catch (e) {
    console.error('Error:', e.message);
    return false;
  }
}

async function main() {
  console.log('API Base:', API_BASE);
  console.log('Testing production API...\n');

  let base = API_BASE;
  let pingOk = await testPing(base);

  if (!pingOk) {
    console.log('\n⚠️ Ping falló. Probando URLs alternativas...');
    for (const url of URLS_ALTERNATIVAS) {
      if (url === base) continue;
      console.log('Probando:', url);
      pingOk = await testPing(url);
      if (pingOk) {
        base = url;
        console.log('✅ Esta URL responde:', base);
        break;
      }
    }
  }
  if (!pingOk) {
    console.log('\n⚠️ Render puede estar en cold start. Esperando 60s...');
    await new Promise((r) => setTimeout(r, 60000));
    pingOk = await testPing(base);
  }

  const diagOk = await testDiagnosticoGeneral(base);
  console.log('\n=== RESUMEN ===');
  console.log('Ping:', pingOk ? '✅ OK' : '❌ FALLO');
  console.log('Diagnóstico General:', diagOk ? '✅ OK' : '❌ FALLO');

  process.exit(diagOk ? 0 : 1);
}

main();
