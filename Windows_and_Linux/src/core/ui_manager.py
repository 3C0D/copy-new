"""
UI Manager - Centralized management of application windows and modals.

This module provides a UIManager class that centralizes the management of all
windows and modals of the Writing Tools application.
"""

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtCore import Qt
from PySide6.QtWidgets import QMessageBox

from ..ui.NonEditableModal import NonEditableModal
from ..ui.OnboardingWindow import OnboardingWindow
from ..ui.ResponseWindow import ResponseWindow
from ..ui.SettingsWindow import SettingsWindow

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


class UIManager:
    """
    Centralized manager for all application windows and modals.

    This class provides methods to display and manage the different
    user interface windows in a centralized manner.
    """

    def __init__(self, app: "WritingToolApp"):
        """
        Initialize the user interface manager.

        Args:
            app: Main application instance of WritingToolApp
        """
        self.app = app
        self._logger = logging.getLogger(__name__)

        # References to active windows
        self.onboarding_window: Optional[OnboardingWindow] = None
        self.settings_window: Optional[SettingsWindow] = None
        self.response_window: Optional[ResponseWindow] = None
        self.non_editable_modal: Optional[NonEditableModal] = None

    def show_onboarding(self) -> None:
        """
        Display the onboarding window for new users.

        Creates an OnboardingWindow instance and displays it, connecting
        the close signal to the appropriate handling method.
        """
        self._logger.debug("Showing onboarding window")

        if self.onboarding_window:
            self.onboarding_window.close()

        self.onboarding_window = OnboardingWindow(self.app)
        self.onboarding_window.close_signal.connect(
            self.app.lifecycle_manager.on_onboarding_closed()
        )
        self.onboarding_window.show()

    def show_settings(self, providers_only: bool = False, previous_window=None) -> None:
        """
        Show the settings window with debounce protection against rapid clicks.

        Args:
            providers_only: If True, show only the provider settings section
            previous_window: Previous window for navigation
        """
        import time

        current_time = time.time() * 1000  # Convert to milliseconds

        # Prevent rapid successive clicks that could accidentally open Settings
        # This fixes the bug where rapid right-clicks on tray icon open Settings accidentally
        if (
            hasattr(self.app.systray_manager, "last_tray_click_time")
            and (current_time - self.app.systray_manager.last_tray_click_time)
            < self.app.systray_manager.tray_click_debounce_ms
        ):
            self._logger.debug("Settings click ignored due to debounce protection")
            return

        self.app.systray_manager.last_tray_click_time = int(current_time)

        self._logger.debug("Showing settings window")

        if self.settings_window:
            self.settings_window.close()

        # Always create a new settings window to handle providers_only correctly
        self.settings_window = SettingsWindow(self.app, providers_only=providers_only)

        # Set reference to previous window for navigation
        if previous_window:
            self.settings_window.previous_window = previous_window

        # self.settings_window.close_signal.connect(self.app.lifecycle_manager.on_onboarding_closed)
        # previously... !!! does it change anything?
        # self.settings_window.close_signal.connect(self.app.lifecycle_manager.exit_app)

        self.settings_window.retranslate_ui()
        self.settings_window.show()

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
        if (
            hasattr(self.app.popup_manager, "has_image")
            and self.app.popup_manager.has_image
            and self.app.popup_manager.image
        ):
            response_window.image = self.app.popup_manager.image
            self._logger.debug("Image configured in response window")
            response_window.selected_text = None
        else:
            response_window.selected_text = text
            response_window.image = None

        response_window.show()
        self.response_window = response_window
        return response_window

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
            self.show_settings()

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
            self.onboarding_window,
            self.settings_window,
            self.response_window,
            self.non_editable_modal,
        ]

        for window in windows_to_close:
            if window:
                window.close()

        # Reset references
        self.onboarding_window = None
        self.settings_window = None
        self.response_window = None
        self.non_editable_modal = None
