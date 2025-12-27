"""Módulo para consultar el inventario de vehículos desde el catálogo CSV."""

import csv
from functools import lru_cache
from io import StringIO
from typing import TYPE_CHECKING

from pydantic import ValidationError

from src.core.interfaces import FileStorage
from src.domain.catalog import (
    CatalogLoadError,
    CatalogNotFoundError,
    InvalidSearchParametersError,
    InventoryError,
    SearchResults,
    VehicleSearchParams,
    VehicleSearchResult,
)

if TYPE_CHECKING:
    from typing import TypedDict

    class VehicleRow(TypedDict):
        stock_id: int
        make: str
        model: str
        year: int
        km: int
        price: float
        version: str
        bluetooth: bool
        car_play: bool

# Ruta relativa del catálogo (se resuelve según el FileStorage adapter)
CATALOG_RELATIVE_PATH = "resources/sample_caso_ai_engineer.csv"


def _get_file_storage() -> FileStorage:
    """Obtiene el FileStorage adapter del container.
    
    Lazy import para evitar circular dependencies.
    
    Returns:
        Instancia de FileStorage configurada.
    """
    from src.factories import get_container
    return get_container().file_storage()


@lru_cache(maxsize=1)
def _load_catalog_data() -> list["VehicleRow"]:
    """Carga y cachea el catálogo de vehículos desde el archivo CSV.

    Esta función carga el archivo CSV del catálogo de vehículos y lo almacena
    en memoria como lista de diccionarios. El resultado se cachea usando
    lru_cache para evitar lecturas repetidas del disco.

    Returns:
        Lista de diccionarios con los datos del catálogo de vehículos.

    Raises:
        CatalogNotFoundError: Si el archivo CSV no existe en la ruta esperada.
        CatalogLoadError: Si ocurre un error al leer o parsear el archivo CSV.
    """
    file_storage = _get_file_storage()
    
    if not file_storage.exists(CATALOG_RELATIVE_PATH):
        raise CatalogNotFoundError(
            f"El archivo del catálogo no se encuentra: {CATALOG_RELATIVE_PATH}"
        )

    try:
        # Leer como texto
        csv_text = file_storage.read_text(CATALOG_RELATIVE_PATH)
        
        if not csv_text.strip():
            raise CatalogLoadError("El archivo del catálogo está vacío.")
        
        # Parsear CSV
        reader = csv.DictReader(StringIO(csv_text))
        vehicles = []
        
        for row in reader:
            try:
                # Normalizar strings
                make = row["make"].strip().lower()
                model = row["model"].strip().lower()
                
                # Convertir booleanos
                bluetooth = row.get("bluetooth", "").strip().lower() == "sí"
                car_play = row.get("car_play", "").strip().lower() == "sí"
                
                vehicle: "VehicleRow" = {
                    "stock_id": int(row["stock_id"]),
                    "make": make,
                    "model": model,
                    "year": int(row["year"]),
                    "km": int(row["km"]),
                    "price": float(row["price"]),
                    "version": str(row.get("version", "")),
                    "bluetooth": bluetooth,
                    "car_play": car_play,
                }
                vehicles.append(vehicle)
            except (KeyError, ValueError, TypeError) as e:
                raise CatalogLoadError(
                    f"Error al parsear fila del catálogo: {row}. Error: {e}"
                ) from e
        
        if not vehicles:
            raise CatalogLoadError("El archivo del catálogo no contiene vehículos válidos.")
        
        return vehicles
        
    except csv.Error as e:
        raise CatalogLoadError(
            f"Error al parsear el archivo CSV del catálogo: {e}"
        ) from e
    except Exception as e:
        if isinstance(e, CatalogLoadError):
            raise
        raise CatalogLoadError(
            f"Error inesperado al cargar el catálogo: {e}"
        ) from e


def clear_catalog_cache() -> None:
    """Limpia el caché del catálogo para forzar una recarga.

    Útil cuando el archivo CSV ha sido actualizado y se necesita
    recargar los datos en memoria.
    """
    _load_catalog_data.cache_clear()


def get_available_makes() -> list[str]:
    """Obtiene la lista de marcas disponibles en el catálogo."""
    vehicles = _load_catalog_data()
    makes = {v["make"].title() for v in vehicles}
    return sorted(makes)


def get_available_models(make: str | None = None) -> list[str]:
    """Obtiene la lista de modelos disponibles en el catálogo.

    Args:
        make: Marca del vehículo. Si se especifica, filtra modelos por marca.
    """
    vehicles = _load_catalog_data()
    if make:
        make_normalized = make.strip().lower()
        models = {v["model"].title() for v in vehicles if v["make"] == make_normalized}
    else:
        models = {v["model"].title() for v in vehicles}
    return sorted(models)


def get_makes_for_model(model: str) -> list[str]:
    """Obtiene las marcas disponibles para un modelo específico."""
    if not model:
        return []
    vehicles = _load_catalog_data()
    model_normalized = model.strip().lower()
    makes = {v["make"].title() for v in vehicles if v["model"] == model_normalized}
    return sorted(makes)


def search_vehicles(
    make: str | None,
    model: str | None,
    year: int | None = None,
    km: int | None = None,
    price: float | None = None,
) -> SearchResults:
    """Busca vehículos en el catálogo basándose en los criterios especificados.

    Esta función permite buscar vehículos en el inventario usando marca y modelo
    como filtros opcionales, y opcionalmente filtrar por año, kilometraje y precio.

    Args:
        make: Marca del vehículo (opcional). La búsqueda es case-insensitive.
        model: Modelo del vehículo (opcional). La búsqueda es case-insensitive.
        year: Año del vehículo. Si se especifica, filtra vehículos de ese año exacto.
        km: Kilometraje máximo. Si se especifica, filtra vehículos con km <= al valor.
        price: Precio máximo. Si se especifica, filtra vehículos con precio <= al valor.

    Returns:
        SearchResults conteniendo la lista de vehículos que coinciden con los
        criterios de búsqueda y el conteo total de resultados.

    Raises:
        InvalidSearchParametersError: Si make o model están vacíos, o si los
            parámetros numéricos tienen valores negativos.
        CatalogNotFoundError: Si el archivo del catálogo no existe.
        CatalogLoadError: Si hay un error al cargar el catálogo.

    Examples:
        >>> # Búsqueda básica por marca y modelo
        >>> results = search_vehicles(make="Toyota", model="Corolla")
        >>> print(f"Se encontraron {results.total_count} vehículos")

        >>> # Búsqueda con filtros opcionales
        >>> results = search_vehicles(
        ...     make="Honda",
        ...     model="CR-V",
        ...     year=2017,
        ...     km=80000,
        ...     price=450000
        ... )
    """
    try:
        params = VehicleSearchParams(
            make=make,
            model=model,
            year=year,
            km=km,
            price=price,
        )
    except ValidationError as e:
        raise InvalidSearchParametersError(str(e)) from e

    vehicles = _load_catalog_data()
    
    # Filtrar vehículos
    filtered = []
    for vehicle in vehicles:
        # Filtro por marca
        if params.make_normalized and vehicle["make"] != params.make_normalized:
            continue
        
        # Filtro por modelo
        if params.model_normalized and vehicle["model"] != params.model_normalized:
            continue
        
        # Filtro por año
        if params.year is not None and vehicle["year"] != params.year:
            continue
        
        # Filtro por kilometraje
        if params.km is not None and vehicle["km"] > params.km:
            continue
        
        # Filtro por precio
        if params.price is not None and vehicle["price"] > params.price:
            continue
        
        filtered.append(vehicle)

    # Convertir a VehicleSearchResult
    results = [
        VehicleSearchResult(
            stock_id=vehicle["stock_id"],
            make=vehicle["make"].title(),
            model=vehicle["model"].title(),
            year=vehicle["year"],
            km=vehicle["km"],
            price=vehicle["price"],
            version=vehicle["version"],
            bluetooth=vehicle["bluetooth"],
            car_play=vehicle["car_play"],
        )
        for vehicle in filtered
    ]

    return SearchResults(results=results, total_count=len(results))


def get_vehicle_details(stock_id: int | str) -> VehicleSearchResult:
    """Obtiene los detalles de un vehículo en el catálogo basándose en su ID de stock.

    Esta función busca un vehículo en el inventario usando su ID de stock y
    devuelve los detalles completos del vehículo si se encuentra.

    Args:
        stock_id: Identificador único del vehículo en stock (int o string numérico).

    Returns:
        VehicleSearchResult con los detalles del vehículo encontrado.

    Raises:
        InventoryError: Si no se encuentra el vehículo o hay un error de conversión.
    """
    # Convertir a int si viene como string
    try:
        stock_id_int = int(stock_id)
    except (ValueError, TypeError) as e:
        raise InventoryError(
            f"stock_id inválido: '{stock_id}'. Debe ser un número entero."
        ) from e

    vehicles = _load_catalog_data()
    
    # Buscar vehículo
    vehicle = None
    for v in vehicles:
        if v["stock_id"] == stock_id_int:
            vehicle = v
            break
    
    if vehicle is None:
        raise InventoryError(f"No se encontró el vehículo con stock_id {stock_id_int}")

    return VehicleSearchResult(
        stock_id=vehicle["stock_id"],
        make=vehicle["make"].title(),
        model=vehicle["model"].title(),
        year=vehicle["year"],
        km=vehicle["km"],
        price=vehicle["price"],
        version=vehicle["version"],
        bluetooth=vehicle["bluetooth"],
        car_play=vehicle["car_play"],
    )
