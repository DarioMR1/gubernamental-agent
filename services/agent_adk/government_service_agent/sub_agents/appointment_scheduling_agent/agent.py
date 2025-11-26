from datetime import datetime, timedelta
import random
import os
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


def send_appointment_email(tool_context: ToolContext, email: str, appointment_reference: str) -> dict:
    """
    Sends appointment confirmation email using Resend.
    
    Args:
        tool_context: The tool context for accessing session state
        email: Email address to send the confirmation to
        appointment_reference: Reference number of the appointment to send
    """
    try:
        import resend
    except ImportError:
        return {
            "status": "error",
            "message": "Resend library not installed. Please install with: pip install resend"
        }
    
    # Get appointment data
    appointments = tool_context.state.get("appointments", [])
    appointment = None
    
    for apt in appointments:
        if apt.get("reference") == appointment_reference:
            appointment = apt
            break
    
    if not appointment:
        return {
            "status": "error",
            "message": f"No se encontró la cita con referencia: {appointment_reference}"
        }
    
    # Get user data
    user_name = tool_context.state.get("full_name", "Usuario")
    
    # Configure Resend API key from environment
    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        return {
            "status": "error", 
            "message": "RESEND_API_KEY no está configurada en las variables de entorno"
        }
    
    resend.api_key = resend_api_key
    
    # Create email content
    service_name = appointment["service"]
    date = appointment["date"]
    time = appointment["time"]
    office = appointment["office"]
    address = appointment["address"]
    requirements = appointment.get("requirements", [])
    
    html_content = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <title>Confirmación de Cita - {service_name}</title>
        <style>
            body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
            .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
            .header {{ background-color: #2563eb; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
            .content {{ background-color: #f8fafc; padding: 30px; border-radius: 0 0 8px 8px; }}
            .info-box {{ background-color: white; padding: 20px; border-radius: 6px; margin: 15px 0; border-left: 4px solid #2563eb; }}
            .requirements {{ background-color: #fef3c7; padding: 15px; border-radius: 6px; border-left: 4px solid #f59e0b; }}
            .footer {{ text-align: center; margin-top: 30px; color: #6b7280; font-size: 14px; }}
            h1 {{ margin: 0; }}
            h2 {{ color: #2563eb; margin-top: 0; }}
            ul {{ margin: 0; padding-left: 20px; }}
            .reference {{ font-family: monospace; background: #e5e7eb; padding: 4px 8px; border-radius: 4px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏛️ Confirmación de Cita Gubernamental</h1>
                <p>Tu cita ha sido agendada exitosamente</p>
            </div>
            
            <div class="content">
                <h2>Hola {user_name},</h2>
                <p>Te confirmamos que tu cita para <strong>{service_name}</strong> ha sido agendada con éxito.</p>
                
                <div class="info-box">
                    <h3>📋 Detalles de tu Cita</h3>
                    <p><strong>Servicio:</strong> {service_name}</p>
                    <p><strong>Referencia:</strong> <span class="reference">{appointment_reference}</span></p>
                    <p><strong>📅 Fecha:</strong> {date}</p>
                    <p><strong>🕐 Hora:</strong> {time}</p>
                    <p><strong>📍 Lugar:</strong> {office}</p>
                    <p><strong>📍 Dirección:</strong> {address}</p>
                </div>
                
                <div class="requirements">
                    <h3>📄 Documentos Requeridos</h3>
                    <p>Por favor lleva contigo los siguientes documentos:</p>
                    <ul>
    """
    
    for req in requirements:
        html_content += f"<li>{req}</li>"
    
    html_content += f"""
                    </ul>
                </div>
                
                <div class="info-box">
                    <h3>ℹ️ Información Importante</h3>
                    <ul>
                        <li>Llega <strong>15 minutos antes</strong> de tu cita</li>
                        <li>Lleva todos los documentos requeridos</li>
                        <li>Tu referencia es: <span class="reference">{appointment_reference}</span></li>
                        <li>Si necesitas cancelar o reprogramar, comunícate con anticipación</li>
                    </ul>
                </div>
                
                <div class="footer">
                    <p>Este correo fue generado automáticamente por el Sistema de Trámites Gubernamentales</p>
                    <p>Esta es una notificación automática. Para consultas, contacta directamente a la oficina correspondiente</p>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    try:
        # Send email using Resend
        from_email = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <notifications@diperion.com>")
        params = {
            "from": from_email,
            "to": [email],
            "subject": f"Confirmación de Cita - {service_name} ({appointment_reference})",
            "html": html_content,
        }
        
        result = resend.Emails.send(params)
        
        # Update state to record that email was sent
        current_history = tool_context.state.get("interaction_history", [])
        new_history = current_history.copy()
        new_history.append({
            "action": "email_sent",
            "email": email,
            "appointment_reference": appointment_reference,
            "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        })
        tool_context.state["interaction_history"] = new_history
        
        return {
            "status": "success",
            "message": f"Confirmación de cita enviada exitosamente a {email}",
            "email_id": result.get("id"),
            "appointment_reference": appointment_reference
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al enviar el correo: {str(e)}"
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

    5. **Envío de confirmación por correo:**
       - Después de agendar exitosamente, SIEMPRE pregunta si desea recibir confirmación por correo
       - Si acepta, solicita su dirección de correo electrónico
       - Usa send_appointment_email() con el email y la referencia de la cita
       - Confirma el envío exitoso

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
    - CURP: PEGJ850515HDFLRN09
    
    📧 ¿Te gustaría recibir la confirmación de tu cita por correo electrónico?"
    """,
    tools=[schedule_appointment, get_available_services, get_appointments, send_appointment_email],
)