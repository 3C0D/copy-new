"""
UI Manager - Centralized management of application windows and modals.

This module provides a UIManager class that centralizes the management of all
windows and modals of the Writing Tools application.
"""

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import QObject, Qt, Signal, Slot
from PySide6.QtWidgets import QMessageBox

from ..ui.non_editable_modal import NonEditableModal
from ..ui.response_window import ResponseWindow

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
        self.response_window: Optional[ResponseWindow] = None
        self.non_editable_modal: Optional[NonEditableModal] = None

    def show_response_window(self, option: str, text: Optional[str] = None) -> ResponseWindow:
        """
        Display a response window to show AI results.

        Args:
            option: Selected option (e.g., "Summary", "Rewrite", etc.)
            text: Selected text or None for image mode

        Returns:
            ResponseWindow: Created window instance
        """
        self._logger.debug(f"Showing response window for option: {option}")

        response_window = ResponseWindow(self.app, f"{option} Result")

        # Configuration for image if available
        if hasattr(self.app.popup_manager, "has_image") and self.app.popup_manager.has_image:
            response_window.image = self.app.popup_manager.image
            self._logger.debug("Image configured in response window")
            response_window.selected_text = None
        else:
            response_window.selected_text = text
            response_window.image = None

        response_window.show()
        self.response_window = response_window
        return response_window

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

    def _show_non_editable_modal(self, transformed_text: Optional[str] = None) -> None:
        """
        Display a modal for non-editable text.

        Used when direct pasting fails and the transformed text needs to be displayed
        in a modal.

        Args:
            transformed_text: Transformed text to display
        """
        self._logger.debug("Showing non-editable modal")

        if self.non_editable_modal:
            self.non_editable_modal.close()

        self.non_editable_modal = NonEditableModal(self.app, transformed_text)
        self.non_editable_modal.show()

    # not used? !!!
    def close_all_windows(self) -> None:
        """
        Close all windows managed by this manager.
        """
        self._logger.debug("Closing all windows")

        windows_to_close = [
            self.response_window,
            self.non_editable_modal,
        ]

        for window in windows_to_close:
            if window:
                window.close()

        # Reset references
        self.response_window = None
        self.non_editable_modal = None
