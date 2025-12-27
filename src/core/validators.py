"""Validadores centralizados para el sistema."""

from typing import Any

from pydantic import ValidationError


def validate_request_payload(payload: dict[str, Any]) -> dict[str, Any]:
    """Valida el payload de request básico.
    
    Args:
        payload: Payload a validar.
        
    Returns:
        Payload validado y normalizado.
        
    Raises:
        ValueError: Si el payload es inválido.
    """
    if not isinstance(payload, dict):
        raise ValueError("Payload debe ser un diccionario")
    
    if not payload:
        raise ValueError("Payload no puede estar vacío")
    
    return payload


def validate_session_id(session_id: str | None) -> str:
    """Valida y normaliza session_id.
    
    Args:
        session_id: ID de sesión a validar.
        
    Returns:
        Session ID válido (default si es None).
    """
    if session_id is None:
        return "default"
    
    if not isinstance(session_id, str):
        raise ValueError("session_id debe ser un string")
    
    if not session_id.strip():
        return "default"
    
    return session_id.strip()


def validate_user_text(message: str | None, user_text: str | None) -> str:
    """Valida y extrae el texto del usuario.
    
    Args:
        message: Campo message del request.
        user_text: Campo user_text del request.
        
    Returns:
        Texto del usuario validado.
        
    Raises:
        ValueError: Si no hay texto válido.
    """
    text = message or user_text
    
    if not text:
        raise ValueError("message o user_text es requerido")
    
    if not isinstance(text, str):
        raise ValueError("message/user_text debe ser un string")
    
    text = text.strip()
    
    if not text:
        raise ValueError("message/user_text no puede estar vacío")
    
    if len(text) > 10000:  # Límite razonable
        raise ValueError("message/user_text excede el límite de caracteres")
    
    return text

