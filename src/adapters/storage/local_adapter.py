"""Adaptador de almacenamiento local en memoria."""

from datetime import datetime, timedelta
from threading import Lock
from typing import TYPE_CHECKING

from src.adapters.storage.base import StorageAdapter

if TYPE_CHECKING:
    from src.core.models import ConversationContext


class LocalStorageAdapter(StorageAdapter):
    """Adaptador de almacenamiento de contexto en memoria local.
    
    Implementa StorageAdapter usando un diccionario en memoria.
    Thread-safe mediante Lock para ambientes concurrentes.
    Incluye TTL (Time To Live) para limpieza automática de sesiones expiradas.
    
    **Características:**
    - Almacenamiento en memoria (no persistente)
    - Thread-safe con Lock
    - TTL configurable para expiración automática
    - Método de limpieza manual de sesiones expiradas
    - Propiedad para contar sesiones activas
    
    **Uso recomendado:**
    - Desarrollo local
    - Testing
    - Ambientes de baja escala
    - Prototipado rápido
    
    **NO recomendado para:**
    - Producción de alta escala
    - Ambientes distribuidos (múltiples instancias)
    - Cuando se requiere persistencia entre reinicios
    
    Attributes:
        ttl_minutes: Tiempo de vida de las sesiones en minutos.
        
    Examples:
        >>> # Crear adaptador con TTL de 10 minutos
        >>> adapter = LocalStorageAdapter(ttl_minutes=10)
        >>> 
        >>> # Usar el adaptador
        >>> context = await adapter.get_or_create("user-123")
        >>> context.add_user_message("Hola")
        >>> await adapter.save(context)
        >>> 
        >>> # Verificar existencia
        >>> exists = await adapter.exists("user-123")
        >>> 
        >>> # Limpiar sesiones expiradas
        >>> cleaned = await adapter.cleanup_expired()
        >>> print(f"Cleaned {cleaned} expired sessions")
    """
    
    def __init__(self, ttl_minutes: int = 10) -> None:
        """Inicializa el adaptador de almacenamiento local.
        
        Args:
            ttl_minutes: Tiempo de vida de las sesiones en minutos.
                Sesiones inactivas por más de este tiempo serán consideradas expiradas.
                Default: 10 minutos.
                
        Raises:
            ValueError: Si ttl_minutes es menor o igual a 0.
            
        Examples:
            >>> # TTL de 10 minutos (default)
            >>> adapter = LocalStorageAdapter()
            >>> 
            >>> # TTL personalizado de 30 minutos
            >>> adapter = LocalStorageAdapter(ttl_minutes=30)
        """
        if ttl_minutes <= 0:
            raise ValueError("ttl_minutes debe ser mayor a 0")
        
        self._store: dict[str, "ConversationContext"] = {}
        self._lock = Lock()
        self._ttl = timedelta(minutes=ttl_minutes)
        self._ttl_minutes = ttl_minutes
    
    async def get(self, session_id: str) -> "ConversationContext | None":
        """Obtiene el contexto de una sesión.
        
        Verifica automáticamente la expiración del contexto.
        Si el contexto expiró, se elimina y retorna None.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext si existe y no expiró, None en caso contrario.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get("user-123")
            >>> if context:
            ...     print(f"Session active with {len(context.messages)} messages")
            ... else:
            ...     print("Session not found or expired")
        """
        with self._lock:
            context = self._store.get(session_id)
            if context is None:
                return None
            
            if self._is_expired(context):
                del self._store[session_id]
                return None
            
            return context
    
    async def get_or_create(self, session_id: str) -> "ConversationContext":
        """Obtiene o crea el contexto de una sesión.
        
        Si la sesión existe y no ha expirado, la retorna.
        Si no existe o expiró, crea una nueva sesión vacía.
        
        Args:
            session_id: Identificador único de la sesión.
            
        Returns:
            ConversationContext existente o nuevo.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> # Primera llamada crea la sesión
            >>> context = await adapter.get_or_create("user-123")
            >>> print(len(context.messages))  # 0
            >>> 
            >>> # Segunda llamada recupera la misma sesión
            >>> context2 = await adapter.get_or_create("user-123")
            >>> print(context.session_id == context2.session_id)  # True
        """
        with self._lock:
            context = self._store.get(session_id)
            
            if context is not None and not self._is_expired(context):
                return context
            
            # Importación tardía para evitar ciclos
            from src.core.models import ConversationContext
            
            context = ConversationContext(session_id=session_id)
            self._store[session_id] = context
            return context
    
    async def save(self, context: "ConversationContext") -> None:
        """Guarda el contexto de una sesión.
        
        Actualiza el timestamp de última modificación automáticamente.
        Thread-safe mediante Lock.
        
        Args:
            context: Contexto a guardar.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get_or_create("user-123")
            >>> context.add_user_message("Busco un Toyota")
            >>> await adapter.save(context)
            >>> print("Context saved successfully")
        """
        with self._lock:
            context.updated_at = datetime.now()
            self._store[context.session_id] = context
    
    async def delete(self, session_id: str) -> bool:
        """Elimina el contexto de una sesión.
        
        Args:
            session_id: Identificador de la sesión a eliminar.
            
        Returns:
            True si la sesión existía y fue eliminada, False si no existía.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> context = await adapter.get_or_create("user-123")
            >>> deleted = await adapter.delete("user-123")
            >>> print(deleted)  # True
            >>> deleted = await adapter.delete("user-123")
            >>> print(deleted)  # False (ya no existe)
        """
        with self._lock:
            if session_id in self._store:
                del self._store[session_id]
                return True
            return False
    
    async def exists(self, session_id: str) -> bool:
        """Verifica si existe una sesión.
        
        Verifica tanto la existencia como la no-expiración del contexto.
        
        Args:
            session_id: Identificador de la sesión.
            
        Returns:
            True si existe y no ha expirado, False en caso contrario.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> exists = await adapter.exists("user-123")
            >>> print(f"Session exists: {exists}")
        """
        context = await self.get(session_id)
        return context is not None
    
    async def clear_all(self) -> int:
        """Elimina todas las sesiones almacenadas.
        
        ADVERTENCIA: Operación destructiva que elimina todos los datos.
        No es reversible. Usar con precaución.
        
        Returns:
            Número de sesiones eliminadas.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> # Crear algunas sesiones
            >>> await adapter.get_or_create("user-1")
            >>> await adapter.get_or_create("user-2")
            >>> # Limpiar todo
            >>> count = await adapter.clear_all()
            >>> print(f"Deleted {count} sessions")  # "Deleted 2 sessions"
        """
        with self._lock:
            count = len(self._store)
            self._store.clear()
            return count
    
    # Métodos adicionales específicos de LocalStorageAdapter
    
    async def cleanup_expired(self) -> int:
        """Limpia las sesiones expiradas del almacenamiento.
        
        Útil para liberar memoria eliminando sesiones que ya expiraron
        pero que aún no han sido accedidas (y por tanto no se limpiaron).
        
        Returns:
            Número de sesiones expiradas eliminadas.
            
        Examples:
            >>> adapter = LocalStorageAdapter(ttl_minutes=1)
            >>> await adapter.get_or_create("user-123")
            >>> # Esperar más de 1 minuto...
            >>> cleaned = await adapter.cleanup_expired()
            >>> print(f"Cleaned {cleaned} expired sessions")
        """
        with self._lock:
            expired = [
                sid for sid, ctx in self._store.items() if self._is_expired(ctx)
            ]
            for sid in expired:
                del self._store[sid]
            return len(expired)
    
    @property
    def session_count(self) -> int:
        """Retorna el número de sesiones activas actualmente en memoria.
        
        Incluye sesiones expiradas que aún no han sido limpiadas.
        Para el número real de sesiones válidas, usar cleanup_expired() primero.
        
        Returns:
            Número total de sesiones en memoria.
            
        Examples:
            >>> adapter = LocalStorageAdapter()
            >>> await adapter.get_or_create("user-1")
            >>> await adapter.get_or_create("user-2")
            >>> print(adapter.session_count)  # 2
        """
        with self._lock:
            return len(self._store)
    
    @property
    def ttl_minutes(self) -> int:
        """Retorna el TTL configurado en minutos.
        
        Returns:
            Tiempo de vida de las sesiones en minutos.
            
        Examples:
            >>> adapter = LocalStorageAdapter(ttl_minutes=30)
            >>> print(adapter.ttl_minutes)  # 30
        """
        return self._ttl_minutes
    
    def _is_expired(self, context: "ConversationContext") -> bool:
        """Verifica si un contexto ha expirado.
        
        Compara el tiempo transcurrido desde la última actualización
        con el TTL configurado.
        
        Args:
            context: Contexto a verificar.
            
        Returns:
            True si el contexto expiró, False si aún está vigente.
        """
        return datetime.now() - context.updated_at > self._ttl
    
    def __repr__(self) -> str:
        """Representación string del adaptador para debugging.
        
        Returns:
            String con información del adaptador.
            
        Examples:
            >>> adapter = LocalStorageAdapter(ttl_minutes=15)
            >>> print(repr(adapter))
            LocalStorageAdapter(ttl_minutes=15, sessions=0)
        """
        return f"LocalStorageAdapter(ttl_minutes={self._ttl_minutes}, sessions={self.session_count})"

