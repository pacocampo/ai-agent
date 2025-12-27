"""Tests for error handler module."""

from unittest.mock import Mock

import pytest
from pydantic import ValidationError

from src.agent.models import UserReply
from src.transport.error_handler import (
    TransportErrorHandler,
    create_fallback_response,
    safe_format_error,
    safe_format_response,
)


class TestCreateFallbackResponse:
    """Tests para create_fallback_response."""
    
    def test_creates_json_response(self):
        """Test que crea una respuesta JSON válida."""
        response = create_fallback_response("Error test", 400)
        
        assert response["statusCode"] == 400
        assert response["headers"]["Content-Type"] == "application/json"
        assert "error" in response["body"]
        assert "Error test" in response["body"]
    
    def test_default_status_code_is_500(self):
        """Test que el status code por defecto es 500."""
        response = create_fallback_response("Error")
        
        assert response["statusCode"] == 500


class TestSafeFormatError:
    """Tests para safe_format_error."""
    
    def test_formats_error_successfully(self):
        """Test que formatea error exitosamente cuando el handler funciona."""
        mock_handler = Mock()
        mock_handler.format_error.return_value = {
            "statusCode": 400,
            "headers": {"Content-Type": "text/xml"},
            "body": "<Response>Error</Response>",
        }
        
        response = safe_format_error(mock_handler, "Test error", 400)
        
        assert response["statusCode"] == 400
        mock_handler.format_error.assert_called_once_with("Test error", status_code=400)
    
    def test_falls_back_when_format_error_fails(self):
        """Test que usa fallback cuando format_error falla."""
        mock_handler = Mock()
        mock_handler.format_error.side_effect = Exception("Format error failed")
        mock_handler.__class__.__name__ = "TestHandler"
        
        response = safe_format_error(mock_handler, "Test error", 400)
        
        assert response["statusCode"] == 400
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Test error" in response["body"]


class TestSafeFormatResponse:
    """Tests para safe_format_response."""
    
    def test_formats_response_successfully(self):
        """Test que formatea respuesta exitosamente."""
        mock_handler = Mock()
        reply = UserReply(message="Test", success=True, vehicles=[])
        mock_handler.format_response.return_value = {
            "statusCode": 200,
            "headers": {"Content-Type": "application/json"},
            "body": '{"message": "Test"}',
        }
        
        response = safe_format_response(mock_handler, reply)
        
        assert response["statusCode"] == 200
        mock_handler.format_response.assert_called_once_with(reply)
    
    def test_handles_valueerror_from_format_response(self):
        """Test que maneja ValueError de format_response."""
        mock_handler = Mock()
        reply = UserReply(message="Test", success=True, vehicles=[])
        mock_handler.format_response.side_effect = ValueError("Format error")
        mock_handler.format_error.return_value = {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Error generando respuesta"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        response = safe_format_response(mock_handler, reply)
        
        assert response["statusCode"] == 500
        mock_handler.format_error.assert_called_once()
    
    def test_handles_runtimeerror_from_format_response(self):
        """Test que maneja RuntimeError de format_response."""
        mock_handler = Mock()
        reply = UserReply(message="Test", success=True, vehicles=[])
        mock_handler.format_response.side_effect = RuntimeError("Runtime error")
        mock_handler.format_error.return_value = {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Error generando respuesta"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        response = safe_format_response(mock_handler, reply)
        
        assert response["statusCode"] == 500
    
    def test_falls_back_when_format_error_also_fails(self):
        """Test que usa fallback cuando format_error también falla."""
        mock_handler = Mock()
        reply = UserReply(message="Test", success=True, vehicles=[])
        mock_handler.format_response.side_effect = ValueError("Format error")
        mock_handler.format_error.side_effect = Exception("Format error also failed")
        mock_handler.__class__.__name__ = "TestHandler"
        
        response = safe_format_response(mock_handler, reply)
        
        assert response["statusCode"] == 500
        assert response["headers"]["Content-Type"] == "application/json"
        assert "Error generando respuesta" in response["body"]


class TestTransportErrorHandler:
    """Tests para TransportErrorHandler."""
    
    def test_handle_parse_error_valueerror(self):
        """Test manejo de ValueError al parsear."""
        mock_handler = Mock()
        mock_handler.format_error.return_value = {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Test error"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        error_handler = TransportErrorHandler(mock_handler)
        error = ValueError("Test error")
        event = {"body": "test body"}
        
        response = error_handler.handle_parse_error(error, event)
        
        assert response["statusCode"] == 400
        mock_handler.format_error.assert_called_once()
    
    def test_handle_parse_error_validationerror(self):
        """Test manejo de ValidationError al parsear."""
        mock_handler = Mock()
        mock_handler.format_error.return_value = {
            "statusCode": 400,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Solicitud inválida"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        error_handler = TransportErrorHandler(mock_handler)
        # Crear un ValidationError simulado
        try:
            from pydantic import BaseModel, Field
            class TestModel(BaseModel):
                required_field: str = Field(...)
            TestModel.model_validate({})
        except ValidationError as e:
            error = e
        
        event = {"body": "test body"}
        
        response = error_handler.handle_parse_error(error, event)
        
        assert response["statusCode"] == 400
        mock_handler.format_error.assert_called_once()
    
    def test_handle_parse_error_generic_exception(self):
        """Test manejo de excepción genérica al parsear."""
        mock_handler = Mock()
        mock_handler.format_error.return_value = {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Error procesando solicitud"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        error_handler = TransportErrorHandler(mock_handler)
        error = RuntimeError("Unexpected error")
        event = {"body": "test body"}
        
        response = error_handler.handle_parse_error(error, event)
        
        assert response["statusCode"] == 500
        mock_handler.format_error.assert_called_once()
    
    def test_handle_processing_error(self):
        """Test manejo de error al procesar mensaje."""
        mock_handler = Mock()
        mock_handler.format_error.return_value = {
            "statusCode": 500,
            "headers": {"Content-Type": "application/json"},
            "body": '{"error": "Error interno del servidor"}',
        }
        mock_handler.__class__.__name__ = "TestHandler"
        
        error_handler = TransportErrorHandler(mock_handler)
        error = Exception("Processing error")
        
        response = error_handler.handle_processing_error(error)
        
        assert response["statusCode"] == 500
        mock_handler.format_error.assert_called_once()

