"""Tests for catalog pydantic models."""

import types

import pytest
from pydantic import ValidationError

from src.domain.catalog import VehicleSearchParams


def test_vehicle_search_params_optional_make_model():
    params = VehicleSearchParams(make=None, model=None)
    assert params.make is None
    assert params.model is None


def test_vehicle_search_params_strip_and_normalize():
    params = VehicleSearchParams(make=" Toyota ", model=" Corolla ")
    assert params.make == "Toyota"
    assert params.model == "Corolla"
    assert params.make_normalized == "toyota"
    assert params.model_normalized == "corolla"


def test_vehicle_search_params_empty_string_raises():
    with pytest.raises(ValidationError):
        VehicleSearchParams(make=" ", model="Corolla")


def test_vehicle_search_params_future_year_raises(monkeypatch):
    from src.domain.catalog import models as models_module

    fake_datetime = types.SimpleNamespace(
        now=lambda: types.SimpleNamespace(year=2024)
    )
    monkeypatch.setattr(models_module, "datetime", fake_datetime)

    with pytest.raises(ValidationError):
        VehicleSearchParams(year=2025)
