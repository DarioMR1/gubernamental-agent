import asyncio
import os
from dotenv import load_dotenv
from google.adk.runners import Runner
from google.adk.sessions import InMemorySessionService

# Import the main government service agent
from government_service_agent.agent import root_agent
from utils import add_user_query_to_history, call_agent_async

load_dotenv()

# ===== PART 1: Initialize In-Memory Session Service =====
# Using in-memory storage for this example (non-persistent)
session_service = InMemorySessionService()

# ===== PART 2: Define Initial State =====
# This will be used when creating a new session
initial_state = {
    "full_name": "",
    "curp": "",
    "address": "",
    "postal_code": "",
    "phone": "",
    "email": "",
    "personal_data": {},  # Will store complete personal data object
    "appointments": [],   # Will store scheduled government appointments
    "interaction_history": [],  # Will track all user interactions
}


async def main_async():
    # Setup constants
    APP_NAME = "Trámites Gubernamentales"
    USER_ID = "ciudadano_mx"

    # ===== PART 3: Session Creation =====
    # Create a new session with initial state
    new_session = session_service.create_session(
        app_name=APP_NAME,
        user_id=USER_ID,
        state=initial_state,
    )
    SESSION_ID = new_session.id
    print(f"📋 Nueva sesión creada: {SESSION_ID}")

    # ===== PART 4: Agent Runner Setup =====
    # Create a runner with the main government service agent
    runner = Runner(
        agent=root_agent,
        app_name=APP_NAME,
        session_service=session_service,
    )

    # ===== PART 5: Interactive Conversation Loop =====
    print("\n🏛️ ¡Bienvenido al Sistema de Trámites Gubernamentales!")
    print("━" * 60)
    print("📋 Puedo ayudarte a agendar citas para:")
    print("   • SAT (Trámites fiscales)")
    print("   • Pasaporte mexicano") 
    print("   • Licencia de conducir")
    print("   • Acta de nacimiento")
    print()
    print("📸 Para empezar, puedes enviarme una foto de tu INE o recibo de luz")
    print("   y extraeré automáticamente tus datos personales.")
    print()
    print("💬 Escribe 'salir' para terminar la conversación.")
    print("━" * 60)
    print()

    while True:
        # Get user input
        user_input = input("🗣️  Tú: ")

        # Check if user wants to exit
        if user_input.lower() in ["salir", "exit", "quit"]:
            print("\n👋 Finalizando conversación. ¡Que tengas un buen día!")
            break

        # Update interaction history with the user's query
        add_user_query_to_history(
            session_service, APP_NAME, USER_ID, SESSION_ID, user_input
        )

        # Process the user query through the agent
        await call_agent_async(runner, USER_ID, SESSION_ID, user_input)

    # ===== PART 6: State Examination =====
    # Show final session state
    final_session = session_service.get_session(
        app_name=APP_NAME, user_id=USER_ID, session_id=SESSION_ID
    )
    
    print("\n📊 RESUMEN FINAL DE LA SESIÓN")
    print("━" * 50)
    
    # Personal data summary
    personal_data = final_session.state.get("personal_data", {})
    if personal_data and any(personal_data.values()):
        print("👤 Datos personales recolectados:")
        for key, value in personal_data.items():
            if key != "extractions" and value:
                print(f"   • {key}: {value}")
    else:
        print("👤 No se recolectaron datos personales")
    
    # Appointments summary  
    appointments = final_session.state.get("appointments", [])
    if appointments:
        print(f"\n📅 Citas agendadas ({len(appointments)}):")
        for i, appointment in enumerate(appointments, 1):
            service = appointment.get("service", "Servicio desconocido")
            date = appointment.get("date", "Fecha no disponible")
            time = appointment.get("time", "Hora no disponible")
            reference = appointment.get("reference", "Sin referencia")
            print(f"   {i}. {service}")
            print(f"      📅 {date} a las {time}")
            print(f"      🎫 Referencia: {reference}")
    else:
        print("\n📅 No se agendaron citas")
    
    print("━" * 50)


def main():
    """Entry point for the application."""
    # Check if GOOGLE_API_KEY is set
    if not os.getenv('GOOGLE_API_KEY'):
        print("❌ Error: GOOGLE_API_KEY no está configurada")
        print("📝 Por favor, configura tu API key de Google AI en el archivo .env")
        print("   Ejemplo: GOOGLE_API_KEY=tu_clave_aqui")
        return
    
    asyncio.run(main_async())


if __name__ == "__main__":
    main()