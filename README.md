Kavak AI Commercial Agent
=========================

Bot comercial impulsado por LLMs para simular a un asesor de Kavak. Responde
preguntas sobre Kavak, recomienda autos del catalogo y calcula financiamiento.

Arquitectura: Ver [ADR.md](ADR.md) para documentación detallada de decisiones arquitectónicas. 

Quickstart
----------
1) Crear un entorno y variables de entorno:

```bash
export OPENAI_API_KEY="..."
export OPENAI_API_BASE_URL="https://api.openai.com/v1"
```

2) Instalar dependencias (ejemplo con uv):

```bash
uv sync
```

3) Probar en local (modo interactivo):

```bash
python src/tests/test_agent.py
```

API local (simulada)
--------------------
El Lambda handler vive en `src/transport/lambda_handler.py` y espera un payload:

```json
{
  "message": "Busco un Toyota Corolla 2020",
  "session_id": "demo-1"
}
```

El response incluye `message`, `success` y `vehicles` (si aplica).

Casos de uso (basados en la prueba tecnica)
------------------------------------------
1) Informacion de Kavak:
   - "Que beneficios ofrece Kavak?"
   - "Tienen garantia?"
   - "Como funciona el proceso de compra?"

2) Recomendacion de inventario:
   - "Busco un Mazda 3 2019"
   - "Quiero un coche barato"
   - "Tengo 350000 de presupuesto"

3) Manejo de lenguaje natural y typos:
   - "Busco un Toyta Corola"
   - "Quiero el mas barato"

4) Financiamiento:
   - "Opciones de financiamiento para el Toyota Corolla"
   - Enganche 20%, tasa 10% anual, plazos 3-6 anos

Pruebas locales
--------------
Script interactivo y batch en `src/tests/test_agent.py`:

```bash
python src/tests/test_agent.py
```

Tests unitarios (pytest)
------------------------
Instala dependencias de testing:

```bash
uv sync --extra test
```

Ejecutar tests:

```bash
pytest -v
```

Cobertura:

```bash
pytest --cov=. --cov-report=html --cov-report=term-missing
```

Despliegue con Serverless (AWS Lambda)
--------------------------------------
Se incluye `serverless.yml` con:
- HTTP API Gateway (POST /agent y POST /twilio/webhook)
- Variables de entorno para OpenAI, Twilio y Powertools
- Layer de Powertools via `POWERTOOLS_LAYER_ARN`
- Layer de dependencias via `serverless-python-requirements`
- Alarmas basicas con `serverless-plugin-aws-alerts`
- Logging con AWS Lambda Powertools (Logger)

Variables de entorno clave:
- `OPENAI_API_KEY`
- `OPENAI_API_BASE_URL`
- `INTEREST_RATE`
- `TWILIO_ACCOUNT_SID`
- `TWILIO_AUTH_TOKEN`
- `TWILIO_WHATSAPP_NUMBER`
- `POWERTOOLS_SERVICE_NAME`
- `POWERTOOLS_METRICS_NAMESPACE`
- `LOG_LEVEL`
- `POWERTOOLS_TRACE_DISABLED`
- `POWERTOOLS_LAYER_ARN`
- `ALERTS_TOPIC_ARN`

Roadmap sugerido (resumen)
--------------------------
Produccion:
- Infra as code + CI/CD para despliegue a Lambda/API Gateway.
- Observabilidad con trazas, metricas y alertas.
- Cache y stores para contexto (Redis/DynamoDB).

Evaluacion del agente:
- Suite de pruebas con casos reales y edge cases.
- Metricas: tasa de respuesta correcta, CSAT simulado, conversion.
- Revisiones humanas de conversaciones.

No regresiones:
- Test suite versionada con snapshots.
- Replay de conversaciones historicas.
- Tests automaticos en CI con umbrales de calidad.

Reproducibilidad
----------------
Este README funciona como manual basico de instalacion y prueba local.
