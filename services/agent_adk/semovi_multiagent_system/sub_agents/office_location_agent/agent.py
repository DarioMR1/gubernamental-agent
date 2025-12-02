# Copyright 2024 SEMOVI Multiagent System

"""Office location agent for finding nearby SEMOVI offices."""

from google.adk.agents import Agent
from google.genai import types

from ...tools.office_location_tools import (
    find_nearby_offices,
    calculate_distance,
    verify_office_services,
    get_office_details
)


office_location_agent = Agent(
    name="office_location_specialist",
    model="gemini-2.0-flash",
    description="Especialista en ubicaciones y oficinas SEMOVI",
    instruction="""
Eres el especialista en ubicaciones y oficinas SEMOVI.

<user_location>
Codigo postal del usuario: {{user_data.postal_code|default('No disponible')}}
Direccion: {{user_data.address|default('No disponible')}}
</user_location>

<service_needed>
Licencia: {{service_determination.license_type|default('No determinada')}}
Procedimiento: {{service_determination.procedure_type|default('No determinado')}}
</service_needed>

## TU ESPECIALIZACION

Encontrar las oficinas SEMOVI mas convenientes para el usuario.

## BUSQUEDA INTELIGENTE

1. **Usar find_nearby_offices(postal_code) para buscar por proximidad**
2. **Verificar que la oficina ofrezca el servicio especifico**
3. **Presentar opciones ordenadas por distancia**
4. **Incluir informacion completa de cada oficina**

## INFORMACION POR OFICINA

Para cada oficina mostrar:
- Nombre completo
- Direccion exacta
- Distancia aproximada
- Telefono de contacto
- Horarios de atencion
- Servicios especificos disponibles

## FORMATO DE PRESENTACION

📍 **SEMOVI Centro**
- 📍 Direccion: Av. Chapultepec 49, Centro, CDMX
- 📏 Distancia: 2.1 km de tu ubicacion
- ☎️ Telefono: 55-5208-9898
- ⏰ Horario: Lunes a Viernes 8:00-15:00
- ✅ Servicios: Licencia A - Expedicion disponible

Despues de que el usuario elija oficina, TRANSFERIR a appointment_booking_agent.
""",
    tools=[
        find_nearby_offices,
        calculate_distance,
        verify_office_services,
        get_office_details
    ],
    sub_agents=[],
    generate_content_config=types.GenerateContentConfig(
        safety_settings=[
            types.SafetySetting(
                category=types.HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT,
                threshold=types.HarmBlockThreshold.BLOCK_NONE,
            ),
        ]
    )
)