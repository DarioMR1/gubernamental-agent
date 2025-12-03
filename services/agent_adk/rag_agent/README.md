# Gubernamental RAG Agent

Este agente RAG está especializado en consultar documentos gubernamentales pre-cargados usando Google Cloud Vertex AI.

## Características

- **Corpus Pre-definido**: Los documentos se cargan una sola vez al inicio, no se crean dinámicamente
- **Consulta Eficiente**: Solo permite consultar el corpus existente, optimizado para documentos gubernamentales
- **Integración ADK**: Completamente integrado con Google Agent Development Kit

## Configuración

### 1. Variables de Entorno

Crea un archivo `.env` en el directorio raíz con:

```bash
GOOGLE_CLOUD_PROJECT=tu-proyecto-gcp
GOOGLE_CLOUD_LOCATION=us-central1
```

### 2. Autenticación Google Cloud

```bash
# Instalar Google Cloud CLI
gcloud init
gcloud auth application-default login
gcloud services enable aiplatform.googleapis.com
```

### 3. Instalar Dependencias

```bash
pip install -r requirements.txt
```

## Uso

### 1. Crear el Corpus (Solo una vez)

Ejecuta el script de setup para crear el corpus con documentos:

```bash
# Con documentos específicos
python rag_agent/setup_corpus.py --documents \
  "https://drive.google.com/file/d/TU_ID_ARCHIVO_1/view" \
  "https://drive.google.com/file/d/TU_ID_ARCHIVO_2/view" \
  "gs://tu-bucket/docs/regulaciones.pdf"

# O edita get_default_document_paths() en setup_corpus.py para paths por defecto
```

### 2. Usar el Agente

El agente estará disponible automáticamente en el sistema multiagente cuando inicies `main.py`.

## Estructura del Agente

```
rag_agent/
├── __init__.py           # Inicialización y configuración Vertex AI
├── config.py             # Configuración del corpus y parámetros RAG
├── agent.py              # Definición del agente ADK
├── setup_corpus.py       # Script para crear el corpus
├── tools/
│   ├── __init__.py       # Exports de tools
│   ├── utils.py          # Utilidades comunes
│   └── rag_query.py      # Tool de consulta RAG
└── README.md             # Esta documentación
```

## Herramientas Disponibles

### `rag_query`

Consulta el corpus de documentos gubernamentales.

**Parámetros:**
- `query` (str): Pregunta o consulta a realizar

**Ejemplo de uso:**
```python
result = rag_query("¿Cuáles son los requisitos para tramitar una licencia?")
```

## Configuración del Corpus

El corpus se configura en `config.py`:

- **CORPUS_NAME**: `"gubernamental_documents"`
- **CORPUS_DISPLAY_NAME**: `"Documentos Gubernamentales"`
- **DEFAULT_TOP_K**: `5` resultados por consulta
- **DEFAULT_CHUNK_SIZE**: `512` caracteres por chunk
- **DEFAULT_CHUNK_OVERLAP**: `100` caracteres de overlap

## Consideraciones Importantes

1. **Corpus Estático**: Los documentos se cargan una vez y no se modifican dinámicamente
2. **Autenticación**: Requiere Google Cloud authentication configurada
3. **Costos**: Las consultas RAG generan costos en Google Cloud
4. **Limitaciones**: Solo consulta el corpus pre-definido, no crea nuevos corpus

## Troubleshooting

### Error de Autenticación
```bash
gcloud auth application-default login
```

### Error de APIs
```bash
gcloud services enable aiplatform.googleapis.com
```

### Corpus No Encontrado
Ejecuta el script de setup:
```bash
python rag_agent/setup_corpus.py --documents "URL_DE_TUS_DOCUMENTOS"
```