# Semovi Licencias Agent - Agent Engine

Agent gubernamental para trámites de SEMOVI desarrollado con Google ADK y desplegado en Vertex AI Agent Engine.

## Prerrequisitos

- Python 3.11+
- Poetry (gestor de paquetes Python)
- Cuenta de Google Cloud con Vertex AI API habilitada
- Google Cloud CLI (`gcloud`) instalado y autenticado

## Instalación

### 1. Clonar e instalar dependencias:
```bash
cd gubernamental-agent/services/agent_adk
```

### 2. Instalar Poetry si no lo tienes:
```bash
curl -sSL https://install.python-poetry.org | python3 -
```

### 3. Instalar dependencias del proyecto:
```bash
poetry install
```

### 4. Activar el entorno virtual:
```bash
poetry shell
```

## Configuración

### 1. Crear archivo .env:
```bash
cp .env.template .env
```

### 2. Editar .env con tus credenciales:
```bash
# Agent Engine Configuration
GOOGLE_GENAI_USE_VERTEXAI=TRUE
GOOGLE_CLOUD_PROJECT=tu-proyecto-id
GOOGLE_CLOUD_LOCATION=us-central1
STAGING_BUCKET=gs://tu-bucket-staging

# Resend Email Configuration
RESEND_API_KEY=tu-resend-api-key
RESEND_FROM_EMAIL=Tu Email <email@tudominio.com>
EMAIL_DOMAIN=tudominio.com
```

### 3. Autenticación Google Cloud:
```bash
gcloud auth login
gcloud config set project tu-proyecto-id
```

### 4. Habilitar APIs necesarias:
```bash
gcloud services enable aiplatform.googleapis.com
```

## Uso

### Testing Local

⚠️ **Nota**: El testing local tiene limitaciones inherentes de Agent Engine. **Se recomienda usar el deployment remoto para testing completo**.

#### 1. Crear una sesión local:
```bash
poetry run deploy-local --create_session
```

#### 2. Listar sesiones:
```bash
poetry run deploy-local --list_sessions
```

#### 3. Enviar mensaje de prueba:
```bash
poetry run deploy-local --send --session_id=tu-session-id --message="Necesito ayuda con el trámite de RFC"
```

**💡 Limitaciones del testing local:**
- Las sesiones locales usan un sistema diferente al remoto
- Agent Engine está optimizado para deployment remoto
- Para testing completo, usar deployment remoto (es más rápido y confiable)

### Despliegue Remoto

#### 1. Desplegar el agente:
```bash
poetry run deploy-remote --create
```

#### 2. Listar despliegues activos:
```bash
poetry run deploy-remote --list
```

#### 3. Crear sesión remota:
```bash
poetry run deploy-remote --create_session --resource_id=tu-resource-id
```

#### 4. Enviar mensaje al agente desplegado:
```bash
poetry run deploy-remote --send --resource_id=tu-resource-id --session_id=tu-session-id --message="Necesito información sobre licencias de conducir"
```

#### 5. Eliminar despliegue:
```bash
poetry run deploy-remote --delete --resource_id=tu-resource-id
```

## Estructura del Proyecto

```
agent_adk/
├── government_service_agent/    # Código del agente principal
│   ├── __init__.py
│   ├── agent.py                # Configuración del agente
│   └── sub_agents/            # Sub-agentes especializados
│       ├── appointment_scheduling_agent/
│       ├── document_extraction_agent/
│       └── web_search_agent/
├── deployment/                # Scripts de despliegue
│   ├── local.py              # Testing local
│   └── remote.py            # Despliegue remoto
├── .env                     # Variables de entorno
├── .env.template           # Plantilla de configuración
├── pyproject.toml         # Configuración Poetry
└── README.md             # Esta documentación
```

## Información del Despliegue Actual

- **Agent Engine ID**: 7858688990784782336
- **Proyecto**: semovi-licencias-agent  
- **Región**: us-central1
- **Estado**: ✅ Activo y funcionando
- **Console**: https://console.cloud.google.com/vertex-ai/agents

### **Estado de funcionalidad:**
- ✅ **Deployment remoto**: Completamente funcional
- ✅ **Gestión de sesiones**: Operativo
- ✅ **Respuestas del agente**: Funcionando correctamente
- ✅ **Sub-agentes**: document_extraction_agent, web_search_agent, appointment_scheduling_agent
- ⚠️ **Testing local**: Funcional con limitaciones (usar remoto recomendado)

### **APIs habilitadas:**
- ✅ Vertex AI API
- ✅ Cloud Resource Manager API
- ✅ Cloud Storage API (para staging bucket)

## Scripts Disponibles

### Comandos Poetry:
- `poetry run deploy-local [opciones]` - Testing local del agente
- `poetry run deploy-remote [opciones]` - Gestión de despliegues remotos

### Opciones del script local:
- `--create_session` - Crear nueva sesión de testing
- `--list_sessions` - Listar sesiones de testing  
- `--get_session --session_id=ID` - Obtener detalles de sesión
- `--send --session_id=ID --message="texto"` - Enviar mensaje

### Opciones del script remoto:
- `--create` - Crear nuevo despliegue
- `--list` - Listar despliegues activos
- `--delete --resource_id=ID` - Eliminar despliegue
- `--create_session --resource_id=ID` - Crear sesión remota
- `--list_sessions --resource_id=ID` - Listar sesiones
- `--send --resource_id=ID --session_id=ID --message="texto"` - Enviar mensaje

## Ventajas de Agent Engine vs Cloud Run

✅ **Gestión automática de sesiones conversacionales**
✅ **Sin configuración de puertos/contenedores** 
✅ **Escalado automático**
✅ **Integración nativa con Vertex AI**
✅ **Monitoreo y logging integrados**
✅ **Sin configuración de base de datos**

## Desarrollo

### Flujo de trabajo recomendado:

#### **🔄 Para cambios menores (testing rápido):**
1. Modificar los agentes en `government_service_agent/`
2. Usar deployment remoto directamente: `poetry run deploy-remote --create`
3. Probar con el agente remoto: `poetry run deploy-remote --send --resource_id=ID --session_id=ID`

#### **🛠️ Para desarrollo extensivo:**
1. Modificar código en `government_service_agent/`
2. Testing local básico (opcional): `poetry run deploy-local --create_session`
3. Deployment remoto para testing completo: `poetry run deploy-remote --create`
4. Probar todas las funciones con el agente remoto
5. Actualizar documentación según sea necesario

### **💡 Mejores prácticas:**

- **Usa el deployment remoto como herramienta principal** de testing
- **Es más rápido** que el testing local para Agent Engine
- **Replica exactamente el entorno de producción**
- **Todas las funciones funcionan al 100%**

### **🚀 Workflow típico:**
```bash
# 1. Hacer cambios en el código
# 2. Desplegar nueva versión
poetry run deploy-remote --create

# 3. Copiar el nuevo resource_id del output
# 4. Crear sesión de testing  
poetry run deploy-remote --create_session --resource_id=NUEVO_ID

# 5. Probar el agente
poetry run deploy-remote --send --resource_id=ID --session_id=ID --message="Prueba de funcionalidad"

# 6. Si todo funciona bien, actualizar .env con el nuevo AGENT_ENGINE_ID
```

## Resolución de Problemas

### Si tienes problemas de autenticación:
- Verifica que estés logueado: `gcloud auth login`
- Confirma el proyecto: `gcloud config get-value project`
- Revisa que las APIs estén habilitadas

### Si el despliegue falla:
- Confirma que el bucket de staging existe y es accesible
- Verifica que todas las variables de entorno estén configuradas
- Asegúrate de tener los permisos necesarios en Google Cloud

### Si hay errores en las dependencias:
- Ejecuta `poetry install` para reinstalar
- Verifica la versión de Python: `python --version`
- Confirma que estés en el entorno virtual: `poetry shell`

### Problemas específicos de Agent Engine:

#### "Session not found" en testing local:
- **Solución**: Usar deployment remoto para testing completo
- **Causa**: Agent Engine optimizado para deployment remoto
- **Comando alternativo**: `poetry run deploy-remote --send`

#### Errores de "resource_id required":
- **Verificar deployments activos**: `poetry run deploy-remote --list`
- **Usar el resource_id correcto** del output del comando anterior

#### Problemas de APIs no habilitadas:
```bash
# Habilitar APIs necesarias
gcloud services enable aiplatform.googleapis.com
gcloud services enable cloudresourcemanager.googleapis.com
```

#### Agent no responde como esperado:
1. **Verificar que el agente esté activo**: `poetry run deploy-remote --list`
2. **Crear nueva sesión**: `poetry run deploy-remote --create_session --resource_id=ID`
3. **Verificar logs en Google Cloud Console**

### **🆘 En caso de problemas mayores:**
1. **Crear nuevo deployment**: `poetry run deploy-remote --create`
2. **Eliminar deployment problemático**: `poetry run deploy-remote --delete --resource_id=ID_VIEJO`
3. **Actualizar .env con nuevo AGENT_ENGINE_ID**