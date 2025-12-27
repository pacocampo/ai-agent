"""Manejo centralizado de errores para transport handlers."""

from typing import Any

from pydantic import ValidationError

from src.core.interfaces import TransportHandler
from src.infrastructure.observability import logger


def create_fallback_response(error_msg: str, status_code: int = 500) -> dict[str, Any]:
    """Crea una respuesta JSON genérica de fallback.
    
    Args:
        error_msg: Mensaje de error.
        status_code: Código HTTP de estado.
        
    Returns:
        Respuesta HTTP con JSON.
    """
    return {
        "statusCode": status_code,
        "headers": {"Content-Type": "application/json"},
        "body": f'{{"error": "{error_msg}"}}',
    }


def safe_format_error(
    transport_handler: TransportHandler,
    error_msg: str,
    status_code: int,
    original_error: Exception | None = None,
) -> dict[str, Any]:
    """Intenta formatear error usando el handler, con fallback si falla.
    
    Args:
        transport_handler: Handler de transporte para formatear el error.
        error_msg: Mensaje de error.
        status_code: Código HTTP de estado.
        original_error: Error original que causó el problema (opcional).
        
    Returns:
        Respuesta HTTP formateada.
    """
    try:
        return transport_handler.format_error(error_msg, status_code=status_code)
    except Exception as format_err:
        logger.exception(
            "Error formateando respuesta de error",
            error=str(format_err),
            original_error=str(original_error) if original_error else None,
            transport=transport_handler.__class__.__name__,
        )
        return create_fallback_response(error_msg, status_code)


def safe_format_response(
    transport_handler: TransportHandler,
    reply: Any,
) -> dict[str, Any]:
    """Intenta formatear respuesta usando el handler, con fallback si falla.
    
    Args:
        transport_handler: Handler de transporte para formatear la respuesta.
        reply: Respuesta del agente a formatear.
        
    Returns:
        Respuesta HTTP formateada.
    """
    try:
        return transport_handler.format_response(reply)
    except (ValueError, RuntimeError) as e:
        logger.exception(
            "Error formateando respuesta",
            error=str(e),
            error_type=type(e).__name__,
            transport=transport_handler.__class__.__name__,
        )
        # Intentar formatear error, pero si también falla, usar fallback
        return safe_format_error(
            transport_handler,
            "Error generando respuesta",
            status_code=500,
            original_error=e,
        )
    except Exception as e:
        logger.exception(
            "Error inesperado formateando respuesta",
            error=str(e),
            error_type=type(e).__name__,
            transport=transport_handler.__class__.__name__,
        )
        return safe_format_error(
            transport_handler,
            "Error generando respuesta",
            status_code=500,
            original_error=e,
        )


class TransportErrorHandler:
    """Maneja errores de transporte de forma centralizada."""
    
    def __init__(self, transport_handler: TransportHandler):
        """Inicializa el error handler.
        
        Args:
            transport_handler: Handler de transporte asociado.
        """
        self.transport_handler = transport_handler
    
    def handle_parse_error(
        self,
        error: Exception,
        event: dict[str, Any],
    ) -> dict[str, Any]:
        """Maneja errores al parsear el request.
        
        Args:
            error: Excepción que ocurrió.
            event: Evento de Lambda.
            
        Returns:
            Respuesta HTTP de error.
        """
        if isinstance(error, ValueError):
            logger.warning(
                "Error parseando request",
                error=str(error),
                error_type=type(error).__name__,
                transport=self.transport_handler.__class__.__name__,
                event_body_preview=str(event.get("body", ""))[:200] if event.get("body") else "N/A",
            )
            return safe_format_error(
                self.transport_handler,
                str(error),
                status_code=400,
                original_error=error,
            )
        
        if isinstance(error, ValidationError):
            logger.warning(
                "Error de validación parseando request",
                error=str(error),
                errors=error.errors() if hasattr(error, 'errors') else None,
                transport=self.transport_handler.__class__.__name__,
                event_body_preview=str(event.get("body", ""))[:200] if event.get("body") else "N/A",
            )
            return safe_format_error(
                self.transport_handler,
                "Solicitud inválida",
                status_code=400,
                original_error=error,
            )
        
        # Error inesperado
        logger.exception(
            "Error inesperado parseando request",
            error=str(error),
            error_type=type(error).__name__,
            transport=self.transport_handler.__class__.__name__,
            event_body_preview=str(event.get("body", ""))[:200] if event.get("body") else "N/A",
        )
        return safe_format_error(
            self.transport_handler,
            "Error procesando solicitud",
            status_code=500,
            original_error=error,
        )
    
    def handle_processing_error(
        self,
        error: Exception,
    ) -> dict[str, Any]:
        """Maneja errores al procesar el mensaje.
        
        Args:
            error: Excepción que ocurrió.
            
        Returns:
            Respuesta HTTP de error.
        """
        logger.exception(
            "Error procesando mensaje",
            error=str(error),
            error_type=type(error).__name__,
            transport=self.transport_handler.__class__.__name__,
        )
        return safe_format_error(
            self.transport_handler,
            "Error interno del servidor",
            status_code=500,
            original_error=error,
        )

