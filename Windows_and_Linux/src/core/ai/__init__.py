"""
AI Core Modules - Contains AI processing related classes.

This package includes specialized classes for AI request processing,
context detection, and message formatting for different providers.
"""

from .context_detector import ContextDetector
from .message_formatter import MessageFormatter

__all__ = [
    "ContextDetector",
    "MessageFormatter",
]
