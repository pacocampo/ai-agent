"""Handler de transporte para API REST (JSON)."""

from typing import Any

from src.agent.models import UserReply
from src.core.interfaces import TransportHandler
from src.core.validators import validate_session_id, validate_user_text
from src.transport.lambda_models import AgentRequest
from src.transport.middleware import error_response, parse_event, success_response


class ApiTransportHandler:
    """Handler para requests de API REST (JSON).
    
    Procesa requests JSON de API Gateway y retorna respuestas JSON.
    """
    
    def can_handle(self, event: dict) -> bool:
        """Determina si este handler puede procesar el evento.
        
        Detecta requests de API Gateway por:
        - Path contiene '/agent'
        - Content-Type es 'application/json' o no es form-encoded
        - Body es JSON parseable
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            True si es un request de API REST.
        """
        # Detectar por path
        path = event.get("requestContext", {}).get("http", {}).get("path", "")
        if "/agent" in path:
            return True
        
        # Detectar por headers
        headers = event.get("headers", {}) or {}
        content_type = headers.get("Content-Type", headers.get("content-type", ""))
        
        # Si no es form-encoded, asumir JSON
        if "application/x-www-form-urlencoded" not in content_type.lower():
            # Intentar parsear como JSON
            body = event.get("body", "")
            if isinstance(body, str):
                try:
                    import json
                    json.loads(body)
                    return True
                except (json.JSONDecodeError, TypeError):
                    pass
            elif isinstance(body, dict):
                return True
        
        return False
    
    def parse_request(self, event: dict) -> tuple[str, str]:
        """Parsea request JSON y extrae user_text y session_id.
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            Tupla (user_text, session_id).
            
        Raises:
            ValueError: Si el request no puede ser parseado.
        """
        payload = parse_event(event)
        request = AgentRequest.model_validate(payload)
        
        user_text = validate_user_text(request.message, request.user_text)
        session_id = validate_session_id(request.session_id)
        
        return user_text, session_id
    
    def format_response(self, reply: UserReply) -> dict[str, Any]:
        """Formatea respuesta como JSON.
        
        Args:
            reply: Respuesta del agente.
            
        Returns:
            Respuesta HTTP con JSON en body.
        """
        return success_response({
            "message": reply.message,
            "success": reply.success,
            "vehicles": [v.model_dump() for v in reply.vehicles],
        })
    
    def format_error(self, error: str, status_code: int = 400) -> dict[str, Any]:
        """Formatea error como JSON.
        
        Args:
            error: Mensaje de error.
            status_code: Código HTTP de estado.
            
        Returns:
            Respuesta de error con JSON en body.
        """
        return error_response(status_code, error)

