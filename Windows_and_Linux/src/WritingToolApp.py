"""
WritingToolApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

import gettext
import logging
import os
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING

from pynput import keyboard as keyboard
from PySide6 import QtCore
from PySide6.QtCore import Signal, Slot
from PySide6.QtWidgets import QApplication

from .aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)
from .AutostartManager import AutostartManager
from .config.settings import SettingsManager
from .core.ai_processor import AIProcessor
from .core.clipboard_manager import ClipboardManager
from .core.config_manager import ConfigManager
from .core.hotkey_manager import HotkeyManager
from .core.image_processor import ImageProcessor
from .core.input_manager import InputManager
from .core.popup_manager import PopupManager
from .core.text_processor import TextProcessor
from .core.ui_manager import UIManager
from .systray import SystrayManager
from .ui.LanguageManager import LanguageManager
from .ui.ResponseWindow import ResponseWindow
from .ui.ThemeManager import ThemeManager
from .update_checker import UpdateChecker

if TYPE_CHECKING:
    from .aiprovider import AIProvider
    from .ui.ResponseWindow import ResponseWindow

os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.mime.warning=false;qt.qpa.mime.debug=false;qt.qpa.mime.info=false"  # Disable QMimeDatabase warnings
)

_ = gettext.gettext


class WritingToolApp(QApplication):
    """
    The main application class for Writing Tools.
    """

    output_ready_signal = Signal(str)
    show_message_signal = Signal(str, str)  # a signal for showing message boxes
    hotkey_triggered_signal = Signal()
    followup_response_signal = Signal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing WritingToolApp")

        try:
            self._logger.debug("Setting up core attributes...")
            self._setup_core_attributes()

            self._logger.debug("Setting up signals...")
            self._setup_signals()

            self._logger.debug("Setting up settings...")
            self._setup_settings()

            self._logger.debug("Setting up UI components...")
            self._setup_ui_components()

            self._logger.debug("Setting up hotkey system...")

            self._logger.debug("Setting up AI providers...")
            self._setup_ai_providers()

            self._logger.debug("Setting up spam protection...")

            # Initialize app based on configuration state
            self._logger.debug("Checking provider configuration...")
            if not self.settings_manager.has_providers_configured():
                self._handle_first_launch()
            else:
                self._handle_normal_launch()

        except Exception as e:
            self._logger.error(f"Critical error during WritingToolApp initialization: {e}")
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

    def _setup_signals(self) -> None:
        """Connect application signals to their handlers."""
        self.output_ready_signal.connect(self.text_processor.replace_text)
        self.show_message_signal.connect(self.show_message_box)
        # Connecter les signaux du text_processor
        self.text_processor.show_message_signal.connect(self.show_message_box)
        self.hotkey_triggered_signal.connect(self.hotkey_manager.on_hotkey_pressed)

    def _setup_settings(self) -> None:
        """Initialize settings manager and load configuration."""
        mode = self._detect_running_mode()
        self._logger.debug(f"Running mode: {mode}")
        self.settings_manager = SettingsManager(mode=mode)

    def _setup_ui_components(self) -> None:
        """Initialize UI component references."""
        self.onboarding_window = None
        self.tray_icon = None
        self.settings_window = None
        self.non_editable_modal = None
        self.theme_manager = ThemeManager(self)
        self.config_manager = ConfigManager(self)
        self.language_manager = LanguageManager(self)
        self.styles = self.theme_manager.get_styles()

    def _setup_ai_providers(self) -> None:
        """Initialize available AI providers."""
        provider_classes = [
            ("Gemini", GeminiProvider),
            ("Ollama", OllamaProvider),
            ("Anthropic", AnthropicProvider),
            ("Mistral", MistralProvider),
            ("OpenAICompatible", OpenAICompatibleProvider),
        ]

        self.providers: list[AIProvider] = []

        failed_providers = []
        for name, provider_class in provider_classes:
            try:
                provider = provider_class(self)
                self.providers.append(provider)
            except BaseException as e:
                self._logger.error(f"Failed to create {name}Provider: {e}")
                failed_providers.append(name)
                import traceback

                self._logger.error(f"Traceback: {traceback.format_exc()}")
                raise

        if failed_providers:
            self._logger.warning(f"Failed to create providers: {failed_providers}")
        else:
            self._logger.debug(f"All {len(self.providers)} providers initialized successfully")

    def _handle_first_launch(self) -> None:
        """Handle first-time application launch."""
        self._logger.debug("First launch detected (no providers configured), showing onboarding")
        self.ui_manager.show_onboarding()

    def _handle_normal_launch(self) -> None:
        """Handle normal application launch with configured providers."""
        self._logger.debug("Providers configured, setting up hotkey and tray icon")

        try:
            self._initialize_ai_provider()
            self._setup_user_interface()
            self.language_manager.change_language(self.settings_manager.language or "en")
            self._initialize_update_checker()
        except Exception as e:
            self._handle_initialization_error(e)

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
        self._sync_autostart_settings()
        self._create_tray_icon_with_startup_delay()
        self.hotkey_manager.register_hotkey()

    def _create_tray_icon_with_startup_delay(self) -> None:
        """
        Create tray icon with a delay if we're likely starting at boot.
        This helps with Windows startup timing issues.
        """
        # Check if we might be starting at boot
        is_frozen = getattr(sys, "frozen", False)
        startup_delay_needed = (
            len(QApplication.topLevelWidgets()) == 0
            or getattr(self.settings_manager, "start_on_boot", False)
            or is_frozen  # Frozen builds (exe) are more likely to be autostart
        )

        if startup_delay_needed:
            # Longer delay for Windows startup - systray needs more time to be ready
            delay = 5000 if is_frozen else 2000  # 5s for exe, 2s for dev
            self._logger.debug(
                f"Startup delay detected - waiting {delay / 1000}s for system tray to be ready"
            )
            self._logger.debug(
                f"Detected potential startup scenario, delaying tray icon creation by {delay}ms"
            )
            QtCore.QTimer.singleShot(delay, self.systray_manager.create_tray_icon)
        else:
            self.systray_manager.create_tray_icon()

    def _sync_autostart_settings(self) -> None:
        """Synchronize autostart settings between registry and configuration."""
        try:
            AutostartManager.sync_with_settings(self.settings_manager)
        except Exception as e:
            self._logger.warning(f"Could not sync autostart settings: {e}")

    def _initialize_update_checker(self) -> None:
        """Initialize the update checker system."""
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()

    def _handle_initialization_error(self, error: Exception) -> None:
        """Handle errors during application initialization."""
        self._logger.exception(f"Error during app initialization: {error}")
        self._logger.exception("Falling back to onboarding")
        import traceback

        self._logger.debug(f"Full traceback: {traceback.format_exc()}")
        self.ui_manager.show_onboarding()

    # ============================================================================
    # CONFIGURATION AND SETUP METHODS
    # ============================================================================

    def _detect_running_mode(self) -> str:
        """
        Detect the operating mode based on the environment.

        Returns:
            str: "dev", "build-dev", or "build-final"
        """

        base_dir = Path(sys.executable).parent

        # dev
        if not getattr(sys, "frozen", False):
            self._logger.debug("Detected dev mode")
            return "dev"

        # build-dev
        elif base_dir.name == "dev":
            self._logger.debug("Detected build-dev mode")
            return "build-dev"

        # build-final
        else:
            self._logger.debug("Detected build-final mode")
            return "build-final"

    # Another way to detect mode
    # import inspect

    # stack = inspect.stack()
    # for frame_info in stack:
    #     filename = frame_info.filename

    #     if (
    #         "build_dev.py" in filename
    #         or "build_final.py" in filename
    #         or "PyInstaller" in filename
    #     ): build...

    def retranslate_ui(self) -> None:
        """Retranslate the user interface elements."""
        self.systray_manager.update_tray_menu()

    # ============================================================================
    # HOTKEY AND INPUT HANDLING METHODS
    # ============================================================================

    def on_onboarding_closed(self) -> None:
        """
        Handle onboarding window being closed.
        Instead of exiting, continue with normal app initialization.
        """
        self._logger.debug("Onboarding window closed, continuing with app initialization")
        self.onboarding_window = None
        # Initialize the current provider with default settings
        self.ai_processor.set_current_provider()

        # Load provider-specific config from system settings
        if self.ai_processor.current_provider:
            provider_config = self.ai_processor.get_provider_config(self.settings_manager.provider)
            self.ai_processor.current_provider.load_config(provider_config)

        self._sync_autostart_settings()
        self._create_tray_icon_with_startup_delay()
        self.hotkey_manager.register_hotkey()

        # Set language from system settings
        self.language_manager.change_language(self.settings_manager.language or "en")

        # Initialize update checker
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()

    def get_current_model(self, provider_name: str) -> str:
        provider = self.settings_manager.providers.get(provider_name, {})
        return provider.get("api_model", "")

    # ============================================================================
    # USER INTERFACE METHODS
    # ============================================================================

    @Slot(str, str)
    def show_message_box(self, title: str, message: str) -> None:
        """
        Show a message box with the given title and message.
        Delegates to the UI manager.
        """
        self.ui_manager.show_message_box(title, message)

    # ============================================================================
    # APPLICATION LIFECYCLE METHODS
    # ============================================================================

    def exit_app(self) -> None:
        """
        Exit the application.
        """
        self.hotkey_manager.cleanup()
        self._logger.debug("Restoring default SIGINT handler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._logger.debug("Exiting application")
        self.quit()
