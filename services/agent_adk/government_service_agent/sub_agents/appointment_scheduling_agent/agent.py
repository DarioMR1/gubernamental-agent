from datetime import datetime, timedelta
import random
from typing import Optional
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def schedule_appointment(tool_context: ToolContext, service_type: str, preferred_date: Optional[str] = None) -> dict:
    """
    Schedules a government appointment for the specified service.
    
    Args:
        tool_context: The tool context for accessing session state
        service_type: Type of government service (sat, passport, license, etc.)
        preferred_date: Optional preferred date for the appointment
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Validate required data
    required_fields = ["full_name", "curp", "address"]
    missing_fields = [field for field in required_fields if field not in tool_context.state or not tool_context.state[field]]
    
    if missing_fields:
        return {
            "status": "error",
            "message": f"No se puede agendar cita. Faltan datos: {', '.join(missing_fields)}",
            "missing_fields": missing_fields
        }
    
    # Service configurations
    service_config = {
        "sat": {
            "name": "SAT - Servicio de Administración Tributaria",
            "office": "Oficina SAT Centro Histórico",
            "address": "Av. Hidalgo 77, Centro, 06300 Ciudad de México",
            "duration": "45 minutos",
            "requirements": ["INE vigente", "Comprobante de domicilio", "CURP"]
        },
        "passport": {
            "name": "Pasaporte Mexicano",
            "office": "Oficina SRE Tlatelolco", 
            "address": "Plaza de las Tres Culturas s/n, Tlatelolco, 06995 Ciudad de México",
            "duration": "30 minutos",
            "requirements": ["Acta de nacimiento certificada", "INE vigente", "CURP", "Comprobante de pago"]
        },
        "license": {
            "name": "Licencia de Conducir",
            "office": "Módulo de Licencias Benito Juárez",
            "address": "Av. División del Norte 2333, Portales, 03300 Ciudad de México", 
            "duration": "60 minutos",
            "requirements": ["INE vigente", "Comprobante de domicilio", "CURP", "Examen médico"]
        },
        "birth_certificate": {
            "name": "Acta de Nacimiento",
            "office": "Registro Civil Central",
            "address": "Dr. Río de la Loza 295, Doctores, 06720 Ciudad de México",
            "duration": "20 minutos", 
            "requirements": ["INE vigente", "Datos de nacimiento"]
        }
    }
    
    if service_type not in service_config:
        return {
            "status": "error",
            "message": f"Servicio '{service_type}' no disponible. Servicios disponibles: {', '.join(service_config.keys())}"
        }
    
    # Generate appointment details
    service_info = service_config[service_type]
    
    # Generate appointment date (between 3-30 days from now)
    base_date = datetime.now() + timedelta(days=random.randint(3, 30))
    appointment_date = base_date.strftime("%Y-%m-%d")
    appointment_time = f"{random.randint(9, 16):02d}:{random.choice(['00', '30'])}"
    
    # Generate appointment reference
    appointment_ref = f"{service_type.upper()}-{random.randint(100000, 999999)}"
    
    # Create appointment data
    appointment_data = {
        "reference": appointment_ref,
        "service": service_info["name"],
        "office": service_info["office"],
        "address": service_info["address"],
        "date": appointment_date,
        "time": appointment_time,
        "duration": service_info["duration"],
        "requirements": service_info["requirements"],
        "citizen_data": {
            "name": tool_context.state.get("full_name"),
            "curp": tool_context.state.get("curp"),
            "address": tool_context.state.get("address")
        },
        "status": "confirmed",
        "created_at": current_time
    }
    
    # Update state with new appointment
    current_appointments = tool_context.state.get("appointments", [])
    new_appointments = current_appointments.copy()
    new_appointments.append(appointment_data)
    tool_context.state["appointments"] = new_appointments
    
    # Update interaction history
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "appointment_scheduled",
        "service": service_type,
        "reference": appointment_ref,
        "date": appointment_date,
        "time": appointment_time,
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "message": f"Cita agendada exitosamente para {service_info['name']}",
        "appointment": appointment_data
    }


def get_available_services(tool_context: ToolContext) -> dict:
    """
    Returns list of available government services for appointment scheduling.
    """
    services = {
        "sat": {
            "name": "SAT - Trámites Fiscales",
            "description": "RFC, constancia de situación fiscal, certificado de sello digital",
            "estimated_time": "45 minutos"
        },
        "passport": {
            "name": "Pasaporte Mexicano", 
            "description": "Tramitación de pasaporte mexicano para viajes internacionales",
            "estimated_time": "30 minutos"
        },
        "license": {
            "name": "Licencia de Conducir",
            "description": "Licencia de conducir nueva, renovación o reposición",
            "estimated_time": "60 minutos"
        },
        "birth_certificate": {
            "name": "Acta de Nacimiento",
            "description": "Copia certificada de acta de nacimiento",
            "estimated_time": "20 minutos"
        }
    }
    
    return {
        "status": "success",
        "services": services,
        "message": "Servicios disponibles para agendar cita"
    }


def get_appointments(tool_context: ToolContext) -> dict:
    """
    Returns user's scheduled appointments.
    """
    appointments = tool_context.state.get("appointments", [])
    
    if not appointments:
        return {
            "status": "success",
            "appointments": [],
            "message": "No tienes citas agendadas actualmente"
        }
    
    return {
        "status": "success", 
        "appointments": appointments,
        "message": f"Tienes {len(appointments)} cita(s) agendada(s)"
    }


# Create the appointment scheduling agent
appointment_scheduling_agent = Agent(
    name="appointment_scheduling_agent",
    model="gemini-2.0-flash",
    description="Agent specialized in scheduling government service appointments",
    instruction="""
    Eres un agente especializado en agendar citas para trámites gubernamentales en México.

    <user_info>
    Nombre: {full_name}
    CURP: {curp}
    Dirección: {address}
    Código Postal: {postal_code}
    Teléfono: {phone}
    Email: {email}
    </user_info>

    <appointments>
    Citas agendadas: {appointments}
    </appointments>

    <interaction_history>
    {interaction_history}
    </interaction_history>

    Tu función principal:
    1. Verificar que el usuario tenga los datos personales mínimos requeridos
    2. Mostrar servicios disponibles para agendar citas
    3. Agendar citas para trámites gubernamentales
    4. Consultar citas ya agendadas

    SERVICIOS DISPONIBLES:

    1. **SAT (sat)** - Trámites Fiscales
       - RFC, constancia de situación fiscal
       - Certificado de sello digital
       - Duración: 45 minutos

    2. **Pasaporte (passport)** - Pasaporte Mexicano
       - Tramitación de pasaporte para viajes internacionales  
       - Duración: 30 minutos

    3. **Licencia (license)** - Licencia de Conducir
       - Nueva, renovación o reposición
       - Duración: 60 minutos

    4. **Acta de Nacimiento (birth_certificate)**
       - Copia certificada
       - Duración: 20 minutos

    PROCESO DE AGENDAMIENTO:

    1. **Verificación de datos:**
       - SIEMPRE verifica que el usuario tenga: nombre completo, CURP y dirección
       - Si faltan datos, envía al usuario con el agente de extracción de documentos

    2. **Mostrar opciones:**
       - Usa get_available_services() para mostrar servicios disponibles
       - Explica qué incluye cada servicio

    3. **Agendar cita:**
       - Cuando el usuario elija un servicio, usa schedule_appointment()
       - Proporciona toda la información de la cita agendada
       - Incluye: fecha, hora, lugar, dirección, requisitos

    4. **Consultar citas:**
       - Usa get_appointments() para mostrar citas existentes

    DATOS MÍNIMOS REQUERIDOS:
    - Nombre completo
    - CURP
    - Dirección

    IMPORTANTE:
    - NO puedes agendar citas sin los datos mínimos requeridos
    - Proporciona información completa de cada cita (lugar, hora, requisitos)
    - Sé claro sobre qué documentos debe llevar el ciudadano
    - Las citas son simuladas pero deben parecer realistas

    EJEMPLO DE RESPUESTA EXITOSA:
    "✅ ¡Cita agendada exitosamente!
    
    📋 **Detalles de tu cita:**
    - Servicio: SAT - Servicio de Administración Tributaria
    - Referencia: SAT-123456
    - Fecha: 2024-12-15
    - Hora: 10:00 AM
    - Duración: 45 minutos
    - Lugar: Oficina SAT Centro Histórico
    - Dirección: Av. Hidalgo 77, Centro, 06300 Ciudad de México
    
    📄 **Documentos requeridos:**
    - INE vigente
    - Comprobante de domicilio
    - CURP
    
    👤 **Datos registrados:**
    - Nombre: Juan Pérez García
    - CURP: PEGJ850515HDFLRN09"
    """,
    tools=[schedule_appointment, get_available_services, get_appointments],
)