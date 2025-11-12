"""Base LLM provider interface."""

from abc import ABC, abstractmethod
from typing import Dict, Any, Optional

from ...types import LLMRequest, LLMResponse


class BaseLLMProvider(ABC):
    """Base class for LLM providers."""
    
    def __init__(self, api_key: str, **kwargs: Any):
        """Initialize LLM provider.
        
        Args:
            api_key: API key for the provider
            **kwargs: Additional provider-specific configuration
        """
        self.api_key = api_key
        self.config = kwargs
    
    @abstractmethod
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response from LLM.
        
        Args:
            request: LLM request with prompt and parameters
            
        Returns:
            LLM response with generated content
        """
        pass
    
    @abstractmethod
    def get_available_models(self) -> list[str]:
        """Get list of available models for this provider.
        
        Returns:
            List of model names
        """
        pass
    
    @abstractmethod
    def estimate_cost(self, request: LLMRequest) -> Optional[float]:
        """Estimate cost for a request.
        
        Args:
            request: LLM request
            
        Returns:
            Estimated cost in USD or None if not available
        """
        pass
    
    def validate_model(self, model: str) -> bool:
        """Validate if model is available for this provider.
        
        Args:
            model: Model name to validate
            
        Returns:
            True if model is available
        """
        return model in self.get_available_models()
    
    def prepare_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare request for the specific provider API.
        
        Args:
            request: LLM request
            
        Returns:
            Provider-specific request dictionary
        """
        return {
            "prompt": request.prompt,
            "model": request.model,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            **request.additional_params
        }