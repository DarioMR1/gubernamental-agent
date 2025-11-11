"""Agent configuration settings."""

from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path

from ..types import LLMProvider


@dataclass
class LLMConfig:
    """Configuration for LLM providers."""
    
    provider: LLMProvider
    model: str
    temperature: float = 0.1
    max_tokens: int = 1000
    timeout_seconds: int = 30
    retry_attempts: int = 3
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "provider": self.provider.value,
            "model": self.model,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "timeout_seconds": self.timeout_seconds,
            "retry_attempts": self.retry_attempts,
        }


@dataclass
class PlaywrightConfig:
    """Configuration for Playwright browser automation."""
    
    headless: bool = True
    browser_type: str = "chromium"  # chromium, firefox, webkit
    window_width: int = 1920
    window_height: int = 1080
    download_path: str = "./downloads"
    user_data_dir: str = "./browser_data"
    timeout_seconds: int = 30
    slow_mo: int = 0  # Slow down operations by milliseconds
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "headless": self.headless,
            "browser_type": self.browser_type,
            "window_width": self.window_width,
            "window_height": self.window_height,
            "download_path": self.download_path,
            "user_data_dir": self.user_data_dir,
            "timeout_seconds": self.timeout_seconds,
            "slow_mo": self.slow_mo,
        }


@dataclass 
class DatabaseConfig:
    """Configuration for database connections."""
    
    url: str = "sqlite:///./gubernamental_agent.db"
    pool_size: int = 5
    max_overflow: int = 10
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "url": self.url,
            "pool_size": self.pool_size,
            "max_overflow": self.max_overflow,
            "pool_timeout": self.pool_timeout,
            "pool_recycle": self.pool_recycle,
            "echo": self.echo,
        }


@dataclass
class SecurityConfig:
    """Security configuration."""
    
    encrypt_credentials: bool = True
    secret_key: Optional[str] = None
    session_timeout_minutes: int = 60
    max_login_attempts: int = 3
    require_approval_for_sensitive_actions: bool = True
    approval_timeout_seconds: int = 300
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "encrypt_credentials": self.encrypt_credentials,
            "secret_key": "***" if self.secret_key else None,
            "session_timeout_minutes": self.session_timeout_minutes,
            "max_login_attempts": self.max_login_attempts,
            "require_approval_for_sensitive_actions": self.require_approval_for_sensitive_actions,
            "approval_timeout_seconds": self.approval_timeout_seconds,
        }


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    
    enable_logging: bool = True
    log_level: str = "INFO"
    log_format: str = "json"
    enable_metrics: bool = True
    enable_telemetry: bool = False
    screenshot_on_action: bool = True
    screenshot_on_error: bool = True
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "log_format": self.log_format,
            "enable_metrics": self.enable_metrics,
            "enable_telemetry": self.enable_telemetry,
            "screenshot_on_action": self.screenshot_on_action,
            "screenshot_on_error": self.screenshot_on_error,
        }


@dataclass
class AgentConfig:
    """Complete agent configuration."""
    
    llm: LLMConfig = field(default_factory=lambda: LLMConfig(
        provider=LLMProvider.OPENAI,
        model="gpt-4"
    ))
    playwright: PlaywrightConfig = field(default_factory=PlaywrightConfig)
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    
    # General execution settings
    max_retry_attempts: int = 3
    execution_timeout_seconds: int = 300
    max_concurrent_sessions: int = 5
    
    # Storage paths
    storage_path: str = "./storage"
    logs_path: str = "./logs"
    screenshots_path: str = "./screenshots"
    downloads_path: str = "./downloads"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "llm": self.llm.to_dict(),
            "playwright": self.playwright.to_dict(),
            "database": self.database.to_dict(),
            "security": self.security.to_dict(),
            "monitoring": self.monitoring.to_dict(),
            "max_retry_attempts": self.max_retry_attempts,
            "execution_timeout_seconds": self.execution_timeout_seconds,
            "max_concurrent_sessions": self.max_concurrent_sessions,
            "storage_path": self.storage_path,
            "logs_path": self.logs_path,
            "screenshots_path": self.screenshots_path,
            "downloads_path": self.downloads_path,
        }
    
    def validate(self) -> None:
        """Validate configuration."""
        # Validate paths exist or can be created
        for path in [self.storage_path, self.logs_path, self.screenshots_path, self.downloads_path]:
            Path(path).mkdir(parents=True, exist_ok=True)
        
        # Validate LLM configuration
        if not self.llm.model:
            raise ValueError("LLM model must be specified")
        
        # Validate timeout values
        if self.execution_timeout_seconds <= 0:
            raise ValueError("Execution timeout must be positive")
        
        if self.playwright.timeout_seconds <= 0:
            raise ValueError("Playwright timeout must be positive")
        
        # Validate retry attempts
        if self.max_retry_attempts < 0:
            raise ValueError("Max retry attempts cannot be negative")
    
    @classmethod
    def from_env(cls) -> "AgentConfig":
        """Create configuration from environment variables."""
        from .environment import Environment
        
        env = Environment()
        env.validate_api_key()
        env.ensure_directories_exist()
        
        llm_provider = LLMProvider.OPENAI if env.llm_provider == "openai" else LLMProvider.ANTHROPIC
        
        config = cls(
            llm=LLMConfig(
                provider=llm_provider,
                model=env.llm_model
            ),
            playwright=PlaywrightConfig(
                headless=env.playwright_headless,
                window_width=env.browser_window_width,
                window_height=env.browser_window_height,
                download_path=env.browser_download_path,
                user_data_dir=env.browser_user_data_dir,
                timeout_seconds=env.default_wait_timeout // 1000  # Convert from ms
            ),
            database=DatabaseConfig(
                url=env.database_url
            ),
            security=SecurityConfig(
                encrypt_credentials=env.encrypt_credentials,
                secret_key=env.secret_key,
                session_timeout_minutes=env.session_timeout_minutes
            ),
            monitoring=MonitoringConfig(
                log_level=env.log_level,
                log_format=env.log_format,
                enable_metrics=env.enable_metrics,
                enable_telemetry=env.enable_telemetry,
                screenshot_on_action=env.screenshot_on_action
            ),
            max_retry_attempts=env.max_retry_attempts,
            execution_timeout_seconds=env.execution_timeout_seconds,
            max_concurrent_sessions=env.max_concurrent_sessions,
            storage_path=env.storage_path,
            logs_path=env.logs_path,
            screenshots_path=env.screenshots_path,
            downloads_path=env.downloads_path
        )
        
        config.validate()
        return config