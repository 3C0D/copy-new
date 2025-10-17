"""
Update notice component for CustomPopupWindow.
Displays update notifications when available.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QLabel, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp


class UpdateNotice(QWidget):
    """Update notice widget for displaying update information."""

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self.update_label: QLabel | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the update notice widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        update_available = self.app.settings_manager.update_available or False

        if update_available:
            self.update_label = QLabel()
            self.update_label.setOpenExternalLinks(True)
            self.update_label.setText(
                '<a href="https://github.com/theJayTea/WritingTools/releases" '
                'style="color:rgb(255, 0, 0); text-decoration: underline; font-weight: bold;">'
                "There's an update! :D Download now."
                "</a>"
            )
            self.update_label.setStyleSheet(self.app.styles["margin_top_10"])
            layout.addWidget(self.update_label, alignment=Qt.AlignmentFlag.AlignCenter)
