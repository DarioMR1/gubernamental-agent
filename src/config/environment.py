"""Environment configuration management."""

import os
from typing import Optional, List, Union
from pydantic_settings import BaseSettings
from pydantic import Field, validator


class Environment(BaseSettings):
    """Environment configuration loaded from environment variables."""
    
    # LLM Provider Configuration
    openai_api_key: Optional[str] = Field(None, env="OPENAI_API_KEY")
    anthropic_api_key: Optional[str] = Field(None, env="ANTHROPIC_API_KEY")
    
    # Agent Configuration
    llm_provider: str = Field("openai", env="LLM_PROVIDER")
    llm_model: str = Field("gpt-4", env="LLM_MODEL")
    playwright_headless: bool = Field(True, env="PLAYWRIGHT_HEADLESS")
    screenshot_on_action: bool = Field(True, env="SCREENSHOT_ON_ACTION")
    max_retry_attempts: int = Field(3, env="MAX_RETRY_ATTEMPTS")
    execution_timeout_seconds: int = Field(300, env="EXECUTION_TIMEOUT_SECONDS")
    
    # Database Configuration
    database_url: str = Field("sqlite:///./gubernamental_agent.db", env="DATABASE_URL")
    
    # Logging Configuration
    log_level: str = Field("INFO", env="LOG_LEVEL")
    log_format: str = Field("json", env="LOG_FORMAT")
    
    # Storage Configuration
    storage_path: str = Field("./storage", env="STORAGE_PATH")
    screenshots_path: str = Field("./screenshots", env="SCREENSHOTS_PATH")
    downloads_path: str = Field("./downloads", env="DOWNLOADS_PATH")
    logs_path: str = Field("./logs", env="LOGS_PATH")
    
    # Security Configuration
    encrypt_credentials: bool = Field(True, env="ENCRYPT_CREDENTIALS")
    secret_key: Optional[str] = Field(None, env="SECRET_KEY")
    
    # Rate Limiting
    max_concurrent_sessions: int = Field(5, env="MAX_CONCURRENT_SESSIONS")
    session_timeout_minutes: int = Field(60, env="SESSION_TIMEOUT_MINUTES")
    
    # API Configuration
    api_host: str = Field("0.0.0.0", env="API_HOST")
    api_port: int = Field(8000, env="API_PORT")
    api_workers: int = Field(1, env="API_WORKERS")
    environment: str = Field("development", env="ENVIRONMENT")
    
    # CORS Configuration
    cors_origins: Union[List[str], str] = Field(["http://localhost:3000", "http://localhost:3001"], env="CORS_ORIGINS")
    allowed_hosts: Optional[Union[List[str], str]] = Field(None, env="ALLOWED_HOSTS")
    
    # Authentication Configuration
    jwt_secret: Optional[str] = Field(None, env="JWT_SECRET")
    jwt_algorithm: str = Field("HS256", env="JWT_ALGORITHM")
    jwt_expiration_hours: int = Field(24, env="JWT_EXPIRATION_HOURS")
    
    # API Rate Limiting
    api_rate_limit_requests: int = Field(100, env="API_RATE_LIMIT_REQUESTS")
    api_rate_limit_window_seconds: int = Field(60, env="API_RATE_LIMIT_WINDOW_SECONDS")
    
    # Monitoring and Observability
    enable_metrics: bool = Field(True, env="ENABLE_METRICS")
    metrics_port: int = Field(8080, env="METRICS_PORT")
    enable_telemetry: bool = Field(False, env="ENABLE_TELEMETRY")
    
    # Browser Configuration
    browser_download_path: str = Field("./downloads", env="BROWSER_DOWNLOAD_PATH")
    browser_user_data_dir: str = Field("./browser_data", env="BROWSER_USER_DATA_DIR")
    browser_window_width: int = Field(1920, env="BROWSER_WINDOW_WIDTH")
    browser_window_height: int = Field(1080, env="BROWSER_WINDOW_HEIGHT")
    
    # Government Portal Specific Settings
    sunat_base_url: str = Field("https://sunat.gob.pe", env="SUNAT_BASE_URL")
    default_wait_timeout: int = Field(30000, env="DEFAULT_WAIT_TIMEOUT")
    page_load_timeout: int = Field(60000, env="PAGE_LOAD_TIMEOUT")
    element_wait_timeout: int = Field(10000, env="ELEMENT_WAIT_TIMEOUT")
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False
    
    @validator("llm_provider")
    def validate_llm_provider(cls, v: str) -> str:
        """Validate LLM provider."""
        valid_providers = ["openai", "anthropic"]
        if v.lower() not in valid_providers:
            raise ValueError(f"LLM provider must be one of: {valid_providers}")
        return v.lower()
    
    @validator("log_level")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"Log level must be one of: {valid_levels}")
        return v.upper()
    
    @validator("log_format")
    def validate_log_format(cls, v: str) -> str:
        """Validate log format."""
        valid_formats = ["json", "text"]
        if v.lower() not in valid_formats:
            raise ValueError(f"Log format must be one of: {valid_formats}")
        return v.lower()
    
    @validator("environment")
    def validate_environment(cls, v: str) -> str:
        """Validate environment."""
        valid_environments = ["development", "staging", "production"]
        if v.lower() not in valid_environments:
            raise ValueError(f"Environment must be one of: {valid_environments}")
        return v.lower()
    
    @validator("cors_origins")
    def validate_cors_origins(cls, v):
        """Validate CORS origins."""
        if isinstance(v, str):
            # If single string, split by comma
            return [origin.strip() for origin in v.split(",") if origin.strip()]
        return v or []
    
    @validator("allowed_hosts")
    def validate_allowed_hosts(cls, v):
        """Validate allowed hosts."""
        if v is None:
            return None
        if isinstance(v, str):
            # If single string, split by comma
            return [host.strip() for host in v.split(",") if host.strip()]
        return v
    
    def validate_api_key(self) -> None:
        """Validate that the appropriate API key is set."""
        if self.llm_provider == "openai" and not self.openai_api_key:
            raise ValueError("OPENAI_API_KEY must be set when using OpenAI provider")
        elif self.llm_provider == "anthropic" and not self.anthropic_api_key:
            raise ValueError("ANTHROPIC_API_KEY must be set when using Anthropic provider")
    
    def get_api_key(self) -> str:
        """Get the API key for the current LLM provider."""
        if self.llm_provider == "openai":
            return self.openai_api_key or ""
        elif self.llm_provider == "anthropic":
            return self.anthropic_api_key or ""
        else:
            raise ValueError(f"Unknown LLM provider: {self.llm_provider}")
    
    def ensure_directories_exist(self) -> None:
        """Ensure all required directories exist."""
        directories = [
            self.storage_path,
            self.screenshots_path,
            self.downloads_path,
            self.logs_path,
            self.browser_download_path,
            self.browser_user_data_dir,
        ]
        
        for directory in directories:
            os.makedirs(directory, exist_ok=True)