import os
import random
import sqlite3
import smtplib
from datetime import datetime, timedelta
from typing import List, Dict, Optional # <--- IMPORTANTE: Optional es necesario

# --- IMPORTS DE CORREO Y PDF ---
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
try:
    from reportlab.pdfgen import canvas
    from reportlab.lib.pagesizes import letter
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


def send_appointment_confirmation_email(
    tool_context: ToolContext, 
    to_email: str, 
    attachment_path: Optional[str] = None
) -> dict:
    """
    Envía un correo con los detalles de la cita (Fecha, Hora, Nombre) obtenidos del estado
    y adjunta el PDF si se proporciona.
    """
    # 1. RECUPERAR DATOS DEL ESTADO (Memoria)
    # Buscamos el nombre
    user_info = tool_context.state.get("user_info", {})
    user_name = user_info.get("full_name", "Contribuyente")

    # Buscamos la última cita agendada para sacar fecha y hora
    appointments = tool_context.state.get("appointments", [])
    if appointments:
        # Tomamos la última de la lista
        last_appt = appointments[-1]
        appt_date = last_appt.get("date", "Fecha pendiente")
        appt_time = last_appt.get("time", "--:--")
        appt_office = last_appt.get("office", {}).get("name", "Oficina SAT")
        service = last_appt.get("service_type", "Trámite")
    else:
        # Valores por defecto si no hay cita en memoria
        appt_date = "N/A"
        appt_time = "N/A"
        appt_office = "Oficina SAT"
        service = "General"

    # 2. CONFIGURACIÓN (Simulada o Real)
    sender_email = "tu_correo_simulado@gmail.com" 
    sender_password = "tu_contraseña"
    
    # MODO SIMULACIÓN (Si no tienes credenciales reales)
    if "simulado" in sender_email:
        print(f"\n📧 [SIMULACIÓN DE CORREO]")
        print(f"   De: SAT Virtual")
        print(f"   Para: {to_email}")
        print(f"   Asunto: Confirmación de Cita - {user_name}")
        print(f"   Mensaje:")
        print(f"     Hola {user_name},")
        print(f"     Tu cita está confirmada para el {appt_date} a las {appt_time}.")
        if attachment_path:
            print(f"   📎 Adjunto incluido: {attachment_path}")
        print("-" * 30)
        return {"status": "success", "message": f"Correo simulado enviado a {to_email} con los datos de la cita."}

    try:
        # 3. CONSTRUIR EL CORREO REAL
        msg = MIMEMultipart()
        msg['From'] = sender_email
        msg['To'] = to_email
        msg['Subject'] = f"Confirmación de Cita SAT - {appt_date}"

        # --- AQUÍ ESTÁ EL CAMBIO DEL BODY ---
        body = f"""
        Estimado/a Contribuyente,
        
        Le confirmamos que su cita ha sido agendada exitosamente.
        
        Detalles del servicio:
        -----------------------------------
        Contribuyente: {user_name}
        📅 Fecha:   {appt_date}
        ⏰ Hora:    {appt_time}
        📍 Lugar:   {appt_office}
        📋 Trámite: {service}
        -----------------------------------
        
        Adjunto encontrará su comprobante oficial en PDF.
        Por favor preséntese 10 minutos antes con su identificación oficial.
        
        Atentamente,
        Servicio de Administración Tributaria
        """
        msg.attach(MIMEText(body, 'plain'))

        # 4. ADJUNTAR PDF
        if attachment_path:
            if os.path.exists(attachment_path):
                with open(attachment_path, "rb") as f:
                    part = MIMEApplication(f.read(), Name=os.path.basename(attachment_path))
                part['Content-Disposition'] = f'attachment; filename="{os.path.basename(attachment_path)}"'
                msg.attach(part)
            else:
                return {"status": "error", "message": f"No encontré el archivo adjunto: {attachment_path}"}

        # 5. ENVIAR
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()
        server.login(sender_email, sender_password)
        server.send_message(msg)
        server.quit()

        return {"status": "success", "message": f"Correo enviado a {to_email} con fecha y hora."}

    except Exception as e:
        return {"status": "error", "message": f"Error enviando correo: {str(e)}"}    

def generate_appointment_pdf(tool_context: ToolContext, confirmation_number: str) -> dict:
    """
    Genera el PDF tomando los datos del usuario directamente del STATE global,
    sin importar dónde se guardó la cita.
    """
    try:
        from reportlab.pdfgen import canvas
        from reportlab.lib.pagesizes import letter
    except ImportError:
        return {"status": "error", "message": "Falta reportlab."}

    # 1. RECUPERAR DATOS DEL USUARIO DIRECTAMENTE DEL STATE
    # No buscamos dentro de la cita, vamos a la memoria global de la sesión.
    state_user_info = tool_context.state.get("user_info", {})
    
    # Extraemos con valores por defecto por si algo falta
    user_name = state_user_info.get("full_name", "Usuario Genérico")
    user_curp = state_user_info.get("curp", "SIN DATO")

    # 2. RECUPERAR DETALLES DE LA CITA
    # Buscamos la cita solo para obtener fecha, hora y oficina
    clean_confirmation = confirmation_number.strip()
    appointments = tool_context.state.get("appointments", [])
    appointment = next((a for a in appointments if a.get("confirmation_number") == clean_confirmation), None)
    
    if not appointment:
        return {"status": "error", "message": "Cita no encontrada en memoria temporal."}

    filename = f"Cita_SAT_{clean_confirmation}.pdf"
    
    try:
        c = canvas.Canvas(filename, pagesize=letter)
        
        # Título
        c.setFont("Helvetica-Bold", 18)
        c.drawString(50, 750, f"CITA SAT: {clean_confirmation}")
        
        # DATOS DEL USUARIO (Sacados del state global)
        c.setFont("Helvetica", 12)
        c.drawString(50, 720, f"Nombre del Contribuyente: {user_name}")
        c.drawString(50, 700, f"CURP: {user_curp}")
        
        # DATOS DE LA CITA
        c.drawString(50, 670, f"Trámite: {appointment.get('service_type', 'General')}")
        c.drawString(50, 650, f"Fecha: {appointment.get('date')} - Hora: {appointment.get('time')}")
        c.drawString(50, 630, f"Oficina: {appointment.get('office_name', appointment.get('office', {}).get('name', 'SAT'))}")
        
        c.save()

        # Ruta absoluta para que la encuentres
        abs_path = os.path.abspath(filename)
        
        return {
            "status": "success", 
            "message": "PDF Generado con datos del State.", 
            "file_path": abs_path,
            "note": f"Archivo guardado en: {abs_path}"
        }
    except Exception as e:
        return {"status": "error", "message": str(e)}
    

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