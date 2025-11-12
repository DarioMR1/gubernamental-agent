from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from api.routes import chat, health, tramites
from dependencies import get_compiled_workflows
from data.database import create_tables
from utils.logging import setup_logging
from config import settings

# Setup logging
setup_logging()


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler"""
    # Startup
    create_tables()
    get_compiled_workflows()
    print(f"🚀 {settings.app_name} started on {settings.host}:{settings.port}")
    print(f"📚 API Documentation: http://{settings.host}:{settings.port}/docs")
    print(f"🏛️ Government Procedures Agent specialized in SAT procedures")
    
    yield
    
    # Shutdown (if needed)
    # Add cleanup code here


# Create FastAPI app
app = FastAPI(
    title=settings.app_name,
    description=settings.description,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(health.router, prefix="/health", tags=["health"])
app.include_router(chat.router, prefix="/api/v1/chat", tags=["chat"])
app.include_router(tramites.router, prefix="/api/v1/tramites", tags=["tramites"])


@app.get("/")
async def root():
    """Root endpoint"""
    return {
        "message": settings.app_name,
        "description": settings.description,
        "version": "1.0.0",
        "endpoints": {
            "docs": "/docs",
            "health": "/health",
            "chat": "/api/v1/chat",
            "tramites": "/api/v1/tramites"
        },
        "specialization": "Mexican Government Procedures (SAT)",
        "supported_tramites": [
            "SAT_RFC_INSCRIPCION_PF - RFC Registration for Individuals",
            "SAT_RFC_ACTUALIZACION_PF - RFC Update for Individuals", 
            "SAT_EFIRMA_NUEVA - New e.firma",
            "SAT_EFIRMA_RENOVACION - e.firma Renewal"
        ]
    }


@app.get("/api/v1/tramites/types")
async def get_supported_tramite_types():
    """Get list of supported tramite types"""
    from domain_types.tramite_types import TramiteType
    
    tramite_info = {
        TramiteType.SAT_RFC_INSCRIPCION_PF: {
            "name": "Inscripción al RFC - Persona Física",
            "description": "Primera inscripción al Registro Federal de Contribuyentes para personas físicas",
            "modality": "En línea (recomendado) o Presencial",
            "estimated_time": "15-30 minutos en línea",
            "requirements": ["CURP", "Identificación oficial", "Domicilio fiscal", "Correo electrónico"]
        },
        TramiteType.SAT_RFC_ACTUALIZACION_PF: {
            "name": "Actualización de datos en RFC",
            "description": "Actualización de información en el RFC existente",
            "modality": "En línea o Presencial", 
            "estimated_time": "10-20 minutos",
            "requirements": ["RFC existente", "Documentos que soporten los cambios"]
        }
    }
    
    return {
        "supported_tramites": tramite_info,
        "total_types": len(tramite_info),
        "specialization": "SAT (Servicio de Administración Tributaria)"
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host=settings.host,
        port=settings.port,
        reload=settings.debug
    )