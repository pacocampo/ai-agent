"""Middleware stack para Lambda handler."""

import json
from typing import Any, Callable

from pydantic import ValidationError

from src.core.validators import validate_request_payload, validate_session_id, validate_user_text
from src.infrastructure.observability import DEFAULT_METRIC_UNIT, logger, metrics, tracer


HandlerFunc = Callable[[dict[str, Any], Any], dict[str, Any]]


def cors_headers() -> dict[str, str]:
    """CORS headers para respuestas."""
    return {
        "Access-Control-Allow-Origin": "*",
        "Access-Control-Allow-Headers": "Content-Type,Authorization",
        "Access-Control-Allow-Methods": "OPTIONS,POST",
    }


def error_response(
    status_code: int,
    error: str,
    details: Any = None,
) -> dict[str, Any]:
    """Formatea respuesta de error.
    
    Args:
        status_code: Código HTTP de estado.
        error: Mensaje de error.
        details: Detalles adicionales del error.
        
    Returns:
        Respuesta formateada.
    """
    body = {"error": error}
    if details:
        body["details"] = details
    
    return {
        "statusCode": status_code,
        "headers": cors_headers(),
        "body": json.dumps(body, ensure_ascii=False, default=str),
    }


def success_response(data: dict[str, Any]) -> dict[str, Any]:
    """Formatea respuesta exitosa.
    
    Args:
        data: Datos a incluir en la respuesta.
        
    Returns:
        Respuesta formateada.
    """
    return {
        "statusCode": 200,
        "headers": cors_headers(),
        "body": json.dumps(data, ensure_ascii=False, default=str),
    }


def parse_event(event: dict[str, Any]) -> dict[str, Any]:
    """Parsea el evento de Lambda y extrae el payload.
    
    Args:
        event: Evento de Lambda.
        
    Returns:
        Payload parseado.
    """
    body = event.get("body")
    
    if isinstance(body, str):
        try:
            return json.loads(body)
        except json.JSONDecodeError:
            return {}
    elif isinstance(body, dict):
        return body
    else:
        return event


def _is_twilio_webhook(event: dict[str, Any]) -> bool:
    """Detecta si el evento es un webhook de Twilio.
    
    Args:
        event: Evento de Lambda.
        
    Returns:
        True si es un webhook de Twilio.
    """
    # Detectar por path
    path = event.get("requestContext", {}).get("http", {}).get("path", "")
    if "/twilio" in path:
        return True
    
    # Detectar por Content-Type
    headers = event.get("headers", {}) or {}
    content_type = headers.get("Content-Type", headers.get("content-type", ""))
    
    if "application/x-www-form-urlencoded" in content_type.lower():
        return True
    
    # Detectar por campos de Twilio en body
    body = event.get("body", "")
    if isinstance(body, str):
        from urllib.parse import parse_qs
        parsed = parse_qs(body)
        if "Body" in parsed or "From" in parsed:
            return True
    elif isinstance(body, dict):
        if "Body" in body or "From" in body:
            return True
    
    return False


def request_validator_middleware(handler: HandlerFunc) -> HandlerFunc:
    """Middleware para validar requests.
    
    Valida el payload solo para requests de API (JSON).
    Los webhooks de Twilio (form-encoded) se validan después por su handler específico.
    
    Args:
        handler: Handler function a envolver.
        
    Returns:
        Handler envuelto con validación.
    """
    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        # Saltar validación de payload para webhooks de Twilio
        # (usan form-encoded, no JSON, y se validan en su handler específico)
        if _is_twilio_webhook(event):
            return handler(event, context)
        
        # Validar payload para requests de API (JSON)
        try:
            payload = parse_event(event)
            validate_request_payload(payload)
        except ValueError as e:
            metrics.add_metric(
                name="InvalidRequest", unit=DEFAULT_METRIC_UNIT, value=1
            )
            logger.warning("Request inválido", error=str(e))
            return error_response(400, "Solicitud inválida", str(e))
        except Exception as e:
            metrics.add_metric(
                name="RequestParseError", unit=DEFAULT_METRIC_UNIT, value=1
            )
            logger.error("Error parseando request", error=str(e))
            return error_response(400, "Error procesando solicitud")
        
        return handler(event, context)
    
    return wrapper


def error_handler_middleware(handler: HandlerFunc) -> HandlerFunc:
    """Middleware para manejo de errores top-level.
    
    Args:
        handler: Handler function a envolver.
        
    Returns:
        Handler envuelto con manejo de errores.
    """
    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        try:
            return handler(event, context)
        except ValidationError as exc:
            metrics.add_metric(
                name="ValidationError", unit=DEFAULT_METRIC_UNIT, value=1
            )
            logger.error("Error de validación", errors=exc.errors())
            return error_response(400, "Solicitud inválida", exc.errors())
        except Exception as e:
            metrics.add_metric(
                name="UnhandledError", unit=DEFAULT_METRIC_UNIT, value=1
            )
            logger.exception("Error no manejado", error=str(e))
            return error_response(500, "Error interno del servidor")
    
    return wrapper


def metrics_middleware(handler: HandlerFunc) -> HandlerFunc:
    """Middleware para métricas de éxito.
    
    Args:
        handler: Handler function a envolver.
        
    Returns:
        Handler envuelto con métricas.
    """
    def wrapper(event: dict[str, Any], context: Any) -> dict[str, Any]:
        response = handler(event, context)
        
        # Métrica de éxito si status code es 200
        if response.get("statusCode") == 200:
            metrics.add_metric(
                name="HandledRequest", unit=DEFAULT_METRIC_UNIT, value=1
            )
        
        return response
    
    return wrapper


def apply_middleware_stack(handler: HandlerFunc) -> HandlerFunc:
    """Aplica el stack completo de middleware.
    
    Orden de aplicación (de afuera hacia adentro):
    1. Error handler (top-level)
    2. Request validator
    3. Metrics
    4. Handler original
    
    Args:
        handler: Handler function original.
        
    Returns:
        Handler con todos los middlewares aplicados.
    """
    # Aplicar en orden inverso (el último aplicado es el más externo)
    handler = metrics_middleware(handler)
    handler = request_validator_middleware(handler)
    handler = error_handler_middleware(handler)
    
    return handler

