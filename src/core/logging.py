"""Configuración de logging con AWS Lambda Powertools."""

import logging
from typing import Any

from src.infrastructure.observability import logger as _logger


def configure_logging(
    level: int = logging.INFO,
    json_format: bool = False,
) -> None:
    """Configura el logging para la aplicación.

    Args:
        level: Nivel de logging (por defecto INFO).
        json_format: No aplica con Powertools; se mantiene por compatibilidad.
    """
    _logger.setLevel(level)


def get_logger(name: str | None = None, **initial_context: Any):
    """Obtiene un logger con contexto inicial.

    Args:
        name: Nombre del logger (típicamente __name__ del módulo).
        **initial_context: Contexto inicial para agregar al logger.

    Returns:
        Logger de Powertools con el contexto inicial.
    """
    if name:
        _logger.append_keys(logger_name=name)
    if initial_context:
        _logger.append_keys(**initial_context)
    return _logger
