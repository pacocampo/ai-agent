Reporte de Brechas de Cobertura
===============================

rutas no se cubren con pruebas de integración de forma intencional:

- `src/llm/client.py`: Las llamadas al cliente de OpenAI requieren red y API keys.
- `src/llm/prompts.py`: El contenido de los prompts es estático y se valida de forma indirecta.

Estas áreas se cubren mediante pruebas unitarias que mockean llamadas externas.
