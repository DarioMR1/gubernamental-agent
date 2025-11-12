# Governmental Agent Service

Servicio principal del agente gubernamental que maneja la automatización de portales peruanos.

## 🚀 Quick Start

```bash
# Install dependencies
make install

# Run development server
make dev

# API Documentation
open http://localhost:8000/docs
```

## 📁 Estructura

```
services/agent/
├── src/                    # Código fuente
│   ├── api/               # FastAPI routes y middleware
│   ├── core/              # Agente principal y state manager
│   ├── llm/               # Integración con LLMs
│   ├── workflow/          # LangGraph workflows
│   ├── executor/          # Playwright automation
│   ├── monitoring/        # Logging y observabilidad
│   └── types/             # Tipos compartidos
├── storage/               # Archivos y datos
├── pyproject.toml         # Configuración Python
├── requirements.txt       # Dependencias
└── Makefile              # Comandos de desarrollo
```

## 🛠️ Comandos Disponibles

```bash
make help           # Ver todos los comandos disponibles
make install        # Instalar dependencias
make dev            # Servidor de desarrollo
make prod           # Servidor de producción
make test           # Ejecutar tests
make format         # Formatear código
make lint           # Verificar código
```

## 📊 API Endpoints

### Sessions
- `POST /sessions` - Crear nueva sesión
- `GET /sessions` - Listar sesiones
- `GET /sessions/{id}` - Detalles de sesión
- `DELETE /sessions/{id}` - Eliminar sesión

### Workflows
- `GET /workflows/pending-approvals` - Aprobaciones pendientes
- `POST /workflows/{session_id}/approve` - Aprobar/denegar
- `GET /workflows/{session_id}/stream` - Stream en tiempo real

### Health
- `GET /health` - Estado del servicio

## 🔧 Configuración

Variables de entorno requeridas:

```bash
# LLM APIs
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=...

# Environment
ENVIRONMENT=development
LOG_LEVEL=DEBUG

# Optional
DATABASE_URL=sqlite:///agent.db
```

## 🎯 Uso

### Ejemplo básico:
```bash
curl -X POST http://localhost:8000/sessions \
  -H "Content-Type: application/json" \
  -d '{"instruction": "descargar constancia de RUC para empresa 20123456789"}'
```

### Response:
```json
{
  "success": true,
  "data": {
    "session_id": "uuid-here",
    "status": "processing",
    "message": "Session created successfully"
  }
}
```

## 📚 Documentación

Para documentación completa del proyecto, ver [CLAUDE.md](../../CLAUDE.md) en la raíz del repositorio.