"""Handlers para cada tipo de acción del agente."""

from difflib import get_close_matches

from src.agent.models import (
    ActionResult,
    ClarifyResult,
    ErrorResult,
    FinancingOptionsResult,
    GetCarDetailsResult,
    KavakInfoResult,
    OutOfScopeResult,
    ResponseResult,
    SearchCarsResult,
)
from src.core.models import AgentDecision, MissingField
from src.domain.catalog import InventoryError
from src.tools.catalog.inventory import (
    get_available_makes,
    get_available_models,
    get_makes_for_model,
    get_vehicle_details,
    search_vehicles,
)
from src.tools.catalog.kavak_info import get_kavak_info


def _suggest_matches(value: str, options: list[str]) -> list[str]:
    if not value:
        return []
    options_map = {opt.lower(): opt for opt in options}
    matches = get_close_matches(
        value.strip().lower(),
        list(options_map.keys()),
        n=3,
        cutoff=0.8,
    )
    return [options_map[m] for m in matches]


def handle_search_cars(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de búsqueda de autos.

    Args:
        decision: Decisión del agente con parámetros de búsqueda.

    Returns:
        SearchCarsResult con los vehículos encontrados o ErrorResult si falla.
    """
    if decision.model and not decision.make:
        makes_for_model = get_makes_for_model(decision.model)
        if len(makes_for_model) > 1:
            message = (
                f"Encontré el modelo {decision.model} en varias marcas: "
                f"{', '.join(makes_for_model)}. ¿Cuál prefieres?"
            )
            return ClarifyResult(
                message=message,
                missing_fields=[MissingField.MAKE],
                decision=decision,
            )

    try:
        results = search_vehicles(
            make=decision.make,
            model=decision.model,
            year=decision.year,
            price=decision.price_max,
        )
        if results.total_count == 0 and (decision.make or decision.model):
            suggestions = []
            available_makes = get_available_makes()
            available_models = get_available_models(
                decision.make
                if decision.make and decision.make.lower() in {m.lower() for m in available_makes}
                else None
            )

            make_suggestions = (
                _suggest_matches(decision.make, available_makes)
                if decision.make
                else []
            )
            model_suggestions = (
                _suggest_matches(decision.model, available_models)
                if decision.model
                else []
            )

            if make_suggestions:
                suggestions.append(f"marca '{make_suggestions[0]}'")
            if model_suggestions:
                suggestions.append(f"modelo '{model_suggestions[0]}'")

            if suggestions:
                message = (
                    "No encontré coincidencias exactas. "
                    f"¿Te referías a {', '.join(suggestions)}?"
                )
                return ClarifyResult(
                    message=message,
                    missing_fields=[],
                    decision=decision,
                )

        return SearchCarsResult(results=results, decision=decision)
    except InventoryError as e:
        return ErrorResult(error=str(e), decision=decision)


def handle_get_car_details(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de obtener detalles de un auto.

    Args:
        decision: Decisión del agente con el ID del auto.

    Returns:
        GetCarDetailsResult o ErrorResult si falta el stock_id.
    """
    if not decision.stock_id:
        return ErrorResult(
            error="Se requiere el ID del auto para consultar detalles.",
            decision=decision,
        )

    try:
        car = get_vehicle_details(decision.stock_id)
        return GetCarDetailsResult(car=car, decision=decision)
    except InventoryError as e:
        return ErrorResult(error=str(e), decision=decision)


def handle_get_kavak_info(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de consultar información de Kavak.

    Args:
        decision: Decisión del agente con la consulta.

    Returns:
        KavakInfoResult con la información o ErrorResult si hay error.
    """
    try:
        info_content = get_kavak_info()
        query = decision.info_query or "información general"
        return KavakInfoResult(
            info_content=info_content,
            query=query,
            decision=decision,
        )
    except Exception as e:
        return ErrorResult(error=str(e), decision=decision)


def handle_get_financing_options(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de obtener opciones de financiamiento.

    Obtiene el precio del vehículo para que el LLM calcule las opciones.

    Args:
        decision: Decisión del agente con el ID del auto.

    Returns:
        FinancingOptionsResult con el precio o ErrorResult si falta el stock_id.
    """
    if not decision.stock_id:
        return ErrorResult(
            error="Se requiere el ID del auto para consultar financiamiento.",
            decision=decision,
        )

    try:
        car = get_vehicle_details(decision.stock_id)
        return FinancingOptionsResult(price=car.price, decision=decision)
    except InventoryError as e:
        return ErrorResult(error=str(e), decision=decision)


def handle_respond(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de responder al usuario.

    Args:
        decision: Decisión del agente con el mensaje.

    Returns:
        ResponseResult con el mensaje para el usuario o ErrorResult si falta.
    """
    if not decision.message:
        return ErrorResult(
            error="La acción RESPOND requiere un mensaje.",
            decision=decision,
        )

    return ResponseResult(
        message=decision.message,
        decision=decision,
    )


def handle_clarify(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de solicitar clarificación.

    Args:
        decision: Decisión del agente con campos faltantes.

    Returns:
        ClarifyResult con el mensaje y campos faltantes.
    """
    return ClarifyResult(
        message=decision.message or "¿Podrías proporcionar más información?",
        missing_fields=decision.missing_information or [],
        decision=decision,
    )


def handle_out_of_scope(decision: AgentDecision) -> ActionResult:
    """Maneja la acción de solicitud fuera de alcance.

    Args:
        decision: Decisión del agente con la razón.

    Returns:
        OutOfScopeResult con el mensaje y razón.
    """
    return OutOfScopeResult(
        message=decision.message or "Lo siento, eso está fuera de mi alcance.",
        reason=decision.reason,
        decision=decision,
    )

