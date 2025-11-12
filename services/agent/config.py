from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Government Procedures Agent API"
    description: str = "AI agent specialized in Mexican government procedures (SAT)"
    debug: bool = False
    
    # LLM Configuration
    openai_api_key: str
    model_name: str = "gpt-4o"
    temperature: float = 0.3  # Lower temperature for more consistent responses
    max_tokens: int = 2000    # More tokens for detailed explanations
    
    # Database Configuration
    database_url: str = "sqlite:///./government_agent.db"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Tramite Configuration
    max_conversation_history: int = 100  # More history for complex procedures
    session_timeout_minutes: int = 60    # Longer sessions for document preparation
    max_document_size_mb: int = 10
    supported_document_formats: list = ["image/jpeg", "image/png", "application/pdf"]
    
    # SAT Specific Configuration
    max_document_age_days: int = 90
    curp_length_characters: int = 18
    postal_code_length: int = 5
    
    # Validation Configuration
    curp_validation_enabled: bool = True
    document_validation_enabled: bool = True
    name_similarity_threshold: float = 0.9
    
    class Config:
        env_file = ".env"


settings = Settings()