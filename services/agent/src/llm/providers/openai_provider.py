"""OpenAI LLM provider implementation."""

import asyncio
import time
from typing import Dict, Any, Optional, List
import openai
from openai import AsyncOpenAI

from .base import BaseLLMProvider
from ...types import LLMRequest, LLMResponse
from ...utils import retry_on_failure


class OpenAIProvider(BaseLLMProvider):
    """OpenAI LLM provider."""
    
    # Model pricing per 1K tokens (input/output) - approximate as of 2024
    MODEL_PRICING = {
        "gpt-4": (0.03, 0.06),
        "gpt-4-turbo": (0.01, 0.03),
        "gpt-4-turbo-preview": (0.01, 0.03),
        "gpt-3.5-turbo": (0.0015, 0.002),
        "gpt-3.5-turbo-16k": (0.003, 0.004),
    }
    
    def __init__(self, api_key: str, **kwargs: Any):
        """Initialize OpenAI provider.
        
        Args:
            api_key: OpenAI API key
            **kwargs: Additional configuration
        """
        super().__init__(api_key, **kwargs)
        self.client = AsyncOpenAI(api_key=api_key)
        self.organization = kwargs.get("organization")
        self.base_url = kwargs.get("base_url")
        
        if self.organization:
            self.client.organization = self.organization
        if self.base_url:
            self.client.base_url = self.base_url
    
    @retry_on_failure(max_attempts=3, base_delay=1.0, exceptions=(openai.APIError,))
    async def generate_response(self, request: LLMRequest) -> LLMResponse:
        """Generate response using OpenAI API.
        
        Args:
            request: LLM request
            
        Returns:
            LLM response
        """
        start_time = time.time()
        
        # Prepare messages
        messages = []
        
        if request.system_prompt:
            messages.append({
                "role": "system",
                "content": request.system_prompt
            })
        
        messages.append({
            "role": "user", 
            "content": request.prompt
        })
        
        # Prepare API call parameters
        api_params = {
            "model": request.model,
            "messages": messages,
            "temperature": request.temperature,
            "max_tokens": request.max_tokens,
            **request.additional_params
        }
        
        try:
            response = await self.client.chat.completions.create(**api_params)
            
            response_time = int((time.time() - start_time) * 1000)
            
            # Extract response content
            content = response.choices[0].message.content or ""
            finish_reason = response.choices[0].finish_reason
            
            # Calculate token usage
            usage = response.usage
            tokens_used = usage.total_tokens if usage else 0
            
            # Estimate cost
            cost_estimate = None
            if request.model in self.MODEL_PRICING and usage:
                input_cost = (usage.prompt_tokens / 1000) * self.MODEL_PRICING[request.model][0]
                output_cost = (usage.completion_tokens / 1000) * self.MODEL_PRICING[request.model][1]
                cost_estimate = input_cost + output_cost
            
            return LLMResponse(
                content=content,
                model=request.model,
                tokens_used=tokens_used,
                cost_estimate=cost_estimate,
                finish_reason=finish_reason,
                response_time_ms=response_time
            )
            
        except openai.APIError as e:
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
        """Get available OpenAI models.
        
        Returns:
            List of model names
        """
        return [
            "gpt-4",
            "gpt-4-turbo",
            "gpt-4-turbo-preview", 
            "gpt-3.5-turbo",
            "gpt-3.5-turbo-16k",
            "gpt-3.5-turbo-1106",
            "gpt-4-1106-preview",
            "gpt-4-0125-preview"
        ]
    
    def estimate_cost(self, request: LLMRequest) -> Optional[float]:
        """Estimate cost for OpenAI request.
        
        Args:
            request: LLM request
            
        Returns:
            Estimated cost in USD
        """
        if request.model not in self.MODEL_PRICING:
            return None
        
        # Rough token estimation (4 chars = 1 token)
        prompt_tokens = len(request.prompt) // 4
        if request.system_prompt:
            prompt_tokens += len(request.system_prompt) // 4
        
        # Estimate output tokens (use max_tokens as upper bound)
        output_tokens = min(request.max_tokens, prompt_tokens)  # Conservative estimate
        
        input_cost = (prompt_tokens / 1000) * self.MODEL_PRICING[request.model][0]
        output_cost = (output_tokens / 1000) * self.MODEL_PRICING[request.model][1]
        
        return input_cost + output_cost
    
    async def list_models(self) -> List[str]:
        """Get actual available models from OpenAI API.
        
        Returns:
            List of available model IDs
        """
        try:
            models = await self.client.models.list()
            return [model.id for model in models.data if "gpt" in model.id]
        except Exception:
            # Fallback to hardcoded list
            return self.get_available_models()
    
    async def validate_api_key(self) -> bool:
        """Validate the OpenAI API key.
        
        Returns:
            True if API key is valid
        """
        try:
            await self.client.models.list()
            return True
        except openai.AuthenticationError:
            return False
        except Exception:
            # Other errors might be temporary
            return True  # Assume key is valid but there's a service issue