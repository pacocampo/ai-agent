"""Servicio de conversación para el agente."""

from src.agent.models import UserReply
from src.core.interfaces import ContextStore
from src.core.logging import get_logger
from src.core.models import ConversationContext, SelectedVehicle
from src.domain.catalog import VehicleSearchResult

logger = get_logger(__name__)


class ConversationService:
    """Orquesta la lógica de contexto de conversación.

    Encapsula las operaciones de contexto para mantener
    el entrypoint limpio y la lógica testeable.
    """

    def __init__(self, store: ContextStore) -> None:
        """Inicializa el servicio.

        Args:
            store: Backend de almacenamiento de contexto.
        """
        self._store = store

    async def start_turn(
        self,
        session_id: str,
        user_message: str,
    ) -> ConversationContext:
        """Inicia un turno de conversación.

        Obtiene o crea el contexto y registra el mensaje del usuario.

        Args:
            session_id: Identificador de la sesión.
            user_message: Mensaje del usuario.

        Returns:
            Contexto de la conversación.
        """
        ctx = await self._store.get_or_create(session_id)
        ctx.add_user_message(user_message)

        logger.debug(
            "Turno iniciado",
            session_id=session_id,
            message_count=len(ctx.messages),
        )

        return ctx

    def update_context(
        self,
        ctx: ConversationContext,
        reply: UserReply,
        action: str,
    ) -> None:
        """Actualiza el contexto con los resultados del turno.

        Esta operación es síncrona y modifica el objeto en memoria.
        Debe llamarse ANTES del fire-and-forget de persist_context.

        Args:
            ctx: Contexto de la conversación.
            reply: Respuesta generada para el usuario.
            action: Acción ejecutada.
        """
        if reply.vehicles:
            ctx.set_search_results(self._to_selected_vehicles(reply.vehicles))

        ctx.last_action = action
        ctx.add_assistant_message(reply.message)

        logger.debug(
            "Contexto actualizado",
            session_id=ctx.session_id,
            action=action,
            vehicles_saved=len(ctx.last_search_results),
        )

    async def persist_context(self, ctx: ConversationContext) -> None:
        """Persiste el contexto al store.

        Esta operación es async y puede ejecutarse como fire-and-forget.

        Args:
            ctx: Contexto a persistir.
        """
        await self._store.save(ctx)
        logger.debug("Contexto persistido", session_id=ctx.session_id)

    async def end_turn(
        self,
        ctx: ConversationContext,
        reply: UserReply,
        action: str,
    ) -> None:
        """Finaliza un turno de conversación (legacy, usa update_context + persist_context).

        Guarda los resultados de búsqueda, la respuesta y persiste el contexto.

        Args:
            ctx: Contexto de la conversación.
            reply: Respuesta generada para el usuario.
            action: Acción ejecutada.
        """
        self.update_context(ctx, reply, action)
        await self.persist_context(ctx)

    async def get_context(self, session_id: str) -> ConversationContext | None:
        """Obtiene el contexto de una sesión.

        Args:
            session_id: Identificador de la sesión.

        Returns:
            Contexto si existe, None si no.
        """
        return await self._store.get(session_id)

    async def select_vehicle(
        self,
        session_id: str,
        stock_id: int,
    ) -> SelectedVehicle | None:
        """Selecciona un vehículo de los últimos resultados.

        Args:
            session_id: Identificador de la sesión.
            stock_id: ID del vehículo a seleccionar.

        Returns:
            Vehículo seleccionado o None si no se encontró.
        """
        ctx = await self._store.get(session_id)
        if ctx is None:
            return None

        if ctx.select_vehicle_by_stock_id(stock_id):
            await self._store.save(ctx)
            return ctx.selected_vehicle

        return None

    async def get_selected_vehicle(
        self,
        session_id: str,
    ) -> SelectedVehicle | None:
        """Obtiene el vehículo seleccionado de una sesión.

        Args:
            session_id: Identificador de la sesión.

        Returns:
            Vehículo seleccionado o None si no hay.
        """
        ctx = await self._store.get(session_id)
        if ctx is None:
            return None
        return ctx.selected_vehicle

    async def clear_session(self, session_id: str) -> bool:
        """Elimina una sesión.

        Args:
            session_id: Identificador de la sesión.

        Returns:
            True si se eliminó, False si no existía.
        """
        return await self._store.delete(session_id)

    def _to_selected_vehicles(
        self,
        vehicles: list[VehicleSearchResult],
    ) -> list[SelectedVehicle]:
        """Convierte VehicleSearchResult a SelectedVehicle.

        Args:
            vehicles: Lista de resultados de búsqueda.

        Returns:
            Lista de vehículos para almacenar en contexto.
        """
        return [
            SelectedVehicle(
                stock_id=v.stock_id,
                make=v.make,
                model=v.model,
                year=v.year,
                price=v.price,
                km=v.km,
            )
            for v in vehicles
        ]
