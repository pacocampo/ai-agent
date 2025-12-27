"""Handlers para cada tipo de acción del agente."""

from src.agent.handlers.catalog import (
    handle_clarify,
    handle_get_car_details,
    handle_get_financing_options,
    handle_get_kavak_info,
    handle_out_of_scope,
    handle_respond,
    handle_search_cars,
)

__all__ = [
    "handle_search_cars",
    "handle_get_car_details",
    "handle_get_financing_options",
    "handle_get_kavak_info",
    "handle_respond",
    "handle_clarify",
    "handle_out_of_scope",
]

