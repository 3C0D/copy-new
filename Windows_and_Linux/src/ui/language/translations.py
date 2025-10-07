"""
Translation management for the application.
"""

import gettext
import logging
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from .. import about_window, help_window
from ..custom_popup import custom_popup_window
from ..SettingsWindow import settings_window


class Translations:
    """Handles translation setup and updates."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._current_translation: gettext.NullTranslations | None = None
        self._ = gettext.gettext

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
        from .. import (
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
            if hasattr(widget, "refresh_language"):
                widget.refresh_language()  # type: ignore
