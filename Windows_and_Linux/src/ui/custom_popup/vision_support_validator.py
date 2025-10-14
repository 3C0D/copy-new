"""
VisionSupportValidator module
Validates AI model vision support.
"""

# Type checking imports
from typing import TYPE_CHECKING

from ...config.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    MISTRAL_MODELS,
    OLLAMA_VISION_INDICATORS,
    OPENAI_MODELS,
)

if TYPE_CHECKING:
    from ...aiprovider.aiprovider import AIProvider


class VisionSupportValidator:
    """Validates model vision support."""

    VISION_MODELS = {
        "gemini": GEMINI_MODELS,
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "mistral": MISTRAL_MODELS,
    }

    @classmethod
    def has_vision_support(
        cls, provider_name: str, api_model: str, provider_instance: "AIProvider | None" = None
    ) -> bool:
        """Checks if the model supports vision."""
        if not provider_name or not api_model:
            return False

        # Special handling for openai-compatible provider
        if provider_name == "openai-compatible":
            # Prefer direct access from provider instance if available
            if provider_instance and hasattr(provider_instance, "has_vision"):
                return bool(getattr(provider_instance, "has_vision", False))
            # Fallback: not supported if we can't determine
            return False

        if provider_name in cls.VISION_MODELS:
            return cls._check_standard_provider(provider_name, api_model)

        if provider_name == "ollama":
            return cls._check_ollama_model(api_model)

        return False

    @classmethod
    def _check_standard_provider(cls, provider: str, model: str) -> bool:
        return any(m[1] == model and m[2].get("vision", False) for m in cls.VISION_MODELS[provider])

    @classmethod
    def _check_ollama_model(cls, model: str) -> bool:
        return any(indicator in model.lower() for indicator in OLLAMA_VISION_INDICATORS)
