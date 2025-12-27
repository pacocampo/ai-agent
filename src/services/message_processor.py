"""Message processing service - Application layer."""

import asyncio
import re

from src.agent.models import UserReply
from src.agent.presenter import render_reply
from src.agent.router import route_decision
from src.agent.services import ConversationService
from src.core.interfaces import LLMAdapter
from src.core.logging import get_logger
from src.core.models import AgentAction, AgentDecision, MissingField

logger = get_logger(__name__)


class MessageProcessorService:
    """Service for processing user messages.
    
    Orchestrates the complete message processing flow:
    1. Start conversation turn (get context, register message)
    2. Get agent decision from LLM
    3. Route decision to appropriate handler
    4. Render and humanize response
    5. Update and persist context
    """
    
    def __init__(
        self,
        conversation_service: ConversationService,
        llm_adapter: LLMAdapter,
    ):
        """Initialize message processor.
        
        Args:
            conversation_service: Service for managing conversation context.
            llm_adapter: LLM adapter for agent decisions.
        """
        self.conversation_service = conversation_service
        self.llm_adapter = llm_adapter
    
    async def process(
        self,
        user_text: str,
        session_id: str = "default",
        humanize: bool = True,
    ) -> UserReply:
        """Process user message and return reply.
        
        Args:
            user_text: User's message text.
            session_id: Session identifier.
            humanize: Whether to humanize response.
            
        Returns:
            UserReply with processed response.
        """
        logger.info(
            "Procesando mensaje de usuario",
            session_id=session_id,
            user_text=user_text[:100],
        )
        
        try:
            ctx = await self.conversation_service.start_turn(session_id, user_text)
            
            # Get agent decision from LLM
            decision = self.llm_adapter.get_agent_decision(user_text, context=ctx)
            decision = self._apply_clarify_guards(user_text, decision, ctx)
            
            logger.debug(
                "Decisión del agente",
                session_id=session_id,
                action=decision.action.value,
            )
            
            # Route decision to handler
            result = route_decision(decision)
            reply = render_reply(result)
            
            # Humanize response if needed
            if humanize and reply.success:
                reply = self._enhance_reply(user_text, decision.action, reply)
            
            # Update context in memory BEFORE fire-and-forget
            self.conversation_service.update_context(ctx, reply, decision.action.value)
            
            # Fire-and-forget: Persist context asynchronously
            asyncio.create_task(
                self._persist_context_with_logging(ctx, session_id)
            )
            
            logger.info(
                "Respuesta generada",
                session_id=session_id,
                action=decision.action.value,
                success=reply.success,
                vehicles_count=len(reply.vehicles),
            )
            
            return reply
            
        except ValueError as e:
            logger.error("Error de validación", session_id=session_id, error=str(e))
            return UserReply(
                message="Hubo un problema procesando tu solicitud. Por favor, intenta de nuevo.",
                success=False,
            )
        except Exception as e:
            logger.exception("Error inesperado", session_id=session_id, error=str(e))
            return UserReply(
                message="Lo siento, ocurrió un error inesperado. Por favor, intenta más tarde.",
                success=False,
            )
    
    async def _persist_context_with_logging(
        self,
        ctx,
        session_id: str,
    ) -> None:
        """Persist context with error handling for fire-and-forget."""
        try:
            await self.conversation_service.persist_context(ctx)
        except Exception as e:
            logger.error(
                "Error persistiendo contexto (fire-and-forget)",
                session_id=session_id,
                error=str(e),
            )
    
    def _enhance_reply(
        self,
        user_text: str,
        action: AgentAction,
        reply: UserReply,
    ) -> UserReply:
        """Enhance reply with specialized handlers or default humanization."""
        enhancer = _RESPONSE_ENHANCERS.get(action)
        
        if enhancer:
            return enhancer(self.llm_adapter, user_text, reply)
        
        # Default: humanize with general prompt
        return self._humanize_reply(user_text, action.value, reply)
    
    def _humanize_reply(
        self,
        user_text: str,
        action: str,
        reply: UserReply,
    ) -> UserReply:
        """Humanize reply using LLM."""
        vehicles_data = [
            {
                "make": v.make,
                "model": v.model,
                "year": v.year,
                "price": v.price,
                "km": v.km,
                "version": v.version,
            }
            for v in reply.vehicles
        ]
        
        humanized_message = self.llm_adapter.humanize_response(
            user_text=user_text,
            action=action,
            base_message=reply.message,
            vehicles=vehicles_data if vehicles_data else None,
        )
        
        return UserReply(
            message=humanized_message,
            vehicles=reply.vehicles,
            success=reply.success,
        )
    
    def _apply_clarify_guards(
        self,
        user_text: str,
        decision: AgentDecision,
        ctx,
    ) -> AgentDecision:
        """Apply clarification rules when context is missing."""
        text = user_text.lower()
        has_context = bool(ctx.last_search_results or ctx.selected_vehicle)
        
        if (
            decision.action == AgentAction.GET_FINANCING_OPTIONS
            and not decision.stock_id
            and not has_context
        ):
            return AgentDecision(
                action=AgentAction.CLARIFY,
                message=(
                    "¿Qué vehículo te interesa financiar? "
                    "Puedes decirme la marca y el modelo."
                ),
                missing_information=[],
            )
        
        if (
            decision.action == AgentAction.GET_FINANCING_OPTIONS
            and not decision.stock_id
            and ctx.last_search_results
            and not ctx.selected_vehicle
        ):
            return AgentDecision(
                action=AgentAction.CLARIFY,
                message=(
                    "¿Cuál de los vehículos encontrados quieres financiar? "
                    "Indícame el número en la lista o dime marca y modelo."
                ),
                missing_information=[],
            )
        
        needs_reference = any(
            phrase in text
            for phrase in (
                "mas barato",
                "más barato",
                "el primero",
                "la primera",
                "el rojo",
                "la roja",
                "ese",
                "ese auto",
                "ese coche",
                "me interesa el",
                "me interesa la",
            )
        )
        
        if needs_reference and not has_context:
            return AgentDecision(
                action=AgentAction.CLARIFY,
                message=(
                    "¿Te refieres a algún vehículo de una búsqueda previa? "
                    "Si no, dime qué marca, modelo o presupuesto tienes en mente."
                ),
                missing_information=[MissingField.MAKE, MissingField.MODEL],
            )
        
        return decision


def _generate_kavak_info_reply(
    llm_adapter: LLMAdapter,
    user_text: str,
    reply: UserReply,
) -> UserReply:
    """Generate Kavak info reply."""
    query_match = re.search(r"Información sobre Kavak: (.+)", reply.message)
    query = query_match.group(1) if query_match else "información general"
    
    from src.tools.catalog.kavak_info import get_kavak_info
    
    kavak_info = get_kavak_info()
    
    info_message = llm_adapter.generate_kavak_info_response(
        user_text=user_text,
        kavak_info=kavak_info,
        query=query,
    )
    
    return UserReply(
        message=info_message,
        vehicles=reply.vehicles,
        success=reply.success,
    )


def _generate_financing_reply(
    llm_adapter: LLMAdapter,
    user_text: str,
    reply: UserReply,
) -> UserReply:
    """Generate financing reply."""
    price_match = re.search(r"\$([0-9,]+)", reply.message)
    if price_match:
        price = float(price_match.group(1).replace(",", ""))
    else:
        return reply
    
    financing_message = llm_adapter.generate_financing_response(
        user_text=user_text,
        vehicle_price=price,
    )
    
    return UserReply(
        message=financing_message,
        vehicles=reply.vehicles,
        success=reply.success,
    )


# Response enhancers registry
# Note: Functions receive llm_adapter as first parameter
_RESPONSE_ENHANCERS: dict[AgentAction, callable] = {
    AgentAction.GET_FINANCING_OPTIONS: _generate_financing_reply,
    AgentAction.GET_KAVAK_INFO: _generate_kavak_info_reply,
}
