"""Tests for catalog inventory helpers."""

import pytest

from src.domain.catalog import InventoryError
from src.tools.catalog.inventory import (
    get_available_makes,
    get_available_models,
    get_makes_for_model,
    get_vehicle_details,
    search_vehicles,
)


def test_get_available_makes_returns_list():
    makes = get_available_makes()
    assert isinstance(makes, list)
    assert makes, "Expected at least one make in the catalog."


def test_get_available_models_filters_by_make(sample_make_model):
    make, _ = sample_make_model
    models = get_available_models(make)
    assert models, "Expected models for the sample make."


def test_get_makes_for_model_returns_matches(sample_make_model):
    make, model = sample_make_model
    makes = get_makes_for_model(model)
    assert make in makes


def test_search_vehicles_no_filters_returns_results():
    results = search_vehicles(make=None, model=None)
    assert results.total_count > 0
    assert results.results


def test_search_vehicles_filters_make_model(sample_make_model):
    make, model = sample_make_model
    results = search_vehicles(make=make, model=model)
    assert results.total_count > 0
    for vehicle in results.results:
        assert vehicle.make.lower() == make.lower()
        assert vehicle.model.lower() == model.lower()


def test_search_vehicles_price_filter_matches(sample_make_model):
    make, model = sample_make_model
    results = search_vehicles(make=make, model=model)
    min_price = min(v.price for v in results.results)
    filtered = search_vehicles(make=make, model=model, price=min_price)
    assert filtered.results
    assert all(v.price <= min_price for v in filtered.results)


def test_get_vehicle_details_valid(sample_vehicle):
    vehicle = get_vehicle_details(sample_vehicle.stock_id)
    assert vehicle.stock_id == sample_vehicle.stock_id


def test_get_vehicle_details_invalid_raises():
    with pytest.raises(InventoryError):
        get_vehicle_details("not-a-number")
