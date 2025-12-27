"""Tests for Lambda handler."""

import json
from unittest.mock import AsyncMock, Mock

import pytest

from src.agent.models import UserReply
from src.transport.lambda_handler import handler


class _FakeLambdaContext:
    function_name = "test-fn"
    memory_limit_in_mb = 128
    invoked_function_arn = "arn:aws:lambda:us-east-1:123:function:test-fn"
    aws_request_id = "test-request-id"


def test_handler_returns_400_on_invalid_payload():
    event = {"body": json.dumps({})}
    response = handler(event, _FakeLambdaContext())
    assert response["statusCode"] == 400
    assert "Solicitud inválida" in response["body"]


def test_handler_returns_200_on_success(monkeypatch):
    # Mock MessageProcessorService
    mock_processor = Mock()
    mock_processor.process = AsyncMock(
        return_value=UserReply(message="ok", success=True, vehicles=[])
    )
    
    # Mock container
    mock_container = Mock()
    mock_container.message_processor.return_value = mock_processor
    
    monkeypatch.setattr(
        "src.transport.lambda_handler.get_container",
        lambda: mock_container,
    )

    event = {
        "body": json.dumps({"message": "hola", "session_id": "s1"}),
        "requestContext": {
            "http": {
                "path": "/agent"
            }
        }
    }
    response = handler(event, _FakeLambdaContext())
    assert response["statusCode"] == 200
    body = json.loads(response["body"])
    assert body["message"] == "ok"
    assert body["success"] is True


def test_handler_handles_twilio_webhook_without_json_validation(monkeypatch):
    """Verifica que los webhooks de Twilio (form-encoded) no sean validados como JSON."""
    # Mock MessageProcessorService
    mock_processor = Mock()
    mock_processor.process = AsyncMock(
        return_value=UserReply(message="Respuesta del agente", success=True, vehicles=[])
    )
    
    # Mock container
    mock_container = Mock()
    mock_container.message_processor.return_value = mock_processor
    
    monkeypatch.setattr(
        "src.transport.lambda_handler.get_container",
        lambda: mock_container,
    )

    # Evento de Twilio con form-encoded body (no JSON)
    event = {
        "body": "Body=Hola&From=whatsapp%3A%2B1234567890",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded"
        },
        "requestContext": {
            "http": {
                "path": "/twilio/webhook"
            }
        }
    }
    
    # No debería fallar con "Payload no puede estar vacío"
    response = handler(event, _FakeLambdaContext())
    
    # Debería retornar 200 con TwiML XML
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/xml"
    assert "<?xml" in response["body"]
    assert "Respuesta del agente" in response["body"]


def test_handler_handles_twilio_webhook_by_content_type(monkeypatch):
    """Verifica que los webhooks de Twilio se detecten por Content-Type."""
    # Mock MessageProcessorService
    mock_processor = Mock()
    mock_processor.process = AsyncMock(
        return_value=UserReply(message="OK", success=True, vehicles=[])
    )
    
    # Mock container
    mock_container = Mock()
    mock_container.message_processor.return_value = mock_processor
    
    monkeypatch.setattr(
        "src.transport.lambda_handler.get_container",
        lambda: mock_container,
    )

    # Evento de Twilio detectado solo por Content-Type (sin path /twilio)
    event = {
        "body": "Body=Test&From=whatsapp%3A%2B9876543210",
        "headers": {
            "Content-Type": "application/x-www-form-urlencoded"
        }
    }
    
    response = handler(event, _FakeLambdaContext())
    assert response["statusCode"] == 200
    assert response["headers"]["Content-Type"] == "text/xml"
