from typing import Optional

from ..config import AgentConfig
from .base import LLMBackend
from .cohere import CohereBackend
from .openai import OpenAIBackend
from .anthropic import AnthropicBackend
from .gemini import GeminiBackend


# Default models for each backend
DEFAULT_MODELS = {
    "cohere": "command-r-08-2024",
    "openai": "gpt-4o",
    "anthropic": "claude-3-5-sonnet-20240620",
    "gemini": "gemini-1.5-pro",
}


def get_backend(
    name: str,
    model: Optional[str] = None,
    config: Optional[AgentConfig] = None,
) -> LLMBackend:
    """
    Factory function to create a backend by name.

    Args:
        name: Backend name - one of "cohere", "openai", "anthropic", "gemini"
        model: Optional model name. Uses backend-specific default if not provided.
        config: Optional AgentConfig for retry settings, etc.

    Returns:
        An instance of the appropriate LLMBackend subclass.

    Raises:
        ValueError: If the backend name is unknown.
    """
    backend_name = name.lower()
    model_name = model or DEFAULT_MODELS.get(backend_name)

    if backend_name == "cohere":
        return CohereBackend(model=model_name or DEFAULT_MODELS["cohere"], config=config)
    elif backend_name == "openai":
        return OpenAIBackend(model=model_name or DEFAULT_MODELS["openai"], config=config)
    elif backend_name == "anthropic":
        return AnthropicBackend(model=model_name or DEFAULT_MODELS["anthropic"], config=config)
    elif backend_name == "gemini":
        return GeminiBackend(model=model_name or DEFAULT_MODELS["gemini"], config=config)
    else:
        available = ", ".join(DEFAULT_MODELS.keys())
        raise ValueError(f"Unknown backend: {name}. Available backends: {available}")


def list_backends() -> list[str]:
    """Return a list of available backend names."""
    return list(DEFAULT_MODELS.keys())
