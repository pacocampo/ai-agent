"""Adaptador de OpenAI para el sistema de LLM."""

import json
from typing import TYPE_CHECKING

from openai import OpenAI

from src.core.config import API_BASE_URL, API_KEY
from src.core.interfaces import LLMAdapter
from src.core.models import AgentDecision
from src.llm.prompts import (
    GET_FINANCING_OPTIONS_PROMPT,
    GET_KAVAK_INFO_PROMPT,
    HUMANIZE_RESPONSE_PROMPT,
    INVENTORY_PROMPT,
)

if TYPE_CHECKING:
    from src.core.models import ConversationContext


class OpenAIAdapter(LLMAdapter):
    """Adaptador para el proveedor OpenAI.
    
    Implementa la interfaz LLMAdapter usando la API de OpenAI.
    Encapsula toda la lógica de comunicación con OpenAI y construcción de prompts.
    
    Attributes:
        client: Cliente de OpenAI configurado.
        decision_model: Modelo para decisiones estructuradas (gpt-4o).
        response_model: Modelo para generación de respuestas (gpt-4o-mini).
    """
    
    def __init__(
        self,
        api_key: str | None = None,
        base_url: str | None = None,
        decision_model: str = "gpt-4o-2024-08-06",
        response_model: str = "gpt-4o-mini",
    ) -> None:
        """Inicializa el adaptador de OpenAI.
        
        Args:
            api_key: API key de OpenAI. Si es None, usa API_KEY de config.
            base_url: URL base de la API. Si es None, usa API_BASE_URL de config.
            decision_model: Modelo para decisiones estructuradas.
            response_model: Modelo para generación de respuestas.
            
        Raises:
            ValueError: Si no se proporcionan credenciales válidas.
        """
        self._api_key = api_key or API_KEY
        self._base_url = base_url or API_BASE_URL
        self.decision_model = decision_model
        self.response_model = response_model
        
        if not self._api_key or not self._base_url:
            raise ValueError(
                "Llaves de API de OpenAI no están configuradas. "
                "Proporciona api_key y base_url o configura las variables de entorno."
            )
        
        self.client = OpenAI(
            api_key=self._api_key,
            base_url=self._base_url,
        )
    
    def get_agent_decision(
        self,
        user_text: str,
        context: "ConversationContext | None" = None,
    ) -> AgentDecision:
        """Obtiene la decisión estructurada del agente para un texto de usuario.
        
        Envía el texto del usuario al modelo de OpenAI y obtiene una decisión
        estructurada usando el schema AgentDecision. Si se proporciona contexto,
        lo incluye para mantener continuidad en la conversación.
        
        Args:
            user_text: Texto del usuario a procesar.
            context: Contexto de conversación opcional para continuidad.
            
        Returns:
            AgentDecision con la acción y parámetros determinados por el modelo.
            
        Raises:
            ValueError: Si no se puede parsear la respuesta del modelo.
            OpenAIError: Si hay un error de comunicación con la API.
            
        Examples:
            >>> adapter = OpenAIAdapter()
            >>> decision = adapter.get_agent_decision("Busco un Toyota Corolla 2023")
            >>> print(decision.action)
            AgentAction.SEARCH_CARS
        """
        messages = self._build_messages_with_context(user_text, context)
        
        response = self.client.beta.chat.completions.parse(
            model=self.decision_model,
            messages=messages,
            response_format=AgentDecision,
        )
        
        decision = response.choices[0].message.parsed
        
        if decision is None:
            raise ValueError("No se pudo parsear la respuesta del modelo.")
        
        return decision
    
    def humanize_response(
        self,
        user_text: str,
        action: str,
        base_message: str,
        vehicles: list[dict] | None = None,
    ) -> str:
        """Humaniza una respuesta estructurada usando el LLM.
        
        Toma la información estructurada del resultado y genera una respuesta
        natural y conversacional apropiada para el usuario.
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            action: Tipo de acción ejecutada (search_cars, clarify, etc.).
            base_message: Mensaje base generado por el presenter.
            vehicles: Lista de vehículos encontrados (si aplica).
            
        Returns:
            Respuesta humanizada como string.
            
        Examples:
            >>> adapter = OpenAIAdapter()
            >>> response = adapter.humanize_response(
            ...     user_text="Busco un Toyota Corolla",
            ...     action="search_cars",
            ...     base_message="Encontré 2 vehículos",
            ...     vehicles=[{"make": "Toyota", "model": "Corolla", ...}]
            ... )
        """
        context = {
            "user_query": user_text,
            "action": action,
            "base_message": base_message,
        }
        
        if vehicles:
            context["vehicles"] = vehicles[:5]
        
        response = self.client.chat.completions.create(
            model=self.response_model,
            messages=[
                {"role": "system", "content": HUMANIZE_RESPONSE_PROMPT},
                {
                    "role": "user",
                    "content": f"Genera una respuesta humanizada para:\n{json.dumps(context, ensure_ascii=False, indent=2)}",
                },
            ],
            temperature=0.7,
            max_tokens=500,
        )
        
        return response.choices[0].message.content or base_message
    
    def generate_financing_response(
        self,
        user_text: str,
        vehicle_price: float,
    ) -> str:
        """Genera opciones de financiamiento usando el LLM.
        
        El LLM calcula las opciones de financiamiento basándose en el precio
        del vehículo y los parámetros configurados (tasa, plazos, enganche).
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            vehicle_price: Precio del vehículo en MXN.
            
        Returns:
            Respuesta con las opciones de financiamiento calculadas.
            
        Examples:
            >>> adapter = OpenAIAdapter()
            >>> response = adapter.generate_financing_response(
            ...     user_text="¿Cuáles son las opciones de financiamiento?",
            ...     vehicle_price=350000.0,
            ... )
        """
        context = {
            "user_query": user_text,
            "vehicle_price": vehicle_price,
        }
        
        response = self.client.chat.completions.create(
            model=self.response_model,
            messages=[
                {"role": "system", "content": GET_FINANCING_OPTIONS_PROMPT},
                {
                    "role": "user",
                    "content": f"Calcula las opciones de financiamiento para:\n{json.dumps(context, ensure_ascii=False, indent=2)}",
                },
            ],
            temperature=0.3,  # Más determinístico para cálculos
            max_tokens=800,
        )
        
        return response.choices[0].message.content or "No se pudieron calcular las opciones de financiamiento."
    
    def generate_kavak_info_response(
        self,
        user_text: str,
        kavak_info: str,
        query: str,
    ) -> str:
        """Genera respuesta sobre información de Kavak usando el LLM.
        
        El LLM procesa toda la información disponible y responde
        específicamente a la consulta del usuario.
        
        Args:
            user_text: Mensaje original del usuario para contexto.
            kavak_info: Información completa de Kavak.
            query: Consulta específica que se está respondiendo.
            
        Returns:
            Respuesta con la información solicitada.
            
        Examples:
            >>> adapter = OpenAIAdapter()
            >>> response = adapter.generate_kavak_info_response(
            ...     user_text="¿Dónde está Kavak en CDMX?",
            ...     kavak_info="...",
            ...     query="ubicaciones en CDMX",
            ... )
        """
        response = self.client.chat.completions.create(
            model=self.response_model,
            messages=[
                {"role": "system", "content": GET_KAVAK_INFO_PROMPT},
                {
                    "role": "user",
                    "content": f"Responde basándote en esta información:\n\nPregunta del usuario: {user_text}\n\nInformación de Kavak:\n{kavak_info[:6000]}",  # Limitar tokens
                },
            ],
            temperature=0.5,
            max_tokens=800,
        )
        
        return response.choices[0].message.content or "No pude encontrar información específica sobre tu consulta."
    
    # Métodos auxiliares privados
    
    def _build_messages_with_context(
        self,
        user_text: str,
        context: "ConversationContext | None",
    ) -> list[dict]:
        """Construye los mensajes para el LLM incluyendo contexto.
        
        Args:
            user_text: Texto del usuario actual.
            context: Contexto de conversación.
            
        Returns:
            Lista de mensajes formateados para la API de OpenAI.
        """
        messages: list[dict] = [{"role": "system", "content": INVENTORY_PROMPT}]
        
        if context:
            context_info = self._format_context_info(context)
            if context_info:
                messages.append({
                    "role": "system",
                    "content": f"## Información de Contexto Actual\n\n{context_info}",
                })
            
            # Agregar historial de mensajes (excluyendo el mensaje actual)
            for msg in context.messages[:-1]:  # Excluir el último (es el actual)
                messages.append(msg.to_dict())
        
        messages.append({"role": "user", "content": user_text})
        
        return messages
    
    def _format_context_info(self, context: "ConversationContext") -> str:
        """Formatea la información del contexto para el prompt.
        
        Args:
            context: Contexto de conversación.
            
        Returns:
            String con la información formateada.
        """
        parts = []
        
        if context.last_action:
            parts.append(f"Última acción: {context.last_action}")
        
        if context.last_search_results:
            vehicles_info = []
            for i, v in enumerate(context.last_search_results[:5], 1):
                vehicles_info.append(
                    f"  {i}. {v.make} {v.model} {v.year} - ${v.price:,.0f} MXN, "
                    f"{v.km:,} km (stock_id: {v.stock_id})"
                )
            parts.append(f"Últimos vehículos encontrados ({len(context.last_search_results)} total):")
            parts.extend(vehicles_info)
        
        if context.selected_vehicle:
            v = context.selected_vehicle
            parts.append(
                f"Vehículo seleccionado: {v.make} {v.model} {v.year} - ${v.price:,.0f} MXN "
                f"(stock_id: {v.stock_id})"
            )
        
        return "\n".join(parts)

