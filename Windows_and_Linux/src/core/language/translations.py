"""
Translation management for the application.
"""

import gettext
import logging
from pathlib import Path

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

from ...ui import about_window, help_window
from ...ui.custom_popup import custom_popup_window
from ...ui.SettingsWindow import settings_window


class Translations:
    """Handles translation setup and updates."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._ = gettext.gettext

    def setup_translations(self, lang: str | None = None) -> str:
        """
        Setup translations for the specified language.

        Args:
            lang: Language code (e.g., 'en', 'fr'). If None, uses system language.

        Returns:
            The language code that was actually set (may be default 'en' if requested not found).
        """
        # If no language specified, use system language code (e.g., 'fr' from 'fr_FR')
        if not lang:
            lang = QLocale.system().name().split("_")[0]

        locales_dir = Path(__file__).parent.parent.parent.parent / "locales"

        try:
            # Load gettext translation object for the specified language
            translation = gettext.translation(
                "messages",
                localedir=str(locales_dir),
                languages=[lang],
            )
            actual_lang = lang
        except FileNotFoundError:
            # Try default language 'en'
            try:
                translation = gettext.translation(
                    "messages",
                    localedir=str(locales_dir),
                    languages=['en'],
                )
                actual_lang = 'en'
            except FileNotFoundError:
                translation = gettext.NullTranslations()
                actual_lang = 'en'  # Default to 'en' even with NullTranslations

        # Install translation as default gettext function
        translation.install()
        # Update translation functions in all UI modules
        self._update_translation_functions(translation)
        self._logger.debug(f"Translations set up for language: {actual_lang}")
        return actual_lang

    def _update_translation_functions(self, translation: gettext.NullTranslations) -> None:
        """
        Update translation functions for all UI components.

        Args:
            translation: gettext translation object
        """
        self._ = translation.gettext

        # Import and update UI modules. Avoid circular imports.
        from ... import systray
        from ...ui import (
            response_window,
        )
        from ...ui.SettingsWindow import general_settings, provider_settings

        about_window._ = self._
        settings_window._ = self._
        response_window._ = self._
        custom_popup_window._ = self._
        help_window._ = self._
        general_settings._ = self._
        provider_settings._ = self._
        systray._ = self._

    def _update_widget_translations(self) -> None:
        """Update translations for all top-level widgets."""

        for widget in QApplication.topLevelWidgets():
            if hasattr(widget, "refresh_language"):
                widget.refresh_language()  # type: ignore
