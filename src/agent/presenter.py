"""Presenter para convertir ActionResult en respuestas user-friendly."""

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
    UserReply,
)
from src.core.logging import get_logger

logger = get_logger(__name__)

_DEFAULT_ERROR_MESSAGE = (
    "Lo siento, ocurrió un problema al procesar tu solicitud. "
    "Por favor, intenta de nuevo."
)


def _render_search_cars(result: SearchCarsResult) -> UserReply:
    count = result.results.total_count
    if count == 0:
        criteria_parts = []
        if result.decision.make:
            criteria_parts.append(result.decision.make)
        if result.decision.model:
            criteria_parts.append(result.decision.model)

        criteria_text = " ".join(criteria_parts)
        if criteria_text:
            message = (
                f"No encontré {criteria_text} con esos criterios. "
                "¿Te gustaría buscar algo diferente?"
            )
        else:
            message = (
                "No encontré vehículos con esos criterios. "
                "¿Te gustaría buscar algo diferente?"
            )
    elif count == 1:
        message = "¡Encontré 1 vehículo que coincide con tu búsqueda!"
    else:
        message = f"¡Encontré {count} vehículos que coinciden con tu búsqueda!"

    return UserReply(
        message=message,
        vehicles=result.results.results,
        success=True,
    )

def _render_get_car_details(result: GetCarDetailsResult) -> UserReply:
    return UserReply(
        message=f"Detalles del vehículo {result.car.stock_id}: {result.car.make} {result.car.model} {result.car.year}",
        success=True,
    )


def _render_financing_options(result: FinancingOptionsResult) -> UserReply:
    return UserReply(
        message=f"Opciones de financiamiento para vehículo con precio ${result.price:,.0f} MXN",
        success=True,
    )


def _render_kavak_info(result: KavakInfoResult) -> UserReply:
    return UserReply(
        message=f"Información sobre Kavak: {result.query}",
        success=True,
    )


def _render_response(result: ResponseResult) -> UserReply:
    return UserReply(message=result.message, success=True)


def _render_clarify(result: ClarifyResult) -> UserReply:
    return UserReply(message=result.message, success=True)


def _render_out_of_scope(result: OutOfScopeResult) -> UserReply:
    return UserReply(message=result.message, success=True)


def _render_error(result: ErrorResult) -> UserReply:
    logger.error(
        "Error en procesamiento de acción",
        action=result.decision.action.value,
        error=result.error,
        decision=result.decision.model_dump(exclude_none=True),
    )

    return UserReply(
        message=_DEFAULT_ERROR_MESSAGE,
        success=False,
    )


def render_reply(result: ActionResult) -> UserReply:
    """Convierte un ActionResult en una respuesta user-friendly.

    Esta función actúa como capa de presentación que:
    - Transforma resultados internos en mensajes amigables
    - Registra errores reales sin exponerlos al usuario
    - Mantiene consistencia en el formato de respuesta

    Args:
        result: Resultado de una acción del router.

    Returns:
        UserReply con mensaje user-friendly y datos relevantes.

    Examples:
        >>> from src.agent import route_decision, render_reply
        >>> result = route_decision(decision)
        >>> reply = render_reply(result)
        >>> print(reply.message)
    """
    match result:
        case SearchCarsResult():
            return _render_search_cars(result)
        case GetCarDetailsResult():
            return _render_get_car_details(result)
        case FinancingOptionsResult():
            return _render_financing_options(result)
        case KavakInfoResult():
            return _render_kavak_info(result)
        case ResponseResult():
            return _render_response(result)
        case ClarifyResult():
            return _render_clarify(result)
        case OutOfScopeResult():
            return _render_out_of_scope(result)
        case ErrorResult():
            return _render_error(result)
        case _:
            logger.error("Tipo de resultado no soportado", result_type=type(result).__name__)
            return UserReply(message=_DEFAULT_ERROR_MESSAGE, success=False)
