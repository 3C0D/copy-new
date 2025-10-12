"""
Markdown Text Browser - Enhanced text browser for displaying Markdown content.
"""

from typing import TYPE_CHECKING

from PySide6 import QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QTextBrowser, QWidget

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .chat_scroll_area import ChatContentScrollArea


def _(x):
    return x


class MarkdownTextBrowser(QTextBrowser):
    """Enhanced text browser for displaying Markdown content with improved sizing"""

    def __init__(
        self, app: "WritingToolsApp", parent: QWidget | None = None, is_user_message: bool = False
    ):
        super().__init__(parent)
        self.app = app
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.zoom_factor = 1.2
        self.base_font_size = 14
        self.is_user_message = is_user_message

        # Critical: Remove scrollbars to prevent extra space
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Set size policies to prevent unwanted expansion
        from PySide6.QtWidgets import QSizePolicy

        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self._apply_zoom()

    def _apply_zoom(self) -> None:
        new_size = int(self.base_font_size * self.zoom_factor)

        current_mode = self.app.settings_manager.color_mode

        self.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {("transparent" if self.is_user_message else "#333" if current_mode == "dark" else "#f8f9fa")};
                color: {"#ffffff" if current_mode == "dark" else "#212529"};
                border: {("none" if self.is_user_message else "1px solid " + ("#555" if current_mode == "dark" else "#dee2e6"))};
                border-radius: 8px;
                padding: 8px;
                margin: 0px;
                font-size: {new_size}px;
                line-height: 1.3;
                width: 100%;
            }}

            /* Table styles */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}

            th, td {{
                border: 1px solid {"#555" if current_mode == "dark" else "#dee2e6"};
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: {"#444" if current_mode == "dark" else "#e9ecef"};
                font-weight: bold;
            }}

            tr:nth-child(even) {{
                background-color: {"#3a3a3a" if current_mode == "dark" else "#f8f9fa"};
            }}

            tr:hover {{
                background-color: {"#484848" if current_mode == "dark" else "#e9ecef"};
            }}
        """,
        )

    def _update_size(self) -> None:
        # Calculate correct document width
        available_width = self.viewport().width() - 16  # Account for padding
        self.document().setTextWidth(available_width)

        # Get precise content height
        doc_size = self.document().size()
        content_height = doc_size.height()

        # Add minimal padding for content
        new_height = int(content_height + 16)  # Reduced total padding

        if self.minimumHeight() != new_height:
            self.setMinimumHeight(new_height)
            self.setMaximumHeight(new_height)  # Force fixed height

            # Update scroll area if needed
            scroll_area = self.get_scroll_area()
            if scroll_area:
                scroll_area.update_content_height()

    def wheelEvent(self, e: QtGui.QWheelEvent) -> None:
        if e.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = e.angleDelta().y()
            # Get the main response window
            parent = self.parent()
            while parent and not hasattr(parent, "zoom_all_messages"):
                parent = parent.parent()

            if parent:
                if delta > 0:
                    parent.zoom_all_messages("in")  # type: ignore
                else:
                    parent.zoom_all_messages("out")  # type: ignore
                e.accept()
        # Pass wheel events to parent for scrolling
        else:
            parent = self.parent()
            if parent and isinstance(parent, QWidget) and hasattr(parent, "wheelEvent"):
                parent.wheelEvent(e)

    def zoom_in(self) -> None:
        old_factor = self.zoom_factor
        self.zoom_factor = min(3.0, self.zoom_factor * 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()
            self._save_zoom()

    def zoom_out(self) -> None:
        old_factor = self.zoom_factor
        self.zoom_factor = max(0.5, self.zoom_factor / 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()
            self._save_zoom()

    def reset_zoom(self) -> None:
        old_factor = self.zoom_factor
        self.zoom_factor = 1.2  # Reset to default zoom
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()
            self._save_zoom()

    def get_scroll_area(self) -> "ChatContentScrollArea | None":
        """Find the parent ChatContentScrollArea"""
        from .chat_scroll_area import ChatContentScrollArea

        parent = self.parent()
        while parent:
            if isinstance(parent, ChatContentScrollArea):
                return parent
            parent = parent.parent()
        return None

    def resizeEvent(self, e: QtGui.QResizeEvent) -> None:
        super().resizeEvent(e)
        self._update_size()

    def _save_zoom(self) -> None:
        """Save the current zoom factor to settings"""
        # Get the ResponseWindow parent
        parent = self.parent()
        while parent and not hasattr(parent, "zoom_all_messages"):
            parent = parent.parent()

        if parent and hasattr(parent, "app"):
            parent.app.settings_manager.response_window_zoom = self.zoom_factor  # type: ignore
