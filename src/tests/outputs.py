"""Script de prueba para el agente de inventario de autos."""

import asyncio
from dotenv import load_dotenv

load_dotenv()

from src.factories import get_container


TEST_INPUTS = [
    "Busco un Toyota Corolla 2023",
    "Quiero un coche barato",
    "¿Quién ganó el mundial?",
]


async def main() -> None:
    """Ejecuta las pruebas del agente."""
    container = get_container()
    processor = container.message_processor()
    
    for i, user_text in enumerate(TEST_INPUTS, start=1):
        print(f"\n{'='*50}")
        print(f"INPUT {i}: {user_text}")
        print("=" * 50)

        reply = await processor.process(user_text, session_id=f"test-{i}")

        print(f"\n--- Respuesta ---")
        print(f"Éxito: {reply.success}")
        print(f"Mensaje: {reply.message}")

        if reply.vehicles:
            print(f"\nVehículos ({len(reply.vehicles)}):")
            for vehicle in reply.vehicles[:3]:
                print(f"  - {vehicle.make} {vehicle.model} {vehicle.year}: ${vehicle.price:,.0f}")


if __name__ == "__main__":
    asyncio.run(main())
