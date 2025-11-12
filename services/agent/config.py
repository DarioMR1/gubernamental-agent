from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    # API Configuration
    app_name: str = "Chat Agent API"
    debug: bool = False
    
    # LLM Configuration
    openai_api_key: str
    model_name: str = "gpt-4o"
    temperature: float = 0.7
    max_tokens: int = 1000
    
    # Database Configuration
    database_url: str = "sqlite:///./chat_agent.db"
    
    # Server Configuration
    host: str = "0.0.0.0"
    port: int = 8000
    
    # Chat Configuration
    max_conversation_history: int = 50
    session_timeout_minutes: int = 30
    
    class Config:
        env_file = ".env"


settings = Settings()