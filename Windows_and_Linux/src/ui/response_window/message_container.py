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

            current_mode = self.app.settings_manager.color_mode

            self.copy_btn.setStyleSheet(
                f"""
                QToolButton {{
                    background-color: {"rgba(68, 68, 68, 0.9)" if current_mode == "dark" else "rgba(248, 249, 250, 0.95)"};
                    border: 1px solid {"#666" if current_mode == "dark" else "#dee2e6"};
                    border-radius: 6px;
                    padding: 2px;
                    margin: 0px;
                    spacing: 0px;
                }}
                QToolButton:hover {{
                    background-color: {"rgba(85, 85, 85, 0.9)" if current_mode == "dark" else "rgba(233, 236, 239, 0.95)"};
                    border: 1px solid {"#777" if current_mode == "dark" else "#adb5bd"};
                }}
            """,
            )
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

    def copy_content(self) -> None:
        """Copy the message content to clipboard with visual feedback"""
        QApplication.clipboard().setText(self.markdown_text)

        # Visual feedback: temporarily change button color
        if hasattr(self, "copy_btn"):
            original_style = self.copy_btn.styleSheet()

            # Success feedback style
            success_style = """
                QToolButton {
                    background-color: rgba(76, 175, 80, 0.9);
                    border: 1px solid #4CAF50;
                    border-radius: 6px;
                    padding: 2px;
                }
            """

            # Apply success style
            self.copy_btn.setStyleSheet(success_style)

            # Reset to original style after 500ms
            QtCore.QTimer.singleShot(
                500,
                lambda: self.copy_btn.setStyleSheet(original_style),
            )
