"""
Centralized language manager for the entire application.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtCore import QObject, Signal
from PySide6.QtWidgets import QWidget

from .language.translations import Translations
from .language.widget_manager import WidgetManager

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class LanguageManager(QObject):
    """Centralized language manager with signals to notify changes."""

    language_changed = Signal(str)  # Emits the new language code (e.g., 'en', 'fr')

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.translations = Translations()
        self.widget_manager = WidgetManager(app)

    def register_widget(self, widget: QWidget) -> None:
        """Register a widget to receive language updates."""
        self.widget_manager.register_widget(widget)

    def unregister_widget(self, widget: QWidget) -> None:
        """Unregister a widget."""
        self.widget_manager.unregister_widget(widget)

    def set_language(self, new_language: str) -> None:
        """Change the language and notify all registered widgets."""
        # Update translations first to get the actual language used
        actual_language = self.translations.setup_translations(new_language)

        # Save the actual language to settings
        self.app.settings_manager.language = actual_language

        # Emit signal with the actual language
        self.language_changed.emit(actual_language)

        # Refresh all registered widgets
        self.widget_manager.refresh_registered_widgets()

        # Update tray menu and other UI elements
        self.app.systray_manager.update_tray_menu()
        self.translations._update_widget_translations()

        self._logger.debug(f"Language changed to: {actual_language}")
