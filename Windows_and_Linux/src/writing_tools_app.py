"""
WritingToolsApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

import gettext
import logging
import os
from typing import TYPE_CHECKING

from pynput import keyboard as keyboard
from PySide6.QtWidgets import QApplication

from .aiprovider.anthropic import AnthropicProvider
from .aiprovider.gemini import GeminiProvider
from .aiprovider.mistral import MistralProvider
from .aiprovider.ollama import OllamaProvider
from .aiprovider.openAI import OpenAIProvider
from .aiprovider.openAI_compatible import OpenAICompatibleProvider
from .autostart_manager import AutostartManager
from .core.ai_processor import AIProcessor
from .core.clipboard_manager import ClipboardManager
from .core.hotkey_manager import HotkeyManager
from .core.image_processor import ImageProcessor
from .core.input_manager import InputManager
from .core.lifecycle_manager import LifecycleManager
from .core.popup_manager import PopupManager
from .core.settings_manager import SettingsManager
from .core.text_processor import TextProcessor
from .core.ui_manager import UIManager
from .core.update_manager import UpdateManager
from .systray import SystrayManager
from .ui.language_manager import LanguageManager
from .ui.response_window import ResponseWindow
from .ui.theme_manager import ThemeManager

if TYPE_CHECKING:
    from .aiprovider.aiprovider import AIProvider
    from .ui.response_window import ResponseWindow

os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.mime.warning=false;qt.qpa.mime.debug=false;qt.qpa.mime.info=false"  # Disable QMimeDatabase warnings
)

_ = gettext.gettext


class WritingToolsApp(QApplication):
    """
    The main application class for Writing Tools.
    """

    def __init__(self, argv):
        super().__init__(argv)
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing WritingToolsApp")

        try:
            self._logger.debug("Setting up core attributes...")
            self._setup_core_attributes()

            self._logger.debug("Setting up settings...")
            self._setup_settings()

            self._logger.debug("Setting up UI components...")
            self._setup_ui_components()


            # Initialize app based on configuration state
            self._logger.debug("Initializing app with normal launch")
            self._handle_normal_launch()

        except Exception as e:
            self._logger.error(f"Critical error during WritingToolsApp initialization: {e}")
            import traceback

            self._logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _setup_core_attributes(self) -> None:
        """Initialize core application attributes."""
        self.current_response_window: ResponseWindow | None = None
        self.ai_processor = AIProcessor(self)
        self.text_processor = TextProcessor(self)
        self.hotkey_manager = HotkeyManager(self)
        self.systray_manager = SystrayManager(self)
        self.image_processor = ImageProcessor(self, self._logger)
        self.clipboard_manager = ClipboardManager(self, self._logger)
        self.input_manager = InputManager(self, self._logger)
        self.popup_manager = PopupManager(self, self._logger)
        self.ui_manager = UIManager(self)
        self.lifecycle_manager = LifecycleManager(self)
        self.update_manager = UpdateManager(self)

    def _setup_settings(self) -> None:
        """Initialize settings manager and load configuration."""
        mode = self.lifecycle_manager._detect_running_mode()
        self._logger.debug(f"Running mode: {mode}")
        self.settings_manager = SettingsManager(mode=mode)

    def _setup_ui_components(self) -> None:
        """Initialize UI component references."""
        self.tray_icon = None
        self.non_editable_modal = None
        self.theme_manager = ThemeManager(self)
        self.language_manager = LanguageManager(self)
        self.styles = self.theme_manager.get_styles()


    def _handle_normal_launch(self) -> None:
        """Handle normal application launch with configured providers."""
        self._logger.debug("Providers configured, setting up hotkey and tray icon")

        try:
            self._initialize_ai_provider()
            self._setup_user_interface()
            self.language_manager.set_language(self.settings_manager.language or "en")
            self.update_manager.check_updates_async()
        except Exception as error:
            self._logger.exception(f"Error during app initialization: {error}")
            import traceback

            self._logger.debug(f"Full traceback: {traceback.format_exc()}")

    def _initialize_ai_provider(self) -> None:
        """Initialize and configure the current AI provider."""
        self.ai_processor.set_current_provider()

        if self.ai_processor.current_provider:
            self._logger.debug(
                f"Current provider: {self.ai_processor.current_provider.provider_name}"
            )
            provider_config = self.ai_processor.get_provider_config(self.settings_manager.provider)
            self._logger.debug(f"Provider config: {provider_config}")
            self.ai_processor.current_provider.load_config(provider_config)
            self._logger.debug("Provider config loaded successfully")

    def _setup_user_interface(self) -> None:
        """Setup user interface components."""
        AutostartManager.sync_with_settings(self.settings_manager) # Synchronize autostart state between system and settings
        self.systray_manager.create_tray_icon_with_startup_delay()
        self.hotkey_manager.register_hotkey()
