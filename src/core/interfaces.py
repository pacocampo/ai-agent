from abc import ABC, abstractmethod
from typing import Protocol, TYPE_CHECKING

if TYPE_CHECKING:
    from typing import Any
    
    from src.agent.models import UserReply
    from src.core.models import AgentDecision, ConversationContext


class MessagingAdapter(ABC):
    """Interfaz para adaptadores de sistemas de mensajería."""
    
    @abstractmethod
    def parse_webhook(self, event: dict) -> str:
        """Parsea un webhook entrante y extrae el mensaje del usuario.
        
        Args:
            event: Evento del webhook (estructura depende del proveedor).
            
        Returns:
            Mensaje del usuario extraído del evento.
        """
        pass
    
    @abstractmethod
    def send_message(self, message: str) -> str:
        """Envía un mensaje al usuario.
        
        Args:
            message: Mensaje a enviar.
            
        Returns:
            Respuesta o confirmación del envío.
        """
        pass
    

class LLMAdapter(ABC):
    """Interfaz para adaptadores de modelos de lenguaje (LLM)."""
    
    @abstractmethod
    def get_agent_decision(
        self,
        user_text: str,
        context: "ConversationContext | None" = None,
    ) -> "AgentDecision":
        """Obtiene la decisión estructurada del agente para un texto de usuario.
        
        Args:
            user_text: Texto del usuario a procesar.
            context: Contexto de conversación opcional para continuidad.
            
        Returns:
            AgentDecision con la acción y parámetros determinados por el modelo.
            
        Raises:
            ValueError: Si no se puede parsear la respuesta del modelo.
        """
        pass
    
    @abstractmethod
    def humanize_response(
        self,
        user_text: str,
        action: str,
        base_message: str,
        vehicles: list[dict] | None = None,
    ) -> str:
        """Humaniza una respuesta estructurada usando el LLM.
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            action: Tipo de acción ejecutada (search_cars, clarify, etc.).
            base_message: Mensaje base generado por el presenter.
            vehicles: Lista de vehículos encontrados (si aplica).
            
        Returns:
            Respuesta humanizada como string.
        """
        pass
    
    @abstractmethod
    def generate_financing_response(
        self,
        user_text: str,
        vehicle_price: float,
    ) -> str:
        """Genera opciones de financiamiento usando el LLM.
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            vehicle_price: Precio del vehículo en MXN.
            
        Returns:
            Respuesta con las opciones de financiamiento calculadas.
        """
        pass
    
    @abstractmethod
    def generate_kavak_info_response(
        self,
        user_text: str,
        kavak_info: str,
        query: str,
    ) -> str:
        """Genera respuesta sobre información de Kavak usando el LLM.
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            kavak_info: Información completa de Kavak.
            query: Consulta específica que se está respondiendo.
            
        Returns:
            Respuesta con la información solicitada.
        """
        pass


class ContextStore(Protocol):
    """Protocolo para almacenamiento de contexto de conversación.
    
    Define el contrato que deben implementar todos los backends
    de almacenamiento (local, Redis, DynamoDB, etc.).
    
    Todas las operaciones son async para consistencia de interfaz,
    permitiendo implementaciones tanto síncronas como asíncronas.
    
    Este protocolo es equivalente a StorageAdapter pero usa Protocol
    en lugar de ABC, siendo más Pythonic y flexible.
    """

    async def get(self, session_id: str) -> "ConversationContext | None":
        """Obtiene el contexto de una sesión.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext si existe, None si no existe o expiró.
        """
        ...

    async def get_or_create(self, session_id: str) -> "ConversationContext":
        """Obtiene o crea el contexto de una sesión.
        
        Si la sesión no existe o expiró, crea un nuevo contexto vacío.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext existente o nuevo.
        """
        ...

    async def save(self, context: "ConversationContext") -> None:
        """Guarda el contexto de una sesión.
        
        Actualiza el contexto existente o crea uno nuevo si no existe.
        Actualiza automáticamente el timestamp de última modificación.
        
        Args:
            context: Contexto a guardar.
        """
        ...

    async def delete(self, session_id: str) -> bool:
        """Elimina el contexto de una sesión.
        
        Args:
            session_id: Identificador de la sesión a eliminar.
            
        Returns:
            True si se eliminó exitosamente, False si la sesión no existía.
        """
        ...

    async def exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión.
        
        Args:
            session_id: Identificador de la sesión.
            
        Returns:
            True si existe y no ha expirado, False si no existe o expiró.
        """
        ...

    async def clear_all(self) -> int:
        """Elimina todas las sesiones almacenadas.
        
        ADVERTENCIA: Esta operación es destructiva y elimina todos los datos.
        Usar solo en desarrollo o con precaución en producción.
        
        Returns:
            Número de sesiones eliminadas.
        """
        ...


class TransportHandler(Protocol):
    """Protocolo para handlers de transporte (API, Twilio, etc.).
    
    Define el contrato que deben implementar todos los handlers
    de transporte que procesan requests y generan respuestas.
    """
    
    def can_handle(self, event: dict) -> bool:
        """Determina si este handler puede procesar el evento.
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            True si este handler puede procesar el evento, False si no.
        """
        ...
    
    def parse_request(self, event: dict) -> tuple[str, str]:
        """Parsea el evento y extrae user_text y session_id.
        
        Args:
            event: Evento de Lambda.
            
        Returns:
            Tupla (user_text, session_id).
            
        Raises:
            ValueError: Si el request no puede ser parseado.
        """
        ...
    
    def format_response(self, reply: "UserReply") -> "dict[str, Any]":
        """Formatea la respuesta del agente para el transporte.
        
        Args:
            reply: Respuesta del agente.
            
        Returns:
            Respuesta formateada con statusCode, headers, body.
        """
        ...
    
    def format_error(self, error: str, status_code: int = 400) -> "dict[str, Any]":
        """Formatea una respuesta de error para el transporte.
        
        Args:
            error: Mensaje de error.
            status_code: Código HTTP de estado.
            
        Returns:
            Respuesta de error formateada.
        """
        ...


class FileStorage(ABC):
    """Interfaz para almacenamiento de archivos estáticos (catálogo, información, etc.).
    
    Esta interfaz permite abstraer el almacenamiento de archivos estáticos,
    permitiendo diferentes implementaciones (local, S3, etc.) sin cambiar
    la lógica de negocio.
    
    En producción, se recomienda usar S3Adapter para almacenar el catálogo
    y archivos de información en la nube, facilitando actualizaciones
    sin redeployar la aplicación.
    """
    
    @abstractmethod
    def read_text(self, file_path: str) -> str:
        """Lee un archivo de texto completo.
        
        Args:
            file_path: Ruta del archivo a leer (formato depende de la implementación).
            
        Returns:
            Contenido del archivo como string.
            
        Raises:
            FileNotFoundError: Si el archivo no existe.
            IOError: Si hay un error al leer el archivo.
        """
        pass
    
    @abstractmethod
    def read_bytes(self, file_path: str) -> bytes:
        """Lee un archivo como bytes.
        
        Útil para archivos binarios o cuando se necesita el contenido
        en formato raw.
        
        Args:
            file_path: Ruta del archivo a leer.
            
        Returns:
            Contenido del archivo como bytes.
            
        Raises:
            FileNotFoundError: Si el archivo no existe.
            IOError: Si hay un error al leer el archivo.
        """
        pass
    
    @abstractmethod
    def exists(self, file_path: str) -> bool:
        """Verifica si un archivo existe.
        
        Args:
            file_path: Ruta del archivo a verificar.
            
        Returns:
            True si el archivo existe, False si no.
        """
        pass
    