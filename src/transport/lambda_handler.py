"""AWS Lambda entrypoint único para todos los transportes."""

import asyncio

from src.factories import get_container
from src.infrastructure.observability import logger, metrics, tracer
from src.transport.error_handler import TransportErrorHandler, safe_format_response
from src.transport.middleware import apply_middleware_stack
from src.transport.router import get_transport_handler


def _run_async(coro):
    """Ejecuta coroutine de forma segura."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None
    
    if loop and loop.is_running():
        return asyncio.run(coro)
    
    return asyncio.run(coro)


@logger.inject_lambda_context
@tracer.capture_lambda_handler
@metrics.log_metrics
def _handler_impl(event: dict, context) -> dict:
    """Implementación del handler sin middleware.
    
    Detecta el tipo de transporte, parsea el request, procesa con el agente,
    y formatea la respuesta según el transporte.
    
    Args:
        event: Evento de Lambda.
        context: Contexto de Lambda.
        
    Returns:
        Respuesta HTTP formateada según el transporte.
    """
    # Obtener handler de transporte apropiado
    try:
        transport_handler = get_transport_handler(event)
    except ValueError as e:
        logger.exception(
            "Handler no encontrado",
            error=str(e),
            event_path=event.get("requestContext", {}).get("http", {}).get("path", "N/A"),
            event_headers=event.get("headers", {}),
            event_body_type=type(event.get("body")).__name__,
        )
        return {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Tipo de transporte no soportado"}',
        }
    except Exception as e:
        logger.exception(
            "Error inesperado obteniendo handler de transporte",
            error=str(e),
            error_type=type(e).__name__,
            event_path=event.get("requestContext", {}).get("http", {}).get("path", "N/A"),
            event_headers=event.get("headers", {}),
            event_body_type=type(event.get("body")).__name__,
        )
        return {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Error interno del servidor"}',
        }
    
    # Inicializar error handler para este transporte
    error_handler = TransportErrorHandler(transport_handler)
    
    # Parsear request según el transporte
    try:
        user_text, session_id = transport_handler.parse_request(event)
    except Exception as e:
        return error_handler.handle_parse_error(e, event)
    
    logger.info(
        "Procesando mensaje",
        session_id=session_id,
        user_text=user_text[:100],
        transport=transport_handler.__class__.__name__,
    )
    
    # Procesar mensaje con el agente
    try:
        container = get_container()
        processor = container.message_processor()
        
        reply = _run_async(
            processor.process(user_text, session_id=session_id, humanize=True)
        )
        
        logger.info(
            "Respuesta generada",
            session_id=session_id,
            success=reply.success,
            transport=transport_handler.__class__.__name__,
        )
        
        # Formatear respuesta según el transporte
        return safe_format_response(transport_handler, reply)
        
    except Exception as e:
        return error_handler.handle_processing_error(e)


# Aplicar middleware stack
handler = apply_middleware_stack(_handler_impl)
