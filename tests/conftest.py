"""Shared pytest fixtures."""

import pytest

from src.core.models import ConversationContext
from src.tools.catalog.inventory import (
    _load_catalog_data,
    clear_catalog_cache,
    get_available_makes,
    get_available_models,
    search_vehicles,
)
from src.tools.catalog.kavak_info import _load_kavak_info, clear_info_cache


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear caches before each test to ensure clean state."""
    clear_catalog_cache()
    clear_info_cache()
    _load_catalog_data.cache_clear()
    _load_kavak_info.cache_clear()
    yield
    # Clear after test too
    clear_catalog_cache()
    clear_info_cache()
    _load_catalog_data.cache_clear()
    _load_kavak_info.cache_clear()


@pytest.fixture(scope="session")
def sample_make_model() -> tuple[str, str]:
    makes = get_available_makes()
    assert makes, "Catalog should contain at least one make."
    make = makes[0]
    models = get_available_models(make)
    assert models, "Catalog should contain at least one model for a make."
    return make, models[0]


@pytest.fixture(scope="session")
def sample_vehicle(sample_make_model):
    make, model = sample_make_model
    results = search_vehicles(make=make, model=model)
    assert results.results, "Expected at least one vehicle for sample make/model."
    return results.results[0]


@pytest.fixture()
def empty_context() -> ConversationContext:
    return ConversationContext(session_id="test-session")
