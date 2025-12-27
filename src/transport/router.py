"""Router para detectar y obtener el handler de transporte apropiado."""

from src.core.interfaces import TransportHandler
from src.infrastructure.observability import logger
from src.transport.handlers import ApiTransportHandler, TwilioTransportHandler


# Lista de handlers disponibles (orden importa para detección)
_TRANSPORT_HANDLERS: list[TransportHandler] = [
    TwilioTransportHandler(),  # Más específico primero
    ApiTransportHandler(),      # Fallback genérico
]


def get_transport_handler(event: dict) -> TransportHandler:
    """Obtiene el handler de transporte apropiado para el evento.
    
    Itera sobre los handlers disponibles y retorna el primero
    que puede manejar el evento (can_handle() retorna True).
    
    Args:
        event: Evento de Lambda.
        
    Returns:
        TransportHandler que puede procesar el evento.
        
    Raises:
        ValueError: Si ningún handler puede procesar el evento.
        
    Examples:
        >>> handler = get_transport_handler(event)
        >>> user_text, session_id = handler.parse_request(event)
    """
    # Logging de debugging para entender qué está pasando
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    headers = event.get("headers", {}) or {}
    content_type = headers.get("Content-Type", headers.get("content-type", ""))
    body_type = type(event.get("body")).__name__
    body_preview = str(event.get("body", ""))[:100] if event.get("body") else "N/A"
    
    logger.debug(
        "Buscando handler de transporte",
        path=path,
        content_type=content_type,
        body_type=body_type,
        body_preview=body_preview,
    )
    
    for transport_handler in _TRANSPORT_HANDLERS:
        handler_name = transport_handler.__class__.__name__
        try:
            can_handle = transport_handler.can_handle(event)
            logger.debug(
                f"Handler {handler_name} puede manejar: {can_handle}",
                handler=handler_name,
                can_handle=can_handle,
            )
            if can_handle:
                logger.info(f"Handler seleccionado: {handler_name}")
                return transport_handler
        except Exception as e:
            logger.exception(
                f"Error verificando si {handler_name} puede manejar el evento",
                handler=handler_name,
                error=str(e),
                error_type=type(e).__name__,
            )
            # Continuar con el siguiente handler en lugar de fallar
            continue
    
    # Si llegamos aquí, ningún handler pudo procesar el evento
    logger.error(
        "Ningún handler pudo procesar el evento",
        path=path,
        content_type=content_type,
        body_type=body_type,
        available_handlers=[h.__class__.__name__ for h in _TRANSPORT_HANDLERS],
    )
    
    raise ValueError(
        "No se encontró un handler de transporte compatible para el evento. "
        "Handlers disponibles: API, Twilio"
    )

