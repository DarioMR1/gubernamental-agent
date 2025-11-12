# LangGraph + FastAPI: Estructura de Proyecto Real

Esta guía explica la estructura pragmática de proyectos LangGraph con FastAPI basada en implementaciones reales de 2024-2025.

## 📁 Estructura General

```
langgraph-fastapi-app/
├── src/
│   ├── main.py                    # 🚀 FastAPI app entry point
│   ├── dependencies.py            # ⚡ Workflow precompilation & DI
│   ├── config.py                  # ⚙️ Application settings
│   │
│   ├── api/                       # 🌐 FastAPI HTTP layer
│   │   ├── routes/
│   │   │   ├── agents.py          # 🤖 Agent interaction endpoints
│   │   │   ├── chat.py            # 💬 Chat/conversation endpoints
│   │   │   └── health.py          # ❤️ Health check endpoints
│   │   └── schemas/               # 📋 Pydantic request/response models
│   │       ├── requests.py
│   │       └── responses.py
│   │
│   ├── agents/                    # 🧠 LangGraph AI layer
│   │   ├── workflows/             # 🔄 Graph definitions & orchestration
│   │   │   ├── rag_agent.py       # 📚 RAG workflow
│   │   │   └── chat_agent.py      # 💭 Chat workflow
│   │   ├── nodes/                 # 🔗 Individual graph nodes
│   │   │   ├── retrieval.py       # 🔍 Document retrieval
│   │   │   ├── generation.py      # ✨ LLM text generation
│   │   │   └── decision.py        # 🤔 Decision/routing logic
│   │   ├── tools/                 # 🛠️ Agent tools & functions
│   │   └── prompts/               # 📝 Prompt templates
│   │
│   ├── data/                      # 💾 Data persistence layer
│   │   ├── models.py              # 🗄️ Database/ORM models
│   │   ├── database.py            # 🔌 Database connections
│   │   └── repositories.py        # 📊 Data access patterns
│   │
│   └── utils/                     # 🔧 Shared utilities
│       ├── logging.py             # 📝 Logging configuration
│       ├── security.py            # 🔒 Authentication helpers
│       └── helpers.py             # 🎯 Common utilities
│
├── tests/                         # ✅ Test suite
├── docker/                        # 🐳 Containerization
├── .env.example                   # 🔑 Environment template
└── requirements.txt               # 📦 Python dependencies
```

---

## 🚀 Archivo Principal: `main.py`

**Propósito:** Entry point de la aplicación FastAPI

```python
from fastapi import FastAPI, Depends
from src.api.routes import agents, chat, health
from src.dependencies import get_compiled_workflows
from src.config import settings

app = FastAPI(title="LangGraph Agent API")

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(agents.router, prefix="/api/v1/agents", tags=["agents"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])

@app.on_event("startup")
async def startup_event():
    """Precompile workflows on startup for performance"""
    await get_compiled_workflows()
```

**Conexión LangGraph:** Inicializa y precompila workflows durante el startup para optimizar performance.

---

## ⚡ Precompilación: `dependencies.py`

**Propósito:** Dependency Injection y precompilación de workflows LangGraph

```python
from functools import lru_cache
from langgraph.graph import StateGraph
from src.agents.workflows.rag_agent import create_rag_workflow
from src.agents.workflows.chat_agent import create_chat_workflow

# Global workflow storage
_compiled_workflows = {}

@lru_cache()
def get_compiled_workflows():
    """Precompile LangGraph workflows for reuse"""
    global _compiled_workflows
    
    if not _compiled_workflows:
        _compiled_workflows = {
            "rag": create_rag_workflow().compile(),
            "chat": create_chat_workflow().compile()
        }
    
    return _compiled_workflows

def get_rag_workflow():
    """Dependency for RAG workflow"""
    workflows = get_compiled_workflows()
    return workflows["rag"]

def get_chat_workflow():
    """Dependency for chat workflow"""
    workflows = get_compiled_workflows()
    return workflows["chat"]
```

**Conexión LangGraph:** 
- Precompila workflows en memoria (evita recompilación en cada request)
- Usa `@lru_cache()` para singleton pattern
- Workflows compilados son reutilizables y thread-safe

---

## ⚙️ Configuración: `config.py`

**Propósito:** Configuración centralizada de la aplicación

```python
from pydantic import BaseSettings

class Settings(BaseSettings):
    # API Configuration
    app_name: str = "LangGraph Agent API"
    debug: bool = False
    
    # LLM Configuration
    openai_api_key: str
    model_name: str = "gpt-4"
    temperature: float = 0.7
    
    # Vector Store
    chroma_persist_directory: str = "./chroma_db"
    
    # Database
    database_url: str = "sqlite:///./app.db"
    
    class Config:
        env_file = ".env"

settings = Settings()
```

**Conexión LangGraph:** Proporciona configuración para modelos LLM, bases de datos vectoriales y checkpoints.

---

## 🌐 API Layer: Routes

### `api/routes/agents.py`

**Propósito:** Endpoints para interactuar con agentes LangGraph

```python
from fastapi import APIRouter, Depends, HTTPException
from src.dependencies import get_rag_workflow
from src.api.schemas.requests import AgentRequest
from src.api.schemas.responses import AgentResponse

router = APIRouter()

@router.post("/invoke", response_model=AgentResponse)
async def invoke_agent(
    request: AgentRequest,
    workflow = Depends(get_rag_workflow)
):
    """Invoke RAG agent with user query"""
    try:
        result = await workflow.ainvoke({
            "question": request.question,
            "context": request.context or []
        })
        
        return AgentResponse(
            answer=result["answer"],
            sources=result.get("sources", []),
            metadata=result.get("metadata", {})
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/stream")
async def stream_agent(
    request: AgentRequest,
    workflow = Depends(get_rag_workflow)
):
    """Stream agent responses"""
    async def generate():
        async for chunk in workflow.astream({
            "question": request.question
        }):
            yield f"data: {chunk}\n\n"
    
    return StreamingResponse(generate(), media_type="text/plain")
```

**Conexión LangGraph:**
- Usa `workflow.ainvoke()` para ejecución asíncrona
- `workflow.astream()` para streaming responses
- Dependency injection de workflows precompilados

### `api/routes/chat.py`

**Propósito:** Endpoints para conversaciones con memoria

```python
@router.post("/conversations/{thread_id}")
async def continue_conversation(
    thread_id: str,
    request: ChatRequest,
    workflow = Depends(get_chat_workflow)
):
    """Continue conversation with thread memory"""
    config = {"configurable": {"thread_id": thread_id}}
    
    result = await workflow.ainvoke(
        {"message": request.message},
        config=config
    )
    
    return ChatResponse(
        response=result["response"],
        thread_id=thread_id
    )
```

**Conexión LangGraph:**
- Usa `thread_id` para manejo de memoria conversacional
- LangGraph maneja automáticamente checkpoints por thread

---

## 🧠 LangGraph Layer: Agents

### `agents/workflows/rag_agent.py`

**Propósito:** Definición del workflow RAG usando LangGraph

```python
from langgraph.graph import StateGraph, END
from typing import TypedDict, List
from src.agents.nodes.retrieval import retrieve_documents
from src.agents.nodes.generation import generate_answer
from src.agents.nodes.decision import should_retrieve

class RAGState(TypedDict):
    question: str
    documents: List[str]
    answer: str
    needs_retrieval: bool

def create_rag_workflow():
    """Create RAG workflow graph"""
    workflow = StateGraph(RAGState)
    
    # Add nodes
    workflow.add_node("decide", should_retrieve)
    workflow.add_node("retrieve", retrieve_documents)
    workflow.add_node("generate", generate_answer)
    
    # Add edges
    workflow.set_entry_point("decide")
    workflow.add_conditional_edges(
        "decide",
        lambda x: "retrieve" if x["needs_retrieval"] else "generate"
    )
    workflow.add_edge("retrieve", "generate")
    workflow.add_edge("generate", END)
    
    return workflow
```

**Conexión LangGraph:**
- `StateGraph` define el flujo de estados
- Cada node es una función que transforma el estado
- Conditional edges permiten routing dinámico

### `agents/nodes/retrieval.py`

**Propósito:** Nodo para recuperación de documentos

```python
from src.data.repositories import get_vector_store
from src.agents.nodes.base import BaseNode

async def retrieve_documents(state: dict) -> dict:
    """Retrieve relevant documents for question"""
    question = state["question"]
    
    # Get vector store
    vector_store = get_vector_store()
    
    # Retrieve similar documents
    docs = await vector_store.asimilarity_search(
        question, 
        k=5
    )
    
    # Update state
    state["documents"] = [doc.page_content for doc in docs]
    state["needs_retrieval"] = False
    
    return state
```

**Conexión LangGraph:**
- Función que recibe y retorna el estado
- Modifica el estado compartido del workflow
- Integra con vector stores para RAG

### `agents/nodes/generation.py`

**Propósito:** Nodo para generación de respuestas con LLM

```python
from langchain.chat_models import ChatOpenAI
from src.agents.prompts.rag_prompts import RAG_PROMPT
from src.config import settings

llm = ChatOpenAI(
    model=settings.model_name,
    temperature=settings.temperature
)

async def generate_answer(state: dict) -> dict:
    """Generate answer using LLM"""
    question = state["question"]
    documents = state.get("documents", [])
    
    # Format context
    context = "\n".join(documents)
    
    # Generate response
    prompt = RAG_PROMPT.format(
        context=context,
        question=question
    )
    
    response = await llm.ainvoke(prompt)
    
    # Update state
    state["answer"] = response.content
    
    return state
```

**Conexión LangGraph:**
- Node function que integra LLM
- Usa estado compartido para context
- Retorna estado actualizado

---

## 📝 Prompts: `agents/prompts/rag_prompts.py`

**Propósito:** Templates de prompts reutilizables

```python
RAG_PROMPT = """
Basándote en el siguiente contexto, responde la pregunta del usuario.

Contexto:
{context}

Pregunta: {question}

Respuesta:
"""

CHAT_PROMPT = """
Eres un asistente útil. Responde de manera conversacional.

Historial:
{history}

Usuario: {message}
Asistente:
"""
```

**Conexión LangGraph:** Prompts reutilizables en múltiples nodes y workflows.

---

## 💾 Data Layer

### `data/database.py`

**Propósito:** Conexiones a bases de datos y vector stores

```python
from chromadb import Client
from sqlalchemy import create_engine
from src.config import settings

# Vector store connection
def get_vector_store():
    client = Client()
    collection = client.get_or_create_collection("documents")
    return collection

# SQL database connection
engine = create_engine(settings.database_url)
```

**Conexión LangGraph:**
- Vector stores para RAG retrieval
- SQL database para checkpoints persistentes
- Memoria conversacional

---

## 🔄 Flujo Completo de Ejecución

### 1. **Startup**
```
main.py → dependencies.py → workflows precompilados
```

### 2. **Request Handling**
```
FastAPI endpoint → Dependency injection → Workflow execution
```

### 3. **LangGraph Execution**
```
StateGraph → Node functions → State transformations → Response
```

### 4. **Memory Management**
```
Thread ID → LangGraph checkpoints → Persistent conversation
```

---

## 🎯 Patrones Clave LangGraph

### **State Management**
- Estado compartido entre nodes
- TypedDict para type safety
- Immutable transformations

### **Workflow Compilation**
- Precompilación para performance
- Thread-safe execution
- Reutilización de workflows

### **Memory & Checkpoints**
- Thread-based conversations
- Automatic state persistence
- Resume from any point

### **Streaming Responses**
- Real-time output
- Progressive generation
- Better UX

---

## 🚀 Beneficios de esta Estructura

✅ **Performance:** Workflows precompilados  
✅ **Escalabilidad:** Stateless design  
✅ **Mantenibilidad:** Separación clara de responsabilidades  
✅ **Flexibilidad:** Easy workflow modification  
✅ **Type Safety:** Pydantic + TypedDict  
✅ **Observabilidad:** Structured logging  

Esta estructura refleja **patrones reales** de proyectos LangGraph + FastAPI en producción, priorizando simplicidad y efectividad sobre arquitectura compleja.