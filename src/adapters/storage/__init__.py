"""Adaptadores de almacenamiento para contexto de conversación."""

from src.adapters.storage.base import StorageAdapter
from src.adapters.storage.local_adapter import LocalStorageAdapter

__all__ = [
    "StorageAdapter",
    "LocalStorageAdapter",
]

