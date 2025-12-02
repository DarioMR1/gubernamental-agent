import os
import random
import sqlite3
import base64
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from io import BytesIO

# --- IMPORTS DE CORREO Y PDF ---
try:
    import resend
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
    from reportlab.lib.colors import black, darkblue
    from reportlab.lib.utils import ImageReader
except ImportError:
    pass 

from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from dotenv import load_dotenv
# Cargar variables de entorno
load_dotenv()

def init_db():
    conn = sqlite3.connect('citas_sat.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS appointments (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            confirmation_number TEXT UNIQUE,
            office_id TEXT,
            office_name TEXT,
            date TEXT,
            time TEXT,
            service_type TEXT,
            user_curp TEXT,
            user_name TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    conn.commit()
    conn.close()

init_db()


def search_sat_locations_by_postal_code(tool_context: ToolContext, postal_code: str) -> dict:
    """
    Busca oficinas del SAT cercanas basándose en el código postal del usuario.
    
    Args:
        tool_context: Contexto de la herramienta para acceso al estado de sesión
        postal_code: Código postal para buscar oficinas cercanas
    """
    # Simulamos búsqueda de oficinas SAT basado en código postal
    # En implementación real, esto consultaría una API o base de datos del SAT
    
    sat_offices = {
        "06000": [  # Centro CDMX
            {
                "id": "sat_centro_01",
                "name": "SAT Centro Histórico",
                "address": "Av. Hidalgo 77, Centro Histórico, Cuauhtémoc, 06300 Ciudad de México",
                "phone": "55-8526-8526",
                "services": ["RFC", "Firma electrónica", "Facturación", "Devoluciones"],
                "distance_km": 2.1
            },
            {
                "id": "sat_centro_02", 
                "name": "SAT Doctores",
                "address": "Dr. Río de la Loza 300, Doctores, Cuauhtémoc, 06720 Ciudad de México",
                "phone": "55-8526-8527",
                "services": ["RFC", "Firma electrónica", "Facturación"],
                "distance_km": 3.5
            }
        ],
        "01000": [  # Álvaro Obregón
            {
                "id": "sat_alvaro_01",
                "name": "SAT San Ángel",
                "address": "Av. Revolución 1245, San Ángel, Álvaro Obregón, 01000 Ciudad de México",
                "phone": "55-8526-8530",
                "services": ["RFC", "Firma electrónica", "Facturación", "Devoluciones"],
                "distance_km": 1.8
            }
        ]
    }
    
    # Obtener oficinas para el código postal (o usar ubicaciones por defecto)
    locations = sat_offices.get(postal_code, [
        {
            "id": "sat_default_01",
            "name": "SAT Servicio Principal",
            "address": f"Oficina del SAT más cercana a CP {postal_code}",
            "phone": "55-8526-8500",
            "services": ["RFC", "Firma electrónica", "Facturación"],
            "distance_km": 5.0
        }
    ])
    
    # Guardar ubicaciones encontradas en el estado
    tool_context.state["sat_locations"] = locations
    
    # Actualizar historial
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "search_sat_locations", 
        "postal_code": postal_code,
        "locations_found": len(locations),
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "postal_code": postal_code,
        "locations": locations,
        "total_found": len(locations),
        "message": f"Se encontraron {len(locations)} oficinas del SAT cerca del código postal {postal_code}"
    }


def get_available_appointments(tool_context: ToolContext, office_id: str, service_type: str) -> dict:
    """
    Consulta horarios disponibles para una oficina específica del SAT.
    
    Args:
        tool_context: Contexto de la herramienta
        office_id: ID de la oficina del SAT
        service_type: Tipo de servicio (RFC, Firma electrónica, etc.)
    """
    # Si no se proporciona service_type, usar valor por defecto
    if not service_type:
        service_type = "RFC"
    # Simular disponibilidad de citas para los próximos 15 días
    available_slots = []
    start_date = datetime.now() + timedelta(days=2)  # Citas disponibles desde pasado mañana
    
    for day_offset in range(15):
        current_date = start_date + timedelta(days=day_offset)
        # Saltar fines de semana
        if current_date.weekday() < 5:  # 0=Lunes, 4=Viernes
            # Horarios disponibles: 9:00-15:00
            time_slots = ["09:00", "10:00", "11:00", "12:00", "14:00", "15:00"]
            # Simular que algunos horarios ya están ocupados
            available_times = random.sample(time_slots, random.randint(2, 5))
            
            for time_slot in sorted(available_times):
                available_slots.append({
                    "date": current_date.strftime("%Y-%m-%d"),
                    "time": time_slot,
                    "slot_id": f"{office_id}_{current_date.strftime('%Y%m%d')}_{time_slot.replace(':', '')}",
                    "day_name": current_date.strftime("%A"),
                    "formatted_date": current_date.strftime("%d de %B")
                })
    
    # Guardar slots disponibles en el estado
    tool_context.state["available_appointments"] = available_slots
    tool_context.state["selected_office_id"] = office_id
    tool_context.state["selected_service_type"] = service_type
    
    # Actualizar historial
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "get_available_appointments",
        "office_id": office_id,
        "service_type": service_type,
        "slots_found": len(available_slots),
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "office_id": office_id,
        "service_type": service_type,
        "available_slots": available_slots[:10],  # Mostrar primeros 10 slots
        "total_slots": len(available_slots),
        "message": f"Se encontraron {len(available_slots)} horarios disponibles para {service_type}"
    }


def schedule_sat_appointment(
    tool_context: ToolContext, 
    office_id: str, 
    date: str, 
    time: str, 
    service_type: str
) -> dict:
    """
    Agenda una cita en el SAT verificando disponibilidad real en base de datos.
    Previene doble agendamiento en la misma oficina/hora.
    """
    conn = sqlite3.connect('citas_sat.db')
    cursor = conn.cursor()

    try:
        # 1. VALIDACIÓN DE DISPONIBILIDAD (EL CANDADO 🔒)
        # Buscamos si ya existe una cita en esa oficina, ese día y a esa hora
        cursor.execute('''
            SELECT count(*) FROM appointments 
            WHERE office_id = ? AND date = ? AND time = ?
        ''', (office_id, date, time))
        
        count = cursor.fetchone()[0]
        
        if count > 0:
            conn.close()
            return {
                "status": "error", 
                "message": f"❌ LO SIENTO: El horario de las {time} el día {date} en esta oficina YA ESTÁ OCUPADO. Por favor selecciona otro horario."
            }

        # 2. GENERAR CITA (Si está libre)
        confirmation_number = f"SAT-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
        
        # Recuperamos info del usuario del estado actual
        user_info = tool_context.state.get("user_info", {})
        user_curp = user_info.get("curp", "GENERICO")
        
        # Intentamos obtener el nombre de la oficina (esto es opcional, solo para guardar bonito)
        # En un caso real haríamos un lookup, aquí usaremos el ID como nombre si no está en el estado
        office_name = office_id 

        # 3. GUARDAR EN BASE DE DATOS (INSERT)
        cursor.execute('''
            INSERT INTO appointments (confirmation_number, office_id, office_name, date, time, service_type, user_curp)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (confirmation_number, office_id, office_name, date, time, service_type, user_curp))
        
        conn.commit()

        # 4. ACTUALIZAR ESTADO DEL AGENTE (Para que el PDF funcione)
        # Esto mantiene la compatibilidad con tu función de PDF y Email
        appointment_details = {
            "confirmation_number": confirmation_number,
            "office": {"id": office_id, "name": office_name, "address": "Dirección registrada en BD"},
            "date": date,
            "time": time,
            "service_type": service_type,
            "user_info": user_info
        }
        
        current_appointments = tool_context.state.get("appointments", [])
        current_appointments.append(appointment_details)
        tool_context.state["appointments"] = current_appointments

        return {
            "status": "success",
            "confirmation_number": confirmation_number,
            "details": f"Cita confirmada en BD para {date} a las {time}.",
            "message": "Cita bloqueada y registrada exitosamente."
        }

    except Exception as e:
        return {"status": "error", "message": f"Error de base de datos: {str(e)}"}
    finally:
        conn.close()


def get_appointment_requirements(tool_context: ToolContext, service_type: str) -> dict:
    """
    Proporciona los requisitos específicos para diferentes tipos de trámites del SAT.
    
    Args:
        tool_context: Contexto de la herramienta
        service_type: Tipo de servicio (RFC, Firma electrónica, etc.)
    """
    requirements = {
        "RFC": {
            "documents": [
                "Acta de nacimiento original",
                "Identificación oficial vigente (INE/Pasaporte)",
                "Comprobante de domicilio no mayor a 3 meses"
            ],
            "additional_info": [
                "Si eres trabajador dependiente, necesitas tu CFDI de nómina",
                "Si tienes actividad empresarial, preparar descripción de la actividad"
            ],
            "duration": "30-45 minutos",
            "cost": "Gratuito"
        },
        "Firma electrónica": {
            "documents": [
                "RFC activo",
                "Identificación oficial vigente (INE/Pasaporte)",
                "Comprobante de domicilio no mayor a 3 meses",
                "Dispositivo USB o CD"
            ],
            "additional_info": [
                "La firma electrónica tiene vigencia de 4 años",
                "Necesario para facturación electrónica"
            ],
            "duration": "20-30 minutos",
            "cost": "Gratuito"
        },
        "Facturación": {
            "documents": [
                "RFC activo",
                "Firma electrónica vigente",
                "Identificación oficial"
            ],
            "additional_info": [
                "Asesoría sobre uso del portal del SAT",
                "Configuración inicial de facturación"
            ],
            "duration": "15-20 minutos", 
            "cost": "Gratuito"
        },
        "Devoluciones": {
            "documents": [
                "RFC activo",
                "Firma electrónica vigente", 
                "Declaración anual presentada",
                "Comprobantes fiscales originales"
            ],
            "additional_info": [
                "Solo se pueden solicitar devoluciones de los últimos 5 años",
                "El proceso puede tomar de 15 a 40 días hábiles"
            ],
            "duration": "45-60 minutos",
            "cost": "Gratuito"
        }
    }
    
    service_requirements = requirements.get(service_type, {
        "documents": ["Consultar en oficina"],
        "additional_info": ["Información no disponible para este servicio"],
        "duration": "Variable",
        "cost": "Consultar en oficina"
    })
    
    # Actualizar historial
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "get_requirements",
        "service_type": service_type,
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "service_type": service_type,
        "requirements": service_requirements,
        "message": f"Requisitos para {service_type} obtenidos exitosamente"
    }


def send_appointment_confirmation_email(
    tool_context: ToolContext, 
    to_email: str
) -> dict:
    """
    Envía un correo con los detalles de la cita usando Resend con PDF automáticamente generado y adjunto.
    """
    try:
        # 1. RECUPERAR DATOS DEL ESTADO (Memoria)
        user_info = tool_context.state.get("user_info", {})
        user_name = user_info.get("full_name", "Contribuyente")

        # Buscamos la última cita agendada para sacar fecha y hora
        appointments = tool_context.state.get("appointments", [])
        if not appointments:
            return {"status": "error", "message": "No se encontró información de la cita para enviar el correo."}
        
        last_appt = appointments[-1]
        appt_date = last_appt.get("date", "Fecha pendiente")
        appt_time = last_appt.get("time", "--:--")
        appt_office = last_appt.get("office", {}).get("name", "Oficina SAT")
        service = last_appt.get("service_type", "Trámite")
        confirmation_number = last_appt.get("confirmation_number", "N/A")

        # 2. GENERAR PDF AUTOMÁTICAMENTE
        pdf_result = generate_appointment_pdf_bytes(tool_context, confirmation_number)
        if pdf_result["status"] != "success":
            return {
                "status": "error",
                "message": f"Error generando PDF: {pdf_result.get('message', 'Error desconocido')}"
            }

        # 3. CONFIGURAR RESEND
        resend_api_key = os.getenv("RESEND_API_KEY")
        from_email = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <notifications@diperion.com>")
        
        if not resend_api_key:
            return {"status": "error", "message": "RESEND_API_KEY no configurada en variables de entorno"}

        resend.api_key = resend_api_key

        # 4. CREAR CONTENIDO HTML PROFESIONAL
        html_body = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="UTF-8">
            <style>
                body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                .header {{ background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }}
                .content {{ background: #f8fafc; padding: 30px; border-radius: 0 0 10px 10px; }}
                .appointment-card {{ background: white; padding: 25px; border-radius: 8px; box-shadow: 0 2px 10px rgba(0,0,0,0.1); margin: 20px 0; }}
                .detail-row {{ display: flex; justify-content: space-between; margin: 12px 0; padding: 8px 0; border-bottom: 1px solid #e2e8f0; }}
                .label {{ font-weight: bold; color: #475569; }}
                .value {{ color: #1e293b; }}
                .confirmation-box {{ background: #10b981; color: white; padding: 15px; border-radius: 6px; text-align: center; margin: 20px 0; }}
                .footer {{ text-align: center; color: #64748b; margin-top: 30px; }}
                .logo {{ font-size: 24px; font-weight: bold; margin-bottom: 10px; }}
            </style>
        </head>
        <body>
            <div class="container">
                <div class="header">
                    <div class="logo">🏛️ SAT</div>
                    <h1>Confirmación de Cita</h1>
                    <p>Servicio de Administración Tributaria</p>
                </div>
                
                <div class="content">
                    <p><strong>Estimado/a {user_name},</strong></p>
                    <p>Su cita ha sido <strong>confirmada exitosamente</strong> en el Sistema de Administración Tributaria.</p>
                    
                    <div class="confirmation-box">
                        <h3>📋 Número de Confirmación: {confirmation_number}</h3>
                    </div>
                    
                    <div class="appointment-card">
                        <h3>📅 Detalles de su Cita</h3>
                        <div class="detail-row">
                            <span class="label">👤 Contribuyente:</span>
                            <span class="value">{user_name}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📅 Fecha:</span>
                            <span class="value">{appt_date}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">⏰ Hora:</span>
                            <span class="value">{appt_time}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📍 Oficina:</span>
                            <span class="value">{appt_office}</span>
                        </div>
                        <div class="detail-row">
                            <span class="label">📋 Trámite:</span>
                            <span class="value">{service}</span>
                        </div>
                    </div>
                    
                    <div style="background: #fef3c7; padding: 20px; border-radius: 6px; margin: 20px 0;">
                        <h4>⚠️ Recordatorios Importantes:</h4>
                        <ul>
                            <li>🕘 Presente se <strong>10 minutos antes</strong> de su cita</li>
                            <li>🆔 Traiga su <strong>identificación oficial vigente</strong></li>
                            <li>📄 Adjunto encontrará su <strong>comprobante en PDF</strong></li>
                            <li>📞 Para reagendar, contacte la oficina con 24 horas de anticipación</li>
                        </ul>
                    </div>
                </div>
                
                <div class="footer">
                    <p>Este correo fue generado automáticamente por el Sistema de Citas del SAT</p>
                    <p><small>© 2024 Servicio de Administración Tributaria - México</small></p>
                </div>
            </div>
        </body>
        </html>
        """

        # 5. ENVIAR EMAIL CON RESEND
        result = resend.Emails.send({
            "from": from_email,
            "to": [to_email],
            "subject": f"✅ Confirmación de Cita SAT - {confirmation_number}",
            "html": html_body,
            "attachments": [{
                "filename": f"Cita_SAT_{confirmation_number}.pdf",
                "content": pdf_result["pdf_base64"]
            }]
        })

        # 6. ACTUALIZAR ESTADO
        tool_context.state["email_confirmation"] = {
            "email": to_email,
            "sent_at": datetime.now().isoformat(),
            "confirmation_code": confirmation_number,
            "status": "sent",
            "resend_id": result.get("id", "unknown")
        }

        return {
            "status": "success",
            "message": f"📧 Correo de confirmación enviado exitosamente a {to_email}",
            "confirmation_code": confirmation_number,
            "resend_id": result.get("id"),
            "email": to_email
        }

    except ImportError:
        return {"status": "error", "message": "Resend no está instalado. Instala con: pip install resend"}
    except Exception as e:
        return {"status": "error", "message": f"Error enviando correo: {str(e)}"}    

def generate_appointment_pdf_bytes(tool_context: ToolContext, confirmation_number: str) -> dict:
    """
    Genera el PDF en memoria para adjuntar al email, sin guardarlo en disco.
    Retorna el PDF en base64 para usar con Resend.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import black, darkblue, darkgreen
    except ImportError:
        return {"status": "error", "message": "reportlab no está instalado"}

    # 1. RECUPERAR DATOS DEL USUARIO Y CITA
    user_info = tool_context.state.get("user_info", {})
    user_name = user_info.get("full_name", "Usuario Genérico")
    user_curp = user_info.get("curp", "SIN DATO")
    user_address = user_info.get("address", "Sin dirección")

    # Buscar la cita específica
    clean_confirmation = confirmation_number.strip()
    appointments = tool_context.state.get("appointments", [])
    appointment = next((a for a in appointments if a.get("confirmation_number") == clean_confirmation), None)
    
    if not appointment:
        return {"status": "error", "message": "Cita no encontrada en memoria temporal."}

    # 2. CREAR PDF EN MEMORIA
    buffer = BytesIO()
    
    try:
        c = canvas.Canvas(buffer, pagesize=letter)
        width, height = letter
        
        # === HEADER CON LOGO Y TÍTULO ===
        c.setFillColor(darkblue)
        c.rect(0, height-80, width, 80, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height-35, "🏛️ SAT - COMPROBANTE DE CITA")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height-55, "Servicio de Administración Tributaria")
        
        # === NÚMERO DE CONFIRMACIÓN DESTACADO ===
        c.setFillColor(darkgreen)
        c.rect(50, height-150, width-100, 40, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredText(width/2, height-135, f"CONFIRMACIÓN: {clean_confirmation}")
        
        # === INFORMACIÓN DEL CONTRIBUYENTE ===
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height-190, "DATOS DEL CONTRIBUYENTE:")
        
        c.setFont("Helvetica", 12)
        y_position = height-210
        contribuyente_data = [
            f"👤 Nombre: {user_name}",
            f"🆔 CURP: {user_curp}",
            f"🏠 Dirección: {user_address}"
        ]
        
        for line in contribuyente_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === DETALLES DE LA CITA ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "DETALLES DE LA CITA:")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        cita_data = [
            f"📋 Trámite: {appointment.get('service_type', 'General')}",
            f"📅 Fecha: {appointment.get('date', 'N/A')}",
            f"⏰ Hora: {appointment.get('time', 'N/A')}",
            f"📍 Oficina: {appointment.get('office', {}).get('name', 'SAT')}"
        ]
        
        for line in cita_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === RECORDATORIOS IMPORTANTES ===
        y_position -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "⚠️ RECORDATORIOS IMPORTANTES:")
        y_position -= 20
        
        c.setFont("Helvetica", 11)
        recordatorios = [
            "• Presente este comprobante el día de su cita",
            "• Llegue 10 minutos antes del horario programado", 
            "• Traiga identificación oficial vigente (INE/Pasaporte)",
            "• Para reagendar, contacte la oficina con 24 horas de anticipación",
            "• En caso de no asistir, su cita será cancelada automáticamente"
        ]
        
        for recordatorio in recordatorios:
            c.drawString(70, y_position, recordatorio)
            y_position -= 18
        
        # === CÓDIGO QR SIMULADO ===
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "📱 CÓDIGO QR PARA CHECK-IN RÁPIDO:")
        c.rect(50, 50, 80, 80, fill=0)
        c.drawCentredText(90, 85, "QR CODE")
        c.drawCentredText(90, 75, f"ID: {clean_confirmation[-4:]}")
        
        # === PIE DE PÁGINA ===
        c.setFont("Helvetica", 9)
        c.drawCentredText(width/2, 30, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawCentredText(width/2, 15, "© 2024 SAT - Este documento es válido únicamente para la cita programada")
        
        c.save()
        
        # 3. CONVERTIR A BASE64 PARA RESEND
        buffer.seek(0)
        pdf_bytes = buffer.getvalue()
        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
        buffer.close()
        
        return {
            "status": "success",
            "message": "PDF generado exitosamente en memoria",
            "pdf_base64": pdf_base64,
            "pdf_size": len(pdf_bytes)
        }
        
    except Exception as e:
        buffer.close()
        return {"status": "error", "message": f"Error generando PDF: {str(e)}"}


def generate_appointment_pdf(tool_context: ToolContext, confirmation_number: str) -> dict:
    """
    Genera el PDF con diseño profesional y lo guarda en disco.
    Versión mejorada que crea un archivo descargable.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.colors import black, darkblue, darkgreen
    except ImportError:
        return {"status": "error", "message": "reportlab no está instalado"}

    # 1. RECUPERAR DATOS DEL USUARIO Y CITA
    user_info = tool_context.state.get("user_info", {})
    user_name = user_info.get("full_name", "Usuario Genérico")
    user_curp = user_info.get("curp", "SIN DATO")
    user_address = user_info.get("address", "Sin dirección")

    # Buscar la cita específica
    clean_confirmation = confirmation_number.strip()
    appointments = tool_context.state.get("appointments", [])
    appointment = next((a for a in appointments if a.get("confirmation_number") == clean_confirmation), None)
    
    if not appointment:
        return {"status": "error", "message": "Cita no encontrada en memoria temporal."}

    filename = f"Cita_SAT_{clean_confirmation}.pdf"
    
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter
        
        # === HEADER CON LOGO Y TÍTULO ===
        c.setFillColor(darkblue)
        c.rect(0, height-80, width, 80, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 24)
        c.drawString(50, height-35, "🏛️ SAT - COMPROBANTE DE CITA")
        
        c.setFont("Helvetica", 12)
        c.drawString(50, height-55, "Servicio de Administración Tributaria")
        
        # === NÚMERO DE CONFIRMACIÓN DESTACADO ===
        c.setFillColor(darkgreen)
        c.rect(50, height-150, width-100, 40, fill=1)
        
        c.setFillColor('white')
        c.setFont("Helvetica-Bold", 16)
        c.drawCentredText(width/2, height-135, f"CONFIRMACIÓN: {clean_confirmation}")
        
        # === INFORMACIÓN DEL CONTRIBUYENTE ===
        c.setFillColor(black)
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, height-190, "DATOS DEL CONTRIBUYENTE:")
        
        c.setFont("Helvetica", 12)
        y_position = height-210
        contribuyente_data = [
            f"👤 Nombre: {user_name}",
            f"🆔 CURP: {user_curp}",
            f"🏠 Dirección: {user_address}"
        ]
        
        for line in contribuyente_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === DETALLES DE LA CITA ===
        y_position -= 20
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "DETALLES DE LA CITA:")
        y_position -= 20
        
        c.setFont("Helvetica", 12)
        cita_data = [
            f"📋 Trámite: {appointment.get('service_type', 'General')}",
            f"📅 Fecha: {appointment.get('date', 'N/A')}",
            f"⏰ Hora: {appointment.get('time', 'N/A')}",
            f"📍 Oficina: {appointment.get('office', {}).get('name', 'SAT')}"
        ]
        
        for line in cita_data:
            c.drawString(70, y_position, line)
            y_position -= 20
        
        # === RECORDATORIOS IMPORTANTES ===
        y_position -= 30
        c.setFont("Helvetica-Bold", 14)
        c.drawString(50, y_position, "⚠️ RECORDATORIOS IMPORTANTES:")
        y_position -= 20
        
        c.setFont("Helvetica", 11)
        recordatorios = [
            "• Presente este comprobante el día de su cita",
            "• Llegue 10 minutos antes del horario programado", 
            "• Traiga identificación oficial vigente (INE/Pasaporte)",
            "• Para reagendar, contacte la oficina con 24 horas de anticipación",
            "• En caso de no asistir, su cita será cancelada automáticamente"
        ]
        
        for recordatorio in recordatorios:
            c.drawString(70, y_position, recordatorio)
            y_position -= 18
        
        # === CÓDIGO QR SIMULADO ===
        c.setFont("Helvetica-Bold", 10)
        c.drawString(50, 100, "📱 CÓDIGO QR PARA CHECK-IN RÁPIDO:")
        c.rect(50, 50, 80, 80, fill=0)
        c.drawCentredText(90, 85, "QR CODE")
        c.drawCentredText(90, 75, f"ID: {clean_confirmation[-4:]}")
        
        # === PIE DE PÁGINA ===
        c.setFont("Helvetica", 9)
        c.drawCentredText(width/2, 30, f"Generado el: {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}")
        c.drawCentredText(width/2, 15, "© 2024 SAT - Este documento es válido únicamente para la cita programada")
        
        c.save()

        # Ruta absoluta para descarga
        abs_path = os.path.abspath(filename)
        
        return {
            "status": "success", 
            "message": "PDF profesional generado exitosamente", 
            "file_path": abs_path,
            "filename": filename,
            "note": f"Archivo guardado en: {abs_path}"
        }
        
    except Exception as e:
        return {"status": "error", "message": f"Error generando PDF: {str(e)}"}   
    

# Crear el agente de agendamiento de citas
appointment_scheduling_agent = Agent(
    name="appointment_scheduling_agent",
    model="gemini-2.0-flash",
    description="Agent specialized in scheduling government appointments, particularly for SAT services",
    instruction="""
    Eres un agente especializado en agendar citas para servicios gubernamentales, especialmente del SAT (Servicio de Administración Tributaria).

    <user_info>
    Nombre: {full_name}
    CURP: {curp}
    Dirección: {address}
    Código Postal: {postal_code}
    Teléfono: {phone}
    Email: {email}
    </user_info>

    <appointments>
    {appointments}
    </appointments>

    <interaction_history>
    {interaction_history}
    </interaction_history>

    ## TU FUNCIÓN PRINCIPAL
    
    Ayudar a los usuarios a agendar citas para trámites del SAT de manera eficiente y completa.

    **⚠️ REGLA CRÍTICA OBLIGATORIA ⚠️**
    **SIEMPRE DEBES USAR LAS HERRAMIENTAS DISPONIBLES PARA OBTENER INFORMACIÓN**
    **NUNCA INVENTES O PROPORCIONES DATOS SIN USAR LAS HERRAMIENTAS CORRESPONDIENTES**
    **CADA PASO DEL PROCESO REQUIERE UNA LLAMADA A UNA HERRAMIENTA ESPECÍFICA**

    ## SERVICIOS DEL SAT DISPONIBLES
    
    1. **RFC (Registro Federal de Contribuyentes)**
       - Inscripción por primera vez
       - Actualización de datos
       - Reactivación de RFC suspendido

    2. **Firma Electrónica (FIEL)**
       - Tramite inicial
       - Renovación 
       - Revocación

    3. **Facturación Electrónica**
       - Asesoría sobre facturación
       - Configuración inicial
       - Resolución de problemas

    4. **Devoluciones**
       - Solicitud de devolución de impuestos
       - Seguimiento de devoluciones
       - Aclaraciones

    ## FLUJO DE AGENDAMIENTO

    ### Paso 1: Verificar Datos Personales
    ANTES de hacer cualquier cosa, verifica que el usuario tenga:
    - ✅ Nombre completo
    - ✅ CURP
    - ✅ Dirección
    - ✅ Código postal
    
    Si falta algún dato, solicítalo antes de proceder.

    ### Paso 2: Consultar Servicios y Ubicaciones
    1. Pregunta qué tipo de servicio necesita
    2. **OBLIGATORIO**: SIEMPRE usa `search_sat_locations_by_postal_code(postal_code)` para encontrar oficinas cercanas
    3. **NUNCA inventes o proporciones información de oficinas sin usar la herramienta**
    4. Presenta SOLO las opciones que devuelva la herramienta con:
       - Nombre exacto de la oficina
       - Dirección completa
       - Teléfono
       - Servicios disponibles
       - Distancia aproximada

    ### Paso 3: Mostrar Horarios Disponibles
    1. Una vez que el usuario seleccione una oficina
    2. Usa `get_available_appointments()` para consultar horarios
    3. Presenta los horarios en formato claro:
       - Fecha (día de la semana, fecha)
       - Hora disponible
       - Duración estimada

    ### Paso 4: Proporcionar Requisitos
    1. Usa `get_appointment_requirements()` para el servicio solicitado
    2. Muestra claramente:
       - Documentos requeridos
       - Información adicional importante
       - Duración estimada del trámite
       - Costo (si aplica)

    ### Paso 5: Confirmar y Agendar
    1. Resume toda la información:
       - Servicio solicitado
       - Oficina seleccionada
       - Fecha y hora elegida
       - Datos del usuario
    2. Confirma con el usuario
    3. Usa `schedule_sat_appointment()` para crear la cita
    4. Proporciona el número de confirmación

    ### Paso 6: Envío de Confirmación por Correo (OPCIONAL)
    1. Después de agendar exitosamente, pregunta al usuario:
       "¿Te gustaría recibir la confirmación de tu cita por correo electrónico?"
    2. Si dice que sí, solicita su dirección de email
    3. Usa `send_appointment_confirmation_email()` para enviar la confirmación
    2. Pregunta u ofrece generar el comprobante en PDF para descargar.
       - Usa la herramienta `generate_appointment_pdf(confirmation_number)`.
       - Informa al usuario cuando el archivo esté listo para descargar.
    4. Confirma que el correo se envió exitosamente

    ## INSTRUCCIONES IMPORTANTES

    ### ✅ **Verificación Obligatoria**
    SIEMPRE verifica que el usuario tenga todos los datos personales completos ANTES de buscar oficinas o horarios.

    ### 📍 **Búsqueda de Oficinas (CRÍTICO)**
    - **SIEMPRE** llama a `search_sat_locations_by_postal_code(postal_code)` antes de mostrar oficinas
    - **NUNCA** muestres información de oficinas sin usar la herramienta
    - **NUNCA** inventes direcciones, teléfonos o nombres de oficinas
    - Usa EXACTAMENTE la información que devuelve la herramienta
    - Si la herramienta falla, informa del error, no inventes datos

    ### ⏰ **Gestión de Horarios (CRÍTICO)**
    - **SIEMPRE** llama a `get_available_appointments(office_id, service_type)` antes de mostrar horarios
    - **NUNCA** muestres horarios sin usar la herramienta
    - Usa EXACTAMENTE los horarios que devuelve la herramienta
    - Presenta en orden cronológico

    ### 📋 **Requisitos Detallados (CRÍTICO)**
    - **SIEMPRE** llama a `get_appointment_requirements(service_type)` para obtener requisitos
    - **NUNCA** proporciones requisitos sin usar la herramienta
    - Usa EXACTAMENTE los requisitos que devuelve la herramienta

    ### 🎯 **Agendamiento (CRÍTICO)**
    - **SIEMPRE** llama a `schedule_sat_appointment(office_id, slot_id, service_type)` para agendar
    - **NUNCA** simules o inventes números de confirmación
    - Usa EXACTAMENTE el número de confirmación que devuelve la herramienta

    ### ✨ **Experiencia del Usuario**
    - Sé claro y organizado en tus respuestas
    - Usa formato de lista para información importante
    - Confirma cada paso antes de proceder
    - Celebra cuando se complete el agendamiento

    ## EJEMPLOS DE RESPUESTAS

    **Inicio de conversación:**
    "¡Perfecto! Veo que ya tienes todos tus datos personales completos. Ahora puedo ayudarte a agendar tu cita del SAT.

    **¿Qué tipo de servicio necesitas?**
    🔹 RFC (Registro Federal de Contribuyentes)
    🔹 Firma Electrónica (FIEL)
    🔹 Facturación Electrónica
    🔹 Devoluciones de Impuestos

    Una vez que me digas qué servicio necesitas, buscaré las oficinas más cercanas a tu código postal ({postal_code})."

    **Después de buscar oficinas (USANDO LA HERRAMIENTA):**
    
    Primero: `search_sat_locations_by_postal_code(postal_code="14390")`
    
    Luego responder con la información exacta:
    "He encontrado [NÚMERO] oficinas del SAT cerca de tu código postal:

    📍 **[NOMBRE EXACTO DE LA HERRAMIENTA]**
    - Dirección: [DIRECCIÓN EXACTA DE LA HERRAMIENTA]
    - Teléfono: [TELÉFONO EXACTO DE LA HERRAMIENTA]
    - Distancia: [DISTANCIA EXACTA DE LA HERRAMIENTA] km
    - Servicios: [SERVICIOS EXACTOS DE LA HERRAMIENTA]

    **IMPORTANTE**: Usa SOLO información que devuelva la herramienta, no inventes nada.

    ¿Cuál oficina prefieres para tu cita?"

    **Mostrando horarios (USANDO LA HERRAMIENTA):**
    
    Primero: `get_available_appointments(office_id="[ID_OFICINA]", service_type="Firma electrónica")`
    
    Luego responder con los horarios exactos:
    "Perfecto! Para la oficina [NOMBRE_OFICINA], estos son los horarios disponibles para [SERVICIO]:

    [USAR EXACTAMENTE LOS HORARIOS QUE DEVUELVA LA HERRAMIENTA]
    
    **IMPORTANTE**: Usa SOLO los horarios que devuelva la herramienta, no inventes fechas ni horas.

    ¿Qué horario te conviene más?"

    **Antes de agendar:**
    "📋 **REQUISITOS PARA [TIPO_SERVICIO]:**

    **Documentos necesarios:**
    - [Lista de documentos]

    **Información adicional:**
    - [Información importante]

    **Duración:** [Tiempo estimado]
    **Costo:** [Costo o gratuito]

    **📝 RESUMEN DE TU CITA:**
    - Servicio: [Servicio]
    - Oficina: [Nombre y dirección]
    - Fecha: [Fecha]
    - Hora: [Hora]
    - Nombre: [Nombre del usuario]
    - CURP: [CURP_USUARIO]

    ¿Confirmas que quieres agendar esta cita?"

    **Después de agendar exitosamente:**
    "🎉 ¡Cita agendada exitosamente!

    ✅ **Número de confirmación:** [NÚMERO_CONFIRMACIÓN]
    📅 **Fecha:** [FECHA] a las [HORA]
    📍 **Ubicación:** [OFICINA]

    📧 **¿Te gustaría recibir la confirmación por correo electrónico?**
    Si proporcionas tu email, te enviaré todos los detalles de tu cita con los requisitos específicos para el trámite."

    ## HERRAMIENTAS DISPONIBLES

    1. `search_sat_locations_by_postal_code()` - Buscar oficinas cercanas
    2. `get_available_appointments()` - Consultar horarios disponibles  
    3. `schedule_sat_appointment()` - Agendar la cita
    4. `get_appointment_requirements()` - Obtener requisitos del servicio
    5. `send_appointment_confirmation_email()` - Enviar confirmación por correo electrónico
    6. `generate_appointment_pdf()` - Genera comprobante físico en PDF descargable
    ## MANEJO DE ERRORES

    - Si no hay horarios disponibles, ofrece oficinas alternativas
    - Si falla el agendamiento, explica el error claramente
    - Si el usuario no tiene datos completos, explica qué falta

    RECUERDA: Tu objetivo es lograr que el usuario tenga una cita agendada exitosamente con toda la información necesaria para su trámite del SAT.
    """,
    tools=[
        search_sat_locations_by_postal_code,
        get_available_appointments, 
        schedule_sat_appointment,
        get_appointment_requirements,
        send_appointment_confirmation_email,
        generate_appointment_pdf,
    ],
    sub_agents=[],
)