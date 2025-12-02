# Sistema Multiagente con Google ADK

## Guía Completa para Construir Arquitecturas de Agentes Inteligentes

### 📋 Tabla de Contenidos
1. [Conceptos Fundamentales](#conceptos-fundamentales)
2. [Arquitectura del Sistema](#arquitectura-del-sistema)
3. [ToolContext - Estado Compartido](#toolcontext---estado-compartido)
4. [Creación de Herramientas (Tools)](#creación-de-herramientas-tools)
5. [Diseño de Agentes](#diseño-de-agentes)
6. [Coordinación Inteligente](#coordinación-inteligente)
7. [Callbacks del Sistema](#callbacks-del-sistema)
8. [Estructura de Proyecto](#estructura-de-proyecto)
9. [Mejores Prácticas](#mejores-prácticas)
10. [Ejemplos de Implementación](#ejemplos-de-implementación)

---

## Conceptos Fundamentales

### ¿Qué es un Sistema Multiagente?

Un sistema multiagente es una arquitectura donde múltiples agentes de IA colaboran para resolver problemas complejos. Cada agente tiene:

- **Especialización**: Responsabilidad específica y bien definida
- **Autonomía**: Capacidad de tomar decisiones dentro de su dominio
- **Colaboración**: Habilidad para transferir control y compartir información
- **Estado Compartido**: Acceso a una memoria común del sistema

### Componentes Clave en ADK

```python
from google.adk.agents import Agent
from google.adk.tools.tool_context import ToolContext
from google.adk.agents.callback_context import CallbackContext
```

---

## Arquitectura del Sistema

### Patrón Coordinador-Especialistas

```
┌─────────────────────┐
│   AGENTE PRINCIPAL  │  ← Coordinador que maneja el flujo
│   (Coordinator)     │
└──────────┬──────────┘
           │
           ├─── Subagente A (Especialista en Dominio X)
           ├─── Subagente B (Especialista en Dominio Y)  
           └─── Subagente C (Especialista en Dominio Z)
```

### Estructura Base

```python
# 1. AGENTE COORDINADOR
main_agent = Agent(
    name="main_coordinator",
    model="gemini-2.0-flash",
    description="Coordinador principal del sistema",
    instruction="Instrucciones de routing y coordinación",
    sub_agents=[specialist_a, specialist_b, specialist_c],
    tools=[shared_tools],
    before_agent_callback=initialize_system_state
)

# 2. SUBAGENTES ESPECIALISTAS  
specialist_agent = Agent(
    name="specialist_domain_x",
    model="gemini-2.0-flash", 
    description="Especialista en dominio X",
    instruction="Instrucciones específicas del dominio",
    tools=[domain_specific_tools],
    sub_agents=[]  # Puede tener sus propios subagentes
)
```

---

## ToolContext - Estado Compartido

### El Cerebro del Sistema

El `ToolContext` es la memoria compartida entre todos los agentes. Actúa como una base de datos en tiempo real donde cada agente puede:

- **Leer** información previa
- **Escribir** nuevos datos
- **Actualizar** estados existentes
- **Mantener** historial de interacciones

### Estructura del Estado

```python
def initialize_session_state(callback_context: CallbackContext):
    """Inicializa el estado compartido del sistema"""
    
    # Campos base del sistema
    base_fields = {
        "user_data": {},           # Información del usuario
        "current_context": "",     # Contexto actual
        "workflow_state": "init",  # Estado del flujo de trabajo
        "session_history": [],     # Historial de acciones
        "shared_memory": {},       # Memoria compartida
        "preferences": {},         # Preferencias del usuario
        "temporary_data": {}       # Datos temporales
    }
    
    # Verificar e inicializar campos faltantes
    for field, default_value in base_fields.items():
        if field not in callback_context.state:
            callback_context.state[field] = default_value
    
    return None  # No modifica la respuesta del agente
```

### Acceso al Estado en Herramientas

```python
def my_tool_function(tool_context: ToolContext, parameter: str) -> dict:
    """Ejemplo de herramienta que utiliza el estado compartido"""
    
    # LEER del estado
    user_data = tool_context.state.get("user_data", {})
    current_workflow = tool_context.state.get("workflow_state", "")
    
    # PROCESAR la lógica específica
    result = process_business_logic(parameter, user_data)
    
    # ESCRIBIR al estado
    tool_context.state["last_action"] = "my_tool_executed"
    tool_context.state["result_data"] = result
    
    # ACTUALIZAR historial
    history = tool_context.state.get("session_history", [])
    history.append({
        "tool": "my_tool_function",
        "parameter": parameter,
        "timestamp": datetime.now().isoformat(),
        "result": "success"
    })
    tool_context.state["session_history"] = history
    
    return {
        "status": "success",
        "data": result,
        "message": "Operación completada exitosamente"
    }
```

---

## Creación de Herramientas (Tools)

### Patrón de Herramientas

Las herramientas son funciones Python que extienden las capacidades de los agentes:

```python
from datetime import datetime
from typing import Dict, List, Optional

def data_processor_tool(
    tool_context: ToolContext, 
    input_data: str, 
    processing_type: str = "default",
    options: Optional[Dict] = None
) -> Dict:
    """
    Herramienta genérica para procesamiento de datos
    
    Args:
        tool_context: Contexto para acceso al estado
        input_data: Datos a procesar
        processing_type: Tipo de procesamiento a realizar
        options: Opciones adicionales de configuración
    
    Returns:
        Dict con resultado del procesamiento
    """
    try:
        # Validar entrada
        if not input_data:
            return {"status": "error", "message": "Datos de entrada requeridos"}
        
        # Obtener configuración del estado
        config = tool_context.state.get("processing_config", {})
        options = options or {}
        
        # Procesar según el tipo
        if processing_type == "analyze":
            result = analyze_data(input_data, config, options)
        elif processing_type == "transform":
            result = transform_data(input_data, config, options)
        elif processing_type == "validate":
            result = validate_data(input_data, config, options)
        else:
            result = default_processing(input_data, config, options)
        
        # Actualizar estado
        tool_context.state["last_processing"] = {
            "type": processing_type,
            "timestamp": datetime.now().isoformat(),
            "input_size": len(str(input_data)),
            "result_status": "success"
        }
        
        return {
            "status": "success",
            "result": result,
            "processing_type": processing_type,
            "timestamp": datetime.now().isoformat()
        }
        
    except Exception as e:
        # Log del error en el estado
        tool_context.state["last_error"] = {
            "tool": "data_processor_tool",
            "error": str(e),
            "timestamp": datetime.now().isoformat()
        }
        
        return {
            "status": "error",
            "message": f"Error en procesamiento: {str(e)}"
        }

def state_manager_tool(
    tool_context: ToolContext,
    action: str,
    key: str,
    value: Optional[str] = None
) -> Dict:
    """
    Herramienta para gestión del estado compartido
    
    Args:
        tool_context: Contexto del sistema
        action: Acción a realizar (get, set, delete, list)
        key: Clave del estado a manipular
        value: Valor a asignar (solo para 'set')
    """
    if action == "get":
        return {
            "status": "success",
            "key": key,
            "value": tool_context.state.get(key, None)
        }
    
    elif action == "set":
        if value is None:
            return {"status": "error", "message": "Valor requerido para 'set'"}
        tool_context.state[key] = value
        return {
            "status": "success", 
            "message": f"Clave '{key}' actualizada",
            "key": key,
            "value": value
        }
    
    elif action == "delete":
        if key in tool_context.state:
            del tool_context.state[key]
            return {"status": "success", "message": f"Clave '{key}' eliminada"}
        return {"status": "warning", "message": f"Clave '{key}' no encontrada"}
    
    elif action == "list":
        keys = list(tool_context.state.keys())
        return {
            "status": "success",
            "keys": keys,
            "total": len(keys)
        }
    
    else:
        return {
            "status": "error", 
            "message": f"Acción inválida: {action}"
        }
```

### Herramientas Especializadas por Dominio

```python
# Ejemplo: Herramientas para un dominio de análisis de datos
def analyze_dataset(tool_context: ToolContext, dataset_id: str, analysis_type: str) -> dict:
    """Analiza un dataset específico"""
    pass

def generate_report(tool_context: ToolContext, data_source: str, format: str) -> dict:
    """Genera reportes en diferentes formatos"""
    pass

def validate_results(tool_context: ToolContext, results: dict, criteria: dict) -> dict:
    """Valida resultados contra criterios específicos"""
    pass
```

---

## Diseño de Agentes

### Agente Coordinador

```python
coordinator_agent = Agent(
    name="system_coordinator",
    model="gemini-2.0-flash",
    description="Coordinador principal que gestiona el flujo del sistema",
    instruction="""
    Eres el coordinador principal de un sistema multiagente.
    
    <current_state>
    Estado actual: {workflow_state}
    Usuario: {user_data}
    Contexto: {current_context}
    </current_state>
    
    <session_history>
    {session_history}
    </session_history>
    
    ## TU FUNCIÓN PRINCIPAL
    
    Analizar las solicitudes del usuario y dirigir el flujo hacia el agente especializado correcto.
    
    ## AGENTES ESPECIALIZADOS DISPONIBLES
    
    1. **Data Analysis Agent**: Procesamiento y análisis de datos
       - Análisis estadístico
       - Visualización de datos  
       - Generación de insights
    
    2. **Content Generation Agent**: Creación de contenido
       - Redacción de textos
       - Generación de reportes
       - Creación de presentaciones
    
    3. **Task Management Agent**: Gestión de tareas
       - Planificación de proyectos
       - Seguimiento de progreso
       - Asignación de recursos
    
    ## LÓGICA DE ROUTING
    
    ### Análisis de Datos
    ```
    Usuario menciona: "analizar", "datos", "estadísticas", "gráficos"
    → Dirigir a Data Analysis Agent
    ```
    
    ### Creación de Contenido  
    ```
    Usuario solicita: "escribir", "generar", "crear documento", "redactar"
    → Dirigir a Content Generation Agent
    ```
    
    ### Gestión de Tareas
    ```
    Usuario necesita: "planificar", "organizar", "agenda", "tareas"
    → Dirigir a Task Management Agent
    ```
    
    ## INSTRUCCIONES ESPECÍFICAS
    
    1. **Análisis del Contexto**: Siempre revisa el estado actual antes de decidir
    2. **Transferencia Inteligente**: Explica por qué transfiere a un agente específico
    3. **Continuidad**: Mantén el contexto entre transferencias
    4. **Fallback**: Si no está claro, pregunta al usuario para clarificar
    """,
    sub_agents=[data_agent, content_agent, task_agent],
    tools=[state_manager_tool],
    before_agent_callback=initialize_session_state
)
```

### Agente Especializado

```python
data_analysis_agent = Agent(
    name="data_analysis_specialist",
    model="gemini-2.0-flash", 
    description="Especialista en análisis y procesamiento de datos",
    instruction="""
    Eres un especialista en análisis de datos con capacidades avanzadas.
    
    <user_context>
    Usuario: {user_data}
    Datos disponibles: {available_datasets}
    Análisis previos: {previous_analyses}
    </user_context>
    
    ## TU ESPECIALIZACIÓN
    
    Procesamiento, análisis y visualización de datos utilizando herramientas especializadas.
    
    ## FLUJO DE TRABAJO
    
    ### 1. Análisis de Requerimientos
    - Identificar el tipo de análisis requerido
    - Validar la disponibilidad de datos
    - Definir métricas y objetivos
    
    ### 2. Procesamiento de Datos
    - Limpieza y preparación
    - Transformación de formatos
    - Validación de calidad
    
    ### 3. Análisis y Cálculos
    - Estadísticas descriptivas
    - Correlaciones y tendencias
    - Modelos predictivos (si aplica)
    
    ### 4. Generación de Resultados
    - Visualizaciones claras
    - Reportes ejecutivos
    - Recomendaciones basadas en datos
    
    ## HERRAMIENTAS DISPONIBLES
    
    - `analyze_dataset()`: Análisis estadístico completo
    - `generate_visualizations()`: Creación de gráficos
    - `data_processor_tool()`: Procesamiento general
    - `validate_results()`: Validación de resultados
    
    ## INSTRUCCIONES ESPECÍFICAS
    
    1. **SIEMPRE** usa las herramientas disponibles para obtener datos reales
    2. **NUNCA** inventes estadísticas o resultados
    3. **EXPLICA** cada paso del análisis al usuario
    4. **VALIDA** los resultados antes de presentarlos
    5. **SUGIERE** próximos pasos basados en los hallazgos
    """,
    tools=[
        analyze_dataset,
        data_processor_tool,
        validate_results,
        state_manager_tool
    ],
    sub_agents=[]  # Puede tener subagentes propios si es necesario
)
```

---

## Coordinación Inteligente

### Patrón de Routing Dinámico

```python
def intelligent_routing_instruction():
    return """
    ## SISTEMA DE ROUTING INTELIGENTE
    
    ### Análisis de Entrada
    1. **Tipo de Solicitud**: ¿Qué quiere hacer el usuario?
    2. **Contexto Actual**: ¿En qué parte del flujo estamos?
    3. **Datos Disponibles**: ¿Qué información tenemos?
    4. **Historia Previa**: ¿Qué ha hecho antes?
    
    ### Decisiones de Transferencia
    
    ```python
    # Pseudocódigo para routing
    if user_request.contains(["analizar", "datos", "estadísticas"]):
        if workflow_state == "data_ready":
            → Transfer to Analysis Agent
        else:
            → First get data, then transfer
    
    elif user_request.contains(["escribir", "documento", "reporte"]):
        if analysis_complete:
            → Transfer to Content Agent with analysis results
        else:
            → First complete analysis, then transfer
    
    elif user_request.contains(["planificar", "organizar"]):
        → Transfer to Task Management Agent
    
    else:
        → Ask for clarification
    ```
    
    ### Transferencia con Contexto
    
    Al transferir a un agente especializado:
    1. **Resume** lo que el usuario necesita
    2. **Proporciona** todo el contexto relevante
    3. **Explica** por qué elegiste ese agente
    4. **Establece** expectativas claras
    """
```

### Ejemplo de Transferencia Inteligente

```python
# En el instruction del agente coordinador
"""
### EJEMPLO DE TRANSFERENCIA EXITOSA

Usuario: "Quiero analizar las ventas del último trimestre y crear un reporte"

Análisis:
- Necesita: Análisis de datos + Generación de contenido
- Estado actual: {workflow_state}
- Datos disponibles: {available_data}

Decisión:
1. Si tenemos datos → Data Analysis Agent primero
2. Cuando termine análisis → Content Generation Agent
3. Coordinar flujo completo

Respuesta:
"Perfecto! Veo que necesitas un análisis completo de ventas y un reporte. 
Te conectaré primero con nuestro especialista en análisis de datos para 
procesar la información del trimestre, y luego con el generador de contenido 
para crear tu reporte ejecutivo."
"""
```

---

## Callbacks del Sistema

### Before Agent Callback

```python
async def system_initializer(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback ejecutado antes de procesar cualquier mensaje
    Ideal para inicialización y verificación de estado
    """
    # Verificar inicialización
    required_fields = [
        "user_data", "workflow_state", "session_history", 
        "preferences", "temporary_data", "shared_memory"
    ]
    
    for field in required_fields:
        if field not in callback_context.state:
            callback_context.state[field] = get_default_value(field)
    
    # Actualizar timestamp de la sesión
    callback_context.state["last_activity"] = datetime.now().isoformat()
    
    # Incrementar contador de interacciones
    interactions = callback_context.state.get("interaction_count", 0)
    callback_context.state["interaction_count"] = interactions + 1
    
    # Logging del sistema (opcional)
    log_interaction(callback_context.state)
    
    return None  # No modifica la respuesta del agente

def get_default_value(field_name: str):
    """Retorna valores por defecto según el campo"""
    defaults = {
        "user_data": {},
        "workflow_state": "initialized", 
        "session_history": [],
        "preferences": {"language": "es", "timezone": "UTC"},
        "temporary_data": {},
        "shared_memory": {}
    }
    return defaults.get(field_name, {})

def log_interaction(state: dict):
    """Log opcional para debugging y monitoreo"""
    print(f"[SYSTEM] Interaction #{state.get('interaction_count', 0)} - "
          f"State: {state.get('workflow_state', 'unknown')}")
```

### After Agent Callback (si es necesario)

```python
async def cleanup_callback(callback_context: CallbackContext) -> Optional[types.Content]:
    """
    Callback ejecutado después del procesamiento
    Útil para limpieza y persistencia
    """
    # Limpiar datos temporales antiguos
    temp_data = callback_context.state.get("temporary_data", {})
    current_time = datetime.now()
    
    for key, data in list(temp_data.items()):
        if should_cleanup(data, current_time):
            del temp_data[key]
    
    # Persistir datos importantes (si tienes BD externa)
    persist_critical_data(callback_context.state)
    
    return None
```

---

## Estructura de Proyecto

### Organización Recomendada

```
my_multiagent_system/
├── main.py                     # Punto de entrada
├── requirements.txt            # Dependencias
├── config/
│   ├── __init__.py
│   ├── settings.py            # Configuraciones generales
│   └── agent_configs.py       # Configuraciones específicas
├── core/
│   ├── __init__.py
│   ├── callbacks.py           # Callbacks del sistema
│   ├── state_manager.py       # Gestión del estado
│   └── routing.py             # Lógica de routing
├── tools/
│   ├── __init__.py
│   ├── common_tools.py        # Herramientas compartidas
│   ├── data_tools.py          # Herramientas de datos
│   ├── content_tools.py       # Herramientas de contenido
│   └── task_tools.py          # Herramientas de tareas
├── agents/
│   ├── __init__.py
│   ├── coordinator/
│   │   ├── __init__.py
│   │   └── agent.py           # Agente coordinador
│   ├── data_specialist/
│   │   ├── __init__.py
│   │   ├── agent.py           # Especialista en datos
│   │   └── tools.py           # Herramientas específicas
│   ├── content_specialist/
│   │   ├── __init__.py
│   │   ├── agent.py           # Especialista en contenido
│   │   └── tools.py
│   └── task_specialist/
│       ├── __init__.py
│       ├── agent.py           # Especialista en tareas
│       └── tools.py
├── utils/
│   ├── __init__.py
│   ├── helpers.py             # Funciones auxiliares
│   └── validators.py          # Validadores
└── tests/
    ├── __init__.py
    ├── test_agents.py
    ├── test_tools.py
    └── test_integration.py
```

### Archivo Principal (main.py)

```python
from google.adk.agents import Agent
from core.callbacks import system_initializer
from agents.coordinator.agent import coordinator_agent

def create_multiagent_system():
    """Crea e inicializa el sistema multiagente"""
    
    # El coordinador ya tiene configurados todos los subagentes
    main_system = coordinator_agent
    
    return main_system

def main():
    """Función principal del sistema"""
    system = create_multiagent_system()
    
    print("🚀 Sistema Multiagente Inicializado")
    print("📁 Agentes disponibles:", [agent.name for agent in system.sub_agents])
    print("🛠️  Herramientas cargadas:", len(system.tools))
    
    return system

if __name__ == "__main__":
    app = main()
```

---

## Mejores Prácticas

### 1. Diseño de Estado

```python
# ✅ BUENA PRÁCTICA: Estado estructurado y tipado
def initialize_structured_state(callback_context: CallbackContext):
    state_schema = {
        # Datos del usuario
        "user": {
            "profile": {},
            "preferences": {},
            "history": []
        },
        
        # Estado del workflow
        "workflow": {
            "current_stage": "init",
            "completed_stages": [],
            "next_actions": []
        },
        
        # Datos de trabajo
        "workspace": {
            "active_data": {},
            "results": {},
            "temporary": {}
        },
        
        # Metadatos del sistema
        "system": {
            "session_id": str(uuid.uuid4()),
            "created_at": datetime.now().isoformat(),
            "last_update": datetime.now().isoformat(),
            "interaction_count": 0
        }
    }
    
    for category, fields in state_schema.items():
        if category not in callback_context.state:
            callback_context.state[category] = fields
```

### 2. Manejo de Errores

```python
def robust_tool_wrapper(tool_func):
    """Decorator para manejo robusto de errores en herramientas"""
    def wrapper(tool_context: ToolContext, *args, **kwargs):
        try:
            result = tool_func(tool_context, *args, **kwargs)
            
            # Log de éxito
            log_tool_success(tool_func.__name__, args, kwargs)
            
            return result
            
        except ValidationError as e:
            return {
                "status": "validation_error",
                "message": f"Error de validación: {str(e)}",
                "tool": tool_func.__name__
            }
            
        except ExternalServiceError as e:
            return {
                "status": "service_error", 
                "message": f"Error de servicio externo: {str(e)}",
                "tool": tool_func.__name__,
                "retry_possible": True
            }
            
        except Exception as e:
            # Log del error
            log_tool_error(tool_func.__name__, str(e), args, kwargs)
            
            return {
                "status": "system_error",
                "message": f"Error del sistema: {str(e)}",
                "tool": tool_func.__name__
            }
    
    return wrapper
```

### 3. Comunicación Entre Agentes

```python
# ✅ BUENA PRÁCTICA: Protocolo de comunicación estandarizado
def create_agent_message(
    from_agent: str,
    to_agent: str, 
    message_type: str,
    payload: dict,
    metadata: dict = None
) -> dict:
    """Crear mensaje estructurado entre agentes"""
    return {
        "from": from_agent,
        "to": to_agent,
        "type": message_type,
        "payload": payload,
        "metadata": metadata or {},
        "timestamp": datetime.now().isoformat(),
        "message_id": str(uuid.uuid4())
    }

def store_agent_message(tool_context: ToolContext, message: dict):
    """Almacenar mensaje en el historial inter-agente"""
    messages = tool_context.state.get("agent_messages", [])
    messages.append(message)
    tool_context.state["agent_messages"] = messages
```

### 4. Validación de Flujos

```python
def validate_agent_transition(
    current_agent: str, 
    target_agent: str, 
    workflow_state: str
) -> bool:
    """Valida si la transición entre agentes es válida"""
    
    valid_transitions = {
        "coordinator": ["data_specialist", "content_specialist", "task_specialist"],
        "data_specialist": ["coordinator", "content_specialist"],
        "content_specialist": ["coordinator", "data_specialist"], 
        "task_specialist": ["coordinator"]
    }
    
    allowed_targets = valid_transitions.get(current_agent, [])
    return target_agent in allowed_targets
```

---

## Ejemplos de Implementación

### Ejemplo 1: Sistema de Análisis de Documentos

```python
# Agente Coordinador
document_coordinator = Agent(
    name="document_coordinator",
    instruction="""
    Coordina el análisis completo de documentos:
    
    1. Si recibo un documento → OCR Agent
    2. Si tengo texto extraído → Analysis Agent  
    3. Si necesito resumen → Summary Agent
    4. Si necesito traducción → Translation Agent
    """,
    sub_agents=[ocr_agent, analysis_agent, summary_agent, translation_agent]
)

# Herramienta de OCR
def extract_text_from_document(tool_context: ToolContext, document_path: str) -> dict:
    # Lógica de extracción de texto
    extracted_text = perform_ocr(document_path)
    
    # Guardar en estado
    tool_context.state["document_text"] = extracted_text
    tool_context.state["document_processed"] = True
    
    return {"status": "success", "text": extracted_text}
```

### Ejemplo 2: Sistema de E-commerce

```python
# Sistema para tienda online
ecommerce_coordinator = Agent(
    name="ecommerce_coordinator", 
    instruction="""
    Gestiona experiencia de compra completa:
    
    - Búsqueda de productos → Search Agent
    - Recomendaciones → Recommendation Agent
    - Carrito y checkout → Payment Agent
    - Soporte al cliente → Support Agent
    """,
    sub_agents=[search_agent, recommendation_agent, payment_agent, support_agent]
)

# Herramienta de gestión de carrito
def manage_shopping_cart(tool_context: ToolContext, action: str, product_id: str = None) -> dict:
    cart = tool_context.state.get("shopping_cart", [])
    
    if action == "add" and product_id:
        cart.append({"product_id": product_id, "quantity": 1})
        tool_context.state["shopping_cart"] = cart
        return {"status": "success", "message": "Producto añadido al carrito"}
    
    elif action == "remove" and product_id:
        cart = [item for item in cart if item["product_id"] != product_id]
        tool_context.state["shopping_cart"] = cart
        return {"status": "success", "message": "Producto eliminado del carrito"}
    
    elif action == "view":
        return {"status": "success", "cart": cart, "total_items": len(cart)}
```

### Ejemplo 3: Sistema de Gestión de Proyectos

```python
# Coordinador de proyectos
project_coordinator = Agent(
    name="project_coordinator",
    instruction="""
    Gestiona el ciclo completo de proyectos:
    
    1. Planificación → Planning Agent
    2. Asignación de recursos → Resource Agent
    3. Seguimiento → Tracking Agent
    4. Reportes → Reporting Agent
    """,
    sub_agents=[planning_agent, resource_agent, tracking_agent, reporting_agent]
)

# Herramienta de gestión de tareas
def manage_project_tasks(tool_context: ToolContext, project_id: str, action: str, task_data: dict = None) -> dict:
    projects = tool_context.state.get("projects", {})
    
    if project_id not in projects:
        projects[project_id] = {"tasks": [], "status": "active", "created": datetime.now().isoformat()}
    
    project = projects[project_id]
    
    if action == "create_task" and task_data:
        task = {
            "id": str(uuid.uuid4()),
            "title": task_data.get("title"),
            "description": task_data.get("description"),
            "priority": task_data.get("priority", "medium"),
            "status": "pending",
            "created": datetime.now().isoformat()
        }
        project["tasks"].append(task)
        
    elif action == "update_status" and task_data:
        task_id = task_data.get("task_id")
        new_status = task_data.get("status")
        
        for task in project["tasks"]:
            if task["id"] == task_id:
                task["status"] = new_status
                task["updated"] = datetime.now().isoformat()
                break
    
    tool_context.state["projects"] = projects
    return {"status": "success", "project": project}
```

---

## Debugging y Monitoreo

### Sistema de Logging

```python
import logging
from datetime import datetime

def setup_multiagent_logging():
    """Configura logging específico para sistemas multiagente"""
    
    # Logger principal
    logger = logging.getLogger("multiagent_system")
    logger.setLevel(logging.INFO)
    
    # Handler para archivos
    file_handler = logging.FileHandler("multiagent_system.log")
    file_handler.setLevel(logging.INFO)
    
    # Formato específico
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - AGENT:%(agent_name)s - %(levelname)s - %(message)s'
    )
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    return logger

def log_agent_transition(from_agent: str, to_agent: str, reason: str):
    """Log específico para transiciones entre agentes"""
    logger = logging.getLogger("multiagent_system")
    logger.info(f"TRANSITION: {from_agent} → {to_agent} | Reason: {reason}", 
                extra={"agent_name": from_agent})

def log_tool_execution(tool_name: str, agent_name: str, success: bool, execution_time: float):
    """Log específico para ejecución de herramientas"""
    logger = logging.getLogger("multiagent_system")
    status = "SUCCESS" if success else "FAILED"
    logger.info(f"TOOL: {tool_name} | Status: {status} | Time: {execution_time:.3f}s",
                extra={"agent_name": agent_name})
```

### Métricas del Sistema

```python
def collect_system_metrics(tool_context: ToolContext) -> dict:
    """Recolecta métricas del sistema multiagente"""
    
    metrics = {
        "session": {
            "duration": calculate_session_duration(tool_context.state),
            "interactions": tool_context.state.get("interaction_count", 0),
            "agents_used": get_agents_used(tool_context.state)
        },
        "performance": {
            "average_response_time": calculate_avg_response_time(tool_context.state),
            "tool_success_rate": calculate_tool_success_rate(tool_context.state),
            "error_count": get_error_count(tool_context.state)
        },
        "workflow": {
            "current_stage": tool_context.state.get("workflow_state", "unknown"),
            "completed_tasks": count_completed_tasks(tool_context.state),
            "pending_tasks": count_pending_tasks(tool_context.state)
        }
    }
    
    return metrics
```

---

## Conclusión

Este sistema multiagente con Google ADK proporciona:

- **🔄 Coordinación Inteligente**: Routing automático basado en contexto
- **🧠 Memoria Compartida**: Estado persistente entre todos los agentes
- **🛠️ Herramientas Especializadas**: Funciones específicas para cada dominio
- **📊 Monitoreo Completo**: Logging y métricas en tiempo real
- **🔧 Extensibilidad**: Fácil adición de nuevos agentes y capacidades

### Próximos Pasos

1. **Implementa** tu primer sistema siguiendo la estructura base
2. **Personaliza** las herramientas según tu dominio específico
3. **Prueba** diferentes configuraciones de routing
4. **Optimiza** el rendimiento basado en métricas
5. **Escala** añadiendo nuevos agentes especializados

¡Tu sistema multiagente está listo para resolver problemas complejos de manera inteligente y coordinada! 🚀