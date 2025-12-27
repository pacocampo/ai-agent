"""Módulo para consultar información general de Kavak."""

from functools import lru_cache

from src.core.interfaces import FileStorage

# Ruta relativa del archivo de información (se resuelve según el FileStorage adapter)
INFO_RELATIVE_PATH = "resources/info.txt"


def _get_file_storage() -> FileStorage:
    """Obtiene el FileStorage adapter del container.
    
    Lazy import para evitar circular dependencies.
    
    Returns:
        Instancia de FileStorage configurada.
    """
    from src.factories import get_container
    return get_container().file_storage()


@lru_cache(maxsize=1)
def _load_kavak_info() -> str:
    """Carga y cachea la información de Kavak.

    Returns:
        Contenido del archivo de información como string.

    Raises:
        FileNotFoundError: Si el archivo no existe.
        IOError: Si hay un error al leer el archivo.
    """
    file_storage = _get_file_storage()
    
    if not file_storage.exists(INFO_RELATIVE_PATH):
        raise FileNotFoundError(
            f"Archivo de información no encontrado: {INFO_RELATIVE_PATH}"
        )

    try:
        return file_storage.read_text(INFO_RELATIVE_PATH)
    except Exception as e:
        raise IOError(f"Error al leer información de Kavak: {e}") from e


def get_kavak_info() -> str:
    """Obtiene la información general de Kavak.

    Retorna todo el contenido para que el LLM lo procese y responda.

    Returns:
        Información completa de Kavak como string.

    Examples:
        >>> info = get_kavak_info()
        >>> "sedes" in info.lower()
        True
    """
    return _load_kavak_info()


def clear_info_cache() -> None:
    """Limpia el caché de información para forzar una recarga.

    Útil cuando el archivo ha sido actualizado y se necesita
    recargar los datos en memoria.
    """
    _load_kavak_info.cache_clear()

