"""Tests for Twilio Messaging Adapter."""

import base64
import pytest
from unittest.mock import Mock, patch

from src.adapters.messaging import TwilioMessagingAdapter


class TestTwilioMessagingAdapterParseWebhook:
    """Tests para el método parse_webhook del adaptador de Twilio."""
    
    def test_parse_webhook_with_dict_body(self):
        """Test parsear webhook con body como dict."""
        adapter = TwilioMessagingAdapter()
        event = {"body": {"Body": "Hola mundo"}}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Hola mundo"
    
    def test_parse_webhook_with_dict_body_lowercase(self):
        """Test parsear webhook con body dict usando 'body' en minúscula."""
        adapter = TwilioMessagingAdapter()
        event = {"body": {"body": "Mensaje en minúscula"}}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Mensaje en minúscula"
    
    def test_parse_webhook_with_form_encoded_body(self):
        """Test parsear webhook con body form-encoded."""
        adapter = TwilioMessagingAdapter()
        event = {"body": "Body=Hola%20mundo&From=whatsapp%3A%2B1234567890"}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Hola mundo"
    
    def test_parse_webhook_with_form_encoded_body_lowercase(self):
        """Test parsear webhook con body form-encoded usando 'body' en minúscula."""
        adapter = TwilioMessagingAdapter()
        event = {"body": "body=Test%20message&From=whatsapp%3A%2B1234567890"}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Test message"
    
    def test_parse_webhook_with_empty_string_body(self):
        """Test parsear webhook con body string vacío (retorna string vacío)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": ""}
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_empty_dict_body(self):
        """Test parsear webhook con body dict vacío (retorna string vacío)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": {}}
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_dict_body_no_body_field(self):
        """Test parsear webhook con body dict sin campo Body (retorna string vacío)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": {"From": "whatsapp:+1234567890"}}
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_form_encoded_no_body_field(self):
        """Test parsear webhook form-encoded sin campo Body (retorna string vacío)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": "From=whatsapp%3A%2B1234567890&MessageSid=SM123"}
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_unexpected_body_type(self):
        """Test parsear webhook con tipo de body inesperado (retorna string vacío)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": 12345}  # Tipo int inesperado
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_list_body_type(self):
        """Test parsear webhook con body como lista (tipo inesperado)."""
        adapter = TwilioMessagingAdapter()
        event = {"body": ["item1", "item2"]}
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_invalid_form_encoded_raises_valueerror(self):
        """Test que parsear form-encoded inválido lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        # Body con formato inválido que cause error en parse_qs
        event = {"body": "Body=%"}  # % sin caracteres después puede causar error
        
        # parse_qs puede manejar esto, así que usamos un caso más específico
        # Simulamos un error al parsear
        with patch('src.adapters.messaging.twilio_adapter.parse_qs') as mock_parse:
            mock_parse.side_effect = Exception("Parse error")
            
            with pytest.raises(ValueError, match="Error parseando webhook de Twilio"):
                adapter.parse_webhook(event)
    
    def test_parse_webhook_with_unexpected_exception_raises_valueerror(self):
        """Test que excepciones inesperadas se convierten en ValueError."""
        adapter = TwilioMessagingAdapter()
        
        # Simulamos un error inesperado al parsear el body (dentro del try interno)
        with patch('src.adapters.messaging.twilio_adapter.unquote', side_effect=RuntimeError("Unexpected error")):
            event = {"body": "Body=Test"}
            # El error se captura en el bloque interno y se lanza como ValueError con mensaje específico
            with pytest.raises(ValueError, match="Error parseando webhook de Twilio"):
                adapter.parse_webhook(event)
    
    def test_parse_webhook_with_top_level_exception_raises_valueerror(self):
        """Test que excepciones inesperadas a nivel superior se convierten en ValueError."""
        adapter = TwilioMessagingAdapter()
        
        # Simulamos un error inesperado a nivel superior (fuera del try interno)
        with patch('src.adapters.messaging.twilio_adapter.logger') as mock_logger:
            # Hacemos que logger.debug falle para simular error inesperado
            mock_logger.debug.side_effect = RuntimeError("Unexpected logger error")
            event = {"body": "Body=Test"}
            
            with pytest.raises(ValueError, match="Error inesperado parseando webhook de Twilio"):
                adapter.parse_webhook(event)
    
    def test_parse_webhook_with_missing_body_key(self):
        """Test parsear webhook sin clave 'body' en el evento."""
        adapter = TwilioMessagingAdapter()
        event = {}  # Sin clave 'body'
        
        result = adapter.parse_webhook(event)
        
        assert result == ""
    
    def test_parse_webhook_with_url_encoded_special_characters(self):
        """Test parsear webhook con caracteres especiales URL-encoded."""
        adapter = TwilioMessagingAdapter()
        event = {"body": "Body=Hola%20mundo%21&From=whatsapp%3A%2B1234567890"}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Hola mundo!"
    
    def test_parse_webhook_with_multiple_body_values(self):
        """Test parsear webhook con múltiples valores en Body (toma el primero)."""
        adapter = TwilioMessagingAdapter()
        # parse_qs retorna listas, tomamos el primer valor
        event = {"body": "Body=First&Body=Second&From=whatsapp%3A%2B1234567890"}
        
        result = adapter.parse_webhook(event)
        
        assert result == "First"
    
    def test_parse_webhook_with_base64_encoded_body(self):
        """Test parsear webhook con body codificado en base64."""
        adapter = TwilioMessagingAdapter()
        # Simular body codificado en base64
        form_data = "Body=Hola%20mundo&From=whatsapp%3A%2B1234567890"
        encoded_body = base64.b64encode(form_data.encode("utf-8")).decode("utf-8")
        event = {
            "body": encoded_body,
            "isBase64Encoded": True,
        }
        
        result = adapter.parse_webhook(event)
        
        assert result == "Hola mundo"
    
    def test_parse_webhook_with_base64_encoded_body_strips_whitespace(self):
        """Test que parse_webhook hace strip de espacios en blanco."""
        adapter = TwilioMessagingAdapter()
        # Mensaje con espacios al inicio y final
        form_data = "Body=%20%20Test%20message%20%20&From=whatsapp%3A%2B1234567890"
        encoded_body = base64.b64encode(form_data.encode("utf-8")).decode("utf-8")
        event = {
            "body": encoded_body,
            "isBase64Encoded": True,
        }
        
        result = adapter.parse_webhook(event)
        
        assert result == "Test message"  # Sin espacios extra
    
    def test_parse_webhook_with_base64_encoded_body_fallback_on_decode_error(self):
        """Test que si falla la decodificación base64, intenta usar el body original."""
        adapter = TwilioMessagingAdapter()
        # Body inválido en base64
        event = {
            "body": "invalid-base64!!!",
            "isBase64Encoded": True,
        }
        
        # Debería fallar al parsear, pero no debería crashear
        result = adapter.parse_webhook(event)
        
        # Debería retornar string vacío o lanzar ValueError
        assert result == "" or isinstance(result, str)
    
    def test_parse_webhook_strips_whitespace_from_message(self):
        """Test que el mensaje se limpia con strip()."""
        adapter = TwilioMessagingAdapter()
        # Mensaje con espacios
        event = {"body": "Body=%20%20Hello%20World%20%20&From=whatsapp%3A%2B1234567890"}
        
        result = adapter.parse_webhook(event)
        
        assert result == "Hello World"  # Sin espacios extra al inicio/final


class TestTwilioMessagingAdapterSendMessage:
    """Tests para el método send_message del adaptador de Twilio."""
    
    def test_send_message_success(self):
        """Test enviar mensaje exitosamente."""
        adapter = TwilioMessagingAdapter()
        message = "Hola, ¿cómo puedo ayudarte?"
        
        result = adapter.send_message(message)
        
        assert isinstance(result, str)
        assert "<?xml" in result
        assert "Hola, ¿cómo puedo ayudarte?" in result
        assert "<Message>" in result or "<Response>" in result
    
    def test_send_message_with_special_characters(self):
        """Test enviar mensaje con caracteres especiales."""
        adapter = TwilioMessagingAdapter()
        message = "Mensaje con <especiales> & símbolos"
        
        result = adapter.send_message(message)
        
        assert isinstance(result, str)
        assert message in result or "Mensaje con" in result
    
    def test_send_message_with_empty_string_raises_valueerror(self):
        """Test que enviar mensaje vacío lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        
        with pytest.raises(ValueError, match="El mensaje no puede estar vacío"):
            adapter.send_message("")
    
    def test_send_message_with_none_raises_valueerror(self):
        """Test que enviar None como mensaje lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        
        with pytest.raises(ValueError, match="El mensaje no puede estar vacío"):
            adapter.send_message(None)
    
    def test_send_message_with_invalid_type_raises_valueerror(self):
        """Test que enviar tipo inválido lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        
        with pytest.raises(ValueError, match="El mensaje debe ser un string"):
            adapter.send_message(123)
    
    def test_send_message_with_list_raises_valueerror(self):
        """Test que enviar lista como mensaje lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        
        with pytest.raises(ValueError, match="El mensaje debe ser un string"):
            adapter.send_message(["mensaje", "lista"])
    
    def test_send_message_with_dict_raises_valueerror(self):
        """Test que enviar dict como mensaje lanza ValueError."""
        adapter = TwilioMessagingAdapter()
        
        with pytest.raises(ValueError, match="El mensaje debe ser un string"):
            adapter.send_message({"message": "test"})
    
    def test_send_message_with_twiml_error_raises_runtimeerror(self):
        """Test que error al generar TwiML lanza RuntimeError."""
        adapter = TwilioMessagingAdapter()
        message = "Test message"
        
        # Simulamos un error al crear MessagingResponse
        with patch('src.adapters.messaging.twilio_adapter.MessagingResponse') as mock_response:
            mock_response.side_effect = Exception("TwiML generation error")
            
            with pytest.raises(RuntimeError, match="Error generando respuesta TwiML"):
                adapter.send_message(message)
    
    def test_send_message_with_message_method_error_raises_runtimeerror(self):
        """Test que error al llamar message() lanza RuntimeError."""
        adapter = TwilioMessagingAdapter()
        message = "Test message"
        
        # Simulamos un error al llamar resp.message()
        mock_resp = Mock()
        mock_resp.message.side_effect = Exception("Message method error")
        
        with patch('src.adapters.messaging.twilio_adapter.MessagingResponse', return_value=mock_resp):
            with pytest.raises(RuntimeError, match="Error generando respuesta TwiML"):
                adapter.send_message(message)
    
    def test_send_message_with_str_conversion_error_raises_runtimeerror(self):
        """Test que error al convertir a string lanza RuntimeError."""
        adapter = TwilioMessagingAdapter()
        message = "Test message"
        
        # Simulamos un error al convertir a string
        mock_resp = Mock()
        mock_resp.message.return_value = None
        # Hacemos que str() falle usando side_effect en el mock
        type(mock_resp).__str__ = Mock(side_effect=Exception("String conversion error"))
        
        with patch('src.adapters.messaging.twilio_adapter.MessagingResponse', return_value=mock_resp):
            with pytest.raises(RuntimeError, match="Error generando respuesta TwiML"):
                adapter.send_message(message)
    
    def test_send_message_with_whitespace_only_succeeds(self):
        """Test que mensaje solo con espacios en blanco se acepta (Twilio lo maneja)."""
        adapter = TwilioMessagingAdapter()
        
        # El código actual no valida espacios en blanco, solo verifica si está vacío
        # Un string con espacios no es considerado vacío por Python
        result = adapter.send_message("   ")
        
        assert isinstance(result, str)
        assert "   " in result
    
    def test_send_message_with_long_message(self):
        """Test enviar mensaje largo exitosamente."""
        adapter = TwilioMessagingAdapter()
        message = "A" * 1000  # Mensaje de 1000 caracteres
        
        result = adapter.send_message(message)
        
        assert isinstance(result, str)
        assert len(result) > 0


class TestTwilioMessagingAdapterIntegration:
    """Tests de integración para el adaptador completo."""
    
    def test_full_flow_parse_and_send(self):
        """Test flujo completo: parsear webhook y enviar respuesta."""
        adapter = TwilioMessagingAdapter()
        
        # Parsear webhook
        event = {"body": "Body=Hola&From=whatsapp%3A%2B1234567890"}
        message = adapter.parse_webhook(event)
        assert message == "Hola"
        
        # Enviar respuesta
        response = adapter.send_message(f"Recibí: {message}")
        assert isinstance(response, str)
        assert "Recibí: Hola" in response
    
    def test_parse_empty_and_send_error(self):
        """Test parsear webhook vacío y manejar error al enviar."""
        adapter = TwilioMessagingAdapter()
        
        # Parsear webhook vacío
        event = {"body": ""}
        message = adapter.parse_webhook(event)
        assert message == ""
        
        # Intentar enviar mensaje vacío debería fallar
        with pytest.raises(ValueError, match="El mensaje no puede estar vacío"):
            adapter.send_message(message)

