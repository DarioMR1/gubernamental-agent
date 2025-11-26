# Agent ADK

Agente general desarrollado con Google ADK para conversación y asistencia básica.

## Instalación

### 1. Crear entorno virtual

```bash
python -m venv venv
```

### 2. Activar entorno virtual

**En Windows:**
```bash
venv\Scripts\activate
```

**En macOS/Linux:**
```bash
source venv/bin/activate
```

### 3. Instalar dependencias

```bash
pip install -r requirements.txt
```

### 4. Configurar variables de entorno

Crea un archivo `.env` con tus credenciales:

```env
GOOGLE_API_KEY=tu_api_key_aqui
```

## Uso

### Ejecutar con ADK Web

```bash
adk web
```

Esto iniciará el servidor web en `http://localhost:8080` donde podrás interactuar con el agente.

### Ejecutar con ADK CLI

```bash
adk run
```

Para chat interactivo desde la terminal.

## Estructura del Proyecto

```
agent_adk/
├── test_agent/
│   ├── __init__.py
│   ├── agent.py          # Configuración del agente
│   └── tools.py          # Herramientas disponibles
├── requirements.txt      # Dependencias
├── .env                 # Variables de entorno (crear)
└── README.md           # Este archivo
```

## Agente

El agente está configurado como un asistente general que puede:
- Mantener conversaciones casuales
- Responder preguntas generales
- Ayudar con tareas básicas

Para modificar el comportamiento del agente, edita el archivo `test_agent/agent.py`.