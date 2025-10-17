"""
Response Window package
Contains classes for displaying AI responses and chat functionality.
"""

from .chat_scroll_area import ChatContentScrollArea
from .image_preview_widget import ImagePreviewWidget
from .markdown_text_browser import MarkdownTextBrowser
from .message_container import MessageContainer
from .response_window import ResponseWindow
from .thinking_animation import ThinkingAnimation
from .window_sizing_manager import WindowSizingManager

__all__ = [
    "ChatContentScrollArea",
    "ImagePreviewWidget",
    "MarkdownTextBrowser",
    "MessageContainer",
    "ResponseWindow",
    "ThinkingAnimation",
    "WindowSizingManager",
]


def _(x):
    return x
