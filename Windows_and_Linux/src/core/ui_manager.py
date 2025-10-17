"""
UI Manager - Centralized management of application windows and modals.

This module provides a UIManager class that centralizes the management of all
windows and modals of the Writing Tools application.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from ..ui.non_editable_modal import NonEditableModal

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class UIManager(QObject):
    """
    Centralized manager for all application windows and modals.

    This class provides methods to display and manage the different
    user interface windows in a centralized manner.
    """

    show_message_signal = Signal(str, str)

    def __init__(self, app: "WritingToolsApp"):
        """
        Initialize the user interface manager.

        Args:
            app: Main application instance of WritingToolsApp
        """
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)

        # Connect signal to slot
        self.show_message_signal.connect(self.show_message_box)

        # References to active windows
        self.non_editable_modal: NonEditableModal | None = None

    @Slot(str, str)
    def show_message_box(self, title: str, message: str) -> None:
        """
        Display a message box with the given title and message.

        For API errors, adds a button to open settings.

        Args:
            title: Message box title
            message: Message to display
        """
        self._logger.debug(f"Showing message box: {title}")
        self._logger.info(f"Message: {message}")

        msg_box = QMessageBox(None)
        msg_box.setWindowFlags(msg_box.windowFlags() | Qt.WindowType.WindowStaysOnTopHint)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Add standard OK button
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        # For API errors, add a button to open settings
        settings_button = None
        if any(
            keyword in title.lower()
            for keyword in [
                "api",
                "key",
                "quota",
                "rate limit",
                "connection",
                "authentication",
                "vision",
                "configuration",
            ]
        ):
            settings_button = msg_box.addButton("Open Settings", QMessageBox.ButtonRole.ActionRole)

        # Show the message box
        msg_box.exec()

        # If the settings button was clicked, open settings
        if settings_button and msg_box.clickedButton() == settings_button:
            self.app.systray_manager.show_settings()

