"""
Chat Scroll Area - Scrollable container for chat messages.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QScrollArea, QSizePolicy, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .markdown_text_browser import MarkdownTextBrowser

# Using hasattr checks instead of isinstance to avoid circular imports


class ChatContentScrollArea(QScrollArea):
    """Improved scrollable container for chat messages with dynamic sizing and proper spacing"""

    def __init__(self, app: "WritingToolsApp", parent: QWidget | None = None):
        super().__init__(parent)
        self.app = app
        self.content_widget: QWidget | None = None
        self.content_layout: QVBoxLayout | None = None
        self.setup_ui()

    def setup_ui(self) -> None:
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Main container widget with explicit size policy
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.MinimumExpanding,
        )
        self.setWidget(self.content_widget)

        # Main layout with improved spacing
        self.content_layout = QVBoxLayout(self.content_widget)
        self.content_layout.setSpacing(8)  # Reduced spacing between messages
        self.content_layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins
        self.content_layout.addStretch()

        # Enhanced scroll area styling - consistent with SettingsWindow
        self.setStyleSheet(self.app.styles["chat_scroll_area"])

    def add_message(self, text: str, is_user: bool = False) -> "MarkdownTextBrowser | None":
        """Add a new message to the chat area and return the text display widget"""
        from .markdown_text_browser import MarkdownTextBrowser
        from .message_container import MessageContainer

        if not self.content_layout:
            return None

        # Remove bottom stretch
        self.content_layout.takeAt(self.content_layout.count() - 1)

        # Create text display first
        import markdown2

        text_display = MarkdownTextBrowser(self.app, self.content_widget, is_user_message=is_user)
        html = markdown2.markdown(text, extras=["tables"])
        text_display.setHtml(html)

        # Wrap in MessageContainer for copy functionality
        msg_container = MessageContainer(
            self.app,
            self.content_widget,
            is_user=is_user,
            text=text,
            text_display=text_display,
        )

        self.content_layout.addWidget(msg_container)
        self.content_layout.addStretch()

        parent = self.parent()
        if hasattr(parent, "current_text_display") and hasattr(parent, "_adjust_window_height"):
            parent.current_text_display = text_display  # type: ignore

        QtCore.QTimer.singleShot(50, self.post_message_updates)

        return text_display

    def post_message_updates(self) -> None:
        """Handle updates after adding a message with proper timing"""
        self.scroll_to_bottom()
        parent = self.parent()
        if hasattr(parent, "_adjust_window_height"):
            parent._adjust_window_height()  # type: ignore

    def update_content_height(self) -> None:
        """Recalculate total content height with improved spacing calculation"""
        if not self.content_layout:
            return

        total_height = 0

        # Calculate height of all messages
        for i in range(self.content_layout.count() - 1):  # Skip stretch item
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                widget_height = item.widget().sizeHint().height()
                total_height += widget_height

        # Add spacing between messages and margins
        total_height += self.content_layout.spacing() * (
            self.content_layout.count() - 2
        )  # Message spacing
        total_height += (
            self.content_layout.contentsMargins().top()
            + self.content_layout.contentsMargins().bottom()
        )

        # Set minimum height with some padding
        if self.content_widget:
            self.content_widget.setMinimumHeight(total_height + 10)

        # Update window height if needed
        parent = self.parent()
        if hasattr(parent, "_adjust_window_height"):
            parent._adjust_window_height()  # type: ignore

    def scroll_to_bottom(self) -> None:
        """Smooth scroll to bottom of content"""
        vsb = self.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def resizeEvent(self, arg__1: QtGui.QResizeEvent) -> None:
        """Handle resize events with improved width calculations"""
        super().resizeEvent(arg__1)

        if not self.content_layout:
            return

        # Update width for all message displays
        available_width = self.width() - 40  # Account for margins
        for i in range(self.content_layout.count() - 1):  # Skip stretch item
            item = self.content_layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                from .message_container import MessageContainer

                if isinstance(container, MessageContainer):
                    # Recalculate text width and height for MessageContainer
                    text_display = container.text_display
                    if text_display and text_display.document():
                        text_display.document().setTextWidth(available_width)
                        doc_size = text_display.document().size()
                        exact_height = int(doc_size.height() + 20)  # Reduced padding
                        text_display.setMinimumHeight(exact_height)
                        text_display.setMaximumHeight(exact_height)  # Fixed height for all messages
