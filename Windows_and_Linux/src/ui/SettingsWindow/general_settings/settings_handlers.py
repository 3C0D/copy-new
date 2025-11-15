"""
settings_handlers.py

Business logic handlers for settings changes.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp
    from ..settings_window import SettingsWindow

from ....autostart_manager import AutostartManager


class SettingsHandlers:
    """Handles all settings change logic."""

    def __init__(self, app: "WritingToolsApp", parent_window: "SettingsWindow"):
        self.app = app
        self.parent_window = parent_window
        self._logger = logging.getLogger(__name__)
        self._changing_language = False

    def handle_autostart_changed(self, state: int) -> None:
        """Handle autostart toggle and auto-save."""
        enable = state == 2  # Qt.Checked
        AutostartManager.set_autostart_with_sync(enable, self.app.settings_manager)

        # Update systray action state if systray exists
        if self.app.systray_manager.autostart_action:
            self.app.systray_manager.autostart_action.setChecked(enable)

    def handle_language_changed(self, language_dropdown) -> None:
        """Handle language change and auto-save."""
        if self._changing_language:
            return

        if language_dropdown is None:
            return

        selected_lang_code = language_dropdown.currentData()
        if selected_lang_code:
            self._changing_language = True
            try:
                self.app.language_manager.set_language(selected_lang_code)
            finally:
                self._changing_language = False

    def handle_shortcut_changed(self, shortcut_input) -> None:
        """Handle shortcut change and auto-save."""
        if shortcut_input is None:
            return

        self.app.settings_manager.hotkey = (
            " ".join((shortcut_input.text() or "ctrl space").split()) or "ctrl space"
        )
        self.app.hotkey_manager.register_hotkey()

    def handle_theme_changed(self, gradient_radio) -> None:
        """Handle theme change and auto-save."""
        if gradient_radio is None:
            return

        theme = "gradient" if gradient_radio.isChecked() else "plain"
        self.app.theme_manager.change_background_theme(theme)

    def handle_color_mode_changed(self, color_mode_dropdown) -> None:
        """Handle color mode change and auto-save."""
        if color_mode_dropdown is None:
            return

        selected_text = color_mode_dropdown.currentText()
        mode_mapping = {"Auto": "auto", "Light": "light", "Dark": "dark"}
        color_mode = mode_mapping.get(selected_text, "auto")

        self.app.theme_manager.change_color_mode(color_mode)
        self.parent_window.refresh_theme()
