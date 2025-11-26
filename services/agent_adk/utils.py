from datetime import datetime
from google.genai import types


# ANSI color codes for terminal output
class Colors:
    RESET = "\033[0m"
    BOLD = "\033[1m"
    UNDERLINE = "\033[4m"
    
    # Foreground colors
    BLACK = "\033[30m"
    RED = "\033[31m"
    GREEN = "\033[32m"
    YELLOW = "\033[33m"
    BLUE = "\033[34m"
    MAGENTA = "\033[35m"
    CYAN = "\033[36m"
    WHITE = "\033[37m"
    
    # Background colors
    BG_BLACK = "\033[40m"
    BG_RED = "\033[41m"
    BG_GREEN = "\033[42m"
    BG_YELLOW = "\033[43m"
    BG_BLUE = "\033[44m"
    BG_MAGENTA = "\033[45m"
    BG_CYAN = "\033[46m"
    BG_WHITE = "\033[47m"


def update_interaction_history(session_service, app_name, user_id, session_id, entry):
    """Add an entry to the interaction history in state.

    Args:
        session_service: The session service instance
        app_name: The application name
        user_id: The user ID
        session_id: The session ID
        entry: A dictionary containing the interaction data
    """
    try:
        # Get current session
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Get current interaction history
        interaction_history = session.state.get("interaction_history", [])

        # Add timestamp if not already present
        if "timestamp" not in entry:
            entry["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # Add the entry to interaction history
        interaction_history.append(entry)

        # Create updated state
        updated_state = session.state.copy()
        updated_state["interaction_history"] = interaction_history

        # Create a new session with updated state
        session_service.create_session(
            app_name=app_name,
            user_id=user_id,
            session_id=session_id,
            state=updated_state,
        )
    except Exception as e:
        print(f"Error updating interaction history: {e}")


def add_user_query_to_history(session_service, app_name, user_id, session_id, query):
    """Add a user query to the interaction history."""
    update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "user_query",
            "query": query,
        },
    )


def add_agent_response_to_history(
    session_service, app_name, user_id, session_id, agent_name, response
):
    """Add an agent response to the interaction history."""
    update_interaction_history(
        session_service,
        app_name,
        user_id,
        session_id,
        {
            "action": "agent_response",
            "agent": agent_name,
            "response": response,
        },
    )


def display_state(
    session_service, app_name, user_id, session_id, label="Estado Actual"
):
    """Display the current session state in a formatted way."""
    try:
        session = session_service.get_session(
            app_name=app_name, user_id=user_id, session_id=session_id
        )

        # Format the output with clear sections
        print(f"\n{'-' * 10} {label} {'-' * 10}")

        # Handle personal data
        personal_data = session.state.get("personal_data", {})
        if personal_data:
            print("👤 Datos Personales:")
            for field, value in personal_data.items():
                if field != "extractions" and value:
                    print(f"  - {field}: {value}")
            
            # Show extractions if available
            extractions = personal_data.get("extractions", [])
            if extractions:
                print("📄 Documentos Procesados:")
                for ext in extractions:
                    doc_type = ext.get("document_type", "unknown")
                    timestamp = ext.get("timestamp", "unknown")
                    fields = ", ".join(ext.get("fields_extracted", []))
                    print(f"  - {doc_type} ({timestamp}): {fields}")
        else:
            print("👤 Datos Personales: Ninguno")

        # Handle appointments
        appointments = session.state.get("appointments", [])
        if appointments:
            print("📅 Citas Agendadas:")
            for idx, appointment in enumerate(appointments, 1):
                service = appointment.get("service", "Unknown service")
                date = appointment.get("date", "Unknown date")
                time = appointment.get("time", "Unknown time")
                reference = appointment.get("reference", "No reference")
                print(f"  {idx}. {service}")
                print(f"     - Fecha: {date} {time}")
                print(f"     - Referencia: {reference}")
                print(f"     - Lugar: {appointment.get('office', 'Unknown')}")
        else:
            print("📅 Citas Agendadas: Ninguna")

        # Handle interaction history
        interaction_history = session.state.get("interaction_history", [])
        if interaction_history:
            print("📝 Historial de Interacciones:")
            for idx, interaction in enumerate(interaction_history[-5:], 1):  # Show last 5
                if isinstance(interaction, dict):
                    action = interaction.get("action", "interaction")
                    timestamp = interaction.get("timestamp", "unknown time")

                    if action == "user_query":
                        query = interaction.get("query", "")
                        if len(query) > 50:
                            query = query[:47] + "..."
                        print(f'  {idx}. Usuario ({timestamp}): "{query}"')
                    elif action == "agent_response":
                        agent = interaction.get("agent", "unknown")
                        response = interaction.get("response", "")
                        if len(response) > 50:
                            response = response[:47] + "..."
                        print(f'  {idx}. {agent} ({timestamp}): "{response}"')
                    elif action == "document_extraction":
                        doc_type = interaction.get("document_type", "unknown")
                        fields = ", ".join(interaction.get("fields_extracted", []))
                        print(f"  {idx}. Extracción ({timestamp}): {doc_type} - {fields}")
                    elif action == "appointment_scheduled":
                        service = interaction.get("service", "unknown")
                        date = interaction.get("date", "unknown")
                        print(f"  {idx}. Cita agendada ({timestamp}): {service} - {date}")
                    else:
                        print(f"  {idx}. {action} ({timestamp})")
        else:
            print("📝 Historial de Interacciones: Ninguno")

        print("-" * (22 + len(label)))
    except Exception as e:
        print(f"Error displaying state: {e}")


async def process_agent_response(event):
    """Process and display agent response events."""
    print(f"Event ID: {event.id}, Author: {event.author}")

    # Check for specific parts first
    has_specific_part = False
    if event.content and event.content.parts:
        for part in event.content.parts:
            if hasattr(part, "text") and part.text and not part.text.isspace():
                print(f"  Text: '{part.text.strip()}'")

    # Check for final response after specific parts
    final_response = None
    if not has_specific_part and event.is_final_response():
        if (
            event.content
            and event.content.parts
            and hasattr(event.content.parts[0], "text")
            and event.content.parts[0].text
        ):
            final_response = event.content.parts[0].text.strip()
            # Use colors and formatting to make the final response stand out
            print(
                f"\n{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╔══ RESPUESTA DEL AGENTE ═══════════════════════════════════{Colors.RESET}"
            )
            print(f"{Colors.CYAN}{Colors.BOLD}{final_response}{Colors.RESET}")
            print(
                f"{Colors.BG_BLUE}{Colors.WHITE}{Colors.BOLD}╚══════════════════════════════════════════════════════════{Colors.RESET}\n"
            )
        else:
            print(
                f"\n{Colors.BG_RED}{Colors.WHITE}{Colors.BOLD}==> Respuesta Final: [Sin contenido de texto]{Colors.RESET}\n"
            )

    return final_response


async def call_agent_async(runner, user_id, session_id, query):
    """Call the agent asynchronously with the user's query."""
    content = types.Content(role="user", parts=[types.Part(text=query)])
    print(
        f"\n{Colors.BG_GREEN}{Colors.BLACK}{Colors.BOLD}--- Procesando Consulta: {query} ---{Colors.RESET}"
    )
    final_response_text = None
    agent_name = None

    # Display state before processing the message
    display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "Estado ANTES del procesamiento",
    )

    try:
        async for event in runner.run_async(
            user_id=user_id, session_id=session_id, new_message=content
        ):
            # Capture the agent name from the event if available
            if event.author:
                agent_name = event.author

            response = await process_agent_response(event)
            if response:
                final_response_text = response
    except Exception as e:
        print(f"{Colors.BG_RED}{Colors.WHITE}ERROR durante la ejecución del agente: {e}{Colors.RESET}")

    # Add the agent response to interaction history if we got a final response
    if final_response_text and agent_name:
        add_agent_response_to_history(
            runner.session_service,
            runner.app_name,
            user_id,
            session_id,
            agent_name,
            final_response_text,
        )

    # Display state after processing the message
    display_state(
        runner.session_service,
        runner.app_name,
        user_id,
        session_id,
        "Estado DESPUÉS del procesamiento",
    )

    print(f"{Colors.YELLOW}{'-' * 50}{Colors.RESET}")
    return final_response_text