"""
Central configuration manager for the Writing Tools application.
Centralizes management of settings, languages, themes, and running mode.
"""

import gettext
import logging
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6.QtCore import QLocale
from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


class ConfigManager:
    """
    Central configuration manager for the application.

    Centralizes management of settings, languages, themes, and running mode.
    """

    def __init__(self, app: "WritingToolApp"):
        """
        Initialize the configuration manager.

        Args:
            app: Main application instance
        """
        self.app = app
        self._logger = logging.getLogger(__name__)

        # Detect running mode
        self.running_mode = self._detect_running_mode()

        # Initialize translations
        self._current_translation: gettext.NullTranslations | None = None
        self._ = gettext.gettext  # Default translation function !!! à garder?

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
            AboutWindow,
            CustomPopupWindow,
            HelpWindow,
            OnboardingWindow,
            ResponseWindow,
            SettingsWindow,
        )

        AboutWindow._ = self._
        SettingsWindow._ = self._
        ResponseWindow._ = self._
        OnboardingWindow._ = self._
        CustomPopupWindow._ = self._
        HelpWindow._ = self._

    def retranslate_ui(self) -> None:
        """
        Retranslate user interface elements.
        """
        self.app.systray_manager.update_tray_menu()
        self._update_widget_translations()  # !!! usefull?
        self._logger.debug("UI retranslated")

    def _update_widget_translations(self) -> None:
        """
        Update translations for all top-level widgets.
        """

        for widget in QApplication.topLevelWidgets():
            if widget != self.app and hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()  # type: ignore

    def _detect_running_mode(self) -> str:
        """
        Detect the running mode based on the environment.

        Returns:
            str: "dev", "build-dev", or "build-final"
        """
        base_dir = Path(sys.executable).parent

        # Development mode
        if not getattr(sys, "frozen", False):
            self._logger.debug("Detected mode: dev")
            return "dev"

        # Build-dev mode
        elif base_dir.name == "dev":
            self._logger.debug("Detected mode: build-dev")
            return "build-dev"

        # Build-final mode
        else:
            self._logger.debug("Detected mode: build-final")
            return "build-final"

    def get_current_language(self) -> str:
        """
        Get the current language.

        Returns:
            str: Current language code
        """
        return getattr(self.app.settings_manager, "language", "en")

    def get_current_theme(self) -> str:
        """
        Get the current theme.

        Returns:
            str: Current color mode ('dark', 'light', 'auto')
        """
        return self.app.settings_manager.color_mode

    def change_theme(self, new_mode: str) -> None:
        """
        Change the application theme.

        Args:
            new_mode: New mode ('dark', 'light', 'auto')
        """
        self.app.theme_manager.change_color_mode(new_mode)
        self._logger.debug(f"Theme changed to: {new_mode}")

    def change_background_theme(self, new_theme: str) -> None:
        """
        Change the background theme.

        Args:
            new_theme: New background theme ('gradient', 'plain')
        """
        self.app.theme_manager.change_background_theme(new_theme)
        self._logger.debug(f"Background theme changed to: {new_theme}")
