from datetime import datetime, timedelta
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
import random
from typing import List, Dict


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


def schedule_sat_appointment(tool_context: ToolContext, office_id: str, slot_id: str, service_type: str) -> dict:
    """
    Agenda una cita en el SAT con la información personal del usuario.
    
    Args:
        tool_context: Contexto de la herramienta
        office_id: ID de la oficina del SAT
        slot_id: ID del horario seleccionado
        service_type: Tipo de servicio solicitado
    """
    # Verificar que tengamos todos los datos personales requeridos
    required_fields = ["full_name", "curp", "address", "postal_code"]
    missing_fields = []
    
    for field in required_fields:
        if field not in tool_context.state or not tool_context.state[field]:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            "status": "error",
            "message": f"Faltan datos personales requeridos: {', '.join(missing_fields)}",
            "missing_fields": missing_fields
        }
    
    # Buscar el slot específico
    available_slots = tool_context.state.get("available_appointments", [])
    selected_slot = None
    for slot in available_slots:
        if slot["slot_id"] == slot_id:
            selected_slot = slot
            break
    
    if not selected_slot:
        return {
            "status": "error", 
            "message": "El horario seleccionado no está disponible"
        }
    
    # Buscar información de la oficina
    sat_locations = tool_context.state.get("sat_locations", [])
    selected_office = None
    for office in sat_locations:
        if office["id"] == office_id:
            selected_office = office
            break
    
    if not selected_office:
        return {
            "status": "error",
            "message": "Oficina no encontrada"
        }
    
    # Generar número de confirmación
    confirmation_number = f"SAT{random.randint(100000, 999999)}"
    
    # Crear objeto de cita
    appointment = {
        "confirmation_number": confirmation_number,
        "service_type": service_type,
        "date": selected_slot["date"],
        "time": selected_slot["time"],
        "office": selected_office,
        "user_info": {
            "full_name": tool_context.state["full_name"],
            "curp": tool_context.state["curp"], 
            "address": tool_context.state["address"],
            "postal_code": tool_context.state["postal_code"],
            "phone": tool_context.state.get("phone", ""),
            "email": tool_context.state.get("email", "")
        },
        "status": "confirmed",
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Guardar cita en el estado
    current_appointments = tool_context.state.get("appointments", [])
    updated_appointments = current_appointments.copy()
    updated_appointments.append(appointment)
    tool_context.state["appointments"] = updated_appointments
    
    # Actualizar historial
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "schedule_appointment",
        "confirmation_number": confirmation_number,
        "service_type": service_type,
        "date": selected_slot["date"],
        "time": selected_slot["time"],
        "office_name": selected_office["name"],
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "appointment": appointment,
        "confirmation_number": confirmation_number,
        "message": f"¡Cita agendada exitosamente! Número de confirmación: {confirmation_number}"
    }


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
    2. Usa `search_sat_locations_by_postal_code()` para encontrar oficinas cercanas
    3. Presenta las opciones de ubicación disponibles con:
       - Nombre de la oficina
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

    ## INSTRUCCIONES IMPORTANTES

    ### ✅ **Verificación Obligatoria**
    SIEMPRE verifica que el usuario tenga todos los datos personales completos ANTES de buscar oficinas o horarios.

    ### 📍 **Búsqueda de Oficinas**
    - Usa el código postal del usuario para encontrar oficinas cercanas
    - Presenta TODAS las opciones disponibles
    - Incluye distancia y servicios disponibles en cada oficina

    ### ⏰ **Gestión de Horarios**
    - Muestra horarios en orden cronológico
    - Indica claramente día de la semana y fecha
    - Menciona duración estimada del trámite

    ### 📋 **Requisitos Detallados**
    - SIEMPRE proporciona la lista completa de requisitos
    - Explica documentos necesarios en términos claros
    - Menciona información adicional importante

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

    **Después de buscar oficinas:**
    "He encontrado [NÚMERO] oficinas del SAT cerca de tu código postal:

    📍 **Oficina 1: [Nombre]**
    - Dirección: [Dirección completa]
    - Teléfono: [Teléfono]
    - Distancia: [DISTANCIA] km
    - Servicios: [Lista de servicios]

    📍 **Oficina 2: [Nombre]**
    [Misma información...]

    ¿Cuál oficina prefieres para tu cita?"

    **Mostrando horarios:**
    "Perfecto! Para la oficina [Nombre], estos son los horarios disponibles para [Servicio]:

    📅 **Esta semana:**
    - Jueves 28 Nov - 10:00 AM, 2:00 PM
    - Viernes 29 Nov - 9:00 AM, 11:00 AM, 3:00 PM

    📅 **Próxima semana:**
    - Lunes 2 Dic - 9:00 AM, 12:00 PM, 2:00 PM
    [...]

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

    ## HERRAMIENTAS DISPONIBLES

    1. `search_sat_locations_by_postal_code()` - Buscar oficinas cercanas
    2. `get_available_appointments()` - Consultar horarios disponibles  
    3. `schedule_sat_appointment()` - Agendar la cita
    4. `get_appointment_requirements()` - Obtener requisitos del servicio

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
        get_appointment_requirements
    ],
    sub_agents=[],
)