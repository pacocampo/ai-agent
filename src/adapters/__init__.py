"""Adaptadores concretos para servicios externos."""

from src.adapters.files import LocalFileStorageAdapter
from src.adapters.llm.openapi_adapter import OpenAIAdapter
from src.adapters.messaging import TwilioMessagingAdapter
from src.adapters.storage.local_adapter import LocalStorageAdapter

__all__ = [
    # LLM Adapters
    "OpenAIAdapter",
    # Messaging Adapters
    "TwilioMessagingAdapter",
    # Storage Adapters
    "LocalStorageAdapter",
    # File Storage Adapters
    "LocalFileStorageAdapter",
]

