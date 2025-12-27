"""Modelos de entrada para Lambda."""

from pydantic import BaseModel, Field, model_validator


class AgentRequest(BaseModel):
    """Payload esperado para el agente."""

    message: str | None = Field(default=None)
    user_text: str | None = Field(default=None)
    session_id: str | None = Field(default=None)

    @model_validator(mode="after")
    def validate_message(self) -> "AgentRequest":
        if not (self.message or self.user_text):
            raise ValueError("message es requerido")
        return self
