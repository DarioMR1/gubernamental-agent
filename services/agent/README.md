# Chat Agent API

Agente conversacional desarrollado con **LangGraph** y **FastAPI** que utiliza OpenAI para generar respuestas inteligentes y mantiene historial de conversaciones en SQLite.

## Características

- 🤖 **LangGraph**: Workflow avanzado para manejo de conversaciones
- ⚡ **FastAPI**: API REST moderna y rápida
- 💾 **SQLite**: Persistencia de conversaciones y mensajes
- 🧠 **OpenAI**: Generación de respuestas con GPT-4
- 🔄 **Memoria Conversacional**: Mantiene contexto entre mensajes
- 📝 **API Documentation**: Swagger UI automática

## Estructura del Proyecto

```
services/agent/
├── src/
│   ├── main.py                    # FastAPI app entry point
│   ├── dependencies.py            # Workflow precompilation & DI
│   ├── config.py                  # Application settings
│   │
│   ├── api/                       # FastAPI HTTP layer
│   │   ├── routes/
│   │   │   ├── chat.py            # Chat endpoints
│   │   │   └── health.py          # Health check
│   │   └── schemas/               # Pydantic models
│   │       ├── requests.py
│   │       └── responses.py
│   │
│   ├── agents/                    # LangGraph AI layer
│   │   ├── workflows/
│   │   │   └── chat_agent.py      # Chat workflow
│   │   ├── nodes/                 # Graph nodes
│   │   │   ├── conversation.py    # LLM interaction
│   │   │   └── memory.py          # Memory management
│   │   └── prompts/               # Prompt templates
│   │       └── chat_prompts.py
│   │
│   ├── data/                      # Data persistence
│   │   ├── models.py              # SQLAlchemy models
│   │   ├── database.py            # DB connection
│   │   └── repositories.py        # Data access
│   │
│   └── utils/                     # Utilities
│       ├── logging.py
│       └── helpers.py
│
├── tests/                         # Test suite
├── .env.example                   # Environment template
└── requirements.txt               # Dependencies
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