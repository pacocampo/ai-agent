"""Dependency Injection Container."""

from functools import lru_cache
from pathlib import Path

from src.adapters import LocalStorageAdapter, OpenAIAdapter
from src.adapters.files import LocalFileStorageAdapter
from src.agent.services import ConversationService
from src.core.interfaces import ContextStore, FileStorage, LLMAdapter
from src.services import MessageProcessorService


class Container:
    """Container for dependency injection.
    
    Provides singleton instances of adapters and services
    configured for the current environment.
    """
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    @lru_cache(maxsize=1)
    def llm_adapter(self) -> LLMAdapter:
        """Get LLM adapter instance."""
        return OpenAIAdapter()
    
    @lru_cache(maxsize=1)
    def storage_adapter(self) -> ContextStore:
        """Get storage adapter instance."""
        return LocalStorageAdapter(ttl_minutes=30)
    
    @lru_cache(maxsize=1)
    def conversation_service(self) -> ConversationService:
        """Get conversation service instance."""
        return ConversationService(self.storage_adapter())
    
    @lru_cache(maxsize=1)
    def file_storage(self) -> FileStorage:
        """Get file storage adapter instance.
        
        Returns LocalFileStorageAdapter by default, configured to use
        the resources directory. In production, this should be replaced
        with S3Adapter or similar cloud storage adapter.
        """
        # Base path: resources directory relative to tools/catalog
        base_path = Path(__file__).parent.parent / "tools" / "catalog"
        return LocalFileStorageAdapter(base_path=base_path)
    
    @lru_cache(maxsize=1)
    def message_processor(self) -> MessageProcessorService:
        """Get message processor service instance."""
        return MessageProcessorService(
            self.conversation_service(),
            self.llm_adapter()
        )


# Global container instance
_container = Container()


def get_container() -> Container:
    """Get global container instance."""
    return _container

