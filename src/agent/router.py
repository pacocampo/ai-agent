"""Router de decisiones del agente."""

from typing import Callable

from src.agent.handlers.catalog import (
    handle_clarify,
    handle_get_car_details,
    handle_get_financing_options,
    handle_get_kavak_info,
    handle_out_of_scope,
    handle_respond,
    handle_search_cars,
)
from src.agent.models import ActionResult
from src.core.models import AgentAction, AgentDecision

#: Tipo para funciones que manejan acciones individuales del agente.
ActionHandler = Callable[[AgentDecision], ActionResult]

_ACTION_HANDLERS: dict[AgentAction, ActionHandler] = {
    AgentAction.SEARCH_CARS: handle_search_cars,
    AgentAction.GET_CAR_DETAILS: handle_get_car_details,
    AgentAction.GET_FINANCING_OPTIONS: handle_get_financing_options,
    AgentAction.GET_KAVAK_INFO: handle_get_kavak_info,
    AgentAction.RESPOND: handle_respond,
    AgentAction.CLARIFY: handle_clarify,
    AgentAction.OUT_OF_SCOPE: handle_out_of_scope,
}


def route_decision(decision: AgentDecision) -> ActionResult:
    """Rutea una decisión del agente al handler correspondiente.

    Esta función actúa como dispatcher central que toma la decisión del agente
    y la dirige al handler apropiado basándose en el campo `action`.

    Args:
        decision: Decisión del agente a procesar.

    Returns:
        ActionResult correspondiente a la acción ejecutada.

    Raises:
        ValueError: Si la acción no tiene un handler registrado.

    Examples:
        >>> from src.core.models import AgentAction, AgentDecision
        >>> decision = AgentDecision(
        ...     action=AgentAction.SEARCH_CARS,
        ...     make="Toyota",
        ...     model="Corolla"
        ... )
        >>> result = route_decision(decision)
    """
    handler = _ACTION_HANDLERS.get(decision.action)

    if handler is None:
        raise ValueError(f"Acción no soportada: {decision.action}")

    return handler(decision)

