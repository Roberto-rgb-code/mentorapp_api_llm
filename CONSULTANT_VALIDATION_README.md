# Validación de Consultores - MentHIA

## 📋 Descripción

Este módulo implementa el sistema de validación de consultores mediante IA para la plataforma MentHIA, siguiendo el prompt maestro y criterios de evaluación definidos en el documento de especificación.

## 🚀 Endpoint

### POST `/api/consultants/validate`

Valida un perfil de consultor usando OpenAI según el prompt maestro de MentHIA.

#### Request Body

```json
{
  "form_data": {
    "fullName": "Juan Pérez",
    "email": "juan@example.com",
    "professionalName": "Juan Pérez Consultoría",
    "languages": ["español", "inglés"],
    "linkedin": "https://linkedin.com/in/juanperez",
    "website": "https://juanperez.com",
    "professionalType": "consultor_independiente",
    "specializationAreas": ["Estrategia empresarial", "Finanzas"],
    "experienceDescription": "Más de 15 años de experiencia...",
    "totalYearsExperience": 15,
    "consultingYearsExperience": 10,
    "companyTypes": ["PYMES", "Medianas"],
    "industries": ["Servicios", "Manufactura"],
    "certifications": ["Certificación en Estrategia"],
    "achievements": "Crecimiento del 200% en empresas asesoradas",
    "hasExecutiveRoles": true,
    "executiveRolesDetails": "Director de Estrategia en...",
    "hasPublicSpeaking": true,
    "publicSpeakingDetails": "Ponente en eventos de...",
    "publicReferences": ["https://articulo.com/juan"],
    "serviceTypes": ["Diagnósticos empresariales", "Sesiones 1 a 1"],
    "motivation": "Ayudar a PYMES a crecer",
    "weeklyAvailability": 10,
    "aiOpenness": "si",
    "aiOpennessReason": "",
    "currentTools": ["CRM", "Herramientas de análisis"]
  },
  "public_data": {
    "linkedin_info": "Información extraída de LinkedIn...",
    "website_info": "Información del sitio web...",
    "articles": ["Artículo 1", "Artículo 2"],
    "events": ["Evento 1", "Evento 2"]
  }
}
```

**Nota:** `public_data` es opcional. Si no se proporciona, la validación se basará únicamente en `form_data`.

#### Response

```json
{
  "resumen_ejecutivo_ia": "Perfil con más de 15 años de experiencia directiva en empresas medianas, enfoque estratégico claro y fuerte afinidad con PYMES. Cuenta con presencia pública consistente y apertura al uso de herramientas de inteligencia artificial. Recomendado para diagnósticos estratégicos y sesiones de crisis.",
  "trust_score": 88,
  "nivel_sugerido": "consultor_senior",
  "desglose_dimensiones": {
    "experiencia": 27,
    "especializacion": 16,
    "reputacion": 15,
    "enfoque_pyme": 13,
    "afinidad_ia": 9,
    "riesgos": 0
  },
  "riesgos_detectados": ["Ninguno"],
  "recomendacion_final": "APROBAR",
  "justificacion": "Score: 88/100. Perfil sólido con experiencia comprobable y especialización clara. Alineado con valores MentHIA."
}
```

#### Campos de Respuesta

- **resumen_ejecutivo_ia**: Resumen generado por IA (máx. 120 palabras)
- **trust_score**: Score de 0-100 (MentHIA Trust Score™)
- **nivel_sugerido**: `"especialista"` | `"consultor_senior"` | `"mentor_ejecutivo"`
- **desglose_dimensiones**: Desglose del score por dimensión
  - **experiencia**: 0-30 puntos
  - **especializacion**: 0-20 puntos
  - **reputacion**: 0-20 puntos
  - **enfoque_pyme**: 0-15 puntos
  - **afinidad_ia**: 0-10 puntos
  - **riesgos**: 0 a -5 puntos
- **riesgos_detectados**: Lista de riesgos o `["Ninguno"]`
- **recomendacion_final**: `"APROBAR"` | `"APROBAR CONDICIONADO"` | `"REVISIÓN HUMANA"` | `"NO APROBAR"`
- **justificacion**: Justificación breve y objetiva

## 📊 Sistema de Scoring

El **MentHIA Trust Score™** se calcula con la siguiente ponderación:

| Dimensión | Peso | Rango |
|-----------|------|-------|
| Experiencia comprobable | 30% | 0-30 |
| Especialización | 20% | 0-20 |
| Autoridad / Reputación | 20% | 0-20 |
| Enfoque PYME | 15% | 0-15 |
| Afinidad con IA | 10% | 0-10 |
| Riesgos reputacionales | -5% | 0 a -5 |

### Criterios de Decisión

| Score | Resultado |
|-------|-----------|
| 85-100 | Aprobado inmediato |
| 70-84 | Aprobado condicionado |
| 50-69 | Revisión humana |
| < 50 | No aprobado |

## 🔧 Uso desde el Frontend

### Ejemplo con fetch

```javascript
const validateConsultant = async (formData, publicData = null) => {
  try {
    const response = await fetch('https://tu-api.com/api/consultants/validate', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        form_data: formData,
        public_data: publicData
      })
    });
    
    const result = await response.json();
    return result;
  } catch (error) {
    console.error('Error validando consultor:', error);
    throw error;
  }
};
```

### Ejemplo con axios

```javascript
import axios from 'axios';

const validateConsultant = async (formData, publicData = null) => {
  try {
    const response = await axios.post(
      'https://tu-api.com/api/consultants/validate',
      {
        form_data: formData,
        public_data: publicData
      }
    );
    return response.data;
  } catch (error) {
    console.error('Error validando consultor:', error);
    throw error;
  }
};
```

## 🛡️ Manejo de Errores

El módulo incluye manejo robusto de errores:

1. **Sin API Key de OpenAI**: Retorna respuesta de fallback basada en datos básicos
2. **Error de parsing JSON**: Retorna fallback con mensaje de error
3. **Error de OpenAI**: Retorna fallback con mensaje de error
4. **Datos incompletos**: El sistema intenta inferir valores razonables

## 📝 Notas de Implementación

- El módulo sigue el mismo patrón que los otros módulos LLM (`llm_general.py`, `llm_profundo.py`, etc.)
- Usa `response_format={"type": "json_object"}` para garantizar respuestas estructuradas
- Incluye validación y normalización de respuestas
- Tiene fallback robusto en caso de errores
- Temperatura baja (0.3) para análisis más objetivo

## 🔄 Integración con Frontend

Para integrar este endpoint en el frontend de Next.js:

1. Crear API route en `pages/api/consultants/validate.ts` que llame a este backend
2. O llamar directamente desde el frontend al backend de FastAPI
3. Guardar resultados en Firestore en el documento del usuario

## ✅ Testing

Para probar el endpoint:

```bash
curl -X POST http://localhost:8000/api/consultants/validate \
  -H "Content-Type: application/json" \
  -d '{
    "form_data": {
      "fullName": "Test User",
      "totalYearsExperience": 10,
      "specializationAreas": ["Estrategia"]
    }
  }'
```

## 📚 Referencias

- Prompt maestro: Documento de especificación de validación de consultores
- Sistema de scoring: Sección B del documento
- Criterios de evaluación: Sección C del documento
