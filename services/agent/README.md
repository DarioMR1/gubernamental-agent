# Government Procedures Agent API

AI agent specialized in Mexican government procedures, specifically focused on SAT (Servicio de Administración Tributaria) tramites.

## Overview

This agent acts as an intelligent consultant for government procedures, helping citizens prepare and validate their documents before executing official tramites. Built with LangGraph's `create_react_agent` and specialized tools for document validation, CURP verification, and procedure guidance.

## Specialization: RFC Registration for Individuals

The agent is currently specialized in **RFC Inscripción Persona Física** (RFC Registration for Physical Persons), providing:

- **Conversational guidance** through the entire process
- **CURP validation** with format checking and data extraction
- **Document validation** (currently without OCR, to be implemented later)
- **Intelligent checklist generation** based on user progress
- **Real-time state management** using SQLite database
- **Natural language explanations** of requirements and procedures

## Architecture

### ReAct Agent with Specialized Tools

```
LangGraph create_react_agent
├── OpenAI GPT-4 (conversational responses)
├── Specialized Tools:
│   ├── manage_conversation_state
│   ├── validate_official_identifier  
│   ├── validate_government_document
│   ├── generate_tramite_checklist
│   └── explain_requirement
└── SQLite Database (real state persistence)
```

## Project Structure

```
services/agent/
├── main.py                        # FastAPI app entry point
├── dependencies.py                # Workflow precompilation & DI
├── config.py                      # Government procedures settings
│
├── types/                         # Government domain types
│   ├── tramite_types.py          # TramiteType, DocumentType enums
│   ├── validation_types.py       # ValidationStatus, ConfidenceLevel
│   └── data_types.py             # ConversationState, UserProfile
│
├── api/                           # FastAPI HTTP layer
│   ├── routes/
│   │   ├── chat.py               # Chat endpoints (backward compatibility)
│   │   ├── tramites.py           # Government procedures endpoints
│   │   └── health.py             # Health check
│   └── schemas/                  # Pydantic models
│       ├── requests.py           # TramiteSession, CURP validation
│       └── responses.py          # ValidationResponse, ChecklistResponse
│
├── agents/                        # LangGraph AI layer
│   ├── workflows/
│   │   └── chat_agent.py         # ReAct agent with government tools
│   ├── tools/                    # Specialized government tools
│   │   ├── conversation_state_tool.py
│   │   ├── identifier_validation_tool.py
│   │   ├── document_validation_tool.py
│   │   ├── tramite_checklist_tool.py
│   │   └── requirement_explanation_tool.py
│   └── prompts/                  # Specialized prompts
│       └── chat_prompts.py       # SAT consultant system prompt
│
├── data/                         # Data persistence
│   ├── models.py                 # SQLAlchemy models (TramiteSession, UserProfile)
│   ├── database.py               # DB connection
│   └── repositories.py           # Data access
│
└── utils/                        # Utilities
    ├── logging.py
    └── helpers.py
```

## Instalación

1. **Clonar y navegar al directorio:**
```bash
cd services/agent
```

2. **Crear entorno virtual:**
```bash
python -m venv venv
source venv/bin/activate  # En Windows: venv\\Scripts\\activate
```

3. **Instalar dependencias:**
```bash
pip install -r requirements.txt
```

4. **Configurar variables de entorno:**
```bash
cp .env.example .env
# Editar .env con tu OpenAI API key
```

## Configuración

Edita el archivo `.env` con tus credenciales:

```env
OPENAI_API_KEY=tu_api_key_de_openai
MODEL_NAME=gpt-4o
TEMPERATURE=0.7
DEBUG=false
PORT=8000
```

## Uso

### Iniciar el servidor
```bash
cd src
python main.py
```

O usando uvicorn:
```bash
uvicorn src.main:app --reload --host 0.0.0.0 --port 8000
```

### Acceder a la API

- **API Docs**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

### Endpoints Principales

#### Crear conversación
```bash
POST /api/v1/chat/conversations
Content-Type: application/json

{
  "title": "Mi nueva conversación"
}
```

#### Enviar mensaje
```bash
POST /api/v1/chat/conversations/{conversation_id}/messages
Content-Type: application/json

{
  "message": "Hola, ¿cómo estás?"
}
```

#### Obtener conversaciones
```bash
GET /api/v1/chat/conversations
```

#### Obtener conversación específica
```bash
GET /api/v1/chat/conversations/{conversation_id}
```

## Arquitectura LangGraph

El workflow de conversación sigue este flujo:

```
Usuario → [load_history] → [generate] → [save_turn] → Respuesta
```

1. **load_history**: Carga el historial de conversación
2. **generate**: Genera respuesta usando OpenAI
3. **save_turn**: Guarda el intercambio en la base de datos

## Desarrollo

### Ejecutar en modo debug
```bash
export DEBUG=true
python src/main.py
```

### Estructura de base de datos

- **conversations**: ID, título, timestamps
- **messages**: ID, conversation_id, role, content, timestamp

## Funcionalidades Avanzadas

- ✅ **Precompilación de workflows** para mejor performance
- ✅ **Manejo de memoria conversacional** limitado para evitar overflow
- ✅ **Validación de entrada** con Pydantic
- ✅ **Manejo de errores** robusto
- ✅ **Logging estructurado**
- ✅ **CORS configurado** para desarrollo frontend

## Próximos pasos

- [ ] Streaming de respuestas
- [ ] Autenticación de usuarios
- [ ] Deployment con Docker
- [ ] Tests automatizados
- [ ] Integración con vector store para RAG