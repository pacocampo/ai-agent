"""Handler de transporte para webhooks de Twilio WhatsApp."""

import base64
from typing import Any
from urllib.parse import parse_qs, unquote

from src.adapters.messaging import TwilioMessagingAdapter
from src.agent.models import UserReply
from src.core.interfaces import TransportHandler
from src.core.validators import validate_session_id, validate_user_text
from src.infrastructure.observability import logger


class TwilioTransportHandler:
    """Handler para webhooks de Twilio WhatsApp.
    
    Procesa webhooks form-encoded de Twilio y retorna respuestas TwiML XML.
    """
    
    def __init__(self):
        """Inicializa el handler con adaptador de Twilio."""
        self.adapter = TwilioMessagingAdapter()
    
    def can_handle(self, event: dict) -> bool:
        """Determina si este handler puede procesar el evento.
        
        Detecta webhooks de Twilio por:
        - Path contiene '/twilio'
        - Content-Type es 'application/x-www-form-urlencoded'
        - Body contiene campos de Twilio (Body, From)
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            True si es un webhook de Twilio.
        """
        try:
            # Detectar por path
            path = event.get("requestContext", {}).get("http", {}).get("path", "")
            if "/twilio" in path:
                return True
            
            # Detectar por Content-Type
            headers = event.get("headers", {}) or {}
            content_type = headers.get("Content-Type", headers.get("content-type", ""))
            
            if content_type and "application/x-www-form-urlencoded" in content_type.lower():
                return True
            
            # Detectar por campos de Twilio en body
            body = event.get("body", "")
            if isinstance(body, str) and body:
                try:
                    parsed = parse_qs(body)
                    if "Body" in parsed or "From" in parsed:
                        return True
                except Exception:
                    # Si falla el parseo, no es un webhook de Twilio válido
                    pass
            elif isinstance(body, dict):
                if "Body" in body or "From" in body:
                    return True
        except Exception:
            # Si hay cualquier error, asumimos que no puede manejar el evento
            return False
        
        return False
    
    def parse_request(self, event: dict) -> tuple[str, str]:
        """Parsea webhook de Twilio y extrae user_text y session_id.
        
        Args:
            event: Evento de Lambda con webhook de Twilio.
            
        Returns:
            Tupla (user_text, session_id).
            
        Raises:
            ValueError: Si el webhook no puede ser parseado.
        """
        # Extraer mensaje
        user_text = self.adapter.parse_webhook(event)
        if not user_text:
            raise ValueError("Mensaje vacío en webhook de Twilio")
        
        user_text = validate_user_text(user_text, None)
        
        # Extraer session_id del número de WhatsApp
        session_id = self._extract_session_id(event)
        
        return user_text, session_id
    
    def format_response(self, reply: UserReply) -> dict[str, Any]:
        """Formatea respuesta como TwiML XML.
        
        Args:
            reply: Respuesta del agente.
            
        Returns:
            Respuesta HTTP con TwiML XML en body.
        """
        twiml_response = self.adapter.send_message(reply.message)
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/xml",
            },
            "body": twiml_response,
        }
    
    def format_error(self, error: str, status_code: int = 400) -> dict[str, Any]:
        """Formatea error como TwiML XML.
        
        Args:
            error: Mensaje de error.
            status_code: Código HTTP de estado (siempre 200 para Twilio).
            
        Returns:
            Respuesta de error con TwiML XML en body.
        """
        # Twilio siempre espera 200 para no reintentar
        error_twiml = self.adapter.send_message(
            f"Lo siento, {error}. Por favor, intenta más tarde."
        )
        
        return {
            "statusCode": 200,
            "headers": {
                "Content-Type": "text/xml",
            },
            "body": error_twiml,
        }
    
    def _extract_session_id(self, event: dict) -> str:
        """Extrae session_id del número de WhatsApp.
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            Session ID basado en el número de WhatsApp.
        """
        body = event.get("body", "")
        
        # Si body es dict, buscar From directamente
        if isinstance(body, dict):
            from_number = body.get("From", body.get("from", ""))
        else:
            # Decodificar body si es necesario (puede estar en base64)
            if isinstance(body, str):
                if event.get("isBase64Encoded"):
                    try:
                        body_bytes = base64.b64decode(body)
                        decoded_body = body_bytes.decode("utf-8")
                    except Exception as e:
                        logger.warning(
                            "Error decodificando body base64 para extraer session_id",
                            error=str(e),
                        )
                        decoded_body = body
                else:
                    decoded_body = body
            else:
                decoded_body = ""
            
            # Parsear form-encoded
            parsed = parse_qs(decoded_body)
            from_values = parsed.get("From", parsed.get("from", []))
            from_number = unquote(from_values[0]).strip() if from_values else ""
        
        # Normalizar: quitar "whatsapp:" prefix si existe
        if from_number.startswith("whatsapp:"):
            from_number = from_number.replace("whatsapp:", "")
        
        # Usar número como session_id, o default si no hay
        return validate_session_id(from_number) if from_number else "default"

