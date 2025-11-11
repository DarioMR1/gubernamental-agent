"""Anthropic LLM provider implementation."""

import asyncio
import time
from typing import Dict, Any, Optional, List
import anthropic
from anthropic import AsyncAnthropic

from .base import BaseLLMProvider
from ...types import LLMRequest, LLMResponse
from ...utils import retry_on_failure


class AnthropicProvider(BaseLLMProvider):
    """Anthropic Claude LLM provider."""
    
    # Model pricing per 1K tokens (input/output) - approximate as of 2024
    MODEL_PRICING = {
        "claude-3-opus-20240229": (0.015, 0.075),
        "claude-3-sonnet-20240229": (0.003, 0.015), 
        "claude-3-haiku-20240307": (0.00025, 0.00125),
        "claude-2.1": (0.008, 0.024),
        "claude-2.0": (0.008, 0.024),
        "claude-instant-1.2": (0.0008, 0.0024),
    }
    
    def __init__(self, api_key: str, **kwargs: Any):
        """Initialize Anthropic provider.
        
        Args:
            api_key: Anthropic API key
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.client = AsyncAnthropic(api_key=api_key)
        self.base_url = kwargs.get("base_url")
        
        if self.base_url:
            self.client.base_url = self.base_url
    
    @retry_on_failure(max_attempts=3, base_delay=1.0, exceptions=(anthropic.APIError,))
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using Anthropic API.
        
        Args:
            request: LLM request
            
        Returns:
            LLM response
        """
        start_time = time.time()
        
        # Prepare API call parameters
        api_params = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            **request.additional_params
        }
        
        # Handle system prompt and user message
        if request.system_prompt:
            api_params["system"] = request.system_prompt
        
        api_params["messages"] = [
            {
                "role": "user",
                "content": request.prompt
            }
        ]
        
        try:
            response = await self.client.messages.create(**api_params)
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Extract response content
            content = ""
            if response.content and len(response.content) > 0:
                # Claude returns a list of content blocks
                content = response.content[0].text
            
            finish_reason = response.stop_reason
            
            # Calculate token usage
            usage = response.usage
            tokens_used = (usage.input_tokens + usage.output_tokens) if usage else 0
            
            # Estimate cost
            cost_estimate = None
            if request.model in self.MODEL_PRICING and usage:
                input_cost = (usage.input_tokens / 1000) * self.MODEL_PRICING[request.model][0]
                output_cost = (usage.output_tokens / 1000) * self.MODEL_PRICING[request.model][1]
                cost_estimate = input_cost + output_cost
            
            return LLMResponse(
                content=content,
                model=request.model,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                finish_reason=finish_reason,
                response_time_ms=response_time
            )
            
        except anthropic.APIError as e:
            # Re-raise to trigger retry
            raise
        except Exception as e:
            # For non-API errors, return error response
            return LLMResponse(
                content=f"Error: {str(e)}",
                model=request.model,
                tokens_used=0,
                response_time_ms=int((time.time() - start_time) * 1000)
            )
    
    def get_available_models(self) -> List[str]:
        """Get available Anthropic models.
        
        Returns:
            List of model names
        """
        return [
            "claude-3-opus-20240229",
            "claude-3-sonnet-20240229", 
            "claude-3-haiku-20240307",
            "claude-2.1",
            "claude-2.0",
            "claude-instant-1.2",
        ]
    
    def estimate_cost(self, request: LLMRequest) -> Optional[float]:
        """Estimate cost for Anthropic request.
        
        Args:
            request: LLM request
            
        Returns:
            Estimated cost in USD
        """
        if request.model not in self.MODEL_PRICING:
            return None
        
        # Rough token estimation for Anthropic (similar to OpenAI)
        prompt_tokens = len(request.prompt) // 4
        if request.system_prompt:
            prompt_tokens += len(request.system_prompt) // 4
        
        # Estimate output tokens (use max_tokens as upper bound)
        output_tokens = min(request.max_tokens, prompt_tokens)  # Conservative estimate
        
        input_cost = (prompt_tokens / 1000) * self.MODEL_PRICING[request.model][0]
        output_cost = (output_tokens / 1000) * self.MODEL_PRICING[request.model][1]
        
        return input_cost + output_cost
    
    def prepare_request(self, request: LLMRequest) -> Dict[str, Any]:
        """Prepare request for Anthropic API format.
        
        Args:
            request: LLM request
            
        Returns:
            Anthropic-specific request dictionary
        """
        api_params = {
            "model": request.model,
            "max_tokens": request.max_tokens,
            "temperature": request.temperature,
            **request.additional_params
        }
        
        if request.system_prompt:
            api_params["system"] = request.system_prompt
        
        api_params["messages"] = [
            {
                "role": "user",
                "content": request.prompt
            }
        ]
        
        return api_params
    
    async def validate_api_key(self) -> bool:
        """Validate the Anthropic API key.
        
        Returns:
            True if API key is valid
        """
        try:
            # Try a minimal API call to validate the key
            test_request = LLMRequest(
                prompt="Test",
                model="claude-3-haiku-20240307",
                max_tokens=1
            )
            await self.generate_response(test_request)
            return True
        except anthropic.AuthenticationError:
            return False
        except Exception:
            # Other errors might be temporary
            return True  # Assume key is valid but there's a service issue