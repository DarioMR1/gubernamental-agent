# Agente Gubernamental - Especificación Técnica

## Visión General

El **Agente Consultor de Trámites Gubernamentales** es un sistema conversacional inteligente construido con LangGraph `create_react_agent` que ayuda a ciudadanos a preparar y validar sus documentos antes de realizar trámites oficiales. Inicialmente enfocado en trámites del SAT, con arquitectura escalable para otros trámites gubernamentales.

## Objetivos Fundamentales

### ✅ Qué Hace
- **Orientación clara**: Explica qué es cada trámite, requisitos y pasos
- **Validación de documentos**: Verifica formato, vigencia y legibilidad usando OCR
- **Preparación estructurada**: Genera checklist y paquete de datos listo para cita
- **Acompañamiento conversacional**: Respuestas naturales del LLM, no templates predefinidos

### ❌ Qué NO Hace
- No ejecuta trámites automáticamente en portales oficiales
- No garantiza aceptación en ventanilla (solo prepara)
- No accede a sistemas gubernamentales reales
- No almacena datos personales (procesamiento efímero opcional)

## Arquitectura con LangGraph

### Framework Base: `create_react_agent`

```python
from langgraph.prebuilt import create_react_agent

# Configuración del agente principal
tramite_agent = create_react_agent(
    model="claude-3-5-sonnet",
    tools=government_tools,
    system_prompt=conversational_system_prompt,
    state_modifier=conversation_state_manager
)
```

### ¿Por Qué ReAct Agent?

1. **Respuestas conversacionales**: El LLM genera texto natural, no respuestas predefinidas
2. **Razonamiento visible**: Puede explicar por qué necesita cada documento
3. **Uso de herramientas**: Integra OCR, validaciones y estado de manera fluida
4. **Estado persistente**: Mantiene contexto del trámite a través de la conversación
5. **Escalabilidad**: Agregar herramientas es trivial sin cambiar el núcleo

## Herramientas Especializadas

### 1. Gestión de Estado Conversacional
```python
@tool("manage_conversation_state")
def manage_conversation_state(action: str, data: ConversationState) -> StateResult:
    """Gestiona el estado del trámite y datos del usuario a través de la conversación"""
```

### 2. Validación de Documentos Gubernamentales
```python
@tool("validate_government_document") 
def validate_government_document(
    document_type: DocumentType, 
    file_data: bytes,
    tramite_context: TramiteContext
) -> DocumentValidationResult:
    """Valida documentos específicos para trámites gubernamentales usando OCR"""
```

### 3. Validación de Identificadores Oficiales
```python
@tool("validate_official_identifier")
def validate_official_identifier(
    identifier_type: IdentifierType,
    value: str
) -> IdentifierValidationResult:
    """Valida CURP, RFC, etc. con reglas específicas del SAT"""
```

### 4. Generación de Checklist Contextual
```python
@tool("generate_tramite_checklist")
def generate_tramite_checklist(
    tramite_type: TramiteType,
    current_documents: List[ValidatedDocument]
) -> TramiteChecklist:
    """Genera checklist específico para el tipo de trámite con estado actual"""
```

### 5. Explicación de Requisitos
```python
@tool("explain_requirement")
def explain_requirement(
    tramite_type: TramiteType,
    requirement: str,
    user_context: UserContext
) -> RequirementExplanation:
    """Explica por qué se necesita un requisito específico"""
```

## Flujo Conversacional Detallado

### Fase 1: Identificación del Trámite
```
Usuario: "Quiero sacar mi RFC"

Agente (razonamiento interno):
- Thought: Usuario solicita inscripción RFC primera vez
- Action: explain_requirement("sat_rfc_inscription", "overview", user_context)
- Observation: Requisitos obtenidos

Agente (respuesta natural):
"Perfecto, te ayudo con tu inscripción al RFC. Es tu clave única como contribuyente 
ante el SAT - la necesitas para trabajar, facturar o abrir cuentas bancarias. 

Para empezar, ¿me das tu nombre completo y CURP? Con eso puedo orientarte 
exactamente qué documentos necesitarás."
```

### Fase 2: Recolección y Validación
```
Usuario: "Me llamo Ana García, CURP: GARA900315MDFRRN05"

Agente (razonamiento interno):
- Thought: Recibí nombre y CURP, debo validar formato
- Action: validate_official_identifier("curp", "GARA900315MDFRRN05")
- Observation: CURP válida, mujer, nacida 1990, DF
- Action: manage_conversation_state("update", {nombre: "Ana García", curp: "GARA900315MDFRRN05"})

Agente (respuesta natural):
"Excelente Ana, tu CURP está correcta. Veo que naciste el 15 de marzo de 1990 
en la Ciudad de México. 

Ahora necesito verificar tu identificación oficial. ¿Tienes tu INE vigente? 
Puedes enviarme la foto - solo asegúrate de que se vean bien los bordes 
y no tenga reflejos."
```

### Fase 3: Validación de Documentos
```
Usuario: [Envía foto del INE]

Agente (razonamiento interno):
- Thought: Recibí imagen de identificación, debo procesarla
- Action: validate_government_document("ine", image_bytes, current_tramite_context)
- Observation: Nombre coincide (95%), documento vigente hasta 2029, legible
- Action: manage_conversation_state("update_document", ine_validation_result)

Agente (respuesta natural):
"Perfecto, tu INE se ve muy bien. El nombre coincide correctamente y está 
vigente hasta 2029. 

Solo me falta un comprobante de domicilio reciente - puede ser de luz, agua 
o teléfono de los últimos 3 meses. ¿Tienes alguno a la mano?"
```

### Fase 4: Preparación Final
```
Usuario: [Envía comprobante de luz]

Agente (razonamiento interno):
- Thought: Recibí comprobante, debo validar antigüedad y legibilidad
- Action: validate_government_document("comprobante_domicilio", file_bytes, tramite_context)
- Observation: Fecha septiembre 2024, CP 03100, legible, válido
- Action: generate_tramite_checklist("sat_rfc_inscription", validated_documents)
- Observation: Checklist completo - todos los requisitos cumplidos

Agente (respuesta natural):
"¡Excelente! Tu comprobante de luz de septiembre está perfecto - tiene menos 
de 3 meses y se ve toda tu información clara.

Ya tienes todo listo para tu cita en el SAT:
✅ CURP válida  
✅ INE vigente y legible
✅ Comprobante de domicilio reciente

¿Quieres que te prepare un resumen con tus datos organizados para que 
sea más fácil capturarlos en el portal del SAT?"
```

## Tipos de Datos Fundamentales

### ConversationState
```python
@dataclass
class ConversationState:
    tramite_type: Optional[TramiteType]
    user_profile: UserProfile
    validated_documents: List[ValidatedDocument]
    conversation_phase: ConversationPhase
    checklist_status: Dict[str, RequirementStatus]
    session_metadata: SessionMetadata
```

### UserProfile
```python
@dataclass
class UserProfile:
    full_name: Optional[str]
    birth_date: Optional[date]
    curp: Optional[ValidatedIdentifier]
    rfc: Optional[ValidatedIdentifier] 
    address: Optional[Address]
    contact_info: Optional[ContactInfo]
```

### ValidatedDocument
```python
@dataclass
class ValidatedDocument:
    document_type: DocumentType
    file_data: Optional[bytes]
    extracted_data: Dict[str, Any]
    validation_score: float
    validation_errors: List[ValidationError]
    expiry_date: Optional[date]
    is_valid: bool
```

### TramiteChecklist
```python
@dataclass
class TramiteChecklist:
    tramite_type: TramiteType
    requirements: List[Requirement]
    completion_status: CompletionStatus
    next_steps: List[NextStep]
    estimated_preparation_time: timedelta
```

## Prompt del Sistema

```
Eres un consultor especializado en trámites gubernamentales mexicanos, específicamente del SAT.

PERSONALIDAD:
- Conversacional, empático y profesional
- Explains el "porqué" de cada requisito
- Transparente sobre limitaciones
- Proactivo pero no invasivo

CAPACIDADES:
- Validas documentos usando OCR
- Explains trámites en lenguaje sencillo  
- Detectas errores comunes y sugieres soluciones
- Mantiene el estado de la conversación

LIMITACIONES QUE DEBES MENCIONAR:
- No ejecutas trámites automáticamente
- No garantizas aceptación final en ventanilla
- Solo preparas documentación y orientas

TONO:
- Siempre responde de manera natural y conversacional
- NUNCA uses respuestas predefinidas o templates
- Adapta tu lenguaje al contexto del usuario
- Sé paciente y explicativo

HERRAMIENTAS:
Tienes acceso a herramientas para validar documentos, identificadores oficiales,
gestionar el estado de la conversación y generar checklists contextuals.

Usa estas herramientas de manera fluida en tu conversación, pero siempre
explica qué estás haciendo y por qué.
```

## Escalabilidad Futura

### Agregar Nuevos Trámites
```python
# Nuevas herramientas específicas por trámite
@tool("validate_driving_license_requirements")
def validate_driving_license_requirements(...) -> ValidationResult:
    """Validación específica para licencias de conducir"""

@tool("validate_passport_requirements") 
def validate_passport_requirements(...) -> ValidationResult:
    """Validación específica para pasaportes"""

# El agente principal no cambia, solo se agregan herramientas
extended_agent = create_react_agent(
    model="claude-3-5-sonnet",
    tools=government_tools + driving_license_tools + passport_tools,
    system_prompt=enhanced_system_prompt
)
```

### Arquitectura Multi-Agente (Futuro)
```python
# Cuando tengas múltiples dominios, migrar a supervisor
from langgraph.prebuilt import create_supervisor_agent

supervisor = create_supervisor_agent([
    ("sat_specialist", sat_agent),
    ("license_specialist", license_agent), 
    ("passport_specialist", passport_agent)
])
```

## Nombres Según Development Standards

### Funciones/Métodos
```python
# ✅ Siguiendo estándares - describe qué hace
def validate_curp_format(curp: str) -> ValidationResult
def extract_document_data(image: bytes) -> ExtractionResult  
def generate_appointment_summary(state: ConversationState) -> AppointmentSummary

# ❌ Evitar - vago o genérico
def process_curp(curp: str) -> bool
def handle_document(image: bytes) -> dict
def create_summary(data: dict) -> str
```

### Tipos/Clases
```python
# ✅ Siguiendo estándares - conceptos claros del dominio
class DocumentValidator
class TramiteSession
class RequirementChecker
class ConversationState

# ❌ Evitar - términos prohibidos
class DocumentProcessor  
class SmartSession
class AdvancedChecker
class UniversalState
```

### Constantes
```python
# ✅ Siguiendo estándares - descriptivos
MAX_DOCUMENT_AGE_DAYS = 90
CURP_LENGTH_CHARACTERS = 18
INE_EXPIRY_CHECK_YEARS = 10

# ❌ Evitar - ambiguos
DOCUMENT_LIMIT = 90
CURP_SIZE = 18
ID_YEARS = 10
```

## Ventajas del Enfoque ReAct

1. **Conversacional Natural**: LLM genera respuestas contextuales, no scripts
2. **Razonamiento Transparente**: Usuario puede ver por qué el agente necesita algo
3. **Flexibilidad**: Se adapta a diferentes estilos de comunicación del usuario
4. **Herramientas Especializadas**: Validaciones precisas sin perder naturalidad
5. **Estado Persistente**: Mantiene contexto completo del trámite
6. **Escalabilidad**: Agregar trámites solo requiere nuevas herramientas
7. **Debugging**: Cada paso del razonamiento es visible

## Resultado Esperado

Un agente que se siente como **hablar con un consultor humano experto** que:
- Entiende tu situación específica
- Explica cada paso en lenguaje claro
- Valida tus documentos en tiempo real
- Te deja completamente preparado para tu trámite
- Nunca suena robótico o predefinido
- Se adapta a tu manera de comunicarte

El usuario nunca sentirá que está llenando un formulario, sino teniendo una **conversación productiva** que lo lleva paso a paso hacia su objetivo.