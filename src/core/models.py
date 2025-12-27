"""Modelos de dominio core del sistema.

Este módulo contiene las entidades y value objects centrales
que son usados a través de todo el sistema.
"""

from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field


class MessageRole(str, Enum):
    """Roles de mensajes en la conversación."""

    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


@dataclass
class Message:
    """Representa un mensaje en la conversación.
    
    Value object que encapsula un mensaje individual en el
    historial de conversación con su rol y timestamp.
    
    Attributes:
        role: Rol del mensaje (user, assistant, system).
        content: Contenido textual del mensaje.
        timestamp: Momento en que se creó el mensaje.
    """

    role: MessageRole
    content: str
    timestamp: datetime = field(default_factory=datetime.now)

    def to_dict(self) -> dict:
        """Convierte el mensaje a diccionario para la API.
        
        Returns:
            Diccionario con role y content para APIs de LLM.
        """
        return {"role": self.role.value, "content": self.content}


@dataclass
class SelectedVehicle:
    """Vehículo seleccionado por el usuario.
    
    Representa un vehículo que el usuario ha expresado interés
    durante la conversación. Contiene información básica para
    mantener el contexto.
    
    Attributes:
        stock_id: Identificador único del vehículo en inventario.
        make: Marca del vehículo (ej: Toyota, Honda).
        model: Modelo del vehículo (ej: Corolla, Civic).
        year: Año del vehículo.
        price: Precio en MXN.
        km: Kilometraje del vehículo.
    """

    stock_id: int
    make: str
    model: str
    year: int
    price: float
    km: int


@dataclass
class ConversationContext:
    """Contexto completo de una conversación.
    
    Entidad principal que almacena el estado completo de una conversación
    incluyendo historial de mensajes, vehículo seleccionado y resultados
    de búsqueda.
    
    Esta es la entidad central del dominio de conversación y es usada
    por múltiples capas del sistema (agent, storage, services).
    
    Attributes:
        session_id: Identificador único de la sesión.
        messages: Historial de mensajes (limitado a MAX_MESSAGES).
        selected_vehicle: Vehículo actualmente seleccionado por el usuario.
        last_search_results: Últimos resultados de búsqueda de vehículos.
        last_action: Última acción ejecutada por el agente.
        created_at: Timestamp de creación del contexto.
        updated_at: Timestamp de última actualización.
    """

    session_id: str
    messages: list[Message] = field(default_factory=list)
    selected_vehicle: SelectedVehicle | None = None
    last_search_results: list[SelectedVehicle] = field(default_factory=list)
    last_action: str | None = None
    created_at: datetime = field(default_factory=datetime.now)
    updated_at: datetime = field(default_factory=datetime.now)

    MAX_MESSAGES: int = 20

    def add_message(self, role: MessageRole, content: str) -> None:
        """Agrega un mensaje al historial.
        
        Mantiene solo los últimos MAX_MESSAGES mensajes para evitar
        que el contexto crezca indefinidamente.
        
        Args:
            role: Rol del mensaje (user, assistant, system).
            content: Contenido del mensaje.
        """
        self.messages.append(Message(role=role, content=content))
        if len(self.messages) > self.MAX_MESSAGES:
            self.messages = self.messages[-self.MAX_MESSAGES:]
        self.updated_at = datetime.now()

    def add_user_message(self, content: str) -> None:
        """Atajo para agregar mensaje del usuario.
        
        Args:
            content: Contenido del mensaje del usuario.
        """
        self.add_message(MessageRole.USER, content)

    def add_assistant_message(self, content: str) -> None:
        """Atajo para agregar mensaje del asistente.
        
        Args:
            content: Contenido del mensaje del asistente.
        """
        self.add_message(MessageRole.ASSISTANT, content)

    def get_messages_for_api(self) -> list[dict]:
        """Retorna los mensajes en formato para la API de OpenAI.
        
        Returns:
            Lista de diccionarios con role y content.
        """
        return [msg.to_dict() for msg in self.messages]

    def select_vehicle(self, vehicle: SelectedVehicle) -> None:
        """Selecciona un vehículo.
        
        Args:
            vehicle: Vehículo a seleccionar.
        """
        self.selected_vehicle = vehicle
        self.updated_at = datetime.now()

    def select_vehicle_by_stock_id(self, stock_id: int) -> bool:
        """Selecciona un vehículo de los últimos resultados por stock_id.
        
        Busca en last_search_results un vehículo con el stock_id dado
        y lo establece como selected_vehicle.
        
        Args:
            stock_id: ID del stock del vehículo a seleccionar.
            
        Returns:
            True si se encontró y seleccionó el vehículo, False si no existe.
        """
        for vehicle in self.last_search_results:
            if vehicle.stock_id == stock_id:
                self.selected_vehicle = vehicle
                self.updated_at = datetime.now()
                return True
        return False

    def set_search_results(self, vehicles: list[SelectedVehicle]) -> None:
        """Guarda los resultados de búsqueda.
        
        Args:
            vehicles: Lista de vehículos encontrados en la búsqueda.
        """
        self.last_search_results = vehicles
        self.updated_at = datetime.now()

    def clear_selection(self) -> None:
        """Limpia el vehículo seleccionado."""
        self.selected_vehicle = None
        self.updated_at = datetime.now()


class AgentAction(str, Enum):
    """Acciones que el agente puede realizar."""

    SEARCH_CARS = "search_cars"
    GET_CAR_DETAILS = "get_car_details"
    GET_FINANCING_OPTIONS = "get_financing_options"
    GET_KAVAK_INFO = "get_kavak_info"
    RESPOND = "respond"
    CLARIFY = "clarify"
    OUT_OF_SCOPE = "out_of_scope"


class MissingField(str, Enum):
    """Campos válidos que pueden faltar en una búsqueda de autos."""

    MAKE = "make"
    MODEL = "model"
    YEAR = "year"
    PRICE_MAX = "price_max"


class AgentDecision(BaseModel):
    """Decisión del agente de inventario de autos.

    Schema aplanado compatible con OpenAI Structured Outputs.
    Todos los campos opcionales; el campo `action` determina cuáles son relevantes.
    """

    # Campo principal - siempre requerido
    action: AgentAction = Field(
        description="Acción a realizar: search_cars, get_financing_options, respond, clarify, out_of_scope."
    )

    # Campos para SEARCH_CARS
    make: str | None = Field(
        default=None,
        description="Marca del auto (Toyota, Honda, Nissan, etc.). Usar con action=search_cars.",
    )
    model: str | None = Field(
        default=None,
        description="Modelo del auto (Corolla, Civic, Sentra, etc.). Usar con action=search_cars.",
    )
    year: int | None = Field(
        default=None,
        description="Año del auto. Usar con action=search_cars.",
    )
    price_max: float | None = Field(
        default=None,
        description="Precio máximo en MXN. Usar con action=search_cars.",
    )

    # Campos para GET_CAR_DETAILS
    stock_id: str | None = Field(
        default=None,
        description="ID del auto para consultar detalles. Usar con action=get_car_details.",
    )

    # Campos para GET_FINANCING_OPTIONS
    # stock_id ya está definido arriba para GET_CAR_DETAILS
    down_payment: float | None = Field(
        default=None,
        description="Enganche inicial en MXN. Usar con action=get_financing_options.",
    )
    duration: int | None = Field(
        default=None,
        description="Duración en meses. Usar con action=get_financing_options.",
    )

    # Campos para GET_KAVAK_INFO
    info_query: str | None = Field(
        default=None,
        description="Consulta sobre información de Kavak. Usar con action=get_kavak_info.",
    )

    # Campos para RESPOND
    message: str | None = Field(
        default=None,
        description="Mensaje de respuesta al cliente. Usar con action=respond, clarify, out_of_scope.",
    )

    # Campos para CLARIFY
    missing_information: list[MissingField] | None = Field(
        default=None,
        description="Campos faltantes que el cliente debe proporcionar. Usar con action=clarify.",
    )

    # Campos para OUT_OF_SCOPE
    reason: str | None = Field(
        default=None,
        description="Razón por la que la solicitud está fuera de alcance. Usar con action=out_of_scope.",
    )
