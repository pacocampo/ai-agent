"""Adaptador local para almacenamiento de archivos estáticos."""

from pathlib import Path

from src.core.interfaces import FileStorage


class LocalFileStorageAdapter(FileStorage):
    """Adaptador para leer archivos desde el sistema de archivos local.
    
    Implementación simple que lee archivos desde el sistema de archivos.
    Adecuado para desarrollo y testing. Para producción, se recomienda
    usar S3Adapter para almacenar archivos en la nube.
    
    Attributes:
        base_path: Ruta base para resolver rutas relativas. Si es None,
            las rutas se interpretan como absolutas.
    """
    
    def __init__(self, base_path: Path | str | None = None):
        """Inicializa el adaptador de archivos local.
        
        Args:
            base_path: Ruta base opcional. Si se proporciona, todas las
                rutas se resuelven relativas a esta ruta base.
        """
        if base_path is None:
            self._base_path = None
        else:
            self._base_path = Path(base_path)
    
    def _resolve_path(self, file_path: str) -> Path:
        """Resuelve la ruta del archivo.
        
        Args:
            file_path: Ruta del archivo (relativa o absoluta).
            
        Returns:
            Path resuelto.
        """
        path = Path(file_path)
        if self._base_path is not None and not path.is_absolute():
            return self._base_path / path
        return path
    
    def read_text(self, file_path: str) -> str:
        """Lee un archivo de texto completo.
        
        Args:
            file_path: Ruta del archivo a leer.
            
        Returns:
            Contenido del archivo como string.
            
        Raises:
            FileNotFoundError: Si el archivo no existe.
            IOError: Si hay un error al leer el archivo.
        """
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {resolved_path}"
            )
        
        try:
            with open(resolved_path, "r", encoding="utf-8") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error al leer archivo {resolved_path}: {e}") from e
    
    def read_bytes(self, file_path: str) -> bytes:
        """Lee un archivo como bytes.
        
        Args:
            file_path: Ruta del archivo a leer.
            
        Returns:
            Contenido del archivo como bytes.
            
        Raises:
            FileNotFoundError: Si el archivo no existe.
            IOError: Si hay un error al leer el archivo.
        """
        resolved_path = self._resolve_path(file_path)
        
        if not resolved_path.exists():
            raise FileNotFoundError(
                f"Archivo no encontrado: {resolved_path}"
            )
        
        try:
            with open(resolved_path, "rb") as f:
                return f.read()
        except Exception as e:
            raise IOError(f"Error al leer archivo {resolved_path}: {e}") from e
    
    def exists(self, file_path: str) -> bool:
        """Verifica si un archivo existe.
        
        Args:
            file_path: Ruta del archivo a verificar.
            
        Returns:
            True si el archivo existe, False si no.
        """
        resolved_path = self._resolve_path(file_path)
        return resolved_path.exists()

