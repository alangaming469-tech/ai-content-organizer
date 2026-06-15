from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Dict


class AIProviderPort(ABC):
    """Abstraction boundary for AI providers.
    
    Implementations must be stateless and thread-safe.
    The port isolates core logic from API specifics.
    """

    @abstractmethod
    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        """Generate completion for given prompt.
        
        Args:
            prompt: Full prompt including system + user instructions.
            max_tokens: Maximum tokens in response.
            temperature: Sampling temperature (0.0 = deterministic).
        
        Returns:
            Raw text response from the model.
        
        Raises:
            RuntimeError: If generation fails.
        """
        raise NotImplementedError


class FakeProvider(AIProviderPort):
    """Deterministic provider for testing."""
    
    def __init__(self, canned_response: str = '{"summary": "Test", "key_points": [], "metadata": {}}'):
        self.canned = canned_response
    
    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        return self.canned


def build_provider(provider_name: str, api_key: str, model_name: str) -> AIProviderPort:
    """Factory for provider instances."""
    provider_name = provider_name.lower()
    
    if provider_name == "gemini":
        from ai_content_organizer.summarizers.summarizer import GeminiProvider
        return GeminiProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "fake":
        return FakeProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
