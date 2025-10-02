"""
Centralized language manager for the entire application.
"""

import logging
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore

if TYPE_CHECKING:
    pass


class LanguageManager(QtCore.QObject):
    """Centralized language manager with signals to notify changes."""

    language_changed = QtCore.Signal(str)  # Emits the new language code (e.g., 'en', 'fr')

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self._registered_widgets = []

    def register_widget(self, widget: Any) -> None:
        """Register a widget to receive language updates."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget: Any) -> None:
        """Unregister a widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def change_language(self, new_language: str) -> None:
        """Change the language and notify all registered widgets."""
        # Save to settings
        self.app.settings_manager.language = new_language

        # Update translations
        self.app.config_manager.setup_translations(new_language)

        # Emit signal
        self.language_changed.emit(new_language)

        # Refresh all registered widgets
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_language"):
                try:
                    widget.refresh_language()
                except RuntimeError:
                    # Widget destroyed, remove it from the list
                    self._registered_widgets.remove(widget)

        # Update tray menu and other UI elements
        self.app.retranslate_ui()
        self._update_widget_translations()

        self._logger.debug(f"Language changed to: {new_language}")

    def _update_widget_translations(self) -> None:
        """Update translations for all top-level widgets."""
        from PySide6.QtWidgets import QApplication

        for widget in QApplication.topLevelWidgets():
            if widget != self.app and hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()  # type: ignore
