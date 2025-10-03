"""
VisionSupportValidator module
Valide le support vision des modèles AI.
"""

from ...config.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    MISTRAL_MODELS,
    OPENAI_MODELS,
)


class VisionSupportValidator:
    """Valide le support vision des modèles."""

    VISION_MODELS = {
        "gemini": GEMINI_MODELS,
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "mistral": MISTRAL_MODELS,
    }

    OLLAMA_VISION_INDICATORS = ["llava", "bakllava", "moondream", "minicpm-v", "qwen2.5vl"]

    @classmethod
    def has_vision_support(cls, provider_name: str, api_model: str) -> bool:
        """Vérifie si le modèle supporte la vision."""
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
        return any(ind in model.lower() for ind in cls.OLLAMA_VISION_INDICATORS)
