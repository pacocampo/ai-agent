"""Módulo de contexto de conversación para el agente.

NOTA: Los modelos y protocolos ahora residen en src.core pero se re-exportan
aquí para backward compatibility.

Para nuevo código, importa desde:
    from src.core.models import ConversationContext, Message, MessageRole, SelectedVehicle
    from src.core.interfaces import ContextStore
    from src.adapters import LocalStorageAdapter  # En lugar de LocalContextStore

Provee abstracción para almacenar y recuperar contexto de sesiones,
permitiendo diferentes implementaciones (local, Redis, DynamoDB, etc.).
"""

from src.adapters import LocalStorageAdapter
from src.core.interfaces import ContextStore
from src.core.models import ConversationContext, Message, MessageRole, SelectedVehicle

# Backward compatibility: LocalContextStore ahora es alias de LocalStorageAdapter
LocalContextStore = LocalStorageAdapter

__all__ = [
    "ContextStore",
    "ConversationContext",
    "Message",
    "MessageRole",
    "SelectedVehicle",
    "LocalContextStore",  # Alias para backward compatibility
]
