"""Tests for agent handlers."""

import pytest

from src.agent.handlers.catalog import (
    handle_get_financing_options,
    handle_search_cars,
)
from src.agent.models import ClarifyResult, ErrorResult, SearchCarsResult
from src.core.models import AgentAction, AgentDecision, MissingField
from src.tools.catalog.inventory import (
    get_available_models,
    get_makes_for_model,
)


def _build_typo(value: str) -> str:
    return value[:-1] if len(value) > 3 else f"{value}x"


def test_handle_search_cars_returns_results(sample_make_model):
    make, model = sample_make_model
    decision = AgentDecision(
        action=AgentAction.SEARCH_CARS, make=make, model=model
    )
    result = handle_search_cars(decision)
    assert isinstance(result, SearchCarsResult)
    assert result.results.total_count > 0


def test_handle_search_cars_clarify_ambiguous_model():
    models = get_available_models()
    ambiguous_model = None
    for model in models:
        if len(get_makes_for_model(model)) > 1:
            ambiguous_model = model
            break

    if not ambiguous_model:
        pytest.skip("No ambiguous models found in catalog.")

    decision = AgentDecision(
        action=AgentAction.SEARCH_CARS, model=ambiguous_model
    )
    result = handle_search_cars(decision)
    assert isinstance(result, ClarifyResult)
    assert MissingField.MAKE in result.missing_fields


def test_handle_search_cars_suggests_typos(sample_make_model):
    make, model = sample_make_model
    decision = AgentDecision(
        action=AgentAction.SEARCH_CARS,
        make=_build_typo(make),
        model=model,
    )
    result = handle_search_cars(decision)
    assert isinstance(result, ClarifyResult)


def test_handle_get_financing_options_missing_stock_id():
    decision = AgentDecision(action=AgentAction.GET_FINANCING_OPTIONS)
    result = handle_get_financing_options(decision)
    assert isinstance(result, ErrorResult)
