"""
UI components setup module for Writing Tools application.

This module contains setup functions for UI components.
"""

from ...autostart_manager import AutostartManager
from ...ui.language_manager import LanguageManager
from ...ui.theme_manager import ThemeManager


def setup_ui_components(app) -> None:
    """Initialize UI component references."""
    app.tray_icon = None
    app.non_editable_modal = None
    app.theme_manager = ThemeManager(app)
    app.language_manager = LanguageManager(app)
    app.styles = app.theme_manager.get_styles()


def setup_user_interface(app) -> None:
    """Setup user interface components."""
    AutostartManager.sync_with_settings(
        app.settings_manager
    )  # Synchronize autostart state between system and settings
    app.systray_manager.create_tray_icon_with_startup_delay()
    app.hotkey_manager.register_hotkey()
