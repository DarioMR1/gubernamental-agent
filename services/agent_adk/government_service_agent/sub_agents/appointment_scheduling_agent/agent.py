from datetime import datetime, timedelta
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import random
from typing import List, Dict
import sqlite3
import os
from dotenv import load_dotenv

# Cargar variables de entorno
load_dotenv()

def init_db():
    """Inicializa la base de datos SQLite para las citas."""
    conn = sqlite3.connect('citas_sat.db')
    cursor = conn.cursor()
    # Creamos una tabla si no existe
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


def get_available_appointments(tool_context: ToolContext, office_id: str, service_type: str = "RFC") -> dict:
    """
    Consulta horarios disponibles para una oficina específica del SAT.
    
    Args:
        tool_context: Contexto de la herramienta
        office_id: ID de la oficina del SAT
        service_type: Tipo de servicio (RFC, Firma electrónica, etc.)
    """
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


def send_appointment_confirmation_email(tool_context: ToolContext, email: str, confirmation_number: str) -> dict:
    """
    Envía un correo de confirmación de cita usando Resend API.
    
    Args:
        tool_context: Contexto de la herramienta
        email: Dirección de correo electrónico del usuario
        confirmation_number: Número de confirmación de la cita
    """
    try:
        import resend
    except ImportError:
        return {
            "status": "error",
            "message": "La librería resend no está instalada. Instala con: pip install resend"
        }
    
    # Buscar la cita por número de confirmación
    appointments = tool_context.state.get("appointments", [])
    appointment = None
    for apt in appointments:
        if apt.get("confirmation_number") == confirmation_number:
            appointment = apt
            break
    
    if not appointment:
        return {
            "status": "error",
            "message": f"No se encontró la cita con número de confirmación: {confirmation_number}"
        }
    
    # Configurar API key de Resend
    resend_api_key = os.getenv("RESEND_API_KEY")
    if not resend_api_key:
        return {
            "status": "error",
            "message": "RESEND_API_KEY no está configurada en las variables de entorno"
        }
    
    resend.api_key = resend_api_key
    
    # Obtener información del usuario y la cita
    user_name = appointment["user_info"]["full_name"]
    service_type = appointment["service_type"]
    date = appointment["date"]
    time = appointment["time"]
    office_name = appointment["office"]["name"]
    office_address = appointment["office"]["address"]
    office_phone = appointment["office"]["phone"]
    
    # Formatear fecha en español
    try:
        date_obj = datetime.strptime(date, "%Y-%m-%d")
        formatted_date = date_obj.strftime("%d de %B de %Y")
        day_name = date_obj.strftime("%A")
        
        # Traducir al español
        day_names = {
            "Monday": "Lunes", "Tuesday": "Martes", "Wednesday": "Miércoles",
            "Thursday": "Jueves", "Friday": "Viernes", "Saturday": "Sábado", "Sunday": "Domingo"
        }
        month_names = {
            "January": "enero", "February": "febrero", "March": "marzo", "April": "abril",
            "May": "mayo", "June": "junio", "July": "julio", "August": "agosto",
            "September": "septiembre", "October": "octubre", "November": "noviembre", "December": "diciembre"
        }
        
        for eng, esp in day_names.items():
            day_name = day_name.replace(eng, esp)
        for eng, esp in month_names.items():
            formatted_date = formatted_date.replace(eng, esp)
            
    except:
        formatted_date = date
        day_name = "N/A"
    
    # Crear contenido HTML del correo
    html_content = f"""
    <!DOCTYPE html>
    <html lang="es">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Confirmación de Cita - SAT</title>
        <style>
            body {{
                font-family: 'Segoe UI', Arial, sans-serif;
                line-height: 1.6;
                color: #333;
                margin: 0;
                padding: 0;
                background-color: #f5f7fa;
            }}
            .container {{
                max-width: 600px;
                margin: 0 auto;
                background-color: #ffffff;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            }}
            .header {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 30px 20px;
                text-align: center;
            }}
            .header h1 {{
                margin: 0;
                font-size: 28px;
                font-weight: 600;
            }}
            .header p {{
                margin: 10px 0 0 0;
                font-size: 16px;
                opacity: 0.9;
            }}
            .content {{
                padding: 30px 20px;
            }}
            .greeting {{
                font-size: 18px;
                margin-bottom: 20px;
                color: #2d3748;
            }}
            .confirmation-box {{
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                padding: 20px;
                border-radius: 10px;
                text-align: center;
                margin: 25px 0;
            }}
            .confirmation-number {{
                font-size: 24px;
                font-weight: 700;
                margin: 10px 0;
                letter-spacing: 2px;
                background: rgba(255,255,255,0.2);
                padding: 10px 15px;
                border-radius: 5px;
                display: inline-block;
            }}
            .info-section {{
                background-color: #f8fafc;
                border-left: 4px solid #667eea;
                padding: 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }}
            .info-section h3 {{
                color: #2d3748;
                margin-top: 0;
                font-size: 18px;
                border-bottom: 2px solid #e2e8f0;
                padding-bottom: 10px;
            }}
            .detail-item {{
                margin: 12px 0;
                display: flex;
                align-items: flex-start;
            }}
            .detail-label {{
                font-weight: 600;
                color: #4a5568;
                min-width: 120px;
                margin-right: 10px;
            }}
            .detail-value {{
                color: #2d3748;
                flex: 1;
            }}
            .requirements {{
                background-color: #fff8e1;
                border-left: 4px solid #ff9800;
                padding: 20px;
                margin: 20px 0;
                border-radius: 0 8px 8px 0;
            }}
            .requirements h3 {{
                color: #e65100;
                margin-top: 0;
                font-size: 18px;
            }}
            .requirements ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .requirements li {{
                margin: 8px 0;
                color: #bf360c;
            }}
            .important-notes {{
                background-color: #e8f5e8;
                border: 1px solid #4caf50;
                border-radius: 8px;
                padding: 20px;
                margin: 20px 0;
            }}
            .important-notes h3 {{
                color: #2e7d32;
                margin-top: 0;
                font-size: 18px;
            }}
            .important-notes ul {{
                margin: 10px 0;
                padding-left: 20px;
            }}
            .important-notes li {{
                margin: 8px 0;
                color: #388e3c;
            }}
            .footer {{
                background-color: #2d3748;
                color: #a0aec0;
                text-align: center;
                padding: 30px 20px;
                font-size: 14px;
            }}
            .footer p {{
                margin: 5px 0;
            }}
            .highlight {{
                background-color: #667eea;
                color: white;
                padding: 2px 6px;
                border-radius: 4px;
                font-weight: 600;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🏛️ SAT - Confirmación de Cita</h1>
                <p>Servicio de Administración Tributaria</p>
            </div>
            
            <div class="content">
                <div class="greeting">
                    Estimado(a) <strong>{user_name}</strong>,
                </div>
                
                <p>Su cita para el trámite de <strong>{service_type}</strong> ha sido agendada exitosamente en el SAT.</p>
                
                <div class="confirmation-box">
                    <h3 style="margin: 0; font-size: 18px;">Número de Confirmación</h3>
                    <div class="confirmation-number">{confirmation_number}</div>
                    <p style="margin: 10px 0 0 0; opacity: 0.9;">Guarde este número para futuras referencias</p>
                </div>
                
                <div class="info-section">
                    <h3>📅 Detalles de su Cita</h3>
                    <div class="detail-item">
                        <div class="detail-label">Servicio:</div>
                        <div class="detail-value"><span class="highlight">{service_type}</span></div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Fecha:</div>
                        <div class="detail-value">{day_name}, {formatted_date}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Hora:</div>
                        <div class="detail-value">{time} hrs</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Oficina:</div>
                        <div class="detail-value">{office_name}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Dirección:</div>
                        <div class="detail-value">{office_address}</div>
                    </div>
                    <div class="detail-item">
                        <div class="detail-label">Teléfono:</div>
                        <div class="detail-value">{office_phone}</div>
                    </div>
                </div>
                
                <div class="requirements">
                    <h3>📄 Documentos Requeridos</h3>
                    <p><strong>Para el trámite de {service_type}, debe presentar:</strong></p>
                    <ul>
                        <li>Identificación oficial vigente (INE/Pasaporte)</li>
                        <li>CURP actualizada</li>
                        <li>Comprobante de domicilio (no mayor a 3 meses)</li>
                        <li>Documentación específica según el trámite solicitado</li>
                    </ul>
                </div>
                
                <div class="important-notes">
                    <h3>⚠️ Información Importante</h3>
                    <ul>
                        <li><strong>Llegue 15 minutos antes</strong> de su cita programada</li>
                        <li>Traiga <strong>todos los documentos originales</strong> y copias</li>
                        <li>Su número de confirmación es: <strong>{confirmation_number}</strong></li>
                        <li>Las citas no utilizadas <strong>NO se reprograman automáticamente</strong></li>
                        <li>Para cancelar o reprogramar, contacte la oficina con anticipación</li>
                    </ul>
                </div>
                
                <p style="margin-top: 30px; color: #4a5568;">
                    Si tiene alguna pregunta, puede comunicarse directamente a la oficina del SAT al teléfono <strong>{office_phone}</strong>.
                </p>
            </div>
            
            <div class="footer">
                <p><strong>Gobierno Digital - Sistema de Citas SAT</strong></p>
                <p>Este correo fue generado automáticamente. Por favor no responda a este mensaje.</p>
                <p>Para soporte técnico, visite: <strong>sat.gob.mx</strong></p>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Configurar parámetros del correo
    from_email = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <notifications@diperion.com>")
    subject = f"Confirmación de Cita SAT - {service_type} ({confirmation_number})"
    
    params = {
        "from": from_email,
        "to": [email],
        "subject": subject,
        "html": html_content,
    }
    
    try:
        # Enviar el correo
        result = resend.Emails.send(params)
        
        # Actualizar el historial de interacciones
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        current_history = tool_context.state.get("interaction_history", [])
        new_history = current_history.copy()
        new_history.append({
            "action": "email_sent",
            "email": email,
            "confirmation_number": confirmation_number,
            "service_type": service_type,
            "email_id": result.get("id"),
            "timestamp": current_time
        })
        tool_context.state["interaction_history"] = new_history
        
        return {
            "status": "success",
            "message": f"Confirmación de cita enviada exitosamente a {email}",
            "email_id": result.get("id"),
            "confirmation_number": confirmation_number
        }
        
    except Exception as e:
        return {
            "status": "error",
            "message": f"Error al enviar el correo: {str(e)}"
        }
    

def generate_appointment_pdf(tool_context: ToolContext, confirmation_number: str) -> dict:
    """
    Genera un PDF robusto. Si faltan datos, usa valores por defecto en lugar de fallar.
    """
    print(f"--- 📄 INTENTANDO GENERAR PDF PARA: {confirmation_number} ---")

    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
    except ImportError:
        return {"status": "error", "message": "Falta librería 'reportlab'. Ejecuta: pip install reportlab"}

    # 1. BUSCAR LA CITA EN EL ESTADO
    # A veces el número viene con espacios extra, los limpiamos
    clean_confirmation = confirmation_number.strip()
    
    appointments = tool_context.state.get("appointments", [])
    appointment = None
    
    # Búsqueda manual para ver qué tenemos
    print(f"    🔍 Buscando en {len(appointments)} citas registradas en memoria...")
    for apt in appointments:
        # Imprimimos para depurar
        print(f"       - Comparando con: {apt.get('confirmation_number')}")
        if apt.get("confirmation_number") == clean_confirmation:
            appointment = apt
            break
    
    if not appointment:
        print("    ❌ Error: No se encontró el folio en la memoria de la sesión.")
        return {"status": "error", "message": f"No encontré la cita {clean_confirmation} en mis registros momentáneos."}

    # 2. OBTENER DATOS DE FORMA SEGURA (USANDO .get PARA EVITAR ERRORES)
    # Si user_info está vacío, usamos diccionarios vacíos por defecto
    user = appointment.get("user_info", {}) or {}
    office = appointment.get("office", {}) or {}
    
    # Datos con valores por defecto (Esto evita que el código truene si falta algo)
    full_name = user.get("full_name", "Usuario no registrado")
    curp = user.get("curp", "N/A")
    email = user.get("email", "N/A")
    
    service_type = appointment.get("service_type", "Trámite General")
    date_str = appointment.get("date", "Fecha pendiente")
    time_str = appointment.get("time", "--:--")
    
    office_name = office.get("name", "Oficina SAT")
    office_address = office.get("address", "Dirección no disponible")

    filename = f"Cita_SAT_{clean_confirmation}.pdf"
    
    try:
        # 3. DIBUJAR EL PDF
        c = canvas.Canvas(filename, pagesize=letter)
        width, height = letter

        # Encabezado
        c.setFillColor(colors.darkblue)
        c.setFont("Helvetica-Bold", 20)
        c.drawString(50, height - 50, "Comprobante de Cita SAT")
        
        c.setFillColor(colors.black)
        c.setFont("Helvetica", 10)
        c.drawString(50, height - 70, "Sistema de Citas Automatizado")
        c.drawString(50, height - 85, f"Emisión: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
        c.line(50, height - 95, width - 50, height - 95)

        # Cuerpo
        y = height - 130
        
        # Sección Cita
        c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "Detalles de la Cita")
        y -= 25
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Folio: {clean_confirmation}")
        y -= 20
        c.drawString(50, y, f"Trámite: {service_type}")
        y -= 20
        c.drawString(50, y, f"Cuándo: {date_str} a las {time_str}")
        y -= 40

        # Sección Usuario
        c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "Solicitante")
        y -= 25
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Nombre: {full_name}")
        y -= 20
        c.drawString(50, y, f"CURP: {curp}")
        y -= 40

        # Sección Ubicación
        c.setFont("Helvetica-Bold", 14); c.drawString(50, y, "Lugar")
        y -= 25
        c.setFont("Helvetica", 12)
        c.drawString(50, y, f"Sede: {office_name}")
        y -= 20
        c.setFont("Helvetica", 10)
        c.drawString(50, y, f"Dir: {office_address}")

        c.save()
        print(f"    ✅ PDF creado exitosamente: {filename}")

        abs_path = os.path.abspath(filename)

        return {
            "status": "success",
            "message": "PDF Generado.",
            "file_name": filename,
            "download_link": f"[{filename}](file:///{abs_path})", 
            "note": "Usa la herramienta 'send_email_with_pdf' para enviarlo."
        }
    except Exception as e:
        print(f"    🔥 Error dibujando PDF: {e}")
        return {"status": "error", "message": f"Error interno al dibujar PDF: {str(e)}"}

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