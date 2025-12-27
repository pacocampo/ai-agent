"""Adaptador de Twilio para mensajería WhatsApp."""

import base64
from urllib.parse import parse_qs, unquote

from twilio.twiml.messaging_response import MessagingResponse

from src.core.interfaces import MessagingAdapter
from src.infrastructure.observability import logger


def _decode_lambda_body(event: dict) -> str:
    """Decodifica el body del evento Lambda, manejando base64 si es necesario.
    
    API Gateway puede enviar el body codificado en base64 cuando isBase64Encoded es True.
    Esta función maneja ambos casos.
    
    Args:
        event: Evento de Lambda.
        
    Returns:
        Body decodificado como string.
    """
    body = event.get("body", "")
    
    # Si body es dict, no necesita decodificación
    if isinstance(body, dict):
        return ""
    
    # Si no es string, retornar vacío
    if not isinstance(body, str):
        return ""
    
    # Verificar si está codificado en base64
    if event.get("isBase64Encoded"):
        try:
            body_bytes = base64.b64decode(body)
            return body_bytes.decode("utf-8")
        except Exception as e:
            logger.warning(
                "Error decodificando body base64",
                error=str(e),
                error_type=type(e).__name__,
            )
            # Si falla la decodificación, intentar usar el body original
            return body
    
    return body


class TwilioMessagingAdapter(MessagingAdapter):
    """Adaptador de Twilio para WhatsApp.
    
    Maneja el parseo de webhooks de Twilio y la generación de respuestas TwiML.
    """
    
    def __init__(self):
        """Inicializa el adaptador de Twilio."""
        pass
    
    def parse_webhook(self, event: dict) -> str:
        """Parsea un webhook entrante de Twilio y extrae el mensaje del usuario.
        
        Twilio envía los datos como form-encoded en el body.
        El campo 'Body' contiene el mensaje del usuario.
        
        Args:
            event: Evento de Lambda con el webhook de Twilio.
                Puede tener 'body' como string (form-encoded) o dict parseado.
        
        Returns:
            Mensaje del usuario extraído del webhook.
            
        Raises:
            ValueError: Si el webhook no puede ser parseado correctamente.
            
        Examples:
            >>> adapter = TwilioMessagingAdapter()
            >>> event = {"body": "Body=Hola&From=whatsapp%3A%2B1234567890"}
            >>> message = adapter.parse_webhook(event)
            >>> print(message)  # "Hola"
        """
        try:
            body = event.get("body", "")
            body_type = type(body).__name__
            
            logger.debug(
                "Parseando webhook de Twilio",
                body_type=body_type,
                body_preview=str(body)[:200] if body else "N/A",
            )
            
            # Si body es dict, buscar directamente
            if isinstance(body, dict):
                message = body.get("Body", body.get("body", ""))
                logger.debug(
                    "Mensaje extraído de body dict",
                    has_body_field="Body" in body or "body" in body,
                    message_length=len(message) if message else 0,
                )
                return message or ""
            
            # Si body es string, decodificar primero (puede estar en base64)
            if isinstance(body, str):
                # Decodificar body (maneja base64 si es necesario)
                decoded_body = _decode_lambda_body(event)
                
                if not decoded_body:
                    logger.warning("Body está vacío en webhook de Twilio")
                    return ""
                
                try:
                    # Parsear query string
                    parsed = parse_qs(decoded_body)
                    logger.debug(
                        "Body parseado como form-encoded",
                        parsed_keys=list(parsed.keys()),
                        is_base64_encoded=event.get("isBase64Encoded", False),
                    )
                    
                    # Twilio usa 'Body' (mayúscula)
                    body_values = parsed.get("Body", parsed.get("body", []))
                    if body_values:
                        # Decodificar URL y limpiar espacios (como en el ejemplo de Twilio)
                        message = unquote(body_values[0]).strip()
                        logger.debug(
                            "Mensaje extraído y decodificado",
                            message_length=len(message),
                        )
                        return message
                    else:
                        logger.warning(
                            "No se encontró campo 'Body' en webhook de Twilio",
                            available_keys=list(parsed.keys()),
                        )
                        return ""
                        
                except Exception as e:
                    logger.exception(
                        "Error parseando body form-encoded",
                        error=str(e),
                        error_type=type(e).__name__,
                        body_preview=decoded_body[:200],
                        is_base64_encoded=event.get("isBase64Encoded", False),
                    )
                    raise ValueError(
                        f"Error parseando webhook de Twilio: {str(e)}"
                    ) from e
            
            # Si body no es dict ni string, es un tipo inesperado
            logger.error(
                "Tipo de body inesperado en webhook de Twilio",
                body_type=body_type,
                body_value=str(body)[:200],
            )
            return ""
            
        except ValueError:
            # Re-lanzar ValueError sin modificar
            raise
        except Exception as e:
            logger.exception(
                "Error inesperado parseando webhook de Twilio",
                error=str(e),
                error_type=type(e).__name__,
                event_keys=list(event.keys()) if isinstance(event, dict) else "N/A",
            )
            raise ValueError(
                f"Error inesperado parseando webhook de Twilio: {str(e)}"
            ) from e
    
    def send_message(self, message: str) -> str:
        """Genera una respuesta TwiML para enviar mensaje al usuario.
        
        Args:
            message: Mensaje a enviar al usuario.
        
        Returns:
            Respuesta TwiML como string XML.
            
        Raises:
            ValueError: Si el mensaje está vacío o no es válido.
            RuntimeError: Si hay un error generando la respuesta TwiML.
            
        Examples:
            >>> adapter = TwilioMessagingAdapter()
            >>> twiml = adapter.send_message("Hola, ¿cómo puedo ayudarte?")
            >>> print(twiml)  # XML TwiML
        """
        try:
            if not message:
                logger.warning("Intento de enviar mensaje vacío")
                raise ValueError("El mensaje no puede estar vacío")
            
            if not isinstance(message, str):
                logger.error(
                    "Tipo de mensaje inválido",
                    message_type=type(message).__name__,
                )
                raise ValueError(f"El mensaje debe ser un string, recibido: {type(message).__name__}")
            
            logger.debug(
                "Generando respuesta TwiML",
                message_length=len(message),
            )
            
            resp = MessagingResponse()
            resp.message(message)
            twiml = str(resp)
            
            logger.debug(
                "Respuesta TwiML generada exitosamente",
                twiml_length=len(twiml),
            )
            
            return twiml
            
        except ValueError:
            # Re-lanzar ValueError sin modificar
            raise
        except Exception as e:
            logger.exception(
                "Error generando respuesta TwiML",
                error=str(e),
                error_type=type(e).__name__,
                message_length=len(message) if isinstance(message, str) else 0,
            )
            raise RuntimeError(
                f"Error generando respuesta TwiML: {str(e)}"
            ) from e
