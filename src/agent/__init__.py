"""Módulo del agente de inventario de autos.

Este módulo contiene la lógica del agente incluyendo:
- Modelos de resultado de acciones
- Handlers para cada tipo de acción
- Router para dispatch de decisiones
- Presenter para respuestas user-friendly
- Entrypoint para procesar mensajes
- Contexto de conversación
- Servicios de orquestación
"""

from src.adapters import LocalStorageAdapter
from src.agent.context import (
    ContextStore,
    ConversationContext,
)

# Backward compatibility: LocalContextStore es alias de LocalStorageAdapter
LocalContextStore = LocalStorageAdapter
from src.agent.models import (
    ActionResult,
    ClarifyResult,
    ErrorResult,
    FinancingOptionsResult,
    OutOfScopeResult,
    ResponseResult,
    SearchCarsResult,
    UserReply,
)
from src.agent.presenter import render_reply
from src.agent.router import route_decision
from src.agent.services import ConversationService

__all__ = [
    # Contexto
    "ContextStore",
    "ConversationContext",
    "LocalContextStore",
    # Servicios
    "ConversationService",
    # Modelos
    "ActionResult",
    "SearchCarsResult",
    "FinancingOptionsResult",
    "ResponseResult",
    "ClarifyResult",
    "OutOfScopeResult",
    "ErrorResult",
    "UserReply",
    # Funciones internas (para uso avanzado)
    "route_decision",
    "render_reply",
]
