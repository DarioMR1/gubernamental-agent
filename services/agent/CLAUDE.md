# Gubernamental Agent - Documentación Técnica Completa

## 🎯 Visión General del Sistema

El **Gubernamental Agent** es un sistema de automatización inteligente que utiliza IA y orquestación de workflows para interactuar autónomamente con portales gubernamentales peruanos. El sistema combina comprensión de lenguaje natural, planificación inteligente de acciones y ejecución web robusta para automatizar tareas complejas como descarga de documentos, llenado de formularios y consultas de información.

### Tecnologías Core
- **LangGraph**: Orquestación de workflows con state management
- **FastAPI**: API REST con middleware stack empresarial  
- **Playwright**: Automatización web cross-browser
- **Pydantic**: Validación de datos type-safe
- **Structlog**: Logging estructurado
- **OpenAI/Anthropic**: Proveedores LLM para IA

## 🏗️ Arquitectura del Sistema

### Flujo de Ejecución Principal
```
Usuario → FastAPI → Core Agent → LangGraph Workflow → Playwright Executor → Portal Web
   ↓           ↓           ↓              ↓                    ↓             ↓
Instrucción  Validación   State      Orquestación         Acciones     Resultados
   ↓           ↓           ↓              ↓                    ↓             ↓
Session    Middleware   Storage       Monitoring         Screenshots   Audit Trail
```

### Componentes Principales

1. **API Layer** (`src/api/`): Interfaz REST con middleware
2. **Core Agent** (`src/core/`): Lógica central y state management
3. **LLM Integration** (`src/llm/`): Procesamiento de lenguaje natural
4. **Workflow Engine** (`src/workflow/`): Orquestación con LangGraph
5. **Web Executor** (`src/executor/`): Automatización con Playwright
6. **Monitoring System** (`src/monitoring/`): Observabilidad completa
7. **Storage Layer** (`src/storage/`): Persistencia y archivos
8. **Configuration** (`src/config/`): Gestión de configuración

## 📝 Componentes Detallados

### 1. API Layer (`src/api/`)

#### `main.py` - Aplicación FastAPI Principal
**Responsabilidad**: Configurar y exponer la API REST

**Funciones Clave**:
- `create_application()`: Factory para crear la app FastAPI
- `_configure_middleware()`: Setup del stack de middleware
- `_configure_error_handlers()`: Manejo global de errores
- `_configure_routes()`: Registro de routers

**Middleware Stack** (orden de ejecución):
1. `TrustedHostMiddleware`: Validación de hosts permitidos
2. `CORSMiddleware`: Configuración CORS
3. `ErrorHandlingMiddleware`: Manejo centralizado de errores
4. `RequestTrackingMiddleware`: Tracking de requests con UUID
5. `LoggingMiddleware`: Logging estructurado de requests
6. `AuthMiddleware`: Autenticación y autorización

#### `types.py` - Tipos API
**Responsabilidad**: Definir tipos para requests/responses de la API

**Tipos Principales**:
- `CreateSessionRequest`: Request para crear nueva sesión
- `SessionResponse`: Response con info de sesión
- `ApprovalRequest/Response`: Manejo de aprobaciones humanas
- `SuccessResponse[T]`: Wrapper genérico para responses exitosos
- `ListResponse[T]`: Response paginado para listados
- `ErrorResponse`: Response estándar para errores

#### `routes/sessions.py` - Gestión de Sesiones
**Responsabilidad**: CRUD de sesiones del agente

**Endpoints**:
- `POST /`: Crear nueva sesión con instrucción NL
- `GET /`: Listar sesiones con paginación y filtros
- `GET /{session_id}`: Obtener detalles de sesión
- `PATCH /{session_id}`: Actualizar propiedades de sesión
- `DELETE /{session_id}`: Eliminar sesión y recursos
- `POST /{session_id}/abort`: Abortar ejecución activa
- `GET /{session_id}/history`: Obtener historial de ejecución
- `GET /{session_id}/downloads/{file_id}`: Descargar archivo

**Características**:
- Autenticación requerida en todos los endpoints
- Validación de ownership de sesiones
- Manejo de archivos descargados
- Control de ejecuciones activas

#### `routes/workflows.py` - Gestión de Workflows
**Responsabilidad**: Control de workflows y aprobaciones

**Endpoints**:
- `GET /pending-approvals`: Lista de sesiones pendientes de aprobación
- `GET /{session_id}/approval-request`: Detalles de request de aprobación
- `POST /{session_id}/approve`: Aprobar/denegar ejecución
- `GET /{session_id}/execution-plan`: Obtener plan de ejecución
- `GET /{session_id}/stream`: Stream SSE de updates en tiempo real
- `GET /{session_id}/history`: Historial completo del workflow

**Funciones de Soporte**:
- `_assess_risk_level()`: Evaluación automática de riesgo
- `_calculate_progress()`: Cálculo de progreso de ejecución

#### `middleware/` - Stack de Middleware

##### `auth.py` - Autenticación
**Responsabilidad**: Autenticación JWT y autorización basada en roles

**Funciones**:
- `get_current_user()`: Extraer usuario del token JWT
- `require_permission()`: Decorator para validar permisos
- `require_role()`: Decorator para validar roles

##### `logging.py` - Logging de Requests
**Responsabilidad**: Logging estructurado de requests HTTP

**Características**:
- Extracción de IP real (X-Forwarded-For, X-Real-IP)
- Timing de requests
- Logging de errores con context
- Headers de response para observabilidad

##### `tracking.py` - Request Tracking
**Responsabilidad**: Generar UUID único por request para trazabilidad

##### `errors.py` - Error Handling
**Responsabilidad**: Manejo centralizado y normalización de errores

### 2. Core Agent (`src/core/`)

#### `agent.py` - Agente Principal
**Responsabilidad**: Orquestación principal y API del agente

**Clase `GovernmentalAgent`**:
```python
class GovernmentalAgent:
    def __init__(self, config: AgentConfig)
    async def execute_instruction(self, instruction: str) -> AgentResponse
    async def get_status(self, session_id: str) -> AgentResponse
    async def abort_execution(self, session_id: str) -> bool
    async def approve_action(self, session_id: str, approved: bool, feedback: str) -> bool
    async def get_execution_summary(self, session_id: str) -> ExecutionSummary
```

**Funcionalidad Clave**:
- Inicialización de componentes (parser, planner, executor)
- Gestión de ejecuciones concurrentes con asyncio.Task
- Tracking de approval requests
- Interface principal para consumidores externos

**Flujo de `execute_instruction()`**:
1. Crear sesión con StateManager
2. Lanzar workflow en background con asyncio.create_task
3. Retornar respuesta inmediata
4. Workflow continúa asíncronamente

#### `state.py` - State Manager
**Responsabilidad**: Persistencia y gestión de estado de sesiones

**Clase `AgentStateManager`**:
```python
class AgentStateManager:
    def __init__(self, config: AgentConfig)
    async def create_session(self, instruction: str) -> AgentState
    async def get_session(self, session_id: str) -> AgentState
    async def update_session(self, state: AgentState) -> None
    async def update_status(self, session_id: str, status: SessionStatus) -> None
    async def set_execution_plan(self, session_id: str, plan: ExecutionPlan) -> None
```

**Características**:
- Cache in-memory para sesiones activas
- Persistencia en disco como backup
- Serialización/deserialización de objetos complejos
- Atomic writes con temp files
- Lock para thread safety

### 3. LLM Integration (`src/llm/`)

#### `instruction_parser.py` - Parser de Instrucciones
**Responsabilidad**: Convertir lenguaje natural en instrucciones estructuradas

**Clase `InstructionParser`**:
```python
class InstructionParser:
    async def parse_instruction(self, text: str) -> ParsedInstruction
    async def extract_intent(self, text: str) -> Intent
    async def identify_entities(self, text: str) -> List[Entity]
```

**Base de Conocimiento de Portales**:
```python
PORTAL_KNOWLEDGE = {
    "sunat": PortalKnowledge(
        name="SUNAT",
        base_url="https://sunat.gob.pe",
        document_types=["constancia de RUC", "certificado de no adeudo"],
        typical_flows=["download_constancia_ruc"],
        authentication_method="form"
    )
}
```

**Flujo de Parsing**:
1. **Extract Intent**: LLM identifica tipo de intención (download_document, fill_form, etc.)
2. **Extract Entities**: NER para extraer RUC, DNI, portales, documentos
3. **Portal Identification**: Mapeo de entidades a portales conocidos
4. **Confidence Calculation**: Score basado en claridad de intent y entities

**Fallback Strategy**: Si LLM falla, usa regex patterns para entidades básicas

#### `action_planner.py` - Planificador de Acciones
**Responsabilidad**: Convertir instrucciones parseadas en planes de ejecución

**Clase `ActionPlanner`**:
```python
class ActionPlanner:
    async def create_execution_plan(self, instruction: ParsedInstruction) -> ExecutionPlan
    async def optimize_plan(self, plan: ExecutionPlan) -> ExecutionPlan
    async def validate_plan(self, plan: ExecutionPlan) -> ValidationResult
```

**Templates de Portal** (Knowledge-based Planning):
```python
PORTAL_TEMPLATES = {
    "sunat": {
        "download_constancia_ruc": [
            {"type": "navigate", "url": "https://sunat.gob.pe"},
            {"type": "click", "selector": "a[href*='consulta-ruc']"},
            {"type": "fill_form", "field": "ruc"},
            {"type": "download", "wait_for": "download"}
        ]
    }
}
```

**Estrategias de Planning**:
1. **Template-based**: Para flujos conocidos de portales específicos
2. **LLM-generated**: Para casos no cubiertos por templates
3. **Hybrid**: Combinación de ambos con customización

**Plan Optimization**:
- Eliminación de screenshots redundantes
- Combinación de waits secuenciales
- Ajuste de timeouts por tipo de acción

**Plan Validation**:
- Verificación de secuencia lógica
- Validación de parámetros requeridos
- Assessment de riesgos de seguridad

#### `providers/` - Proveedores LLM

##### `base.py` - Interfaz Base
**Responsabilidad**: Definir contrato común para proveedores LLM

##### `openai_provider.py` - Proveedor OpenAI
**Responsabilidad**: Implementación específica para API de OpenAI

##### `anthropic_provider.py` - Proveedor Anthropic
**Responsabilidad**: Implementación específica para API de Anthropic

### 4. Workflow Engine (`src/workflow/`)

#### `graph.py` - Definición del Workflow
**Responsabilidad**: Construcción y compilación del grafo LangGraph

**Clase `AgentWorkflow`**:
```python
class AgentWorkflow:
    def __init__(self, config: AgentConfig)
    def _build_graph(self) -> StateGraph
    def compile_workflow(self) -> None
    async def execute_workflow(self, initial_state: AgentState) -> AgentState
    async def resume_workflow(self, thread_id: str, approved: bool) -> AgentState
```

**Nodos del Grafo**:
- `parse_instruction`: Parseo con LLM
- `create_plan`: Generación de plan
- `validate_plan`: Validación de seguridad
- `request_approval`: Solicitud de aprobación humana
- `execute_action`: Ejecución individual de acciones
- `validate_result`: Validación de resultados
- `handle_error`: Manejo de errores
- `complete`: Finalización

**Edges Condicionales**:
```python
workflow.add_conditional_edges(
    "validate_plan",
    self.conditions.should_request_approval,
    {
        "approve": "request_approval",
        "execute": "execute_action", 
        "error": "handle_error"
    }
)
```

**Checkpointing**: LangGraph persiste estado automáticamente para resumption

#### `nodes.py` - Implementación de Nodos
**Responsabilidad**: Lógica de cada nodo del workflow

**Clase `WorkflowNodes`**:
```python
class WorkflowNodes:
    async def instruction_parsing_node(self, state: AgentState) -> AgentState
    async def planning_node(self, state: AgentState) -> AgentState
    async def execution_node(self, state: AgentState) -> AgentState
    # ... otros nodos
```

**Patrón por Nodo**:
1. Update del stage en AgentState
2. Ejecución de la lógica específica
3. Storage de resultados en session_variables
4. Error handling con ErrorContext
5. Return del estado actualizado

#### `conditions.py` - Lógica Condicional
**Responsabilidad**: Funciones de routing para edges condicionales

**Funciones Clave**:
- `should_request_approval()`: Evalúa si requiere aprobación humana
- `approval_granted()`: Verifica respuesta de aprobación
- `should_continue_execution()`: Determina si continuar ejecución
- `should_retry_after_error()`: Estrategia de recovery post-error

### 5. Web Executor (`src/executor/`)

#### `playwright_executor.py` - Executor Principal
**Responsabilidad**: Orquestación de automatización web con Playwright

**Clase `PlaywrightExecutor`**:
```python
class PlaywrightExecutor:
    async def start(self) -> None
    async def execute_action(self, action: Action) -> ActionResult
    async def take_screenshot(self, filename: str) -> str
    async def cleanup(self) -> None
```

**Lifecycle Management**:
1. `start()`: Launch browser, create context, setup downloads
2. `execute_action()`: Dispatch por tipo de acción
3. `cleanup()`: Close browser y resources

**Browser Configuration**:
- Headless mode configurable
- Window size personalizable
- Download directory setup
- Context con permisos de descarga
- Timeouts configurables

**Action Dispatch**:
```python
if action.type == ActionType.NAVIGATE:
    await self._execute_navigate(action)
elif action.type == ActionType.CLICK:
    await self._execute_click(action)
# ... otros tipos
```

**Error Handling**:
- Screenshot automático en errores
- Retry logic por acción
- Cleanup en exceptions

#### `actions/navigation.py` - Acciones de Navegación
**Responsabilidad**: Operaciones de navegación y interacción básica

**Funciones**:
- `navigate_to_page()`: Navegación con wait conditions
- `click_element()`: Click con scroll y wait
- `scroll_to_element()`: Scroll inteligente
- `wait_for_navigation()`: Wait por navegación
- `check_element_exists()`: Verificación de existencia

**Características**:
- Retry automático con `@retry_on_failure`
- Wait conditions apropiadas (`networkidle`, `domcontentloaded`)
- Scroll automático para elementos fuera del viewport

#### `actions/form_filling.py` - Llenado de Formularios
**Responsabilidad**: Interacción con formularios web

**Funciones**:
- `fill_text_field()`: Llenado de campos de texto
- `select_dropdown_option()`: Selección en dropdowns
- `check_checkbox()`: Manejo de checkboxes
- `upload_file()`: Upload de archivos
- `submit_form()`: Envío de formularios

**Características Avanzadas**:
- `fill_text_field_slowly()`: Typing gradual para evitar detección
- Dispatch de eventos (change, blur) para validación JS
- Validation helpers para campos requeridos
- Multiple selection strategies para dropdowns

#### `actions/file_download.py` - Gestión de Descargas
**Responsabilidad**: Manejo de descargas de archivos

**Funciones**:
- `download_file()`: Download via click en link
- `download_file_direct_url()`: Download directo de URL
- `wait_for_download()`: Esperar completación
- `verify_download_completed()`: Verificación de integridad

**Características**:
- Sanitización automática de filenames
- Verificación de completitud de descarga
- Multiple download strategies
- Cleanup de descargas parciales

### 6. Monitoring System (`src/monitoring/`)

#### `logger.py` - Structured Logging
**Responsabilidad**: Sistema de logging estructurado con contexto

**Clase `StructuredLogger`**:
```python
class StructuredLogger:
    def __init__(self, config: AgentConfig)
    def get_session_logger(self, session_id: str) -> BoundLogger
    def log_action_start(self, action: Action, session_id: str) -> None
    def log_llm_request(self, session_id: str, provider: str, ...) -> None
```

**Configuración Structlog**:
- Processors para timestamp, level, JSON rendering
- File + console handlers
- Session-specific log files
- Filtering por log level

**Tipos de Logs**:
- Action lifecycle (start, success, error)
- LLM interactions (requests, tokens, cost)
- Approval events (requests, responses)
- Security events (con severity levels)
- Performance metrics

#### `screenshot_manager.py` - Gestión de Screenshots
**Responsabilidad**: Captura, organización y procesamiento de screenshots

**Clase `ScreenshotManager`**:
```python
class ScreenshotManager:
    async def capture_on_action(self, session_id: str, action_name: str) -> str
    async def capture_on_error(self, session_id: str, error_context: str) -> str
    async def create_session_timeline(self, session_id: str) -> List[Screenshot]
    async def create_session_collage(self, session_id: str) -> str
```

**Características**:
- Screenshots automáticos por acción
- Error screenshots con contexto visual
- Timeline cronológico de sesión
- Collage visual para overview
- Metadata completa por screenshot

#### `session_recorder.py` - Grabación de Sesiones
**Responsabilidad**: Audit trail completo de sesiones

**Clase `SessionRecorder`**:
```python
class SessionRecorder:
    async def start_recording(self, session_id: str, instruction: str) -> None
    async def record_action(self, session_id: str, action: Action, result: ActionResult) -> None
    async def stop_recording(self, session_id: str, final_status: SessionStatus) -> SessionRecording
```

**SessionRecording Data**:
- Actions ejecutadas y resultados
- Workflow events y transiciones
- LLM interactions completas
- Approval events
- Screenshots y archivos
- Performance metrics

**Export Formats**:
- JSON estructurado
- HTML report visual
- CSV para análisis

### 7. Types System (`src/types/`)

#### Tipos de Estado
```python
@dataclass
class AgentState:
    session_id: str
    user_instruction: str
    status: SessionStatus
    current_stage: WorkflowStage
    current_step: int = 0
    execution_plan: Optional[ExecutionPlan] = None
    execution_history: List[ActionResult] = field(default_factory=list)
    session_variables: Dict[str, Any] = field(default_factory=dict)
    error_context: Optional[ErrorContext] = None
```

#### Tipos de Acción
```python
@dataclass
class Action:
    id: str
    type: ActionType
    parameters: Dict[str, Any]
    expected_result: str
    timeout_seconds: int = 30
    retry_attempts: int = 0
```

#### Tipos de Resultado
```python
@dataclass
class ActionResult:
    action_id: str
    success: bool
    execution_time: float
    screenshot_path: Optional[str] = None
    error_message: Optional[str] = None
    data_extracted: Optional[Dict[str, Any]] = None
    retry_count: int = 0
```

### 8. Configuration (`src/config/`)

#### `settings.py` - Configuración Principal
**Responsabilidad**: Gestión centralizada de configuración

```python
@dataclass
class AgentConfig:
    llm: LLMConfig
    playwright: PlaywrightConfig
    monitoring: MonitoringConfig
    storage_path: str = "./storage"
    max_retry_attempts: int = 3
    execution_timeout_seconds: int = 300
```

#### `environment.py` - Variables de Entorno
**Responsabilidad**: Carga de configuración desde environment

```python
class Environment:
    OPENAI_API_KEY: str
    ANTHROPIC_API_KEY: str
    DATABASE_URL: str = "sqlite:///gubernamental_agent.db"
    LOG_LEVEL: str = "INFO"
    ENVIRONMENT: str = "development"
```

## 🔄 Flujos de Ejecución Detallados

### Flujo Principal: Execute Instruction
```
1. API Request (POST /sessions)
   ├─ Middleware stack processing
   ├─ Request validation
   └─ Authentication/authorization

2. Core Agent.execute_instruction()
   ├─ Create session with StateManager
   ├─ Launch background workflow task
   └─ Return immediate response

3. Background Workflow Execution
   ├─ parse_instruction node
   │  ├─ LLM instruction parsing
   │  ├─ Entity extraction
   │  └─ Confidence calculation
   ├─ create_plan node
   │  ├─ Template matching
   │  ├─ LLM plan generation (fallback)
   │  └─ Plan optimization
   ├─ validate_plan node
   │  ├─ Safety validation
   │  ├─ Parameter checking
   │  └─ Risk assessment
   ├─ Conditional: Approval Required?
   │  ├─ Yes: request_approval node → wait for human
   │  └─ No: execute_action node
   ├─ execute_action node (loop)
   │  ├─ Get next action from plan
   │  ├─ Playwright execution
   │  ├─ Screenshot capture
   │  ├─ Result validation
   │  └─ Continue if more actions
   ├─ validate_result node
   │  ├─ Success rate calculation
   │  ├─ Data validation
   │  └─ Determine completion
   └─ complete node
      ├─ Cleanup resources
      ├─ Final status update
      └─ Session recording finalization
```

### Flujo de Error Handling
```
Error Occurs in Any Node
├─ handle_error node
│  ├─ Error classification
│  ├─ Retry count check
│  ├─ Recovery strategy determination
│  │  ├─ Retry: return to execute_action
│  │  ├─ Human intervention: request_approval
│  │  └─ Abort: complete with failed status
│  ├─ Error context storage
│  └─ Screenshot capture
├─ Error logging
├─ Metrics update
└─ User notification (if applicable)
```

### Flujo de Approval
```
request_approval Node
├─ Set status to REQUIRES_APPROVAL
├─ Create approval context
├─ Store approval request
└─ Interrupt workflow (LangGraph checkpoint)

Human Approval via API
├─ POST /workflows/{session_id}/approve
├─ Validation of pending approval
├─ Resume workflow with approval response
├─ Continue execution or abort based on response
└─ Audit log of approval decision
```

## 🔧 Configuración y Deployment

### Configuración por Entornos

#### Development
```python
ENVIRONMENT = "development"
LOG_LEVEL = "DEBUG"
PLAYWRIGHT_HEADLESS = False
SCREENSHOT_ON_ACTION = True
SCREENSHOT_ON_ERROR = True
```

#### Production
```python
ENVIRONMENT = "production"
LOG_LEVEL = "INFO"
PLAYWRIGHT_HEADLESS = True
SCREENSHOT_ON_ACTION = False  # Performance
SCREENSHOT_ON_ERROR = True
```

### Comandos de Desarrollo (Makefile)
```bash
make install          # Install dependencies + Playwright browsers
make dev             # Run development server
make test            # Run test suite
make lint            # Code quality checks
make format          # Code formatting
make clean           # Cleanup generated files
```

## 🔒 Seguridad y Compliance

### Medidas Implementadas
1. **Input Validation**: Pydantic schemas en toda la API
2. **Authentication**: JWT con roles y permisos
3. **Request Tracking**: UUID por request para audit
4. **Error Sanitization**: No exposición de internals
5. **Resource Timeouts**: Prevención de ejecuciones infinitas
6. **Human Approval**: Control para operaciones sensibles
7. **Audit Trail**: Logging completo de todas las operaciones

### Evaluación de Riesgos
```python
def _assess_risk_level(state) -> str:
    # High risk: Authentication, form submission, updates
    if intent_type in ["submit_application", "update_information", "authenticate"]:
        return "high"
    
    # Medium risk: Low confidence or form filling
    if confidence < 0.7 or intent_type in ["fill_form", "download_document"]:
        return "medium"
    
    # Low risk: Read-only operations
    return "low"
```

## 📊 Monitoring y Observabilidad

### Métricas Clave
- **Session Success Rate**: % sesiones completadas exitosamente
- **Action Success Rate**: % acciones individuales exitosas
- **Average Execution Time**: Tiempo promedio por sesión
- **LLM Token Usage**: Consumo y costo de tokens LLM
- **Error Rate by Portal**: Errores específicos por portal
- **Human Intervention Rate**: % sesiones que requirieron aprobación

### Logging Structure
```json
{
  "timestamp": "2024-01-15T10:30:45.123Z",
  "session_id": "uuid-session-id",
  "level": "info",
  "event": "Action completed successfully",
  "action_id": "action-uuid",
  "action_type": "click",
  "execution_time": 1.23,
  "screenshot_path": "/path/to/screenshot.png"
}
```

## 🚀 Extensibilidad

### Agregar Nuevo Portal
1. **Knowledge Base**: Actualizar `PORTAL_KNOWLEDGE` en `instruction_parser.py`
2. **Templates**: Agregar templates en `PORTAL_TEMPLATES` en `action_planner.py`
3. **Testing**: Crear tests específicos para el nuevo portal
4. **Documentation**: Actualizar documentación de portales soportados

### Agregar Nuevo Action Type
1. **Enum**: Agregar a `ActionType` en `types/action_types.py`
2. **Executor**: Implementar `_execute_new_action()` en `playwright_executor.py`
3. **Action Module**: Crear módulo específico en `executor/actions/`
4. **Validation**: Agregar validación en `action_planner.py`

### Agregar Nuevo LLM Provider
1. **Interface**: Implementar `BaseLLMProvider` en `llm/providers/`
2. **Configuration**: Agregar config en `LLMConfig`
3. **Factory**: Actualizar factory en parsers y planners
4. **Testing**: Tests de integración específicos

## 🧪 Testing Strategy

### Tipos de Tests
1. **Unit Tests**: Componentes individuales aislados
2. **Integration Tests**: Interacción entre componentes
3. **E2E Tests**: Flujos completos con portales reales
4. **Performance Tests**: Load testing y benchmarks

### Estructura de Tests
```
tests/
├── unit/
│   ├── test_agent.py
│   ├── test_parser.py
│   ├── test_planner.py
│   └── test_executor.py
├── integration/
│   ├── test_workflow.py
│   ├── test_api.py
│   └── test_storage.py
└── e2e/
    ├── test_sunat_flow.py
    ├── test_essalud_flow.py
    └── test_approval_flow.py
```

## 📈 Performance Considerations

### Optimizaciones Implementadas
1. **Async/Await**: Operaciones no-bloqueantes
2. **Connection Pooling**: Reutilización de conexiones HTTP
3. **Caching**: Cache de sesiones activas en memoria
4. **Resource Cleanup**: Liberación automática de recursos
5. **Screenshot Optimization**: Compresión y cleanup automático

### Scaling Strategies
1. **Horizontal Scaling**: Múltiples instancias del agente
2. **Load Balancing**: Distribución de carga entre instancias
3. **Database Scaling**: PostgreSQL para persistencia distribuida
4. **Caching Layer**: Redis para cache distribuido
5. **Queue System**: Celery para processing asíncrono

## 🔄 Mantenimiento y Operaciones

### Health Checks
- **API Health**: `/health` endpoint con dependency checks
- **Database Connectivity**: Verificación de conexión a DB
- **LLM Provider Status**: Validación de APIs externas
- **Browser Status**: Verificación de Playwright

### Backup Strategy
- **Database Backups**: Snapshots regulares de estado
- **File Backups**: Screenshots y downloads importantes
- **Configuration Backups**: Versioning de configuración

### Log Rotation
- **Daily Rotation**: Logs por día con compresión
- **Retention Policy**: 30 días de logs locales
- **Archive Strategy**: Backup a almacenamiento externo

## 🎯 Casos de Uso Específicos

### Ejemplo: Descarga de Constancia RUC
```python
# Request
POST /sessions
{
    "instruction": "descargar constancia de RUC para la empresa 20123456789",
    "priority": 3
}

# Flujo interno:
1. Parser identifica: intent=download_document, portal=sunat, entity=RUC
2. Planner usa template sunat.download_constancia_ruc
3. Workflow ejecuta: navigate → authenticate → find_section → download
4. Screenshots capturados en cada paso
5. Archivo descargado y disponible via API
```

### Ejemplo: Consulta con Baja Confianza
```python
# Request
POST /sessions
{
    "instruction": "hacer algo en el portal del gobierno"
}

# Flujo interno:
1. Parser retorna confidence < 0.7
2. Planner marca requires_approval = true
3. Workflow llega a request_approval node
4. Status cambia a REQUIRES_APPROVAL
5. Workflow se pausa esperando decisión humana
6. Admin aprueba/rechaza via API
7. Workflow continúa o aborta según decisión
```

## 📚 Conclusiones y Arquitectura

Este sistema representa un ejemplo de **arquitectura empresarial moderna** que combina:

1. **Event-Driven Architecture**: Workflows asíncronos con state management
2. **Microservices Patterns**: Componentes desacoplados con interfaces bien definidas
3. **Observability First**: Logging, metrics y tracing comprehensive
4. **Security by Design**: Validación, autenticación y audit trail
5. **Extensibility**: Plugin architecture para nuevos portales y actions

La implementación demuestra **best practices** en:
- Type safety con Pydantic
- Error handling robusto
- Resource management
- Testing strategy
- Configuration management
- Performance optimization

El resultado es un sistema **production-ready** capaz de manejar automatización compleja con supervisión humana apropiada y observabilidad completa.