# Governmental Agent REST API

FastAPI-based REST API for the Governmental Agent system. This API provides endpoints for managing agent sessions, workflow execution, and human approval processes.

## 🚀 Quick Start

### Development Server

```bash
# Simple development server
python dev_server.py

# Or with full options
python run_server.py --env development --reload
```

### Using Make Commands

```bash
# Install dependencies
make install

# Run development server
make dev

# Run with auto-reload
make dev-reload

# Run tests
make test

# Format code
make format
```

## 📋 API Endpoints

### Health Check
- `GET /health/` - Comprehensive health check
- `GET /health/ready` - Readiness probe  
- `GET /health/live` - Liveness probe

### Sessions Management
- `POST /v1/sessions/` - Create new session
- `GET /v1/sessions/` - List sessions (paginated)
- `GET /v1/sessions/{session_id}` - Get session details
- `PATCH /v1/sessions/{session_id}` - Update session
- `DELETE /v1/sessions/{session_id}` - Delete session
- `POST /v1/sessions/{session_id}/abort` - Abort session execution
- `GET /v1/sessions/{session_id}/history` - Get execution history
- `GET /v1/sessions/{session_id}/downloads/{file_id}` - Download session files

### Workflow Management
- `GET /v1/workflows/pending-approvals` - Get pending approvals
- `GET /v1/workflows/{session_id}/approval-request` - Get approval details
- `POST /v1/workflows/{session_id}/approve` - Approve/deny session
- `GET /v1/workflows/{session_id}/execution-plan` - Get execution plan
- `GET /v1/workflows/{session_id}/stream` - Stream execution updates (SSE)
- `GET /v1/workflows/{session_id}/history` - Get workflow history

## 🔐 Authentication

The API uses JWT Bearer token authentication. Include the token in the Authorization header:

```bash
curl -H "Authorization: Bearer YOUR_JWT_TOKEN" \
  http://localhost:8000/v1/sessions/
```

### Development Mode
For development, you can use the bypass token:
```bash
curl -H "Authorization: Bearer dev-bypass-token" \
  http://localhost:8000/v1/sessions/
```

## 📊 API Documentation

When running in development mode:
- **OpenAPI/Swagger**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## 🔧 Configuration

Configure the API using environment variables (see `.env.example`):

### API Settings
```env
API_HOST=0.0.0.0
API_PORT=8000
ENVIRONMENT=development
```

### CORS for React Frontend
```env
CORS_ORIGINS=http://localhost:3000,http://localhost:3001
```

### Authentication
```env
JWT_SECRET=your_jwt_secret_key_here
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24
```

## 🎯 Example Usage

### Create a New Session

```bash
curl -X POST "http://localhost:8000/v1/sessions/" \
  -H "Authorization: Bearer dev-bypass-token" \
  -H "Content-Type: application/json" \
  -d '{
    "instruction": "entra al portal SUNAT y descarga mi constancia de RUC",
    "priority": 2,
    "timeout_seconds": 600,
    "metadata": {
      "user_context": "business_owner"
    }
  }'
```

### Get Session Status

```bash
curl -H "Authorization: Bearer dev-bypass-token" \
  "http://localhost:8000/v1/sessions/session-123"
```

### Approve a Session

```bash
curl -X POST "http://localhost:8000/v1/workflows/session-123/approve" \
  -H "Authorization: Bearer dev-bypass-token" \
  -H "Content-Type: application/json" \
  -d '{
    "approved": true,
    "feedback": "Approved for business document download",
    "conditions": ["monitor_execution", "capture_screenshots"]
  }'
```

### Stream Execution Updates

```javascript
// JavaScript example for Server-Sent Events
const eventSource = new EventSource(
  'http://localhost:8000/v1/workflows/session-123/stream',
  {
    headers: {
      'Authorization': 'Bearer dev-bypass-token'
    }
  }
);

eventSource.onmessage = function(event) {
  const data = JSON.parse(event.data);
  console.log('Update:', data);
};
```

## 📝 API Response Format

### Success Response
```json
{
  "data": {
    "id": "session-123",
    "instruction": "entra al portal SUNAT...",
    "status": "running",
    "progress_percentage": 45.5
  },
  "meta": {
    "request_id": "req-456",
    "timestamp": "2024-01-15T10:30:00Z"
  }
}
```

### Error Response
```json
{
  "error": {
    "code": "validation_error",
    "message": "Request validation failed",
    "details": {
      "field": "instruction",
      "suggestion": "Instruction cannot be empty"
    },
    "request_id": "req-789"
  }
}
```

### Paginated Response
```json
{
  "data": [
    {"id": "session-1", "status": "completed"},
    {"id": "session-2", "status": "running"}
  ],
  "meta": {
    "page": 1,
    "per_page": 20,
    "total": 45,
    "total_pages": 3
  }
}
```

## 🔍 Monitoring & Observability

### Request Tracking
Every request gets a unique ID for tracking:
- Header: `X-Request-ID: uuid-here`
- Logs include request ID for correlation

### Health Monitoring
```bash
# Check overall health
curl http://localhost:8000/health/

# Kubernetes probes
curl http://localhost:8000/health/ready  # Readiness
curl http://localhost:8000/health/live   # Liveness
```

### Structured Logs
All requests are logged with structured JSON format including:
- Request ID, method, path, user info
- Response time and status code
- Error details when applicable

## 🚦 Rate Limiting

API endpoints are rate limited:
- Default: 100 requests per minute
- Headers include rate limit status:
  - `X-RateLimit-Remaining`
  - `X-RateLimit-Reset`

## 🐳 Docker Support (Optional)

```bash
# Build image
make docker-build

# Run container
make docker-run

# Or manually
docker build -t gubernamental-agent .
docker run -p 8000:8000 --env-file .env gubernamental-agent
```

## 🔧 Development

### Code Quality
```bash
make format      # Format with black/isort
make lint        # Check linting
make type-check  # Run mypy
make quality     # Run all checks
```

### Testing
```bash
make test        # Run tests
make test-cov    # Run with coverage
```

### Database Operations
```bash
make db-migrate  # Run migrations
make db-seed     # Seed sample data
```

## 🌐 React Frontend Integration

The API is configured for React frontend development:

1. **CORS**: Configured for `localhost:3000` and `localhost:3001`
2. **Authentication**: JWT tokens for user sessions
3. **WebSocket Alternative**: Server-Sent Events for real-time updates
4. **File Downloads**: Direct file download endpoints
5. **Pagination**: Standard pagination for list endpoints

### Example React Hook

```javascript
import { useState, useEffect } from 'react';

export function useSession(sessionId) {
  const [session, setSession] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetch(`/v1/sessions/${sessionId}`, {
      headers: {
        'Authorization': `Bearer ${localStorage.getItem('token')}`
      }
    })
    .then(res => res.json())
    .then(data => {
      setSession(data.data);
      setLoading(false);
    });
  }, [sessionId]);

  return { session, loading };
}
```

## ⚠️ Important Notes

1. **Development vs Production**: Some endpoints (like `/docs`) are only available in development mode
2. **Authentication**: Always required except for health checks
3. **File Security**: Downloaded files are session-scoped and user-scoped
4. **Rate Limits**: Apply per-user, not globally
5. **HTTPS**: Use HTTPS in production (configure reverse proxy)

## 🆘 Troubleshooting

### Common Issues

1. **Port already in use**: Change `API_PORT` in `.env`
2. **JWT errors**: Check `JWT_SECRET` configuration  
3. **CORS errors**: Verify `CORS_ORIGINS` includes your frontend URL
4. **Database errors**: Check `DATABASE_URL` and run migrations

### Debug Mode
```bash
LOG_LEVEL=DEBUG python dev_server.py
```

### Check Logs
```bash
make logs  # Or tail -f logs/gubernamental_agent.log
```