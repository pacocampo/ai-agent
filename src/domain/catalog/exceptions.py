"""Excepciones personalizadas para el módulo de catálogo de inventario."""


class InventoryError(Exception):
    """Excepción base para errores del módulo de inventario."""

    pass


class CatalogNotFoundError(InventoryError):
    """Excepción cuando el archivo del catálogo no se encuentra."""

    pass


class CatalogLoadError(InventoryError):
    """Excepción cuando falla la carga del archivo CSV."""

    pass


class InvalidSearchParametersError(InventoryError):
    """Excepción cuando los parámetros de búsqueda son inválidos."""

    pass

