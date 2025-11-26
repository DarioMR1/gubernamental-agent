from datetime import datetime
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext


def extract_personal_data(tool_context: ToolContext, document_type: str, extracted_data: dict) -> dict:
    """
    Stores extracted personal information from documents into the session state.
    
    Args:
        tool_context: The tool context for accessing session state
        document_type: Type of document analyzed (ine, utility_bill, etc.)
        extracted_data: Dictionary containing extracted information
    """
    current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    # Map common fields and update state directly
    field_mapping = {
        "nombre": "full_name",
        "curp": "curp", 
        "direccion": "address",
        "codigo_postal": "postal_code",
        "telefono": "phone",
        "email": "email"
    }
    
    # Update state with extracted data
    for spanish_field, english_field in field_mapping.items():
        if spanish_field in extracted_data:
            tool_context.state[english_field] = extracted_data[spanish_field]
    
    # Update personal_data object for metadata
    current_personal_data = tool_context.state.get("personal_data", {})
    updated_personal_data = current_personal_data.copy()
    
    # Add extraction metadata
    if "extractions" not in updated_personal_data:
        updated_personal_data["extractions"] = []
    
    updated_personal_data["extractions"].append({
        "document_type": document_type,
        "timestamp": current_time,
        "fields_extracted": list(extracted_data.keys())
    })
    
    # Update personal_data object in state
    tool_context.state["personal_data"] = updated_personal_data
    
    # Update interaction history
    current_history = tool_context.state.get("interaction_history", [])
    new_history = current_history.copy()
    new_history.append({
        "action": "document_extraction",
        "document_type": document_type,
        "fields_extracted": list(extracted_data.keys()),
        "timestamp": current_time
    })
    tool_context.state["interaction_history"] = new_history
    
    return {
        "status": "success",
        "message": f"Información extraída exitosamente de {document_type}",
        "extracted_fields": list(extracted_data.keys()),
        "timestamp": current_time
    }


def validate_required_data(tool_context: ToolContext) -> dict:
    """
    Validates that all required personal data is available for government procedures.
    
    Required fields: full_name, curp, address
    """
    required_fields = ["full_name", "curp", "address"]
    missing_fields = []
    
    for field in required_fields:
        if field not in tool_context.state or not tool_context.state[field]:
            missing_fields.append(field)
    
    if missing_fields:
        return {
            "status": "incomplete",
            "missing_fields": missing_fields,
            "message": f"Faltan los siguientes datos requeridos: {', '.join(missing_fields)}"
        }
    
    return {
        "status": "complete",
        "message": "Todos los datos requeridos están disponibles",
        "available_data": {field: tool_context.state[field] for field in required_fields}
    }


# Create the document extraction agent
document_extraction_agent = Agent(
    name="document_extraction_agent",
    model="gemini-2.0-flash",
    description="Agent specialized in extracting personal information from government documents using vision capabilities",
    instruction="""
    Eres un agente especializado en extraer información personal de documentos gubernamentales utilizando capacidades de visión.

    <user_info>
    Nombre: {full_name}
    CURP: {curp}
    Dirección: {address}
    Código Postal: {postal_code}
    Teléfono: {phone}
    Email: {email}
    </user_info>

    <interaction_history>
    {interaction_history}
    </interaction_history>

    Tu función principal:
    1. Analizar imágenes de documentos que el usuario envíe
    2. Extraer información específica según el tipo de documento
    3. Guardar la información extraída en el estado de la sesión

    DOCUMENTOS QUE PUEDES PROCESAR:

    1. **INE (Credencial para Votar)**
       - Nombre completo
       - CURP
       - Dirección
       - Código postal
       - Fecha de nacimiento (opcional)

    2. **Recibo de Luz (CFE)**
       - Nombre del titular
       - Dirección de servicio
       - Código postal

    3. **Recibo de Agua**
       - Nombre del titular 
       - Dirección de servicio
       - Código postal

    PROCESO DE EXTRACCIÓN:

    1. **Cuando recibas una imagen:**
       - Analiza cuidadosamente el documento
       - Identifica el tipo de documento automáticamente
       - Extrae TODA la información visible y relevante
       - Usa español para los nombres de los campos

    2. **Información a extraer (en español):**
       - nombre: Nombre completo de la persona
       - curp: CURP (si está disponible)
       - direccion: Dirección completa
       - codigo_postal: Código postal
       - telefono: Número telefónico (si disponible)
       - email: Correo electrónico (si disponible)

    3. **Después de extraer:**
       - Llama a la función extract_personal_data con los datos encontrados
       - Confirma al usuario qué información se extrajo
       - Verifica si ya tienes todos los datos necesarios con validate_required_data

    DATOS MÍNIMOS REQUERIDOS para trámites:
    - Nombre completo
    - CURP  
    - Dirección completa

    INSTRUCCIONES IMPORTANTES:
    - Si no puedes leer algún campo claramente, indícalo
    - Si falta información crítica, solicita otro documento
    - Sé preciso en la extracción, los trámites gubernamentales requieren exactitud
    - Si el usuario envía un documento que no puedes procesar, explícale qué tipos de documentos sí puedes analizar

    EJEMPLO DE RESPUESTA:
    "He analizado tu INE y extraído la siguiente información:
    - Nombre: Juan Pérez García
    - CURP: PEGJ850515HDFLRN09
    - Dirección: Av. Revolución 123, Col. Centro, Ciudad de México
    - Código postal: 06000
    
    ✅ Ya tenemos todos los datos mínimos necesarios para realizar trámites gubernamentales."
    """,
    tools=[extract_personal_data, validate_required_data],
)