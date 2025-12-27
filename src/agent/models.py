"""Modelos de resultado para las acciones del agente."""

from dataclasses import dataclass, field

from src.core.models import AgentDecision, MissingField
from src.domain.catalog import SearchResults, VehicleSearchResult


class ActionResult:
    """Resultado base de una acción del router."""

    pass


@dataclass
class SearchCarsResult(ActionResult):
    """Resultado de búsqueda de autos."""

    results: SearchResults
    decision: AgentDecision


@dataclass
class GetCarDetailsResult(ActionResult):
    """Resultado de consulta de detalles de un auto."""

    car: VehicleSearchResult
    decision: AgentDecision


@dataclass
class FinancingOptionsResult(ActionResult):
    """Resultado de opciones de financiamiento."""

    price: float
    decision: AgentDecision


@dataclass
class KavakInfoResult(ActionResult):
    """Resultado de consulta de información de Kavak."""

    info_content: str
    query: str
    decision: AgentDecision


@dataclass
class ResponseResult(ActionResult):
    """Resultado de respuesta directa al usuario."""

    message: str
    decision: AgentDecision


@dataclass
class ClarifyResult(ActionResult):
    """Resultado de solicitud de clarificación."""

    message: str
    missing_fields: list[MissingField]
    decision: AgentDecision

    @property
    def missing_fields_display(self) -> list[str]:
        """Retorna los campos faltantes como strings para renderizado."""
        return [f.value for f in self.missing_fields]


@dataclass
class OutOfScopeResult(ActionResult):
    """Resultado de solicitud fuera de alcance."""

    message: str
    reason: str | None
    decision: AgentDecision


@dataclass
class ErrorResult(ActionResult):
    """Resultado de error en el procesamiento."""

    error: str
    decision: AgentDecision


@dataclass
class UserReply:
    """Respuesta final para el usuario.

    Attributes:
        message: Mensaje user-friendly para mostrar.
        vehicles: Lista de vehículos encontrados (si aplica).
        success: Indica si la operación fue exitosa.
    """

    message: str
    vehicles: list[VehicleSearchResult] = field(default_factory=list)
    success: bool = True

