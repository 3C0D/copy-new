"""
Centralized language manager for the entire application.
"""

import gettext
import logging
from pathlib import Path
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore
from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from ..ui import about_window, help_window
from ..ui.custom_popup import custom_popup_window
from ..ui.SettingsWindow import settings_window

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class LanguageManager(QtCore.QObject):
    """Centralized language manager with signals to notify changes."""

    language_changed = QtCore.Signal(str)  # Emits the new language code (e.g., 'en', 'fr')

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self._registered_widgets = []
        self._current_translation: gettext.NullTranslations | None = None
        # self._ = gettext.gettext

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
        self.setup_translations(new_language)

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
        self.app.systray_manager.update_tray_menu()
        self._update_widget_translations()

        self._logger.debug(f"Language changed to: {new_language}")

    def setup_translations(self, lang: str | None = None) -> None:
        """
        Setup translations for the specified language.

        Args:
            lang: Language code (e.g., 'en', 'fr'). If None, uses system language.
        """
        if not lang:
            lang = QLocale.system().name().split("_")[0]

        try:
            locales_dir = Path(__file__).parent.parent.parent / "locales"
            translation = gettext.translation(
                "messages",
                localedir=str(locales_dir),
                languages=[lang],
            )
        except FileNotFoundError:
            translation = gettext.NullTranslations()

        translation.install()
        self._current_translation = translation
        self._update_translation_functions(translation)
        self._logger.debug(f"Translations set up for language: {lang}")

    def _update_translation_functions(self, translation: gettext.NullTranslations) -> None:
        """
        Update translation functions for all UI components.

        Args:
            translation: gettext translation object
        """
        self._ = translation.gettext

        # Import and update UI modules
        from ..ui import (
            response_window,
        )

        about_window._ = self._
        settings_window._ = self._
        response_window._ = self._
        custom_popup_window._ = self._
        help_window._ = self._

    def _update_widget_translations(self) -> None:
        """Update translations for all top-level widgets."""

        for widget in QApplication.topLevelWidgets():
            if widget != self.app and hasattr(widget, "refresh_language"):
                widget.refresh_language()  # type: ignore
