# Arquitectura del Sistema de Licencias SEMOVI

## Sistema Multiagente para Trámites de Licencias de Conducir

### 📋 Tabla de Contenidos
1. [Visión General del Sistema](#visión-general-del-sistema)
2. [Arquitectura de Agentes](#arquitectura-de-agentes)
3. [Flujo de Usuario Completo](#flujo-de-usuario-completo)
4. [Agente Coordinador](#agente-coordinador)
5. [Agentes Especialistas](#agentes-especialistas)
6. [Herramientas del Sistema](#herramientas-del-sistema)
7. [Integración con Supabase](#integración-con-supabase)
8. [Estado Compartido](#estado-compartido)
9. [Casos de Uso Específicos](#casos-de-uso-específicos)

---

## Visión General del Sistema

### Propósito
Sistema inteligente que automatiza completamente el proceso de agendamiento de citas para trámites de licencias de conducir en SEMOVI, desde la captura de datos del INE hasta la confirmación de la cita.

### Servicios Soportados
- **Licencias Tipo A**: Automóviles particulares y motocicletas hasta 400cc
- **Licencias Tipo A1**: Motocicletas de 125cc hasta 400cc  
- **Licencias Tipo A2**: Motocicletas mayores a 400cc

### Procedimientos Disponibles
- **Expedición**: Primera vez (incluye examen y curso)
- **Renovación**: Licencia vencida o próxima a vencer
- **Reposición**: Por robo, extravío o deterioro

### Capacidades Clave
- ✅ **Extracción automática de datos** del INE con Google Vision
- ✅ **Determinación inteligente** del tipo de licencia requerida
- ✅ **Búsqueda de oficinas** por proximidad geográfica
- ✅ **Agendamiento en tiempo real** con verificación de disponibilidad
- ✅ **Cálculo automático** de costos y requisitos
- ✅ **Confirmación multimedia** (email, PDF, SMS)

---

## Arquitectura de Agentes

### Patrón Arquitectónico: Coordinador + Especialistas

```
┌─────────────────────────────────────┐
│        SEMOVI_COORDINATOR           │ ← Agente principal que maneja el flujo
│   (Gestión del proceso completo)    │
└─────────────┬───────────────────────┘
              │
              ├─── INE_EXTRACTION_AGENT (Google Vision + Validación)
              ├─── LICENSE_CONSULTATION_AGENT (Requisitos + Costos)  
              ├─── OFFICE_LOCATION_AGENT (Búsqueda geográfica)
              ├─── APPOINTMENT_BOOKING_AGENT (Reservas + Confirmación)
              └─── SEMOVI_INFORMATION_AGENT (RAG + Consultas de procedimientos)
```

### Responsabilidades por Agente

| Agente | Responsabilidad Principal | Herramientas Clave |
|--------|-------------------------|-------------------|
| `semovi_coordinator` | Flujo general, routing inteligente | `validate_process_stage()` |
| `ine_extraction_agent` | Procesamiento de documentos | `extract_ine_data_with_vision()` |
| `license_consultation_agent` | Determinación de servicios | `determine_license_requirements()` |
| `office_location_agent` | Búsqueda geográfica | `find_nearby_offices()` |
| `appointment_booking_agent` | Gestión de citas | `create_appointment()` |
| `semovi_information_agent` | Consultas de procedimientos con RAG | `rag_query_semovi()` |

---

## Flujo de Usuario Completo

### Fase 1: Bienvenida y Presentación 
```
Usuario entra al sistema
    ↓
SEMOVI_COORDINATOR presenta servicios disponibles
    ↓
"Hola! Soy tu asistente para tramitar licencias de conducir en SEMOVI.
Puedo ayudarte con:
- Licencia Tipo A (autos y motos hasta 400cc) 
- Licencia Tipo A1 (motos 125-400cc)
- Licencia Tipo A2 (motos +400cc)

Para cualquier procedimiento: expedición, renovación o reposición.

Para comenzar, por favor envíame una foto de tu INE o credencial para votar."
```

### Fase 2: Extracción de Datos del INE
```
Usuario envía foto del INE
    ↓
COORDINADOR detecta imagen → transfiere a INE_EXTRACTION_AGENT
    ↓
INE_EXTRACTION_AGENT:
    1. Procesa imagen con Google Vision API
    2. Extrae: nombre, CURP, dirección, código postal, fecha nacimiento
    3. Valida calidad de los datos extraídos
    4. Almacena en ToolContext: {
        "full_name": "Juan Pérez García",
        "curp": "PEGJ850515HDFLRN09", 
        "address": "Av. Revolución 123, Col. Centro",
        "postal_code": "06000",
        "birth_date": "1985-05-15"
       }
    ↓
Confirma datos extraídos → transfiere a LICENSE_CONSULTATION_AGENT
```

### Fase 3: Consulta de Servicios
```
LICENSE_CONSULTATION_AGENT analiza necesidades:
    ↓
"Perfecto! He extraído tu información. Ahora dime:

1. ¿Para qué tipo de vehículo necesitas la licencia?
   - Automóvil
   - Motocicleta

2. Si es motocicleta, ¿de qué cilindraje?
   - Hasta 125cc
   - 125cc a 400cc  
   - Mayor a 400cc

3. ¿Qué tipo de trámite necesitas?
   - Primera vez (expedición)
   - Renovar licencia vencida
   - Reponer por pérdida/robo"
    ↓
Determina: Licencia A + Expedición
Calcula: Costo total = $866.00
Lista requisitos específicos
    ↓
Transfiere a OFFICE_LOCATION_AGENT
```

### Fase 4: Búsqueda de Ubicaciones
```
OFFICE_LOCATION_AGENT busca por código postal:
    ↓
find_nearby_offices(postal_code="06000")
    ↓
Consulta Supabase → encuentra oficinas cercanas
    ↓
"He encontrado estas oficinas SEMOVI cerca de tu ubicación (CP: 06000):

📍 SEMOVI Centro
   - Dirección: Av. Chapultepec 49, Centro, CDMX
   - Distancia: 2.1 km
   - Teléfono: 55-5208-9898
   - Horario: Lunes a Viernes 8:00-15:00

📍 SEMOVI Coyoacán  
   - Dirección: Av. Universidad 1200, Coyoacán, CDMX
   - Distancia: 8.5 km
   - Teléfono: 55-5208-9895

¿En cuál oficina te gustaría agendar tu cita?"
    ↓
Usuario selecciona oficina → transfiere a APPOINTMENT_BOOKING_AGENT
```

### Fase 5: Agendamiento de Cita
```
APPOINTMENT_BOOKING_AGENT gestiona la reserva:
    ↓
get_available_slots(office_id=1, service_type="EXPEDITION")
    ↓
Consulta slots disponibles en Supabase
    ↓
"Horarios disponibles en SEMOVI Centro para Expedición de Licencia A:

🗓️ Miércoles 4 Dic - 9:00 AM (disponible)
🗓️ Miércoles 4 Dic - 11:00 AM (disponible) 
🗓️ Jueves 5 Dic - 10:00 AM (disponible)
🗓️ Viernes 6 Dic - 2:00 PM (disponible)

¿Qué horario prefieres?"
    ↓
Usuario selecciona → create_appointment() 
    ↓
Verifica disponibilidad en BD → reserva slot → actualiza capacidad
    ↓
"✅ ¡Cita confirmada!

📋 DETALLES DE TU CITA
Número de confirmación: SEMOVI-20241204-7829
Trámite: Expedición Licencia Tipo A
Fecha: Miércoles 4 Diciembre 2024
Hora: 9:00 AM
Oficina: SEMOVI Centro
Costo total: $866.00

📧 ¿Quieres recibir la confirmación por email?"
```

---

## Agente Coordinador

### `semovi_coordinator`

**Propósito**: Orquestador principal que gestiona el flujo completo del proceso de licencias SEMOVI.

#### Instruction Principal
```python
instruction = """
Eres el coordinador principal del sistema de licencias SEMOVI (Secretaría de Movilidad).

<user_session>
Nombre: {full_name}
CURP: {curp}  
Dirección: {address}
Código Postal: {postal_code}
Fecha Nacimiento: {birth_date}
</user_session>

<process_state>
Etapa actual: {current_stage}
Licencia determinada: {license_type} 
Procedimiento: {procedure_type}
Oficina seleccionada: {selected_office}
</process_state>

## TU MISIÓN PRINCIPAL

Guiar a los usuarios a través del proceso COMPLETO de agendamiento de citas para licencias de conducir, desde la captura de datos hasta la confirmación final.

## SERVICIOS DE SEMOVI DISPONIBLES

### Tipos de Licencia:
- **Tipo A**: Automóviles particulares y motocicletas hasta 400cc ($866.00)
- **Tipo A1**: Motocicletas 125cc-400cc ($651.00)  
- **Tipo A2**: Motocicletas +400cc ($1,055.00)

### Procedimientos:
- **Expedición**: Primera vez ($0 adicional + curso requerido)
- **Renovación**: Licencia vencida ($0 adicional)
- **Reposición**: Pérdida/robo/deterioro (+$158.00)

## FLUJO DE PROCESO INTELIGENTE

### ETAPA 1: Bienvenida e Identificación
Si es la primera interacción:
→ Presentar servicios SEMOVI disponibles
→ Solicitar foto del INE/credencial para votar
→ Transferir INMEDIATAMENTE a INE_EXTRACTION_AGENT

### ETAPA 2: Datos del INE Completos  
Si tenemos datos extraídos del INE:
→ Confirmar información extraída
→ Transferir a LICENSE_CONSULTATION_AGENT para determinar servicio

### ETAPA 3: Servicio Determinado
Si sabemos qué licencia y procedimiento necesita:
→ Transferir a OFFICE_LOCATION_AGENT para buscar ubicaciones

### ETAPA 4: Oficina Seleccionada
Si el usuario eligió oficina:
→ Transferir a APPOINTMENT_BOOKING_AGENT para agendar

### ETAPA 5: Cita Confirmada
Si la cita está agendada:
→ Mostrar resumen completo
→ Ofrecer opciones de confirmación (email, PDF)

## ROUTING INTELIGENTE

**Detectar imagen de INE**: → INE_EXTRACTION_AGENT
**Falta información personal**: → INE_EXTRACTION_AGENT  
**Necesita determinar licencia**: → LICENSE_CONSULTATION_AGENT
**Requiere buscar oficinas**: → OFFICE_LOCATION_AGENT
**Listo para agendar**: → APPOINTMENT_BOOKING_AGENT
**Preguntas sobre procedimientos**: → SEMOVI_INFORMATION_AGENT

## MENSAJE DE BIENVENIDA

"👋 ¡Hola! Soy tu asistente inteligente para tramitar licencias de conducir en SEMOVI.

🚗 **Servicios disponibles:**
- Licencia Tipo A (autos y motos hasta 400cc)
- Licencia Tipo A1 (motos 125-400cc) 
- Licencia Tipo A2 (motos +400cc)

📋 **Procedimientos:**
- Expedición (primera vez)
- Renovación (licencia vencida)
- Reposición (por pérdida o deterioro)

Para comenzar, **envíame una foto de tu INE o credencial para votar** y extraeré automáticamente toda tu información necesaria."
"""
```

#### Sub-agentes
```python
sub_agents = [
    ine_extraction_agent,
    license_consultation_agent, 
    office_location_agent,
    appointment_booking_agent,
    semovi_information_agent
]
```

#### Herramientas Propias
```python
tools = [validate_process_stage, get_session_summary]
```

---

## Agentes Especialistas

### 1. `ine_extraction_agent`

**Especialización**: Procesamiento inteligente de documentos de identidad usando Google Vision API.

#### Capacidades
- Extracción automática de datos del INE/credencial para votar
- Validación de calidad y completitud de los datos
- Manejo de errores de reconocimiento óptico
- Solicitud de datos faltantes si es necesario

#### Instruction
```python
instruction = """
Eres el especialista en extracción de datos de documentos de identidad para SEMOVI.

Tu ÚNICA función es procesar imágenes del INE/credencial para votar y extraer:
- Nombre completo
- CURP  
- Dirección completa
- Código postal
- Fecha de nacimiento

## PROCESO DE EXTRACCIÓN

1. **Recibir imagen del INE**
2. **Usar extract_ine_data_with_vision() para procesar con Google Vision**
3. **Validar calidad de los datos extraídos**
4. **Almacenar en el estado de la sesión**
5. **Confirmar datos con el usuario**
6. **TRANSFERIR INMEDIATAMENTE al license_consultation_agent**

## MANEJO DE ERRORES

Si la imagen es borrosa o no se puede leer:
- Solicitar nueva foto más clara
- Ofrecer captura manual de datos como alternativa

## DATOS MÍNIMOS REQUERIDOS

- Nombre completo ✅
- CURP ✅  
- Código postal ✅ (para búsqueda de oficinas)

Si faltan datos críticos, solicita complementar antes de continuar.

DESPUÉS de extracción exitosa, SIEMPRE transfiere al license_consultation_agent.
"""
```

#### Herramientas
```python
tools = [
    extract_ine_data_with_vision,
    validate_extracted_data,
    request_missing_information
]
```

### 2. `license_consultation_agent`

**Especialización**: Determinación inteligente del tipo de licencia y procedimiento requerido.

#### Capacidades
- Análisis de necesidades del usuario (vehículo, cilindraje)
- Determinación automática del tipo de licencia (A, A1, A2)
- Identificación del procedimiento (expedición, renovación, reposición)
- Cálculo de costos totales y requisitos específicos

#### Instruction
```python
instruction = """
Eres el consultor especializado en licencias de SEMOVI.

<user_data>
Datos del usuario: {full_name}, {curp}, {address}
Fecha de nacimiento: {birth_date}
</user_data>

## TU ESPECIALIZACIÓN

Determinar exactamente qué tipo de licencia y procedimiento necesita el usuario.

## LÓGICA DE DETERMINACIÓN

### Tipo de Licencia:
**Pregunta clave**: "¿Para qué tipo de vehículo necesitas la licencia?"

- **Automóvil** → Licencia Tipo A
- **Motocicleta hasta 125cc** → Licencia Tipo A1  
- **Motocicleta 125cc-400cc** → Licencia Tipo A1
- **Motocicleta +400cc** → Licencia Tipo A2

### Tipo de Procedimiento:
**Pregunta clave**: "¿Qué trámite necesitas realizar?"

- **Primera vez** → Expedición
- **Renovar licencia vencida** → Renovación
- **Reponerla por pérdida/robo** → Reposición

## CÁLCULO DE COSTOS

Usar determine_license_requirements() para obtener:
- Costo base de la licencia
- Costo adicional del procedimiento  
- Requisitos específicos
- Tiempo de procesamiento

## FLUJO DE TRABAJO

1. **Hacer preguntas específicas** para determinar licencia y procedimiento
2. **Calcular costos totales**
3. **Listar requisitos específicos**
4. **Confirmar el servicio determinado**
5. **TRANSFERIR a office_location_agent**
"""
```

#### Herramientas
```python
tools = [
    determine_license_requirements,
    calculate_total_cost,
    get_specific_requirements,
    validate_age_requirements
]
```

### 3. `office_location_agent`

**Especialización**: Búsqueda geográfica inteligente de oficinas SEMOVI cercanas.

#### Capacidades
- Búsqueda por código postal extraído del INE
- Cálculo de distancias aproximadas
- Información detallada de cada oficina (horarios, servicios, contacto)
- Verificación de disponibilidad de servicios por oficina

#### Instruction
```python
instruction = """
Eres el especialista en ubicaciones y oficinas SEMOVI.

<user_location>
Código postal del usuario: {postal_code}
Dirección: {address}
</user_location>

<service_needed>
Licencia: {license_type}
Procedimiento: {procedure_type}  
</service_needed>

## TU ESPECIALIZACIÓN

Encontrar las oficinas SEMOVI más convenientes para el usuario.

## BÚSQUEDA INTELIGENTE

1. **Usar find_nearby_offices(postal_code) para buscar por proximidad**
2. **Verificar que la oficina ofrezca el servicio específico**
3. **Presentar opciones ordenadas por distancia**
4. **Incluir información completa de cada oficina**

## INFORMACIÓN POR OFICINA

Para cada oficina mostrar:
- Nombre completo
- Dirección exacta
- Distancia aproximada
- Teléfono de contacto
- Horarios de atención
- Servicios específicos disponibles

## FORMATO DE PRESENTACIÓN

📍 **SEMOVI Centro**
- 📍 Dirección: Av. Chapultepec 49, Centro, CDMX
- 📏 Distancia: 2.1 km de tu ubicación  
- ☎️ Teléfono: 55-5208-9898
- ⏰ Horario: Lunes a Viernes 8:00-15:00
- ✅ Servicios: Licencia A - Expedición disponible

Después de que el usuario elija oficina, TRANSFERIR a appointment_booking_agent.
"""
```

#### Herramientas
```python
tools = [
    find_nearby_offices,
    calculate_distance,
    verify_office_services,
    get_office_details
]
```

### 4. `appointment_booking_agent`

**Especialización**: Gestión completa de citas con integración en tiempo real a Supabase.

#### Capacidades
- Consulta de disponibilidad en tiempo real
- Reserva de slots con verificación de capacidad
- Generación de códigos de confirmación únicos
- Actualización automática de disponibilidad
- Envío de confirmaciones multicanal

#### Instruction
```python
instruction = """
Eres el especialista en agendamiento de citas para SEMOVI.

<appointment_context>
Usuario: {full_name} ({curp})
Servicio: {license_type} - {procedure_type}
Oficina: {selected_office}
Costo total: {total_cost}
</appointment_context>

## TU ESPECIALIZACIÓN

Gestionar el proceso completo de agendamiento de citas.

## FLUJO DE RESERVA

1. **Consultar disponibilidad real con get_available_slots()**
2. **Presentar opciones de horarios disponibles**
3. **Reservar slot seleccionado con create_appointment()**
4. **Generar código de confirmación único**
5. **Actualizar capacidad de slots en Supabase**
6. **Ofrecer confirmaciones adicionales**

## PRESENTACIÓN DE HORARIOS

🗓️ **Miércoles 4 Diciembre 2024**
- 9:00 AM (✅ Disponible)
- 11:00 AM (✅ Disponible)

🗓️ **Jueves 5 Diciembre 2024**  
- 10:00 AM (✅ Disponible)
- 2:00 PM (✅ Disponible)

## CONFIRMACIÓN DE CITA

Después de agendar exitosamente:

✅ **CITA CONFIRMADA**

📋 **Detalles:**
- Confirmación: SEMOVI-20241204-7829
- Trámite: {license_type} - {procedure_type}
- Fecha: {appointment_date}
- Hora: {appointment_time}
- Oficina: {office_name}
- Costo: ${total_cost}

📧 ¿Te gustaría recibir la confirmación por email?
📱 ¿Necesitas el comprobante en PDF?
"""
```

#### Herramientas
```python
tools = [
    get_available_slots,
    create_appointment,
    generate_confirmation_code,
    update_slot_capacity,
    send_email_confirmation,
    generate_pdf_confirmation
]
```

### 5. `semovi_information_agent`

**Especialización**: Consultas inteligentes sobre procedimientos SEMOVI usando Vertex AI RAG.

#### Capacidades
- Búsqueda en documentación oficial SEMOVI usando RAG
- Respuestas precisas sobre procedimientos presenciales
- Consulta de requisitos específicos por tipo de licencia
- Información sobre horarios, ubicaciones y procesos internos
- Manejo de preguntas frecuentes sobre trámites

#### Instruction
```python
instruction = """
Eres el especialista en información y consultas sobre procedimientos SEMOVI.

<rag_context>
Corpus disponible: semovi_procedures
Documentación: Trámites de vehículos particulares SEMOVI
Tipo de consultas: Procedimientos presenciales, requisitos, ubicaciones
</rag_context>

## TU ESPECIALIZACIÓN

Responder preguntas específicas sobre cómo realizar trámites SEMOVI de manera presencial usando la documentación oficial.

## TIPOS DE CONSULTAS QUE MANEJAS

### Procedimientos Presenciales:
- "¿Cómo tramito una licencia tipo A en persona?"
- "¿Qué documentos necesito llevar para renovar?"
- "¿Cuál es el proceso completo para expedición?"

### Requisitos Específicos:
- "¿Qué examen médico necesito para licencia A2?"
- "¿Dónde hago el curso de manejo obligatorio?"
- "¿Qué documentos adicionales pide la reposición?"

### Información de Oficinas:
- "¿En qué horarios atienden las oficinas?"
- "¿Todas las oficinas dan el mismo servicio?"
- "¿Puedo ir a cualquier oficina SEMOVI?"

### Costos y Tiempos:
- "¿Cuánto tarda el trámite completo?"
- "¿Los costos incluyen exámenes médicos?"
- "¿Hay descuentos para adultos mayores?"

## FLUJO DE RESPUESTA

1. **Usar rag_query_semovi() para buscar información relevante**
2. **Procesar resultados y extraer información específica**
3. **Estructurar respuesta clara y actionable**
4. **Incluir referencias a documentación oficial**
5. **Ofrecer seguimiento si necesita más detalles**

## FORMATO DE RESPUESTA

📋 **Procedimiento: {procedure_name}**

**Requisitos:**
- Documento 1
- Documento 2  
- Examen/curso específico

**Proceso:**
1. Paso específico 1
2. Paso específico 2
3. Resultado esperado

**Tiempo estimado:** {processing_time}
**Costo:** ${cost}

*Fuente: Documentación oficial SEMOVI*

## IMPORTANTES

- SIEMPRE usa rag_query_semovi() para buscar información
- NUNCA inventes datos o procedimientos  
- Si no encuentras información específica, dilo claramente
- Siempre indica que la información viene de documentos oficiales
- Ofrece continuar con el agendamiento si el usuario está listo
"""
```

#### Herramientas
```python
tools = [
    rag_query_semovi,
    search_requirements_by_license,
    get_procedure_details,
    validate_information_query
]
```

---

## Herramientas del Sistema

### Consultas RAG

#### `rag_query_semovi(tool_context, query, filter_by_section)`
```python
def rag_query_semovi(
    tool_context: ToolContext, 
    query: str,
    filter_by_section: str = None  # "requirements", "procedures", "costs", "offices"
) -> dict:
    """
    Consulta el corpus de documentación SEMOVI usando Vertex AI RAG
    
    Args:
        query: Pregunta o consulta del usuario
        filter_by_section: Filtro opcional por sección del documento
        
    Returns:
        {
            "status": "success",
            "query": "Cómo tramito licencia tipo A?",
            "results": [
                {
                    "content": "Para tramitar licencia tipo A se requiere...",
                    "source_section": "Expedición - Licencia A",
                    "confidence_score": 0.94,
                    "page_reference": "Página 3"
                }
            ],
            "results_count": 3
        }
    """
```

#### `search_requirements_by_license(tool_context, license_type, procedure_type)`
```python
def search_requirements_by_license(
    tool_context: ToolContext,
    license_type: str,  # "A", "A1", "A2"
    procedure_type: str  # "expedition", "renewal", "replacement"
) -> dict:
    """
    Búsqueda específica de requisitos por tipo de licencia
    
    Usa RAG con queries optimizadas:
    - "requisitos licencia {license_type} {procedure_type}"
    - "documentos necesarios {license_type}"
    - "examen médico {license_type}"
    """
```

#### `get_procedure_details(tool_context, procedure_name)`
```python
def get_procedure_details(
    tool_context: ToolContext,
    procedure_name: str
) -> dict:
    """
    Obtiene detalles completos de un procedimiento específico
    
    Procedimientos soportados:
    - "expedicion_licencia_a"
    - "renovacion_licencia_a1" 
    - "reposicion_por_robo"
    - "examen_medico_proceso"
    - "curso_manejo_requisitos"
    """
```

### Configuración del Corpus RAG

#### Estructura del Corpus SEMOVI
```python
SEMOVI_RAG_CONFIG = {
    "corpus_name": "semovi_procedures",
    "embedding_model": "text-embedding-005",
    "chunk_size": 512,
    "chunk_overlap": 100,
    "documents": [
        {
            "source": "Trámites de vehículos particulares SEMOVI.pdf",
            "sections": [
                "Licencia Tipo A - Requisitos y Procedimientos",
                "Licencia Tipo A1 - Motocicletas 125-400cc", 
                "Licencia Tipo A2 - Motocicletas +400cc",
                "Procedimientos de Expedición",
                "Procedimientos de Renovación",
                "Procedimientos de Reposición",
                "Costos y Tarifas Oficiales",
                "Ubicaciones y Horarios de Oficinas",
                "Exámenes Médicos Requeridos",
                "Cursos de Manejo Obligatorios"
            ]
        }
    ],
    "retrieval_config": {
        "top_k": 5,
        "distance_threshold": 0.3,
        "include_metadata": True
    }
}
```

#### Inicialización del Corpus
```python
# Al inicializar el sistema, crear corpus si no existe
def initialize_semovi_rag_corpus(tool_context: ToolContext):
    """
    Inicializa el corpus RAG con documentación SEMOVI
    
    1. Verificar si corpus 'semovi_procedures' existe
    2. Si no existe, crear corpus nuevo
    3. Agregar PDF de trámites SEMOVI
    4. Procesar y vectorizar contenido
    5. Validar que corpus está listo para consultas
    """
    
    if not corpus_exists("semovi_procedures"):
        create_corpus("semovi_procedures")
        add_document(
            corpus_name="semovi_procedures",
            document_path="docs/Tramites_SEMOVI_Vehiculos_Particulares.pdf",
            metadata={
                "document_type": "official_procedures",
                "source_authority": "SEMOVI_CDMX",
                "version": "2024",
                "language": "es"
            }
        )
```

### Extracción de Documentos

#### `extract_ine_data_with_vision(tool_context, image_data)`
```python
def extract_ine_data_with_vision(tool_context: ToolContext, image_data: str) -> dict:
    """
    Extrae datos del INE usando Google Vision API
    
    Returns:
        {
            "status": "success",
            "extracted_data": {
                "full_name": "Juan Pérez García",
                "curp": "PEGJ850515HDFLRN09",
                "address": "Av. Revolución 123, Col. Centro",
                "postal_code": "06000", 
                "birth_date": "1985-05-15"
            }
        }
    """
```

#### `validate_extracted_data(tool_context, extracted_data)`
```python
def validate_extracted_data(tool_context: ToolContext, extracted_data: dict) -> dict:
    """
    Valida la calidad y completitud de los datos extraídos
    
    Verifica:
    - CURP tiene formato válido
    - Código postal es numérico y válido para CDMX
    - Nombre no está vacío
    - Dirección contiene información suficiente
    """
```

### Consulta de Servicios

#### `determine_license_requirements(tool_context, vehicle_type, cylinder_capacity, procedure)`
```python
def determine_license_requirements(
    tool_context: ToolContext, 
    vehicle_type: str,  # "auto" | "motorcycle"
    cylinder_capacity: int,  # Para motos: ej. 150, 250, 500
    procedure: str  # "expedition" | "renewal" | "replacement"
) -> dict:
    """
    Determina tipo de licencia y requisitos específicos
    
    Lógica:
    - auto → LICENSE_A
    - motorcycle ≤125cc → LICENSE_A1  
    - motorcycle 125-400cc → LICENSE_A1
    - motorcycle >400cc → LICENSE_A2
    
    Returns:
        {
            "license_type": "LICENSE_A",
            "procedure_type": "EXPEDITION",
            "base_cost": 866.00,
            "additional_cost": 0.00,
            "total_cost": 866.00,
            "requirements": [...],
            "processing_days": 1
        }
    """
```

#### `calculate_total_cost(tool_context, license_type, procedure_type)`
```python
def calculate_total_cost(tool_context: ToolContext, license_type: str, procedure_type: str) -> dict:
    """
    Calcula costo total basado en tablas de Supabase
    
    Consulta:
    - service_categories para costo base de licencia
    - service_types para costo adicional del procedimiento
    
    Returns total_cost y desglose
    """
```

### Búsqueda de Oficinas

#### `find_nearby_offices(tool_context, postal_code)`
```python
def find_nearby_offices(tool_context: ToolContext, postal_code: str) -> dict:
    """
    Busca oficinas SEMOVI cercanas al código postal
    
    Consulta Supabase:
    SELECT o.*, COUNT(os.id) as services_count
    FROM offices o
    LEFT JOIN office_services os ON o.id = os.office_id  
    WHERE o.is_active = true
    ORDER BY distance_calculation(o.postal_code, :user_postal_code)
    
    Returns:
        {
            "offices": [
                {
                    "id": 1,
                    "name": "SEMOVI Centro",
                    "address": "Av. Chapultepec 49, Centro, CDMX",
                    "postal_code": "06000",
                    "phone": "55-5208-9898",
                    "distance_km": 2.1,
                    "operating_hours": {...}
                }
            ]
        }
    """
```

#### `verify_office_services(tool_context, office_id, license_type, procedure_type)`
```python
def verify_office_services(
    tool_context: ToolContext, 
    office_id: int, 
    license_type: str, 
    procedure_type: str
) -> dict:
    """
    Verifica que la oficina ofrezca el servicio específico
    
    Consulta office_services junction table
    """
```

### Agendamiento de Citas

#### `get_available_slots(tool_context, office_id, target_date_range)`
```python
def get_available_slots(
    tool_context: ToolContext, 
    office_id: int, 
    target_date_range: int = 14  # días hacia adelante
) -> dict:
    """
    Consulta slots disponibles en tiempo real
    
    Query Supabase:
    SELECT slot_date, start_time, end_time, available_capacity
    FROM appointment_slots 
    WHERE office_id = :office_id
      AND slot_date BETWEEN CURRENT_DATE AND CURRENT_DATE + :target_date_range
      AND available_capacity > 0
      AND is_active = true
    ORDER BY slot_date, start_time
    
    Returns slots agrupados por fecha
    """
```

#### `create_appointment(tool_context, office_id, slot_id, user_info)`
```python
def create_appointment(
    tool_context: ToolContext,
    office_id: int,
    slot_id: int, 
    user_info: dict
) -> dict:
    """
    Crea cita en Supabase con transacción atómica
    
    Transacción:
    1. Verificar disponibilidad del slot
    2. Reducir available_capacity en 1
    3. Insertar appointment con user_info JSON
    4. Generar confirmation_code único
    
    Returns:
        {
            "appointment_id": 123,
            "confirmation_code": "SEMOVI-20241204-7829",
            "status": "confirmed"
        }
    """
```

#### `generate_confirmation_code(tool_context)`
```python
def generate_confirmation_code(tool_context: ToolContext) -> str:
    """
    Genera código único de confirmación
    
    Formato: SEMOVI-YYYYMMDD-NNNN
    Ejemplo: SEMOVI-20241204-7829
    """
```

### Confirmaciones

#### `send_email_confirmation(tool_context, email, appointment_details)`
```python
def send_email_confirmation(
    tool_context: ToolContext, 
    email: str, 
    appointment_details: dict
) -> dict:
    """
    Envía email de confirmación con detalles completos
    
    Incluye:
    - Datos de la cita (fecha, hora, oficina)
    - Código de confirmación
    - Requisitos específicos para el trámite
    - Mapa/direcciones a la oficina
    - Código QR para check-in rápido
    """
```

#### `generate_pdf_confirmation(tool_context, appointment_details)`
```python
def generate_pdf_confirmation(
    tool_context: ToolContext, 
    appointment_details: dict
) -> dict:
    """
    Genera PDF con comprobante oficial de la cita
    
    Incluye:
    - Logo SEMOVI
    - Datos del usuario (del INE extraído)
    - Detalles completos de la cita
    - Código QR para verificación
    - Lista de requisitos a llevar
    """
```

---

## Integración con Supabase

### Conexión y Configuración
```python
from supabase import create_client, Client
import os

SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_ANON_KEY")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
```

### Consultas Principales

#### Búsqueda de Oficinas
```sql
SELECT 
  o.*,
  COUNT(os.id) as total_services
FROM offices o
LEFT JOIN office_services os ON o.id = os.office_id  
WHERE o.is_active = true
  AND o.postal_code SIMILAR TO %(user_postal_code_pattern)s
GROUP BY o.id
ORDER BY o.postal_code;
```

#### Verificación de Servicios
```sql
SELECT 1 
FROM office_services os
JOIN service_categories sc ON os.service_category_id = sc.id
JOIN service_types st ON os.service_type_id = st.id
WHERE os.office_id = %(office_id)s
  AND sc.code = %(license_type)s
  AND st.code = %(procedure_type)s
  AND os.is_available = true;
```

#### Slots Disponibles
```sql
SELECT 
  slot_date,
  start_time, 
  end_time,
  available_capacity,
  max_capacity
FROM appointment_slots
WHERE office_id = %(office_id)s
  AND slot_date BETWEEN CURRENT_DATE AND CURRENT_DATE + INTERVAL '%(days)s days'
  AND available_capacity > 0
  AND is_active = true
ORDER BY slot_date, start_time;
```

#### Crear Cita (Transacción)
```sql
-- 1. Verificar y reservar slot
UPDATE appointment_slots 
SET available_capacity = available_capacity - 1
WHERE id = %(slot_id)s 
  AND available_capacity > 0
RETURNING id;

-- 2. Crear appointment
INSERT INTO appointments (
  user_id,
  office_id, 
  service_category_id,
  service_type_id,
  appointment_slot_id,
  user_info,
  confirmation_code
) VALUES (
  %(user_id)s,
  %(office_id)s,
  (SELECT id FROM service_categories WHERE code = %(license_type)s),
  (SELECT id FROM service_types WHERE code = %(procedure_type)s), 
  %(slot_id)s,
  %(user_info_json)s,
  %(confirmation_code)s
) RETURNING id, confirmation_code;
```

---

## Estado Compartido

### Estructura del ToolContext

```python
tool_context.state = {
    # Datos del usuario (extraídos del INE)
    "user_data": {
        "full_name": "Juan Pérez García",
        "curp": "PEGJ850515HDFLRN09", 
        "address": "Av. Revolución 123, Col. Centro",
        "postal_code": "06000",
        "birth_date": "1985-05-15",
        "extraction_timestamp": "2024-12-04T10:30:00Z"
    },
    
    # Proceso de determinación de servicio
    "service_determination": {
        "vehicle_type": "auto",  # "auto" | "motorcycle"
        "cylinder_capacity": null,  # Para motos
        "license_type": "LICENSE_A",  # LICENSE_A | LICENSE_A1 | LICENSE_A2
        "procedure_type": "EXPEDITION",  # EXPEDITION | RENEWAL | REPLACEMENT
        "total_cost": 866.00,
        "requirements": [...]
    },
    
    # Búsqueda de oficinas
    "office_search": {
        "search_postal_code": "06000",
        "found_offices": [...],
        "selected_office": {
            "id": 1,
            "name": "SEMOVI Centro",
            "address": "Av. Chapultepec 49, Centro, CDMX"
        }
    },
    
    # Agendamiento
    "appointment": {
        "available_slots": [...],
        "selected_slot": {
            "date": "2024-12-04",
            "time": "09:00:00",
            "slot_id": 123
        },
        "confirmation": {
            "appointment_id": 456,
            "confirmation_code": "SEMOVI-20241204-7829",
            "status": "confirmed"
        }
    },
    
    # Control de flujo
    "process_stage": "appointment_confirmed",  # Etapa actual
    "session_metadata": {
        "session_id": "sess_123abc",
        "created_at": "2024-12-04T10:00:00Z",
        "last_activity": "2024-12-04T10:45:00Z",
        "agent_transitions": [
            {"from": "coordinator", "to": "ine_extraction", "timestamp": "..."},
            {"from": "ine_extraction", "to": "license_consultation", "timestamp": "..."},
            {"from": "coordinator", "to": "semovi_information", "timestamp": "..."}
        ]
    },
    
    # Historial de consultas RAG
    "information_queries": {
        "queries_made": [
            {
                "query": "¿Qué examen médico necesito para licencia A2?",
                "timestamp": "2024-12-04T10:35:00Z",
                "results_found": 3,
                "satisfaction_score": 0.94
            }
        ],
        "corpus_status": "ready",
        "last_corpus_update": "2024-12-01T00:00:00Z"
    }
}
```

---

## Casos de Uso Específicos

### Caso 1: Expedición de Licencia Tipo A (Primera vez)

**Usuario**: Joven de 18 años que quiere sacar su primera licencia para auto.

**Flujo**:
1. Envía foto del INE → Extracción automática de datos
2. Consulta: "auto" + "primera vez" → Licencia A + Expedición 
3. Costo: $866.00 + requisitos (curso, examen médico)
4. Búsqueda por CP → Oficinas cercanas
5. Selecciona oficina y horario → Cita confirmada

**Requisitos específicos mostrados**:
- Acta de nacimiento original
- Curso de manejo aprobado  
- Examen médico vigente
- Comprobante de domicilio

### Caso 2: Renovación Licencia A1 (Motocicleta)

**Usuario**: Motociclista con licencia A1 vencida.

**Flujo**:
1. Extracción del INE → Datos personales
2. Consulta: "moto 250cc" + "renovar" → Licencia A1 + Renovación
3. Costo: $651.00 (sin costo adicional)  
4. Requisitos simplificados (sin curso)
5. Agendamiento directo

**Diferencias**:
- No requiere curso de manejo
- Proceso más rápido
- Costos reducidos

### Caso 3: Reposición por Robo (Licencia A2)

**Usuario**: Motociclista de moto grande que le robaron la licencia.

**Flujo**:
1. Extracción del INE → Validación de identidad
2. Consulta: "moto 650cc" + "reponer por robo" → A2 + Reposición
3. Costo: $1,055.00 + $158.00 = $1,213.00
4. Requisitos especiales (denuncia ministerial)
5. Verificación adicional de identidad

**Requisitos especiales**:
- Denuncia por robo ante MP
- Declaración bajo protesta de decir verdad
- Identificación oficial adicional

### Caso 4: Error en Extracción del INE

**Escenario**: La imagen del INE está borrosa o el CURP no se lee correctamente.

**Manejo**:
1. `ine_extraction_agent` detecta datos incompletos
2. Solicita nueva foto más clara
3. Ofrece opción de captura manual como alternativa
4. Valida datos ingresados manualmente
5. Continúa proceso normal una vez completos

### Caso 5: Oficina Sin Disponibilidad

**Escenario**: La oficina preferida no tiene slots disponibles en fechas cercanas.

**Manejo**:
1. `appointment_booking_agent` consulta disponibilidad
2. No encuentra slots en los próximos 7 días
3. Ofrece oficinas alternativas cercanas
4. Muestra disponibilidad en fechas posteriores  
5. Permite al usuario elegir entre alternativas

### Caso 6: Consulta de Información Específica

**Escenario**: Usuario hace preguntas detalladas sobre procedimientos antes o durante el proceso.

**Ejemplos de Preguntas**:
- "Qué tipo de examen médico necesito para licencia A2?"
- "Dónde puedo hacer el curso de manejo obligatorio?"
- "Qué documentos adicionales necesito para reposición por robo?"
- "Puedo usar mi licencia vencida como identificación?"

**Flujo del SEMOVI_INFORMATION_AGENT**:
1. Usuario hace pregunta específica
2. Coordinador detecta consulta de información → transfiere a `semovi_information_agent`
3. Agente usa `rag_query_semovi()` con la pregunta
4. Vertex AI RAG busca en documentación oficial
5. Procesa resultados y estructura respuesta clara
6. Proporciona información precisa con referencias
7. Ofrece continuar con el proceso de agendamiento

**Respuesta de Ejemplo**:
```
📋 **Examen Médico - Licencia Tipo A2**

**Requisitos del examen:**
• Examen de agudeza visual
• Evaluación de reflejos y coordinación
• Prueba de audición
• Certificado médico vigente (máximo 30 días)

**Dónde realizarlo:**
• Centros médicos autorizados por SEMOVI
• Clínicas del IMSS/ISSSTE
• Consultorios particulares con cédula profesional

**Costo aproximado:** $200-400 pesos
**Validez:** 30 días naturales

*Fuente: Documentación oficial SEMOVI 2024*

¿Te gustaría continuar con el agendamiento de tu cita?
```

---

## Métricas y Monitoreo

### KPIs del Sistema
- **Tasa de extracción exitosa del INE**: >95%
- **Tiempo promedio de proceso completo**: <5 minutos  
- **Tasa de confirmación de citas**: >90%
- **Precisión en determinación de licencias**: >98%
- **Precisión de respuestas RAG**: >92%
- **Tiempo de respuesta de consultas RAG**: <3 segundos

### Logging Específico
```python
# Cada herramienta registra métricas
{
    "tool": "extract_ine_data_with_vision",
    "success": true,
    "processing_time_ms": 1250,
    "confidence_score": 0.94,
    "fields_extracted": ["name", "curp", "address", "postal_code"]
}
```

### Alertas y Monitoreo
- Error rate en Google Vision API
- Disponibilidad de slots por oficina  
- Tiempo de respuesta de Supabase
- Capacidad de procesamiento de imágenes
- Disponibilidad del corpus RAG de SEMOVI
- Tiempo de respuesta de Vertex AI RAG
- Precisión de respuestas vs documentación oficial

Este sistema proporciona una experiencia completa y automatizada para el agendamiento de citas SEMOVI, desde la captura de documentos hasta la confirmación final, incluyendo un sistema de consultas inteligentes que permite a los usuarios obtener información precisa sobre procedimientos usando la documentación oficial. El sistema optimiza el proceso tanto para usuarios como para la administración pública, reduciendo tiempos de espera y mejorando la calidad de la información proporcionada.

### Integración RAG con Vertex AI

El agente de información utiliza **Vertex AI RAG** para proporcionar respuestas precisas basadas en documentación oficial:

- **Corpus**: Documentos oficiales SEMOVI procesados y vectorizados
- **Embeddings**: text-embedding-005 de Google para máxima precisión en español
- **Retrieval**: Top-K con filtrado por distancia para resultados relevantes
- **Respuestas**: Estructuradas con referencias y validación de fuentes oficiales

Esto garantiza que toda la información proporcionada sea veraz, actualizada y conforme a los procedimientos oficiales de SEMOVI.