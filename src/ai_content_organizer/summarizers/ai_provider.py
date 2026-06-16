from __future__ import annotations

import logging
from abc import ABC, abstractmethod

import google.generativeai as genai
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

logger = logging.getLogger(__name__)


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


class GeminiProvider(AIProviderPort):
    """Google Gemini provider implementation."""

    def __init__(self, api_key: str, model_name: str = "gemini-2.5-flash"):
        genai.configure(api_key=api_key)
        self.model = genai.GenerativeModel(model_name)
        self.model_name = model_name

    @retry(
        wait=wait_exponential(multiplier=1, min=2, max=30),
        stop=stop_after_attempt(3),
        retry=retry_if_exception_type(Exception),
        reraise=True,
    )
    def generate(self, prompt: str, max_tokens: int, temperature: float) -> str:
        response = self.model.generate_content(
            prompt,
            generation_config=genai.GenerationConfig(
                max_output_tokens=max_tokens,
                temperature=temperature,
            ),
        )
        if not response.text:
            raise RuntimeError("Gemini returned empty response")
        logger.debug("Gemini response: %d chars", len(response.text))
        return response.text


def build_provider(provider_name: str, api_key: str, model_name: str) -> AIProviderPort:
    """Factory for provider instances."""
    provider_name = provider_name.lower()

    if provider_name == "gemini":
        return GeminiProvider(api_key=api_key, model_name=model_name)
    elif provider_name == "fake":
        return FakeProvider()
    else:
        raise ValueError(f"Unknown provider: {provider_name}")
