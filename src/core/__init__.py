"""Módulo core con la lógica de dominio.

Este módulo contiene las interfaces, modelos y configuración central
del sistema que son independientes de la implementación.
"""

from src.core.interfaces import ContextStore, FileStorage, LLMAdapter, MessagingAdapter
from src.core.models import (
    AgentAction,
    AgentDecision,
    ConversationContext,
    Message,
    MessageRole,
    MissingField,
    SelectedVehicle,
)

__all__ = [
    # Interfaces
    "ContextStore",
    "FileStorage",
    "LLMAdapter",
    "MessagingAdapter",
    # Models
    "AgentAction",
    "AgentDecision",
    "ConversationContext",
    "Message",
    "MessageRole",
    "MissingField",
    "SelectedVehicle",
]
