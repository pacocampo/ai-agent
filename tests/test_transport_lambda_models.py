"""Tests for Lambda request models."""

import pytest
from pydantic import ValidationError

from src.transport.lambda_models import AgentRequest


def test_agent_request_accepts_message():
    req = AgentRequest(message="hola")
    assert req.message == "hola"


def test_agent_request_accepts_user_text():
    req = AgentRequest(user_text="hola")
    assert req.user_text == "hola"


def test_agent_request_requires_message_or_user_text():
    with pytest.raises(ValidationError):
        AgentRequest()
