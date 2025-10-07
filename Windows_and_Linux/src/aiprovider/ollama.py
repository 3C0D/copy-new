"""
Ollama Provider and State Manager - Combined module for Ollama integration.

This module provides backward compatibility by importing the separated classes:
- OllamaStateManager: Handles Ollama state, installation, and model management
- OllamaProvider: AI provider implementation for Ollama server communication

For new code, prefer importing directly from the specific modules:
- from .ollama_state import OllamaStateManager
- from .ollama_provider import OllamaProvider
"""

# Import the separated classes for backward compatibility
from .ollama_provider import OllamaProvider
from .ollama_state import OllamaStateManager

# Re-export for backward compatibility
__all__ = ["OllamaStateManager", "OllamaProvider"]
