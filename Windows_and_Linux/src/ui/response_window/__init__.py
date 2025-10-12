"""
Response Window package
Contains classes for displaying AI responses and chat functionality.
"""

from .chat_scroll_area import ChatContentScrollArea
from .markdown_text_browser import MarkdownTextBrowser
from .message_container import MessageContainer
from .response_window import ResponseWindow

__all__ = [
    "ChatContentScrollArea",
    "MarkdownTextBrowser",
    "MessageContainer",
    "ResponseWindow",
]


def _(x):
    return x
