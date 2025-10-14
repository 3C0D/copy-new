"""
VisionSupportValidator module
Validates AI model vision support.
"""

from ...config.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    MISTRAL_MODELS,
    OLLAMA_VISION_INDICATORS,
    OPENAI_MODELS,
)


class VisionSupportValidator:
    """Validates model vision support."""

    VISION_MODELS = {
        "gemini": GEMINI_MODELS,
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "mistral": MISTRAL_MODELS,
    }

    @classmethod
    def has_vision_support(cls, provider_name: str, api_model: str) -> bool:
        """Checks if the model supports vision."""
        if not provider_name or not api_model:
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
