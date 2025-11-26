import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """Configuration class for government service agent."""
    
    # Resend Email Configuration
    RESEND_API_KEY: Optional[str] = os.getenv("RESEND_API_KEY")
    RESEND_FROM_EMAIL: str = os.getenv("RESEND_FROM_EMAIL", "Trámites Gubernamentales <citas@diperion.com>")
    
    # Email Templates Configuration
    EMAIL_DOMAIN: str = os.getenv("EMAIL_DOMAIN", "diperion.com")
    
    # Google AI Configuration
    GOOGLE_API_KEY: Optional[str] = os.getenv("GOOGLE_API_KEY")
    
    # Application Configuration
    APP_NAME: str = os.getenv("AGENT_APP_NAME", "Gobierno Digital")
    
    @classmethod
    def validate_config(cls) -> list[str]:
        """
        Validates that required configuration is present.
        
        Returns:
            List of missing configuration keys
        """
        missing_config = []
        
        if not cls.RESEND_API_KEY:
            missing_config.append("RESEND_API_KEY")
        
        if not cls.GOOGLE_API_KEY:
            missing_config.append("GOOGLE_API_KEY")
            
        return missing_config
    
    @classmethod
    def is_email_enabled(cls) -> bool:
        """Check if email functionality is properly configured."""
        return bool(cls.RESEND_API_KEY)
    
    @classmethod
    def get_resend_config(cls) -> dict:
        """Get Resend configuration for email sending."""
        return {
            "api_key": cls.RESEND_API_KEY,
            "from_email": cls.RESEND_FROM_EMAIL,
            "domain": cls.EMAIL_DOMAIN
        }


# Create a singleton instance
config = Config()