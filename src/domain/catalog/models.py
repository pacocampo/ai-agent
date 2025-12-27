"""Modelos Pydantic para el catálogo de inventario de vehículos."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator
from src.core.config import APPROVED_DURATIONS, INTEREST_RATE


class VehicleSearchParams(BaseModel):
    """Parámetros de búsqueda de vehículos con validación integrada.

    Attributes:
        make: Marca del vehículo (opcional).
        model: Modelo del vehículo (opcional).
        year: Año del vehículo (opcional, entre 1900 y año actual).
        km: Kilometraje máximo (opcional, >= 0).
        price: Precio máximo (opcional, >= 0).
    """

    make: str | None = Field(
        default=None, min_length=1, description="Marca del vehículo"
    )
    model: str | None = Field(
        default=None, min_length=1, description="Modelo del vehículo"
    )
    year: int | None = Field(None, ge=1900, description="Año del vehículo")
    km: int | None = Field(None, ge=0, description="Kilometraje máximo")
    price: float | None = Field(None, ge=0, description="Precio máximo")

    @field_validator("make", "model", mode="before")
    @classmethod
    def strip_and_validate_not_empty(cls, value: str | None) -> str | None:
        """Elimina espacios en blanco y valida que no esté vacío.

        Args:
            value: Valor del campo a validar.

        Returns:
            Valor sin espacios en blanco al inicio y final.

        Raises:
            ValueError: Si el valor está vacío después de eliminar espacios.
        """
        if isinstance(value, str):
            value = value.strip()
            if not value:
                raise ValueError("No puede estar vacío")
        return value

    @field_validator("year")
    @classmethod
    def validate_year_not_future(cls, value: int | None) -> int | None:
        """Valida que el año no sea mayor al año actual.

        Args:
            value: Año a validar.

        Returns:
            El año validado.

        Raises:
            ValueError: Si el año es mayor al año actual.
        """
        if value is not None:
            current_year = datetime.now().year
            if value > current_year:
                raise ValueError(f"No puede ser mayor a {current_year}")
        return value

    @property
    def make_normalized(self) -> str | None:
        """Retorna la marca normalizada en minúsculas."""
        return self.make.lower() if self.make else None

    @property
    def model_normalized(self) -> str | None:
        """Retorna el modelo normalizado en minúsculas."""
        return self.model.lower() if self.model else None


class InventoryExtraction(BaseModel):
    """Modelo para extracción de inventario."""

    class Item(BaseModel):
        """Representa un item del inventario."""

        make: str
        model: str
        year: int
        version: str
        bluetooth: bool
        car_play: bool
        quantity: int
        price: float
        km: int

    items: list[Item]


class VehicleSearchResult(BaseModel):
    """Modelo para representar un resultado de búsqueda de vehículo."""

    stock_id: int = Field(..., description="Identificador único del vehículo en stock")
    make: str = Field(..., description="Marca del vehículo")
    model: str = Field(..., description="Modelo del vehículo")
    year: int = Field(..., description="Año del vehículo")
    km: int = Field(..., description="Kilometraje del vehículo")
    price: float = Field(..., description="Precio del vehículo en MXN")
    version: str = Field(..., description="Versión del vehículo")
    bluetooth: bool = Field(False, description="Indica si tiene bluetooth")
    car_play: bool = Field(False, description="Indica si tiene CarPlay")


class SearchResults(BaseModel):
    """Modelo para representar los resultados de una búsqueda."""

    results: list[VehicleSearchResult] = Field(
        default_factory=list, description="Lista de vehículos encontrados"
    )
    total_count: int = Field(0, description="Cantidad total de vehículos encontrados")


class FinancingOptionsResult(BaseModel):
    """Modelo para representar los resultados de una solicitud de opciones de financiamiento."""

    class Amortization(BaseModel):
        """Modelo para representar una opción de financiamiento."""

        month: int
        balance: float
        interest: float
        amortization: float
        total_payment: float

