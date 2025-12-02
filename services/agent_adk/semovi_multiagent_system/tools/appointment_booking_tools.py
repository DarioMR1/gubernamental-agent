# Copyright 2024 SEMOVI Multiagent System

"""Tools for appointment booking and management."""

import uuid
import os
import base64
from datetime import datetime, date, timedelta
from io import BytesIO

from google.adk.tools.tool_context import ToolContext
from .supabase_connection import execute_supabase_query, get_user_id_from_jwt, ensure_user_profile_exists

# Imports for email and PDF
try:
    import resend
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import black, darkblue, darkgreen
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass


def get_available_slots(
    tool_context, 
    office_id: int, 
    target_date_range: int
):
    """
    Get available appointment slots for a specific office from Supabase.
    
    Args:
        tool_context: Context for accessing session state
        office_id: ID of the office to check availability
        target_date_range: Number of days to look ahead (default 14)
        
    Returns:
        Dict with available slots grouped by date
    """
    try:
        # Validate office_id
        office_search = tool_context.state.get("office_search", {})
        found_offices = office_search.get("found_offices", [])
        
        target_office = None
        for office in found_offices:
            if office["id"] == office_id:
                target_office = office
                break
        
        if not target_office:
            return {
                "status": "error",
                "message": f"Office with ID {office_id} not found in search results"
            }
        
        # Calculate date range
        start_date = (date.today() + timedelta(days=1)).isoformat()
        end_date = (date.today() + timedelta(days=target_date_range)).isoformat()
        
        # Query available slots from Supabase
        query_result = execute_supabase_query(
            tool_context,
            endpoint=f"appointment_slots?select=*&office_id=eq.{office_id}&slot_date=gte.{start_date}&slot_date=lte.{end_date}&available_capacity=gt.0&is_active=eq.true&order=slot_date,start_time",
            method="GET"
        )
        
        if query_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Failed to query appointment slots: {query_result.get('message', 'Unknown error')}"
            }
        
        slots = query_result["data"]
        
        if not slots:
            return {
                "status": "no_availability",
                "message": f"No available slots found for {target_office['name']} in the next {target_date_range} days",
                "office_name": target_office["name"],
                "suggested_action": "Try selecting a different office or extending the date range"
            }
        
        # Group slots by date for better presentation
        slots_by_date = _group_slots_by_date(slots)
        
        # Store availability information in state
        tool_context.state["appointment"] = {
            "office_id": office_id,
            "office_name": target_office["name"],
            "available_slots": slots,
            "slots_by_date": slots_by_date,
            "search_range_days": target_date_range,
            "last_availability_check": datetime.now().isoformat()
        }
        
        return {
            "status": "success",
            "office_id": office_id,
            "office_name": target_office["name"],
            "total_slots": len(slots),
            "slots_by_date": slots_by_date,
            "date_range": f"{start_date} to {end_date}",
            "message": f"Found {len(slots)} available slots at {target_office['name']}"
        }
        
    except Exception as e:
        tool_context.state["last_error"] = {
            "tool": "get_available_slots",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error getting available slots: {str(e)}"
        }


def _group_slots_by_date(slots: list):
    """Group appointment slots by date for better presentation."""
    slots_by_date = {}
    
    for slot in slots:
        slot_date = slot["slot_date"]
        if slot_date not in slots_by_date:
            slots_by_date[slot_date] = []
        
        slots_by_date[slot_date].append({
            "id": slot["id"],
            "start_time": slot["start_time"],
            "end_time": slot["end_time"],
            "available_capacity": slot["available_capacity"],
            "max_capacity": slot["max_capacity"]
        })
    
    # Sort dates and times
    for date_key in slots_by_date:
        slots_by_date[date_key].sort(key=lambda x: x["start_time"])
    
    return dict(sorted(slots_by_date.items()))


def create_appointment(
    tool_context,
    office_id: int,
    slot_id: int,
    selected_date: str,
    selected_time: str
):
    """
    Create a new appointment for the user using Supabase.
    
    Args:
        tool_context: Context for accessing session state
        office_id: ID of the selected office
        slot_id: ID of the selected time slot
        selected_date: Selected appointment date
        selected_time: Selected appointment time
        
    Returns:
        Dict with appointment confirmation details
    """
    try:
        # Validate inputs
        user_data = tool_context.state.get("user_data", {})
        service_determination = tool_context.state.get("service_determination", {})
        
        if not user_data.get("curp"):
            return {
                "status": "error",
                "message": "User identification required. Please provide INE information first."
            }
        
        if not service_determination.get("license_type"):
            return {
                "status": "error", 
                "message": "Service type required. Please determine license requirements first."
            }
        
        # Get service category and type IDs
        license_type = service_determination.get("license_type", "")
        procedure_type = service_determination.get("procedure_type", "")
        
        # Query service category ID
        service_category_result = execute_supabase_query(
            tool_context,
            endpoint=f"service_categories?select=id&code=eq.{license_type}",
            method="GET"
        )
        
        if service_category_result["status"] != "success" or not service_category_result["data"]:
            return {
                "status": "error",
                "message": f"Service category not found: {license_type}"
            }
        
        service_category_id = service_category_result["data"][0]["id"]
        
        # Query service type ID
        service_type_result = execute_supabase_query(
            tool_context,
            endpoint=f"service_types?select=id&code=eq.{procedure_type}",
            method="GET"
        )
        
        if service_type_result["status"] != "success" or not service_type_result["data"]:
            return {
                "status": "error",
                "message": f"Service type not found: {procedure_type}"
            }
        
        service_type_id = service_type_result["data"][0]["id"]
        
        # Generate confirmation code
        confirmation_code = f"SEMOVI-{datetime.now().strftime('%Y%m%d')}-{str(uuid.uuid4())[:4].upper()}"
        
        # Prepare user information for appointment
        user_info = {
            "full_name": user_data.get("full_name", ""),
            "curp": user_data.get("curp", ""),
            "address": user_data.get("address", ""),
            "postal_code": user_data.get("postal_code", ""),
            "birth_date": user_data.get("birth_date", ""),
            "phone": user_data.get("phone", ""),
            "email": user_data.get("email", "")
        }
        
        # Ensure user profile exists and get user_id (production approach)
        profile_result = ensure_user_profile_exists(tool_context)
        
        if profile_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Authentication error: {profile_result.get('message', 'Unable to verify user profile')}"
            }
        
        user_id = profile_result["user_id"]
        
        # Prepare appointment data
        appointment_data = {
            "user_id": user_id,
            "office_id": office_id,
            "service_category_id": service_category_id,
            "service_type_id": service_type_id,
            "appointment_slot_id": slot_id,
            "user_info": user_info,
            "status": "scheduled",
            "confirmation_code": confirmation_code
        }
        
        # Create appointment in Supabase
        appointment_result = execute_supabase_query(
            tool_context,
            endpoint="appointments",
            method="POST",
            data=appointment_data
        )
        
        if appointment_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Failed to create appointment: {appointment_result.get('message', 'Unknown error')}"
            }
        
        created_appointment = appointment_result["data"][0]
        
        # Update slot capacity atomically
        capacity_update_result = execute_supabase_query(
            tool_context,
            endpoint=f"appointment_slots?id=eq.{slot_id}",
            method="PATCH",
            data={"available_capacity": "available_capacity - 1"}
        )
        
        if capacity_update_result["status"] != "success":
            # Log warning but don't fail the appointment
            print(f"Warning: Failed to update slot capacity for slot {slot_id}")
        
        # Get office information
        office_search = tool_context.state.get("office_search", {})
        found_offices = office_search.get("found_offices", [])
        selected_office = None
        
        for office in found_offices:
            if office["id"] == office_id:
                selected_office = office
                break
        
        # Store appointment confirmation in state
        confirmation_details = {
            "appointment_id": created_appointment["id"],
            "confirmation_code": confirmation_code,
            "status": "confirmed",
            "office": selected_office,
            "date": selected_date,
            "time": selected_time,
            "license_type": license_type,
            "procedure_type": procedure_type,
            "total_cost": service_determination.get("costs", {}).get("total_cost", 0),
            "created_at": created_appointment["created_at"]
        }
        
        tool_context.state["appointment"]["confirmation"] = confirmation_details
        tool_context.state["appointment"]["selected_slot"] = {
            "slot_id": slot_id,
            "date": selected_date,
            "time": selected_time
        }
        tool_context.state["process_stage"] = "appointment_confirmed"
        
        # Flatten key variables for template access
        tool_context.state["appointment_date"] = selected_date
        tool_context.state["appointment_time"] = selected_time
        tool_context.state["office_name"] = selected_office.get("name", "") if selected_office else ""
        tool_context.state["total_cost"] = service_determination.get("costs", {}).get("total_cost", 0)
        
        return {
            "status": "success",
            "appointment": confirmation_details,
            "message": f"Appointment confirmed! Your confirmation code is {confirmation_code}"
        }
        
    except Exception as e:
        tool_context.state["last_error"] = {
            "tool": "create_appointment",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error creating appointment: {str(e)}"
        }


def generate_confirmation_code(tool_context):
    """
    Generate a unique confirmation code for appointments.
    
    Args:
        tool_context: Tool context for state access
        
    Returns:
        Unique confirmation code
    """
    timestamp = datetime.now().strftime("%Y%m%d")
    unique_id = str(uuid.uuid4())[:4].upper()
    confirmation_code = f"SEMOVI-{timestamp}-{unique_id}"
    
    # Store in state for reference
    tool_context.state["last_generated_code"] = {
        "code": confirmation_code,
        "generated_at": datetime.now().isoformat()
    }
    
    return confirmation_code


def update_slot_capacity(
    tool_context,
    slot_id: int,
    capacity_change: int
):
    """
    Update the available capacity for a time slot.
    
    Args:
        tool_context: Tool context for state access
        slot_id: ID of the slot to update
        capacity_change: Change in capacity (negative = reduce, positive = increase)
        
    Returns:
        Dict with update results
    """
    try:
        # In production, this would update the database
        # For now, we'll just simulate the update
        
        appointment_info = tool_context.state.get("appointment", {})
        available_slots = appointment_info.get("available_slots", [])
        
        # Find and update the specific slot
        updated = False
        for slot in available_slots:
            if slot.get("id") == slot_id:
                current_capacity = slot.get("available_capacity", 0)
                new_capacity = max(0, current_capacity + capacity_change)
                slot["available_capacity"] = new_capacity
                updated = True
                break
        
        if updated:
            # Update state
            tool_context.state["appointment"]["available_slots"] = available_slots
            
            return {
                "status": "success",
                "slot_id": slot_id,
                "capacity_change": capacity_change,
                "message": f"Slot capacity updated successfully"
            }
        else:
            return {
                "status": "not_found",
                "message": f"Slot {slot_id} not found for capacity update"
            }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error updating slot capacity: {str(e)}"
        }


def send_email_confirmation(
    tool_context,
    email: str,
    appointment_details: dict
):
    """
    Send email confirmation using Resend with professional PDF attachment.
    
    Args:
        tool_context: Tool context for state access
        email: Email address to send confirmation to
        appointment_details: Details of the appointment
        
    Returns:
        Dict with email sending results
    """
    try:
        if not email or "@" not in email:
            return {
                "status": "error",
                "message": "Valid email address required"
            }
        
        # Validar que appointment_details sea un diccionario
        if not isinstance(appointment_details, dict):
            return {
                "status": "error", 
                "message": f"appointment_details debe ser un diccionario, recibido: {type(appointment_details)}"
            }
        
        # Extract appointment details
        confirmation_code = appointment_details.get("confirmation_code", "")
        office = appointment_details.get("office", {})
        office_name = office.get("name", "SEMOVI")
        appointment_date = appointment_details.get("date", "")
        appointment_time = appointment_details.get("time", "")
        license_type = appointment_details.get("license_type", "")
        procedure_type = appointment_details.get("procedure_type", "")
        total_cost = appointment_details.get("total_cost", 0)
        
        # Get user data
        user_data = tool_context.state.get("user_data", {})
        user_name = user_data.get("full_name", "Estimado/a Ciudadano/a")
        
        # 1. GENERAR PDF AUTOMÁTICAMENTE
        pdf_result = _generate_semovi_pdf_bytes(tool_context, appointment_details)
        if pdf_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Error generando PDF: {pdf_result.get('message', 'Error desconocido')}"
            }
        
        # 2. CONFIGURAR RESEND
        resend_api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <notifications@diperion.com>")
        
        if not resend_api_key:
            return {"status": "error", "message": "RESEND_API_KEY no configurada en variables de entorno"}

        resend.api_key = resend_api_key

        # 3. CREAR CONTENIDO HTML PROFESIONAL PARA SEMOVI
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #fef2f2; padding: 30px; border-radius: 0 0 10px 10px; }}
                .appointment-card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; border-left: 4px solid #dc2626; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 12px 0; padding: 8px 0; border-bottom: 1px solid #f3f4f6; }}
                .label {{ font-weight: bold; color: #7f1d1d; }}
                .value {{ color: #1f2937; }}
                .confirmation-box {{ background: #16a34a; color: white; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; }}
                .cost-box {{ background: #fbbf24; color: #1f2937; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; }}
                .footer {{ text-align: center; color: #6b7280; margin-top: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🚗 SEMOVI</div>
                    <h1>Confirmación de Cita</h1>
                    <p>Secretaría de Movilidad - Ciudad de México</p>
                </div>
                
                <div class="content">
                    <p><strong>{user_name},</strong></p>
                    <p>Su cita para trámite de licencia de conducir ha sido <strong>confirmada exitosamente</strong>.</p>
                    
                    <div class="confirmation-box">
                        <h3>📋 Número de Confirmación: {confirmation_code}</h3>
                    </div>
                    
                    <div class="appointment-card">
                        <h3>🎫 Detalles de su Cita</h3>
                        <div class="detail-row">
                            <span class="label">👤 Solicitante:</span>
                            <span class="value">{user_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📅 Fecha:</span>
                            <span class="value">{appointment_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Hora:</span>
                            <span class="value">{appointment_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📍 Oficina SEMOVI:</span>
                            <span class="value">{office_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📋 Tipo de Licencia:</span>
                            <span class="value">{license_type}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">🔄 Procedimiento:</span>
                            <span class="value">{procedure_type}</span>
                        </div>
                    </div>
                    
                    <div class="cost-box">
                        <h4>💰 Costo Total: ${total_cost:.2f} MXN</h4>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 20px; border-radius: 6px; margin: 20px 0; border-left: 4px solid #f59e0b;">
                        <h4>⚠️ Recordatorios Importantes:</h4>
                        <ul>
                            <li>🕘 Presente se <strong>10 minutos antes</strong> de su cita</li>
                            <li>🆔 Traiga su <strong>identificación oficial vigente</strong></li>
                            <li>📄 Adjunto encontrará su <strong>comprobante en PDF</strong></li>
                            <li>💳 Lleve el <strong>pago exacto</strong> en efectivo o tarjeta</li>
                            <li>📞 Para reagendar, contacte la oficina con 24 horas de anticipación</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Este correo fue generado automáticamente por el Sistema de Citas SEMOVI</p>
                    <p><small>© 2024 Secretaría de Movilidad - Ciudad de México</small></p>
                </div>
            </div>
        </body>
        </html>
        """

        # 4. ENVIAR EMAIL CON RESEND (SINTAXIS OFICIAL)
        params = {
            "from": from_email,
            "to": [email],
            "subject": f"✅ Confirmación de Cita SEMOVI - {confirmation_code}",
            "html": html_body,
            "attachments": [
                {
                    "content": pdf_result["pdf_base64"],
                    "filename": f"SEMOVI_Cita_{confirmation_code}.pdf"
                }
            ]
        }
        
        result = resend.Emails.send(params)

        # 5. ACTUALIZAR ESTADO
        tool_context.state["email_confirmation"] = {
            "email": email,
            "sent_at": datetime.now().isoformat(),
            "confirmation_code": confirmation_code,
            "status": "sent",
            "resend_id": result.get("id", "unknown")
        }

        return {
            "status": "success",
            "message": f"📧 Correo de confirmación enviado exitosamente a {email}",
            "confirmation_code": confirmation_code,
            "resend_id": result.get("id"),
            "email": email
        }

    except ImportError:
        return {"status": "error", "message": "Resend no está instalado. Instala con: pip install resend"}
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error enviando correo: {str(e)}"
        }


def _generate_email_content(
    confirmation_code,
    office_name,
    appointment_date,
    appointment_time,
    license_type,
    procedure_type
):
    """Generate email content for appointment confirmation."""
    
    content = f"""
Subject: SEMOVI Appointment Confirmation - {confirmation_code}

Dear Citizen,

Your SEMOVI license appointment has been confirmed!

APPOINTMENT DETAILS:
- Confirmation Code: {confirmation_code}
- Service: {license_type} - {procedure_type}
- Date: {appointment_date}
- Time: {appointment_time}
- Office: {office_name}

IMPORTANT REMINDERS:
1. Arrive 15 minutes before your appointment time
2. Bring all required documents
3. Bring exact payment amount
4. Present this confirmation code at the office

REQUIRED DOCUMENTS:
- Official identification (INE/Passport)
- CURP
- Proof of address
- Birth certificate
- Medical examination certificate
- Driving course certificate (if applicable)

If you need to cancel or reschedule, please contact the office at least 24 hours in advance.

Thank you for using SEMOVI services.

Government Digital Services
SEMOVI - Mexico City
    """.strip()
    
    return content


def _generate_semovi_pdf_bytes(tool_context, appointment_details: dict) -> dict:
    """
    Generate SEMOVI PDF in memory for email attachment.
    Returns PDF as base64 for use with Resend attachments.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import black, red, darkgreen
    except ImportError:
        return {"status": "error", "message": "reportlab no está instalado"}

    # Validar que appointment_details sea un diccionario
    if not isinstance(appointment_details, dict):
        return {
            "status": "error", 
            "message": f"appointment_details debe ser un diccionario, recibido: {type(appointment_details)}"
        }

    # 1. RECUPERAR DATOS
    user_data = tool_context.state.get("user_data", {})
    user_name = user_data.get("full_name", "Usuario")
    user_curp = user_data.get("curp", "SIN DATO")
    user_address = user_data.get("address", "Sin dirección")

    confirmation_code = appointment_details.get("confirmation_code", "")
    office = appointment_details.get("office", {})
    license_type = appointment_details.get("license_type", "")
    procedure_type = appointment_details.get("procedure_type", "")
    appointment_date = appointment_details.get("date", "")
    appointment_time = appointment_details.get("time", "")
    total_cost = appointment_details.get("total_cost", 0)

    # 2. CREAR PDF EN MEMORIA
    buffer = BytesIO()
    
    try:
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # === HEADER SEMOVI ===
        c.setFillColor(red)
        c.rect(0, height-80, width, 80, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 22)
        c.drawString(50, height-35, "🚗 SEMOVI - COMPROBANTE DE CITA")
        
        c.setFont("Helvetica", 11)
        c.drawString(50, height-55, "Secretaría de Movilidad - Ciudad de México")
        
        # === CONFIRMACIÓN DESTACADA ===
        c.setFillColor(darkgreen)
        c.rect(50, height-150, width-100, 40, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 16)
        text_width = c.stringWidth(f"CONFIRMACIÓN: {confirmation_code}", "Helvetica-Bold", 16)
        c.drawString((width - text_width) / 2, height-135, f"CONFIRMACIÓN: {confirmation_code}")
        
        # === DATOS DEL SOLICITANTE ===
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height-190, "DATOS DEL SOLICITANTE:")
        
        c.setFont("Helvetica", 12)
        y_position = height-210
        solicitante_data = [
            f"👤 Nombre: {user_name}",
            f"🆔 CURP: {user_curp}",
            f"🏠 Dirección: {user_address}"
        ]
        
        for line in solicitante_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === DETALLES DE LA CITA ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "DETALLES DE LA CITA:")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        cita_data = [
            f"🎫 Tipo de Licencia: {license_type}",
            f"🔄 Procedimiento: {procedure_type}",
            f"📅 Fecha: {appointment_date}",
            f"⏰ Hora: {appointment_time}",
            f"📍 Oficina: {office.get('name', 'SEMOVI')}",
            f"💰 Costo Total: ${total_cost:.2f} MXN"
        ]
        
        for line in cita_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === OFICINA INFORMACIÓN ===
        if office.get('address'):
            y_position -= 10
            c.setFont("Helvetica", 10)
            c.drawString(70, y_position, f"📧 Dirección: {office.get('address', '')}")
            y_position -= 15
            
        if office.get('phone'):
            c.drawString(70, y_position, f"📞 Teléfono: {office.get('phone', '')}")
            y_position -= 20
        
        # === RECORDATORIOS ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "⚠️ RECORDATORIOS IMPORTANTES:")
        y_position -= 20
        
        c.setFont("Helvetica", 10)
        recordatorios = [
            "• Presente este comprobante el día de su cita",
            "• Llegue 10 minutos antes del horario programado",
            "• Traiga identificación oficial vigente (INE/Pasaporte)",
            "• Lleve el pago exacto en efectivo o tarjeta",
            "• Para reagendar, contacte la oficina con 24 horas de anticipación",
            "• Complete el curso de manejo si es requerido para su tipo de licencia"
        ]
        
        for recordatorio in recordatorios:
            c.drawString(70, y_position, recordatorio)
            y_position -= 16
        
        # === CÓDIGO QR SIMULADO ===
        c.setFont("Helvetica-Bold", 9)
        c.drawString(50, 100, "📱 CÓDIGO QR PARA CHECK-IN:")
        c.rect(50, 50, 70, 70, fill=0)
        c.drawString(70, 80, "QR")
        c.drawString(60, 70, f"ID:{confirmation_code[-4:]}")
        
        # === PIE DE PÁGINA ===
        c.setFont("Helvetica", 8)
        text1 = f"Generado: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}"
        text2 = "© 2024 SEMOVI - Válido únicamente para la cita programada"
        text1_width = c.stringWidth(text1, "Helvetica", 8)
        text2_width = c.stringWidth(text2, "Helvetica", 8)
        c.drawString((width - text1_width) / 2, 30, text1)
        c.drawString((width - text2_width) / 2, 15, text2)
        
        c.save()
        
        # 3. CONVERTIR A BASE64
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        buffer.close()
        
        return {
            "status": "success",
            "message": "PDF SEMOVI generado en memoria",
            "pdf_base64": pdf_base64,
            "pdf_size": len(pdf_bytes)
        }
        
    except Exception as e:
        buffer.close()
        return {"status": "error", "message": f"Error generando PDF: {str(e)}"}


def generate_pdf_confirmation(
    tool_context,
    appointment_details: dict
):
    """
    Generate professional PDF confirmation document for SEMOVI appointment.
    Creates a downloadable file and saves to disk.
    
    Args:
        tool_context: Tool context for state access
        appointment_details: Details of the appointment
        
    Returns:
        Dict with PDF generation results
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import black, red, darkgreen
    except ImportError:
        return {"status": "error", "message": "reportlab no está instalado"}
    
    # Validar que appointment_details sea un diccionario
    if not isinstance(appointment_details, dict):
        return {
            "status": "error", 
            "message": f"appointment_details debe ser un diccionario, recibido: {type(appointment_details)}"
        }
    
    confirmation_code = appointment_details.get("confirmation_code", "")
    user_data = tool_context.state.get("user_data", {})
    
    # Use the same PDF generation logic but save to file
    pdf_result = _generate_semovi_pdf_bytes(tool_context, appointment_details)
    if pdf_result["status"] != "success":
        return pdf_result
    
    # Save to file
    filename = f"SEMOVI_Cita_{confirmation_code}.pdf"
    try:
        with open(filename, "wb") as f:
            f.write(base64.b64decode(pdf_result["pdf_base64"]))
        
        abs_path = os.path.abspath(filename)
        
        # Store PDF information in state
        tool_context.state["pdf_confirmation"] = {
            "filename": filename,
            "generated_at": datetime.now().isoformat(),
            "confirmation_code": confirmation_code,
            "size_kb": pdf_result["pdf_size"] / 1024,
            "file_path": abs_path,
            "status": "generated"
        }
        
        return {
            "status": "success",
            "filename": filename,
            "file_path": abs_path,
            "confirmation_code": confirmation_code,
            "message": "PDF profesional generado y guardado exitosamente"
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error guardando PDF: {str(e)}"
        }


def _generate_pdf_content(appointment_details: dict, user_data: dict):
    """Generate PDF content for appointment confirmation."""
    
    # Simulate PDF content as text
    content = f"""
SEMOVI - SECRETARIA DE MOVILIDAD
APPOINTMENT CONFIRMATION

Confirmation Code: {appointment_details.get('confirmation_code', '')}

CITIZEN INFORMATION:
Name: {user_data.get('full_name', '')}
CURP: {user_data.get('curp', '')}
Address: {user_data.get('address', '')}

APPOINTMENT DETAILS:
Service: {appointment_details.get('license_type', '')} - {appointment_details.get('procedure_type', '')}
Date: {appointment_details.get('date', '')}
Time: {appointment_details.get('time', '')}
Office: {appointment_details.get('office', {}).get('name', '')}
Address: {appointment_details.get('office', {}).get('address', '')}
Cost: ${appointment_details.get('total_cost', 0):.2f} MXN

QR CODE: [QR code would be here for quick check-in]

IMPORTANT: Present this document and valid ID at your appointment.

Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M')}
    """.strip()
    
    return content