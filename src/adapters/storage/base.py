"""Interfaz base para adaptadores de almacenamiento de contexto."""

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from src.core.models import ConversationContext


class StorageAdapter(ABC):
    """Interfaz para almacenamiento de contexto de conversación.
    
    Define el contrato que deben implementar todos los backends
    de almacenamiento (local, Redis, DynamoDB, S3, etc.).
    
    Todas las operaciones son async para consistencia de interfaz,
    permitiendo implementaciones tanto síncronas como asíncronas.
    """
    
    @abstractmethod
    async def get(self, session_id: str) -> "ConversationContext | None":
        """Obtiene el contexto de una sesión.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext si existe, None si no existe o expiró.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get("user-123")
            >>> if context:
            ...     print(f"Found {len(context.messages)} messages")
        """
        pass
    
    @abstractmethod
    async def get_or_create(self, session_id: str) -> "ConversationContext":
        """Obtiene o crea el contexto de una sesión.
        
        Si la sesión no existe o expiró, crea un nuevo contexto vacío.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext existente o nuevo.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get_or_create("user-123")
            >>> print(context.session_id)  # "user-123"
        """
        pass
    
    @abstractmethod
    async def save(self, context: "ConversationContext") -> None:
        """Guarda el contexto de una sesión.
        
        Actualiza el contexto existente o crea uno nuevo si no existe.
        Actualiza automáticamente el timestamp de última modificación.
        
        Args:
            context: Contexto a guardar.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get_or_create("user-123")
            >>> context.add_user_message("Hola")
            >>> await adapter.save(context)
        """
        pass
    
    @abstractmethod
    async def delete(self, session_id: str) -> bool:
        """Elimina el contexto de una sesión.
        
        Args:
            session_id: Identificador de la sesión a eliminar.
            
        Returns:
            True si se eliminó exitosamente, False si la sesión no existía.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> deleted = await adapter.delete("user-123")
            >>> print(f"Deleted: {deleted}")
        """
        pass
    
    @abstractmethod
    async def exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión.
        
        Args:
            session_id: Identificador de la sesión.
            
        Returns:
            True si existe y no ha expirado, False si no existe o expiró.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> if await adapter.exists("user-123"):
            ...     print("Session exists")
        """
        pass
    
    @abstractmethod
    async def clear_all(self) -> int:
        """Elimina todas las sesiones almacenadas.
        
        ADVERTENCIA: Esta operación es destructiva y elimina todos los datos.
        Usar solo en desarrollo o con precaución en producción.
        
        Returns:
            Número de sesiones eliminadas.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> count = await adapter.clear_all()
            >>> print(f"Deleted {count} sessions")
        """
        pass

