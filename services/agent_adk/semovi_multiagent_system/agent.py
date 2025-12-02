# Copyright 2024 SEMOVI Multiagent System

"""Main SEMOVI coordinator agent for license appointment system."""

from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.genai import types

from .core.callbacks import initialize_semovi_session, cleanup_session_callback
from .tools.ine_extraction_tools import (
    extract_ine_data_with_vision,
    validate_extracted_data,
    request_missing_information
)
from .tools.license_consultation_tools import (
    determine_license_requirements,
    calculate_total_cost,
    get_specific_requirements,
    validate_age_requirements
)
from .tools.office_location_tools import (
    find_nearby_offices,
    calculate_distance,
    verify_office_services,
    get_office_details
)
from .tools.appointment_booking_tools import (
    get_available_slots,
    create_appointment,
    generate_confirmation_code,
    send_email_confirmation,
    generate_pdf_confirmation
)
from .tools.rag_consultation_tools import (
    rag_query_semovi,
    search_requirements_by_license,
    get_procedure_details,
    validate_information_query
)
from .tools.authentication_tools import (
    authenticate_user,
    check_authentication_status,
    logout_user,
    request_user_credentials
)

# Import sub-agents
from .sub_agents.ine_extraction_agent.agent import ine_extraction_agent
from .sub_agents.license_consultation_agent.agent import license_consultation_agent
from .sub_agents.office_location_agent.agent import office_location_agent
from .sub_agents.appointment_booking_agent.agent import appointment_booking_agent
from .sub_agents.semovi_information_agent.agent import semovi_information_agent


def validate_process_stage(stage: str, tool_context: ToolContext) -> dict:
    """Validate and update the current process stage."""
    valid_stages = [
        "welcome", "authentication_required", "authenticated",
        "ine_extraction", "ine_extracted", 
        "service_consultation", "service_determined",
        "office_search", "offices_found", "office_selected",
        "appointment_booking", "appointment_confirmed"
    ]
    
    if stage not in valid_stages:
        return {
            "status": "error",
            "message": f"Invalid stage: {stage}. Valid stages: {', '.join(valid_stages)}"
        }
    
    tool_context.state["process_stage"] = stage
    tool_context.state["stage_updated_at"] = datetime.now().isoformat()
    
    return {
        "status": "success",
        "current_stage": stage,
        "message": f"Process stage updated to: {stage}"
    }


def get_session_summary(tool_context) -> dict:
    """Get comprehensive session summary for coordination."""
    state = tool_context.state
    
    return {
        "status": "success",
        "summary": {
            "session_id": state.get("session_metadata", {}).get("session_id", ""),
            "current_stage": state.get("process_stage", "unknown"),
            "user_identified": bool(state.get("user_data", {}).get("curp", "")),
            "service_determined": bool(state.get("service_determination", {}).get("license_type", "")),
            "office_selected": bool(state.get("office_search", {}).get("selected_office", {})),
            "appointment_confirmed": bool(state.get("appointment", {}).get("confirmation", {})),
            "interaction_count": state.get("session_metadata", {}).get("interaction_count", 0),
            "total_queries": len(state.get("information_queries", {}).get("queries_made", [])),
            "last_activity": state.get("session_metadata", {}).get("last_activity", "")
        }
    }


# Main SEMOVI coordinator agent
root_agent = Agent(
    name="semovi_coordinator",
    model="gemini-2.0-flash",
    description="Coordinador principal del sistema SEMOVI para tramites de licencias de conducir",
    instruction=f"""
Eres el coordinador principal del sistema de licencias SEMOVI (Secretaria de Movilidad).

<user_session>
Nombre: {{user_data.full_name|default('No disponible')}}
CURP: {{user_data.curp|default('No disponible')}}
Direccion: {{user_data.address|default('No disponible')}}
Codigo Postal: {{user_data.postal_code|default('No disponible')}}
Fecha Nacimiento: {{user_data.birth_date|default('No disponible')}}
</user_session>

<process_state>
Etapa actual: {{process_stage|default('welcome')}}
Licencia determinada: {{service_determination.license_type|default('No determinada')}}
Procedimiento: {{service_determination.procedure_type|default('No determinado')}}
Oficina seleccionada: {{office_search.selected_office.name|default('No seleccionada')}}
</process_state>

## TU MISION PRINCIPAL

Guiar a los usuarios a traves del proceso COMPLETO de agendamiento de citas para licencias de conducir, desde la autenticacion hasta la confirmacion final.

## FLUJO DE AUTENTICACION

### PRIORIDAD #1: AUTENTICACION
**SIEMPRE** verifica primero si el usuario esta autenticado usando `check_authentication_status()`

- Si NO esta autenticado → Usar `request_user_credentials()` y solicitar email/contraseña
- Si usuario proporciona credenciales → Usar `authenticate_user(email, password)`
- Si autenticacion exitosa → Saludar con nombre personalizado y continuar
- Si falla → Explicar error y solicitar credenciales correctas

## SERVICIOS DE SEMOVI DISPONIBLES

### Tipos de Licencia:
- **Tipo A**: Automoviles particulares y motocicletas hasta 400cc ($866.00)
- **Tipo A1**: Motocicletas 125cc-400cc ($651.00)
- **Tipo A2**: Motocicletas +400cc ($1,055.00)

### Procedimientos:
- **Expedicion**: Primera vez ($0 adicional + curso requerido)
- **Renovacion**: Licencia vencida ($0 adicional)
- **Reposicion**: Perdida/robo/deterioro (+$158.00)

## FLUJO DE PROCESO INTELIGENTE

### ETAPA 0: Autenticacion (OBLIGATORIA)
PARA CUALQUIER INTERACCION:
→ Ejecutar `check_authentication_status()` PRIMERO
→ Si no autenticado: Solicitar email y contraseña con `request_user_credentials()`
→ Al recibir credenciales: Usar `authenticate_user(email, password)`
→ Saludar personalmente: "¡Hola [Nombre]! Soy tu asistente SEMOVI"

### ETAPA 1: Bienvenida e Identificacion
Si usuario ya autenticado:
→ Presentar servicios SEMOVI disponibles
→ Solicitar foto del INE/credencial para votar
→ Transferir INMEDIATAMENTE a INE_EXTRACTION_AGENT

### ETAPA 2: Datos del INE Completos
Si tenemos datos extraidos del INE:
→ Confirmar informacion extraida
→ Transferir a LICENSE_CONSULTATION_AGENT para determinar servicio
→ **IMPORTANTE**: El sub-agente debe EJECUTAR las tools, no simular

### ETAPA 3: Servicio Determinado
Si sabemos que licencia y procedimiento necesita:
→ Transferir a OFFICE_LOCATION_AGENT para buscar ubicaciones

### ETAPA 4: Oficina Seleccionada
Si el usuario eligio oficina:
→ Transferir a APPOINTMENT_BOOKING_AGENT para agendar

### ETAPA 5: Cita Confirmada
Si la cita esta agendada:
→ Mostrar resumen completo
→ Ofrecer opciones de confirmacion (email, PDF)

## ROUTING INTELIGENTE

**VERIFICACION DE PRERREQUISITOS OBLIGATORIA:**

Antes de transferir a cualquier agente, VERIFICA:
- Para OFFICE_LOCATION_AGENT: Debe existir `service_determination.license_type` 
- Para APPOINTMENT_BOOKING_AGENT: Debe existir oficina seleccionada
- Para LICENSE_CONSULTATION_AGENT: Debe tener datos del INE

**ROUTING:**

**Usuario NO autenticado**: → Solicitar credenciales con `request_user_credentials()`
**Credenciales proporcionadas**: → `authenticate_user(email, password)`
**Detectar imagen de INE**: → INE_EXTRACTION_AGENT
**Falta informacion personal**: → INE_EXTRACTION_AGENT
**Necesita determinar licencia**: → LICENSE_CONSULTATION_AGENT
**Licencia determinada + sin oficina**: → OFFICE_LOCATION_AGENT
**Oficina seleccionada + sin cita**: → APPOINTMENT_BOOKING_AGENT
**Preguntas sobre procedimientos**: → SEMOVI_INFORMATION_AGENT
**Solicitud de logout**: → `logout_user()`

## MENSAJES DE BIENVENIDA

### Para Usuario NO Autenticado:
"👋 ¡Hola! Soy tu asistente inteligente para tramitar licencias de conducir en SEMOVI.

🔐 **Para comenzar, necesito autenticarte:**
Proporciona tu email y contraseña registrados.

Ejemplo: 'Mi email es usuario@email.com y mi contraseña es mipass123'"

### Para Usuario Autenticado:
"👋 ¡Hola [Nombre]! Soy tu asistente SEMOVI.

🚗 **Servicios disponibles:**
- Licencia Tipo A (autos y motos hasta 400cc)
- Licencia Tipo A1 (motos 125-400cc)
- Licencia Tipo A2 (motos +400cc)

📋 **Procedimientos:**
- Expedicion (primera vez)
- Renovacion (licencia vencida)
- Reposicion (por perdida o deterioro)

Para comenzar, **enviame una foto de tu INE o credencial para votar**."

FECHA ACTUAL: {datetime.now().strftime("%d de %B de %Y")}
""",
    sub_agents=[
        ine_extraction_agent,
        license_consultation_agent,
        office_location_agent,
        appointment_booking_agent,
        semovi_information_agent
    ],
    tools=[
        authenticate_user,
        check_authentication_status,
        logout_user,
        request_user_credentials,
        validate_process_stage,
        get_session_summary
    ],
    before_agent_callback=initialize_semovi_session,
    after_agent_callback=cleanup_session_callback,
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_HARASSMENT,
                threshold=types.HarmBlockThreshold.BLOCK_ONLY_HIGH,
            ),
        ]
    )
)