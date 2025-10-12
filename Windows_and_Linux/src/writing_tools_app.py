"""
WritingToolsApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

from __future__ import annotations

import gettext
import logging
import os
from typing import TYPE_CHECKING

from pynput import keyboard as keyboard
from PySide6.QtWidgets import QApplication

from .core.ai_processor import AIProcessor
from .core.clipboard_manager import ClipboardManager
from .core.hotkey_manager import HotkeyManager
from .core.image_processor import ImageProcessor
from .core.input_manager import InputManager
from .core.lifecycle_manager import LifecycleManager
from .core.popup_manager import PopupManager
from .core.settings_manager import SettingsManager
from .core.setup.core_attributes import setup_core_attributes
from .core.setup.provider import initialize_ai_provider
from .core.setup.ui_initialization import setup_ui_components, setup_user_interface
from .core.text_processor import TextProcessor
from .core.ui_manager import UIManager
from .core.update_manager import UpdateManager
from .systray import SystrayManager
from .ui.response_window import ResponseWindow

if TYPE_CHECKING:
    from .core.ai_processor import AIProcessor
    from .core.clipboard_manager import ClipboardManager
    from .core.hotkey_manager import HotkeyManager
    from .core.image_processor import ImageProcessor
    from .core.input_manager import InputManager
    from .core.language_manager import LanguageManager
    from .core.lifecycle_manager import LifecycleManager
    from .core.popup_manager import PopupManager
    from .core.text_processor import TextProcessor
    from .core.theme_manager import ThemeManager
    from .core.ui_manager import UIManager
    from .core.update_manager import UpdateManager
    from .systray import SystrayManager
    from .ui.response_window import ResponseWindow

os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.mime.warning=false;qt.qpa.mime.debug=false;qt.qpa.mime.info=false"  # Disable QMimeDatabase warnings
)

_ = gettext.gettext


class WritingToolsApp(QApplication):
    """
    The main application class for Writing Tools.
    """

    # Core attributes (set in setup_core_attributes)
    current_response_window: ResponseWindow | None = None
    ai_processor: AIProcessor
    text_processor: TextProcessor
    hotkey_manager: HotkeyManager
    systray_manager: SystrayManager
    image_processor: ImageProcessor
    clipboard_manager: ClipboardManager
    input_manager: InputManager
    popup_manager: PopupManager
    ui_manager: UIManager
    lifecycle_manager: LifecycleManager
    update_manager: UpdateManager

    # UI components (set in setup_ui_components)
    language_manager: LanguageManager
    theme_manager: ThemeManager
    tray_icon: object | None = None
    non_editable_modal: object | None = None
    styles: dict # updated from theme_manager

    def __init__(self, argv: list[str]):
        super().__init__(argv)
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing WritingToolsApp")

        try:
            self._logger.debug("Setting up core attributes...")
            setup_core_attributes(self)

            self._logger.debug("Setting up settings...")
            self._setup_settings()

            self._logger.debug("Setting up UI components...")
            setup_ui_components(self)

            # Initialize app based on configuration state
            self._logger.debug("Initializing app with normal launch")
            self._handle_normal_launch()

        except Exception as e:
            self._logger.error(f"Critical error during WritingToolsApp initialization: {e}")
            import traceback

            self._logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _setup_settings(self) -> None:
        """Initialize settings manager and load configuration."""
        mode: str = self.lifecycle_manager._detect_running_mode()
        self._logger.debug(f"Running mode: {mode}")
        self.settings_manager = SettingsManager(mode=mode)

    def _handle_normal_launch(self) -> None:
        """Handle normal application launch with configured providers."""
        self._logger.debug("Providers configured, setting up hotkey and tray icon")

        try:
            initialize_ai_provider(self)
            setup_user_interface(self)
            self.language_manager.set_language(self.settings_manager.language)
            self.update_manager.check_updates_async()
        except Exception as error:
            self._logger.exception(f"Error during app initialization: {error}")
            import traceback

            self._logger.debug(f"Full traceback: {traceback.format_exc()}")
