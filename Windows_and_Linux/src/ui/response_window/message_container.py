"""
Message Container - Container for individual messages with copy functionality.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QApplication, QSizePolicy, QToolButton, QVBoxLayout, QWidget

from ..ui_utils import ui_utils

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .markdown_text_browser import MarkdownTextBrowser


def _(x):
    return x


class MessageContainer(QWidget):
    """Container for individual messages with copy functionality"""

    def __init__(
        self,
        app: "WritingToolsApp",
        parent: QWidget | None = None,
        is_user: bool = False,
        text: str = "",
        text_display: "MarkdownTextBrowser | None" = None,
    ):
        super().__init__(parent)
        self.app = app
        self.markdown_text = text
        self.is_user = is_user
        self.text_display = text_display
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        # Main layout for the message container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if self.text_display:
            layout.addWidget(self.text_display)

        # Add copy button for assistant messages only (positioned absolutely)
        if not is_user:
            self.copy_btn = QToolButton(self)
            # Use the copy_md icon (SVG format with theme support)

            icon_path = ui_utils.get_icon_path(self.app, "copy_md", with_theme=True)
            if icon_path.exists():
                self.copy_btn.setIcon(QtGui.QIcon(icon_path.as_posix()))

            self.copy_btn.setStyleSheet(self.app.styles["copy_button"])
            self.copy_btn.setToolTip(_("Copy as Markdown"))
            self.copy_btn.clicked.connect(self.copy_content)
            self.copy_btn.setFixedSize(32, 32)
            self.copy_btn.setIconSize(QtCore.QSize(24, 24))
            self.copy_btn.hide()  # Initially hidden

            # Install event filter to handle hover
            self.installEventFilter(self)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Handle mouse enter/leave events to show/hide copy button"""
        if watched == self and not self.is_user:
            if event.type() == QtCore.QEvent.Type.Enter:
                if hasattr(self, "copy_btn"):
                    self.copy_btn.show()
            elif event.type() == QtCore.QEvent.Type.Leave:
                if hasattr(self, "copy_btn"):
                    self.copy_btn.hide()
        return super().eventFilter(watched, event)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Position the copy button in the top-right corner"""
        super().resizeEvent(event)
        if hasattr(self, "copy_btn") and not self.is_user:
            # Position button in top-right corner with some margin
            btn_size = self.copy_btn.size()
            self.copy_btn.move(
                self.width() - btn_size.width() - 8,  # 8px from right edge
                8,  # 8px from top edge
            )

    def refresh_language(self) -> None:
        """Refresh tooltip text to reflect current language."""
        try:
            if hasattr(self, "copy_btn") and not self.is_user:
                self.copy_btn.setToolTip(_("Copy as Markdown"))
        except RuntimeError:
            # Widget might be destroyed, skip refresh
            pass

    def copy_content(self) -> None:
        """Copy the message content to clipboard with visual feedback"""
        QApplication.clipboard().setText(self.markdown_text)

        # Visual feedback: temporarily change button color
        if hasattr(self, "copy_btn"):
            original_style = self.copy_btn.styleSheet()

            # Apply success style
            self.copy_btn.setStyleSheet(self.app.styles["copy_button_success"])

            # Reset to original style after 500ms
            QtCore.QTimer.singleShot(
                500,
                lambda: self.copy_btn.setStyleSheet(original_style),
            )
