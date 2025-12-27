"""Tests for agent presenter."""

from src.agent.models import ErrorResult, SearchCarsResult
from src.agent.presenter import render_reply
from src.core.models import AgentAction, AgentDecision
from src.domain.catalog import SearchResults


def test_render_search_cars_no_results_no_criteria():
    decision = AgentDecision(action=AgentAction.SEARCH_CARS)
    result = SearchCarsResult(results=SearchResults(), decision=decision)
    reply = render_reply(result)
    assert "No encontré vehículos" in reply.message


def test_render_search_cars_no_results_with_criteria():
    decision = AgentDecision(
        action=AgentAction.SEARCH_CARS, make="Toyota", model="Corolla"
    )
    result = SearchCarsResult(results=SearchResults(), decision=decision)
    reply = render_reply(result)
    assert "Toyota Corolla" in reply.message


def test_render_error_returns_default_message():
    decision = AgentDecision(action=AgentAction.RESPOND, message="hello")
    result = ErrorResult(error="boom", decision=decision)
    reply = render_reply(result)
    assert reply.success is False
    assert "Lo siento" in reply.message
