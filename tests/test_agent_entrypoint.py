"""Tests for agent entrypoint helpers."""

import pytest

from src.adapters import LocalStorageAdapter
from src.agent.models import UserReply
from src.agent.services import ConversationService
from src.core.models import (
    AgentAction,
    AgentDecision,
    ConversationContext,
    MissingField,
    SelectedVehicle,
)
from src.services import MessageProcessorService


@pytest.mark.asyncio
async def test_process_user_message_happy_path(monkeypatch):
    async_store = LocalStorageAdapter(ttl_minutes=1)
    service = ConversationService(async_store)

    def fake_decision(*args, **kwargs):
        return AgentDecision(
            action=AgentAction.RESPOND, message="ok"
        )

    def fake_route(*args, **kwargs):
        from src.agent.models import ResponseResult

        return ResponseResult(message="ok", decision=fake_decision())

    def fake_render(*args, **kwargs):
        return UserReply(message="ok", success=True)

    from unittest.mock import Mock
    from src.core.interfaces import LLMAdapter
    
    mock_llm = Mock(spec=LLMAdapter)
    mock_llm.get_agent_decision.return_value = fake_decision()
    mock_llm.humanize_response.return_value = "ok"

    processor = MessageProcessorService(service, mock_llm)
    
    monkeypatch.setattr("src.agent.router.route_decision", fake_route)
    monkeypatch.setattr("src.agent.presenter.render_reply", fake_render)

    reply = await processor.process(
        "hola", session_id="s1", humanize=False
    )
    assert reply.message == "ok"
    assert reply.success is True


def test_apply_clarify_guards_financing_without_context(empty_context):
    from src.services.message_processor import MessageProcessorService
    from unittest.mock import Mock
    from src.core.interfaces import LLMAdapter
    
    mock_llm = Mock(spec=LLMAdapter)
    processor = MessageProcessorService(Mock(), mock_llm)
    
    decision = AgentDecision(action=AgentAction.GET_FINANCING_OPTIONS)
    updated = processor._apply_clarify_guards("financiamiento", decision, empty_context)
    assert updated.action == AgentAction.CLARIFY


def test_apply_clarify_guards_financing_without_selection(empty_context):
    from src.services.message_processor import MessageProcessorService
    from unittest.mock import Mock
    from src.core.interfaces import LLMAdapter
    
    mock_llm = Mock(spec=LLMAdapter)
    processor = MessageProcessorService(Mock(), mock_llm)
    
    empty_context.last_search_results = [
        SelectedVehicle(
            stock_id=1,
            make="Test",
            model="Car",
            year=2020,
            price=100.0,
            km=1000,
        )
    ]
    decision = AgentDecision(action=AgentAction.GET_FINANCING_OPTIONS)
    updated = processor._apply_clarify_guards("financiamiento", decision, empty_context)
    assert updated.action == AgentAction.CLARIFY


def test_apply_clarify_guards_reference_without_context(empty_context):
    from src.services.message_processor import MessageProcessorService
    from unittest.mock import Mock
    from src.core.interfaces import LLMAdapter
    
    mock_llm = Mock(spec=LLMAdapter)
    processor = MessageProcessorService(Mock(), mock_llm)
    
    decision = AgentDecision(action=AgentAction.RESPOND)
    updated = processor._apply_clarify_guards("el mas barato", decision, empty_context)
    assert updated.action == AgentAction.CLARIFY
    assert MissingField.MAKE in updated.missing_information
    assert MissingField.MODEL in updated.missing_information
