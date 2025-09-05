"""
WritingToolApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

import base64
import gettext
import logging
import os
import signal
import sys
import tempfile
import threading
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Any, Optional

from pynput import keyboard as keyboard

os.environ["QT_LOGGING_RULES"] = (
    "qt.qpa.mime.warning=false;qt.qpa.mime.debug=false;qt.qpa.mime.info=false"  # Disable QMimeDatabase warnings
)
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QLocale, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

import ui.AboutWindow
import ui.CustomPopupWindow
import ui.HelpWindow
import ui.NonEditableModal
import ui.OnboardingWindow
import ui.ResponseWindow
import ui.SettingsWindow
from config.interfaces import ActionConfig
from config.settings import SettingsManager
from ui.ResponseWindow import ResponseWindow
from ui.systray import SystrayManager
from ui.ui_utils import get_icon_path
from update_checker import UpdateChecker

if TYPE_CHECKING:
    from aiprovider import AIProvider
    from ui.ResponseWindow import ResponseWindow


from aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
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
    theme_changed_signal = Signal(str)  # signal for theme changes from systray

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
            self._setup_hotkey_system()

            self._logger.debug("Setting up AI providers...")
            self._setup_ai_providers()

            self._logger.debug("Setting up spam protection...")
            self._setup_spam_protection()

            # Initialize app based on configuration state
            self._logger.debug("Checking provider configuration...")
            if not self.settings_manager.has_providers_configured():
                self._logger.debug("No providers configured, handling first launch...")
                self._handle_first_launch()
            else:
                self._logger.debug("Providers configured, handling normal launch...")
                self._handle_normal_launch()

        except Exception as e:
            self._logger.error(f"Critical error during WritingToolApp initialization: {e}")
            import traceback

            self._logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _setup_core_attributes(self) -> None:
        """Initialize core application attributes."""
        self.current_response_window: ResponseWindow | None = None
        self.current_provider: AIProvider | None = None
        self.output_queue = ""
        self.original_selection: str | None = None
        self.image: QImage | None = None
        self.has_image = bool(self.image is not None)
        self.systray_manager = SystrayManager(self)

    def _setup_signals(self) -> None:
        """Connect application signals to their handlers."""
        self.output_ready_signal.connect(self.replace_text)
        self.show_message_signal.connect(self.show_message_box)
        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)
        self.theme_changed_signal.connect(self.on_theme_changed)

    @Slot(str)
    def on_theme_changed(self, new_mode: str) -> None:
        """Handle theme changes from ThemeManager."""
        if self.systray_manager.tray_menu:
            self.systray_manager.apply_tray_menu_styles(self.systray_manager.tray_menu)

    def _setup_settings(self) -> None:
        """Initialize settings manager and load configuration."""
        mode = self._detect_mode()
        self._logger.debug(f"Running mode: {mode}")
        self.settings_manager = SettingsManager(mode=mode)
        self.load_settings()

    def _setup_ui_components(self) -> None:
        """Initialize UI component references."""
        self.onboarding_window = None
        self.popup_window = None
        self.tray_icon = None
        self.settings_window = None
        self.about_window = None
        self.help_window = None
        self.non_editable_modal = None

    def _setup_hotkey_system(self) -> None:
        """Initialize hotkey and keyboard listener system."""
        self.registered_hotkey = None
        self.hotkey_listener = None
        self.ctrl_c_timer = None
        self.setup_ctrl_c_listener()

    def _setup_ai_providers(self) -> None:
        """Initialize available AI providers."""
        self._ = gettext.gettext
        self.providers = [
            GeminiProvider(self),
            OpenAICompatibleProvider(self),
            OllamaProvider(self),
            AnthropicProvider(self),
            MistralProvider(self),
        ]

    def _setup_spam_protection(self) -> None:
        """Initialize hotkey spam protection system."""
        self.recent_triggers = []
        self.TRIGGER_WINDOW = 1.5  # Time window in seconds
        self.MAX_TRIGGERS = 3  # Max allowed triggers in window

    def _handle_first_launch(self) -> None:
        """Handle first-time application launch."""
        self._logger.debug("First launch detected (no providers configured), showing onboarding")
        self.show_onboarding()

    def _handle_normal_launch(self) -> None:
        """Handle normal application launch with configured providers."""
        self._logger.debug("Providers configured, setting up hotkey and tray icon")

        try:
            self._initialize_ai_provider()
            self._setup_user_interface()
            self._setup_language()
            self._initialize_update_checker()
        except Exception as e:
            self._handle_initialization_error(e)

    def _initialize_ai_provider(self) -> None:
        """Initialize and configure the current AI provider."""
        provider_internal_name = self.settings_manager.provider or "gemini"
        self._logger.debug(f"Selected provider: {provider_internal_name}")

        self.current_provider = next(
            (
                provider
                for provider in self.providers
                if provider.internal_name == provider_internal_name
            ),
            None,
        )

        if not self.current_provider:
            self._logger.warning(
                f"Provider {provider_internal_name} not found. Using default provider."
            )
            self.current_provider = self.providers[0]

        if self.current_provider:
            self._logger.debug(f"Current provider: {self.current_provider.provider_name}")
            provider_config = self._get_provider_config(provider_internal_name)
            self._logger.debug(f"Provider config: {provider_config}")
            self.current_provider.load_config(provider_config)
            self._logger.debug("Provider config loaded successfully")

    def _setup_user_interface(self) -> None:
        """Setup user interface components."""
        self._sync_autostart_settings()
        self._create_tray_icon_with_startup_delay()
        self.register_hotkey()

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
            from ui.AutostartManager import AutostartManager

            AutostartManager.sync_with_settings(self.settings_manager)
        except Exception as e:
            self._logger.warning(f"Could not sync autostart settings: {e}")

    def _setup_language(self) -> None:
        """Configure application language."""
        lang = self.settings_manager.language or "en"
        self.change_language(lang if lang != "en" else "en")

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
        self.show_onboarding()

    # ============================================================================
    # CONFIGURATION AND SETUP METHODS
    # ============================================================================

    def _detect_mode(self) -> str:
        """
        Detect the operating mode based on the environment.

        Returns:
            str: "dev", "build-dev", or "build-final"
        """

        base_dir = Path(sys.executable).parent
        self._logger.debug(f"Base directory name in build detect_mode: {base_dir.name}")

        # dev
        if not getattr(sys, "frozen", False):
            return "dev"

        # build-dev
        elif base_dir.name == "dev":
            return "build-dev"

        # build-final
        else:
            return "build-final"

    def setup_translations(self, lang=None) -> None:
        """Setup application translations for the specified language."""
        if not lang:
            lang = QLocale.system().name().split("_")[0]

        try:
            translation = gettext.translation(
                "messages",
                localedir=os.path.join(os.path.dirname(__file__), "locales"),
                languages=[lang],
            )
        except FileNotFoundError:
            translation = gettext.NullTranslations()

        translation.install()
        self._update_translation_functions(translation)

    def _update_translation_functions(self, translation: gettext.NullTranslations) -> None:
        """Update translation functions for all UI components."""
        self._ = translation.gettext
        ui.AboutWindow._ = self._
        ui.SettingsWindow._ = self._
        ui.ResponseWindow._ = self._
        ui.OnboardingWindow._ = self._
        ui.CustomPopupWindow._ = self._
        ui.HelpWindow._ = self._

    def retranslate_ui(self) -> None:
        """Retranslate the user interface elements."""
        self.systray_manager.update_tray_menu()

    def change_language(self, lang: str) -> None:
        """Change the application language and update all UI elements."""
        self.setup_translations(lang)
        self.retranslate_ui()
        self._update_widget_translations()

    def _update_widget_translations(self) -> None:
        """Update translations for all top-level widgets."""
        for widget in QApplication.topLevelWidgets():
            if widget != self and hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()  # type: ignore

    def load_settings(self) -> None:
        """Load unified settings using the SettingsManager."""
        self.settings_manager.load_settings()
        self._logger.debug("Unified settings loaded successfully")

    def save_settings(self) -> None:
        """Save the current unified settings."""
        self.settings_manager.save()

    # ============================================================================
    # HOTKEY AND INPUT HANDLING METHODS
    # ============================================================================

    def check_trigger_spam(self) -> bool:
        """
        Check if hotkey is being triggered too frequently.
        Returns True if spam is detected (3+ times in 1.5 seconds).
        """
        current_time = time.time()
        self.recent_triggers.append(current_time)

        # Remove old triggers outside the window
        self.recent_triggers = [
            t for t in self.recent_triggers if current_time - t <= self.TRIGGER_WINDOW
        ]

        return len(self.recent_triggers) >= self.MAX_TRIGGERS

    def _get_provider_config(self, provider_name: str) -> dict:
        """
        Extract provider-specific configuration from custom_data.

        Args:
            provider_name: Name of the provider

        Returns:
            dict: Provider-specific configuration
        """

        # Default configuration based on provider type
        default_configs = {
            ("Gemini", "Gemini (Recommended)"): {
                "api_key": "",
                "model": self.settings_manager.model or "",
            },
            ("Ollama", "Ollama (Local)", "Ollama (For Experts)"): {
                "base_url": self.settings_manager.ollama_base_url or "http://localhost:11434",
                "model": "",
                "keep_alive": self.settings_manager.ollama_keep_alive or "5",
            },
            ("Mistral", "Mistral AI"): {
                "api_key": "",
                "api_model": "",
                "base_url": self.settings_manager.mistral_base_url or "https://api.mistral.ai/v1",
            },
            ("Anthropic", "Anthropic (Claude)"): {"api_key": "", "model": ""},
            ("OpenAI", "OpenAI-Compatible"): {
                "api_key": "",
                "base_url": self.settings_manager.openai_base_url or "https://api.openai.com/v1",
                "model": "",
            },
        }

        # Find the default config
        config = {}
        for provider_names, default_config in default_configs.items():
            if provider_name in provider_names:
                config = default_config.copy()
                break

        # Override with saved config
        saved_config = self.settings_manager.providers.get(provider_name, {})
        config.update(saved_config)

        return config

    def show_onboarding(self) -> None:
        """
        Show the onboarding window for first-time users.
        """
        self._logger.debug("Showing onboarding window")

        self.onboarding_window = ui.OnboardingWindow.OnboardingWindow(self)
        self.onboarding_window.close_signal.connect(self.on_onboarding_closed)
        self.onboarding_window.show()

    def on_onboarding_closed(self) -> None:
        """
        Handle onboarding window being closed.
        Instead of exiting, continue with normal app initialization.
        """
        self._logger.debug("Onboarding window closed, continuing with app initialization")

        # Initialize the current provider with default settings
        provider_name = self.settings_manager.provider or "gemini"

        if not provider_name.strip():
            # Default to Gemini if no provider is set
            provider_name = "gemini"
            self.settings_manager.provider = provider_name

        self.current_provider = next(
            (provider for provider in self.providers if provider.internal_name == provider_name),
            self.providers[0],  # Default to first provider
        )

        # Load provider-specific config from system settings
        if self.current_provider:
            provider_config = self._get_provider_config(provider_name)
            self.current_provider.load_config(provider_config)

        self._sync_autostart_settings()
        self._create_tray_icon_with_startup_delay()
        self.register_hotkey()

        # Set language from system settings
        lang = self.settings_manager.language or "en"
        self.change_language(lang if lang != "en" else "en")

        # Initialize update checker
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()

    # ============================================================================
    # HOTKEY MANAGEMENT METHODS
    # ============================================================================

    def start_hotkey_listener(self) -> None:
        """
        Create listener for hotkeys on Linux/Mac.
        """
        orig_shortcut = self.settings_manager.hotkey or "ctrl+space"

        # Parse the shortcut string, for example ctrl+alt+h -> <ctrl>+<alt>+<h>. Space are removed.
        shortcut = "+".join(
            [
                f"{t}" if len(t) <= 1 else f"<{t}>"
                for t in [part.strip() for part in orig_shortcut.split("+")]
            ],
        )
        self._logger.debug(f"Registering global hotkey for shortcut: {shortcut}")

        try:
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()
                self.hotkey_listener = None

            def on_activate():
                if self.systray_manager.paused:
                    return
                self._logger.debug("triggered hotkey")
                self.hotkey_triggered_signal.emit()  # Emit the signal when hotkey is pressed

            # Define the hotkey combination
            hotkey = keyboard.HotKey(keyboard.HotKey.parse(shortcut), on_activate)
            self.registered_hotkey = orig_shortcut

            # Helper function to standardize key event
            def for_canonical(f):
                return lambda k: f(
                    self.hotkey_listener.canonical(k)
                    if k is not None and self.hotkey_listener is not None
                    else k
                )

            # Create a listener and store it as an attribute to stop it later
            self.hotkey_listener = keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release),
            )

            # Start the listener
            self.hotkey_listener.start()
        except Exception as e:
            self._logger.error(f"Failed to register hotkey: {e}")

    def register_hotkey(self) -> None:
        """
        Register the global hotkey for activating Writing Tools.
        """
        self._logger.debug("Registering hotkey")
        self.start_hotkey_listener()
        self._logger.debug("Hotkey registered")

    def on_hotkey_pressed(self) -> None:
        """
        Handle the hotkey press event.
        """
        self._logger.debug("Hotkey pressed ==============================")

        # Check for spam triggers
        if self.check_trigger_spam():
            self._logger.warning("Hotkey spam detected - quitting application")
            self.exit_app()
            return

        # Close existing non-editable modal if open
        if hasattr(self, "non_editable_modal") and self.non_editable_modal is not None:
            self._logger.debug("Closing existing non-editable modal")
            self.non_editable_modal.close()
            self.non_editable_modal = None

        # Close existing popup window if open
        if hasattr(self, "popup_window") and self.popup_window is not None:
            self._logger.debug("Closing existing popup window")
            self.popup_window.close()
            self.popup_window = None

        # Close existing response window if open
        if hasattr(self, "current_response_window") and self.current_response_window is not None:
            self._logger.debug("Closing existing response window")
            self.current_response_window.close()
            self.current_response_window = None

        # Original hotkey handling continues...
        if self.current_provider:
            self._logger.debug("Cancelling current provider's request")
            self.current_provider.cancel()
            self.output_queue = ""

        # noinspection PyTypeChecker
        QtCore.QMetaObject.invokeMethod(
            self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection
        )

    @Slot()
    def _show_popup(self) -> None:
        """
        Show the popup window when the hotkey is pressed.
        """
        self._logger.debug("🪟\u00a0 Showing popup window")

        # Check for image first
        if self.image is None:
            self.image = self.get_clipboard_image()

        # Update has_image flag based on actual image presence
        self.has_image = bool(self.image is not None)

        if self.image is None:
            selected_text = self.original_selection = self.get_selected_text(sleep_duration=0.1)
            self._logger.debug(f'Selected text: "{selected_text}"')
            self._logger.debug(" 🖼️\u00a0 No image found, processing text selection")
        else:
            selected_text = None
            self._logger.debug(
                f" 🖼️\u00a0 Image found in clipboard - size: {self.image.width()}x{self.image.height()}"
            )
            self._logger.debug("Image found in clipboard, skipping text capture")

        try:
            self._logger.debug("🆕🪟\u00a0 Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(
                self, selected_text, self.image
            )

            # Position the popup window near the cursor
            self._position_popup_near_cursor()
        except Exception as e:
            self._logger.error(f"Error showing popup window: {e}", exc_info=True)

    def _position_popup_near_cursor(self) -> None:
        """
        Position the popup window near the cursor, handling screen boundaries and visibility.
        """
        if not self.popup_window:
            self._logger.error("Popup window not initialized")
            return

        # Set the window icon
        icon_path = get_icon_path(
            self,
            "app_icon",
            with_theme=False,
        )
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(icon_path.as_posix()))

        # Get the screen containing the cursor
        cursor_pos = QCursor.pos()
        screen = QGuiApplication.screenAt(cursor_pos)
        if screen is None:
            screen = QGuiApplication.primaryScreen()
        screen_geometry = screen.geometry()
        self._logger.debug(f"Cursor is on screen: {screen.name()}")
        self._logger.debug(f"Screen geometry: {screen_geometry}")

        # Show the popup to get its size
        self.popup_window.show()
        self.popup_window.adjustSize()
        # Ensure the popup it's focused, even on lower-end machines
        self.popup_window.activateWindow()
        if self.popup_window.custom_input:
            QtCore.QTimer.singleShot(100, self.popup_window.custom_input.setFocus)

        popup_width = self.popup_window.width()
        popup_height = self.popup_window.height()

        # Calculate position
        x = cursor_pos.x()
        y = cursor_pos.y() + 20  # 20 pixels below cursor

        # Adjust if the popup would go off the right edge of the screen
        if x + popup_width > screen_geometry.right():
            x = screen_geometry.right() - popup_width

        # Adjust if the popup would go off the bottom edge of the screen
        if y + popup_height > screen_geometry.bottom():
            y = cursor_pos.y() - popup_height - 10  # 10 pixels above cursor

        self.popup_window.move(x, y)
        self._logger.debug(f"Popup window moved to position: ({x}, {y})")

    def get_clipboard_image(self) -> QImage | None:
        """
        Get the image data currently stored in the clipboard from screenshots or image copy operations.
        Enhanced error handling and format support.
        """
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            if not mime_data.hasImage():
                self._logger.debug("No image found in clipboard")
                return None

            # Check available formats for debugging
            available_formats = mime_data.formats()
            self._logger.debug(f"Available clipboard formats: {available_formats}")

            image_data = mime_data.imageData()

            if isinstance(image_data, QImage):
                self._logger.debug("QImage found in clipboard")
                if image_data.isNull():
                    self._logger.warning("QImage is null")
                    return None
                clipboard.clear()
                self._logger.debug("Clipboard cleared after image retrieval")
                return image_data

            elif hasattr(image_data, "toImage"):  # QPixmap
                self._logger.debug("Converting QPixmap to QImage")
                qimage = image_data.toImage()
                if qimage.isNull():
                    self._logger.warning("Converted QImage is null")
                    return None
                self._logger.debug(f"QPixmap converted: {qimage.width()}x{qimage.height()}")
                clipboard.clear()
                self._logger.debug("Clipboard cleared after image retrieval")
                return qimage

            else:
                self._logger.warning(f"Unknown image type: {type(image_data)}")
                return None

        except Exception as e:
            self._logger.error(f"Error processing clipboard image data: {e}")
            return None

    def get_selected_text(
        self, sleep_duration: float = 0.2, max_retries: int = 3, retry_delay: float = 0.1
    ) -> str:
        """
        Get the currently selected text from any application by simulating Ctrl+C.
        """
        self._logger.debug("Getting selected text")
        clipboard = QApplication.clipboard()
        clipboard_backup = clipboard.text()
        self._logger.debug(
            f"Clipboard backed up: {clipboard_backup[:30] if clipboard_backup else 'Empty'} ..."
        )

        # Clear the clipboard
        clipboard.clear()
        selected_text = ""

        # Simulate Ctrl+C to copy selected text
        self._logger.debug("Simulating Ctrl+C")
        kbrd = keyboard.Controller()

        def press_ctrl_c():
            with kbrd.pressed(keyboard.Key.ctrl):
                kbrd.press("c")
                kbrd.release("c")

        # Retry mechanism for Ctrl+C
        for attempt in range(max_retries):
            self._logger.debug(f"Attempting Ctrl+C - attempt {attempt + 1}/{max_retries}")

            # Clear clipboard before each attempt to detect success
            clipboard.clear()

            # Simulate Ctrl+C
            press_ctrl_c()

            # Wait for clipboard to update
            time.sleep(sleep_duration)

            # Check if clipboard has new content
            current_clipboard = clipboard.text()

            if current_clipboard:  # Success - clipboard has content
                # Check if it's a file path (from QuickLook/file selection)
                if self._is_file_path(current_clipboard):
                    self._logger.debug(
                        f"Detected file path, treating as no selection: {current_clipboard}"
                    )
                    selected_text = ""
                    break
                else:
                    selected_text = current_clipboard
                    self._logger.debug(
                        f"Ctrl+C successful on attempt {attempt + 1}: {selected_text[:30] if selected_text else 'Empty'} ..."
                    )
                    break
            else:
                # Failed attempt
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    self._logger.debug(
                        f"Ctrl+C failed on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    self._logger.warning(
                        f"Ctrl+C failed after {max_retries} attempts - no text selected or clipboard access failed"
                    )

        # Clean the selected text
        if selected_text:
            selected_text = selected_text
            self._logger.debug(f"Text retrieved and cleaned: {len(selected_text)} characters")
        else:
            selected_text = ""
            self._logger.debug("No text was retrieved")

        # Restore the clipboard
        clipboard.setText(clipboard_backup if clipboard_backup else "")
        self._logger.debug("Clipboard restored")

        return selected_text

    def _is_file_path(self, text: str) -> bool:
        """
        Check if the text is a file path (from file/icon selection).

        Args:
            text: The text to check

        Returns:
            bool: True if it's a file path, False if it's regular text
        """
        if not text or not text.strip():
            return False

        text = text.strip()

        # Check for file:// URLs (what we saw in the logs)
        if text.startswith("file:///"):
            return True

        # Check for Windows file paths (C:\, D:\, etc.)
        if len(text) > 2 and text[1:3] == ":\\":
            return True

        # Check for UNC paths (\\server\share)
        if text.startswith("\\\\"):
            return True

        # Check for Unix-style absolute paths
        if text.startswith("/") and "/" in text[1:]:
            return True

        return False

    def process_option(
        self,
        option: str,
        selected_text: str | None,
        force_chat: bool = False,
        custom_change: str | None = None,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Process the selected writing option.

        Args:
            option: The action option to process
            selected_text: The text selected by the user
            force_chat: If True, force response to open in ResponseWindow (chat mode)
            custom_change: Optional custom instruction text entered by the user in the input field
            image: Optional image copied from the clipboard
        """
        self._logger.debug(f"Processing option: {option}")

        if self.current_provider is not None and not self.current_provider.validate_connection():
            return

        has_image = image is not None
        is_custom_option = option == "Custom"
        has_selected_text = bool(selected_text and selected_text.strip() != "")
        action_config = self.settings_manager.actions.get(option, {})

        should_setup_response_window = (
            (is_custom_option and not has_selected_text)
            or (is_custom_option and has_image)
            or action_config.get("open_in_window", False)
            or (force_chat and has_selected_text)  # Force Chat with text
        )

        self._logger.debug(f"should_setup_response_window: {should_setup_response_window}")
        self._logger.debug(f"has_image: {has_image}")

        if should_setup_response_window:
            self._setup_response_window(option, selected_text, image)
        elif hasattr(self, "current_response_window"):
            delattr(self, "current_response_window")

        # Store force_chat state for the thread
        self._current_force_chat = force_chat

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, image, custom_change),
            daemon=True,
        ).start()

    def _setup_response_window(
        self, option: str, selected_text: str | None, image: QImage | None
    ) -> None:
        """
        Set up the response window for the selected writing option.
        """
        is_custom = option == "Custom"
        window_title = "Chat" if not is_custom else option
        self.current_response_window = self.show_response_window(window_title, selected_text)

        # Handle chat history based on content type
        if image is not None:
            # Image mode - no selected text
            self.current_response_window.chat_history = [
                {"role": "user", "content": f"Image analysis request: {option.lower()}"}
            ]
        elif is_custom and not selected_text:  # needed ???
            # Custom mode without text
            self.current_response_window.chat_history = [
                {
                    "role": "user",
                    "content": f"Original text to {option.lower()}:\n\n{selected_text}",
                }
            ]
        else:
            # Text mode
            self.current_response_window.chat_history = (
                []
                if not is_custom
                else [
                    {
                        "role": "user",
                        "content": f"Original text to {option.lower()}:\n\n{selected_text}",
                    },
                ]
            )

        self._logger.debug(f"💬📜 Chat history: {self.current_response_window.chat_history}")

    # ============================================================================
    # AI PROCESSING METHODS
    # ============================================================================

    def process_option_thread(
        self,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None = None,
        custom_change: str | None = None,
    ) -> None:
        """
        Thread function to process the selected writing option using the AI model.
        Enhanced to support image processing.

        Args:
            option: The selected writing option (e.g., "Summary", "Custom", "Proofread")
            selected_text: The text selected by the user
            image: Optional image copied from the clipboard
            custom_change: Optional custom change description for Custom option
        """
        self._logger.debug(f"Starting processing thread for option: {option}")

        try:
            prompt_data = self._prepare_prompt_data(option, selected_text, image, custom_change)
            if not prompt_data:
                return

            self.output_queue = ""
            should_open_window = self._should_display_in_window(
                option, selected_text, prompt_data["action_config"], image is not None
            )

            if should_open_window:
                self._process_window_response(option, selected_text, custom_change, prompt_data)
            else:
                self._process_direct_replacement(prompt_data)

            # Clean up image resources
            self.clean_image()

        except Exception as e:
            self._handle_processing_error(e)

    def clean_image(self) -> None:
        if hasattr(self, "image") and self.image:
            self.image = None
        self.has_image = False

    def _prepare_prompt_data(
        self,
        option: str,
        selected_text: str,
        image: QImage | None,
        custom_change: str | None,
    ) -> dict | None:
        """
        Prepare prompt data for AI processing including image support.

        Args:
            option: The selected writing option (e.g., "Summary", "Custom", "Proofread")
            selected_text: The text selected by the user
            image: The image copied from the clipboard
            custom_change: The custom instruction text entered by the user in the input field

        Returns:
            dict: Contains prompt, system_instruction, action_config, and image_data, or None if invalid
        """
        has_selected_text = selected_text and selected_text.strip() != ""
        is_custom_option = option == "Custom"
        has_image = image is not None

        if not has_selected_text and not has_image:
            return self._handle_no_text_selected(is_custom_option, custom_change)
        else:
            return self._handle_text_or_image_selected(
                option, selected_text, image, is_custom_option, custom_change
            )

    def _handle_no_text_selected(
        self, is_custom_option: bool, custom_change: str | None
    ) -> dict | None:
        """Handle case where no text is selected."""
        if custom_change is None:
            custom_change = ""

        if is_custom_option:
            return {
                "prompt": custom_change,
                "system_instruction": "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                "action_config": {},
            }
        else:
            self.show_message_signal.emit("Error", "Please select text to use this option.")
            return None

    def _handle_text_or_image_selected(
        self,
        option: str,
        selected_text: str,
        image: QImage | None,
        is_custom_option: bool,
        custom_change: str | None,
    ) -> dict | None:
        """Handle case where text is selected or image is available."""
        action_config: ActionConfig = self.settings_manager.actions.get(option, {})

        # For image analysis, use a specialized system instruction
        if image is not None:
            if is_custom_option:
                system_instruction = (
                    "You are a helpful AI assistant specialized in image analysis. "
                    "Analyze the provided image and respond to the user's specific request."
                    "If it is about a translation of the text in the image, please provide the translation and nothing else."
                    "Be detailed, accurate, and helpful in your analysis."
                    "Use clear, well-structured responses with markdown formatting when appropriate."
                )
                prompt = custom_change or "Please analyze this image and describe what you see."
            else:
                if not action_config:
                    self._logger.error(f"Action not found: {option}")
                    return None

                # For pre-defined actions with images, adapt the instruction
                system_instruction = action_config.get("instruction", "") + (
                    " Analyze the provided image in the context of this request."
                )
                prompt = action_config.get("prefix", "") + (custom_change or "")
        else:
            # Text-based processing
            if not action_config:
                self._logger.error(f"Action not found: {option}")
                return None

            prompt_prefix = action_config.get("prefix", "")
            system_instruction = action_config.get("instruction", "")

            if is_custom_option:
                prompt = (
                    f"{prompt_prefix}Described change: {custom_change}\nText: {selected_text}\n"
                )
            else:
                prompt = f"{prompt_prefix}{selected_text}\n"

        # Convert QImage to base64 if present
        image_data = None
        if image:
            self._logger.debug(
                f" 🖼️\u00a0 Processing image in _handle_text_or_image_selected - image size: {image.width()}x{image.height()}"
            )
            image_data = self._qimage_to_base64(image, use_physical_file=False)
            if image_data:
                self._logger.debug(
                    f" 🖼️\u00a0 Image converted to base64 successfully - length: {len(image_data)}"
                )
            else:
                self._logger.error(" 🖼️\u00a0 Failed to convert image to base64")

        return {
            "prompt": prompt,
            "system_instruction": system_instruction,
            "action_config": action_config,
            "image_data": image_data,
        }

    def _qimage_to_base64(self, image: QImage, use_physical_file: bool = True) -> str:
        """
        Convert QImage to base64 string for API transmission.

        Supports two approaches:
        1. Physical file approach (use_physical_file=True): Creates temporary file, saves QImage, reads and converts to base64
        2. Memory approach (use_physical_file=False): Direct conversion using QBuffer without file I/O

        Args:
            image: QImage to convert
            use_physical_file: Whether to use temporary file approach. Defaults to False for memory-based conversion.

        Returns:
            str: Base64 encoded image data
        """
        try:
            if use_physical_file:
                # Original approach using temporary file
                return self._qimage_to_base64_with_file(image)
            else:
                # Alternative approach using memory buffer
                return self._qimage_to_base64_memory(image)

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64: {e}")
            return ""

    def _qimage_to_base64_with_file(self, image: QImage) -> str:
        """
        Convert QImage to base64 using temporary file approach (legacy method).

        Args:
            image: QImage to convert

        Returns:
            str: Base64 encoded image data
        """
        try:
            # Create temporary file path
            temp_path = self._get_temp_image_path()
            self._logger.debug(
                f" 🖼️\u00a0 Converting QImage to base64 with file - temp path: {temp_path}"
            )

            # Save QImage to temporary file (PNG format for compatibility)
            if not image.save(str(temp_path)):  # Use overload without format parameter
                self._logger.error(" 🖼️\u00a0 Failed to save QImage to temporary file")
                return ""

            self._logger.debug(f" 🖼️\u00a0 QImage saved successfully to: {temp_path}")

            # Read the temporary file and convert to base64
            try:
                with open(temp_path, "rb") as image_file:
                    image_bytes = image_file.read()
                    base64_string = base64.b64encode(image_bytes).decode("utf-8")

                self._logger.debug(
                    f" 🖼️\u00a0 Converted image to base64: {len(base64_string)} characters"
                )
                self._logger.debug(f" 🖼️\u00a0 Base64 preview: {base64_string[:100]}...")
                return base64_string

            finally:
                # Clean up temporary file
                try:
                    temp_path.unlink(missing_ok=True)
                    self._logger.debug(f" 🖼️\u00a0 Cleaned up temporary file: {temp_path}")
                except Exception as cleanup_error:
                    self._logger.warning(
                        f" 🖼️\u00a0 Failed to cleanup temporary file {temp_path}: {cleanup_error}"
                    )

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64 with file: {e}")
            return ""

    def _qimage_to_base64_memory(self, image: QImage) -> str:
        """
        Convert QImage to base64 using memory buffer approach (new method).

        Args:
            image: QImage to convert

        Returns:
            str: Base64 encoded image data
        """
        try:
            from PySide6.QtCore import QBuffer, QByteArray, QIODevice

            # Validate image
            if image.isNull():
                self._logger.error(" 🖼️\u00a0 Image is null, cannot convert")
                return ""

            self._logger.debug(
                f" 🖼️\u00a0 Image size: {image.width()}x{image.height()}, format: {image.format()}"
            )

            # Create byte array and buffer
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)

            if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
                self._logger.error(" 🖼️\u00a0 Failed to open buffer for writing")
                return ""

            # Save QImage to buffer in PNG format
            # Try to save directly first, then fallback to conversion
            save_success = image.save(buffer, "PNG")  # type: ignore
            if not save_success:
                # Fallback: convert to RGB32 format
                rgb_image = image.convertToFormat(QtGui.QImage.Format.Format_RGB32)
                buffer.close()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                save_success = rgb_image.save(buffer, "PNG")  # type: ignore
            buffer.close()

            if not save_success:
                self._logger.error(" 🖼️\u00a0 Failed to save QImage to memory buffer")
                return ""

            # Get the size of saved data
            image_bytes = byte_array.data()
            if not image_bytes:
                self._logger.error(" 🖼️\u00a0 No data saved to buffer")
                return ""

            self._logger.debug(f" 🖼️\u00a0 Image saved to buffer: {len(image_bytes)} bytes")

            # Convert to base64
            base64_string = base64.b64encode(image_bytes).decode("utf-8")

            self._logger.debug(
                f" 🖼️\u00a0 Converted image to base64 from memory: {len(base64_string)} characters"
            )
            return base64_string

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64 from memory: {e}", exc_info=True)
            return ""

    def _get_temp_image_path(self) -> Path:
        """
        Get appropriate temporary file path for clipboard image based on execution mode.

        Returns:
            Path: Temporary file path for clipboard image
        """
        try:
            # Determine execution mode
            mode = self._detect_mode()

            if mode == "dev":
                # Development mode: use project directory
                temp_dir = Path(__file__).parent
            elif mode in ["build-dev", "build-final"]:
                # Build mode: use system temp directory
                temp_dir = Path(tempfile.gettempdir())
            else:
                # Fallback to system temp directory
                temp_dir = Path(tempfile.gettempdir())

            # Create unique temporary file name
            temp_filename = f"writingtools_clipboard_{int(time.time() * 1000)}.png"
            temp_path = temp_dir / temp_filename

            self._logger.debug(f"Using temporary image path: {temp_path}")
            return temp_path

        except Exception as e:
            self._logger.error(f"Error creating temp image path: {e}")
            # Fallback to system temp directory
            return (
                Path(tempfile.gettempdir())
                / f"writingtools_clipboard_{int(time.time() * 1000)}.png"
            )

    def _should_display_in_window(
        self, option: str, selected_text: str, action_config: ActionConfig, has_image: bool
    ) -> bool:
        """Determine if response should be displayed in a window."""
        is_custom_option = option == "Custom"
        has_selected_text = selected_text and selected_text.strip() != "" or False
        force_chat = getattr(self, "_current_force_chat", False)

        return (
            (
                is_custom_option and not has_selected_text
            )  # Custom without text (includes image case)
            or (has_selected_text and action_config.get("open_in_window", False))  # Window mode
            or (has_image and action_config.get("open_in_window", False))  # Window mode
            or (force_chat and has_selected_text)  # Force Chat with text
        )

    def _process_window_response(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        prompt_data: dict,
    ) -> None:
        """Process AI response for window display with image support."""
        if not self.current_provider:
            return

        self._logger.debug("Getting response for window display")

        # Extract image data from prompt_data
        image_data = prompt_data.get("image_data")

        if image_data:
            self._logger.debug(
                f" 🖼️\u00a0 Passing image data to provider - length: {len(image_data)}"
            )
            self._logger.debug(f" 🖼️\u00a0 Image data preview: {image_data[:100]}...")
        else:
            self._logger.debug(" 🖼️\u00a0 No image data to pass to provider")

        response = self.current_provider.get_response(
            prompt_data["system_instruction"],
            str(prompt_data["prompt"]),
            return_response=True,
            image_data=image_data,  # Pass image data to provider
        )
        self._logger.debug(f"Got response of length: {len(response) if response else 0}")

        self._update_chat_history_if_needed(option, selected_text, custom_change, image_data)
        self._update_response_window(response)

    def _update_chat_history_if_needed(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        image_data: str | None = None,
    ) -> None:
        """Update chat history for custom prompts, including image context."""
        is_custom_option = option == "Custom"
        # has_selected_text = selected_text and selected_text.strip() != ""
        has_image = image_data is not None

        if not self.current_response_window or not is_custom_option:
            return

        if has_image:
            # Image analysis request
            self.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or "Analyze this image"},
            )
        else:
            # Text-only custom request
            self.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or ""},
            )

        self._logger.debug(
            f"💬📜 Chat history updated to: {self.current_response_window.chat_history}"
        )

    def _update_response_window(self, response: str) -> None:
        """Update response window with AI response (thread-safe)."""
        if hasattr(self, "current_response_window") and self.current_response_window:
            QtCore.QMetaObject.invokeMethod(
                self.current_response_window,
                "set_text",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response),
            )
            self._logger.debug("🆕🪟\u00a0 Invoked set_text on response window")
        else:
            self._logger.warning("No current_response_window to update")

    def _process_direct_replacement(self, prompt_data: dict) -> None:
        """Process AI response for direct text replacement."""
        if not self.current_provider:
            return

        self._logger.debug("Getting response for direct replacement")
        prompt_str = str(prompt_data["prompt"])
        self.current_provider.get_response(prompt_data["system_instruction"], prompt_str)
        self._logger.debug("Response processed")

    def _handle_processing_error(self, error: Exception) -> None:
        """Handle errors during AI processing."""
        self._logger.error(f"An error occurred: {error}", exc_info=True)

        if "Resource has been exhausted" in str(error):
            self.show_message_signal.emit(
                "Error - Rate Limit Hit",
                "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
            )
        else:
            self.show_message_signal.emit("Error", f"An error occurred: {error}")

    # ============================================================================
    # USER INTERFACE METHODS
    # ============================================================================

    @Slot(str, str)
    def show_message_box(self, title: str, message: str) -> None:
        """
        Show a message box with the given title and message.
        For API errors, adds a button to open settings.
        """
        msg_box = QMessageBox(None)
        msg_box.setWindowFlags(msg_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Add standard 'OK' button
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        # For API errors, add a button to open settings
        settings_button = None
        if any(
            keyword in title.lower()
            for keyword in [
                "api",
                "key",
                "quota",
                "rate limit",
                "connection",
                "authentication",
                "vision",
                "configuration",
            ]
        ):
            settings_button = msg_box.addButton("Open Settings", QMessageBox.ButtonRole.ActionRole)

        # Show the message box
        msg_box.exec()

        # If settings button was clicked, open settings
        if settings_button and msg_box.clickedButton() == settings_button:
            self.show_settings()

    def show_response_window(self, option: str, text: str | None) -> ResponseWindow:
        """
        Show the response in a new window instead of pasting it.
        Enhanced to support image display and analysis.
        """
        response_window = ResponseWindow(self, f"{option} Result")

        # Set image and text context
        if self.has_image and self.image:
            response_window.image = self.image
            self._logger.debug("Image set in response window")
            # For image analysis, we don't need selected text
            response_window.selected_text = None
        else:
            response_window.selected_text = text  # Store the text for regeneration
            response_window.image = None

        response_window.show()
        return response_window

    @Slot(str)
    def replace_text(self, new_text: str) -> None:
        """
        Replaces the text by pasting in the LLM generated text. With "Key Points" and "Summary", invokes a window with the output instead.
        If pasting fails (non-editable page), shows the text in a modal window.
        """
        self._logger.debug(
            f"replace_text called with text length: {len(new_text) if new_text else 0}"
        )

        # Early return if no valid text
        if not new_text or not isinstance(new_text, str):
            self._logger.debug("No new text to process")
            return

        error_message = "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"
        self.output_queue += new_text
        current_output = (
            self.output_queue
        )  # no strip there the answer can be code with indentation, on several lines

        # Handle error message
        if current_output.strip() == error_message:
            self.show_message_signal.emit(
                "Error", "The text is incompatible with the requested change."
            )
            return

        # Check if we're building up to the error message (to prevent partial pasting)
        if len(current_output.strip()) <= len(error_message):
            clean_current = "".join(current_output.split())
            clean_error = "".join(error_message.split())
            if clean_current == clean_error[: len(clean_current)]:
                return

        self._logger.debug("Processing output text")

        try:
            # Handle Summary and Key Points - show in response window
            if hasattr(self, "current_response_window") and self.current_response_window:
                self._handle_response_window_output(new_text)
            else:
                # Handle other options - try clipboard-based replacement with fallback
                self._handle_clipboard_paste()

                # Check if selection changed (indicating successful paste)
                new_selection = self.get_selected_text(sleep_duration=0.1)

                # If selection is the same, paste failed (non-editable page)
                if (
                    self.original_selection == new_selection
                    and self.original_selection
                    and self.original_selection.strip()
                ):
                    # Fallback to modal window for non-editable pages
                    cleaned_text = self.output_queue.rstrip("\n")
                    QtCore.QMetaObject.invokeMethod(
                        self,
                        "_show_non_editable_modal",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, cleaned_text),
                    )
                self.original_selection = None
                self.output_queue = ""

        except Exception as e:
            self._logger.exception(f"Error processing output: {e}")

    def _handle_response_window_output(self, new_text: str) -> None:
        """Handle output for response window (Summary/Key Points)"""
        # Check if current_response_window exists and is not None
        current_window = getattr(self, "current_response_window", None)
        if not current_window:
            self._logger.warning("No current_response_window to handle output")
            return

        # Check if chat_area exists and is not None
        chat_area = getattr(current_window, "chat_area", None)
        if chat_area:
            chat_area.add_message(new_text)
        else:
            self._logger.warning("No chat_area found in current_response_window")
            return

        # If this is the initial response, add it to chat history
        if len(current_window.chat_history) == 1:  # Only original text exists
            current_window.chat_history.append(
                {
                    "role": "assistant",
                    "content": self.output_queue.rstrip("\n"),
                }
            )

    def _handle_clipboard_paste(self) -> None:
        """Handle clipboard-based text replacement with simple pyperclip approach"""
        try:
            import pyperclip

            clipboard_backup = pyperclip.paste()
            cleaned_text = self.output_queue.rstrip("\n")
            pyperclip.copy(cleaned_text)

            kbrd = keyboard.Controller()

            def press_ctrl_v():
                with kbrd.pressed(keyboard.Key.ctrl):
                    kbrd.press("v")
                    kbrd.release("v")

            press_ctrl_v()
            time.sleep(0.2)
            pyperclip.copy(clipboard_backup)

        except Exception as e:
            self._logger.error(f"Error in clipboard paste: {e}")
            # Fallback to modal window for non-editable pages
            cleaned_text = self.output_queue.rstrip("\n")
            QtCore.QMetaObject.invokeMethod(
                self,
                "_show_non_editable_modal",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, cleaned_text),
            )

    @Slot(str)
    def _show_non_editable_modal(self, transformed_text: str) -> None:
        """
        Show a modal window with the transformed text when pasting fails (non-editable page).
        """
        self._logger.debug("Showing non-editable modal window")
        try:
            # Close existing modal if any
            if hasattr(self, "non_editable_modal") and self.non_editable_modal is not None:
                self.non_editable_modal.close()
                self.non_editable_modal = None

            # Create and show the modal window
            self.non_editable_modal = ui.NonEditableModal.NonEditableModal(self, transformed_text)
            self.non_editable_modal.close_signal.connect(self.on_onboarding_closed)
            self.non_editable_modal.show()

        except Exception as e:
            self._logger.error(f"Error showing non-editable modal: {e}", exc_info=True)

    @Slot()
    def _on_non_editable_modal_closed(self) -> None:
        """Clean up modal reference when it's closed"""
        self.non_editable_modal = None

    """
    The function below (process_followup_question) processes follow-up questions in the chat interface for Summary, Key Points, and Table operations.

    This method handles the complex interaction between the UI, chat history, and AI providers:

    1. Chat History Management:
    - Maintains a list of all messages (original text, summary, follow-ups)
    - Properly formats roles (user/assistant) for each message
    - Preserves conversation context across multiple questions (until the Window is closed)

    2. Provider-Specific Handling:
    a) Gemini:
        - Converts internal roles to Gemini's user/model format
        - Uses chat sessions with proper history formatting
        - Maintains context through chat.send_message()

    b) OpenAI-compatible:
        - Uses standard OpenAI message array format
        - Includes system instruction and full conversation history
        - Properly maps internal roles to OpenAI roles

    3. Flow:
    a) User asks follow-up question
    b) Question is added to chat history
    c) Full history is formatted for the current provider
    d) Response is generated while maintaining context
    e) Response is displayed in chat UI
    f) New response is added to history for future context

    4. Threading:
    - Runs in a separate thread to prevent UI freezing
    - Uses signals to safely update UI from background thread
    - Handles errors too

    Args:
        response_window: The ResponseWindow instance managing the chat UI
        question: The follow-up question from the user

    This implementation is a bit convoluted, but it allows us to manage chat history & model roles across both providers! :3
    """

    def process_followup_question(self, response_window: ResponseWindow, question: str) -> None:
        """
        Process a follow-up question in the chat window, with image support.
        """
        self._logger.debug(f"Processing follow-up question: {question}")

        def process_thread():
            self._logger.debug("Starting follow-up processing thread")
            try:
                if not response_window.chat_history:
                    self._logger.error("No chat history found")
                    self.show_message_signal.emit("Error", "Chat history not found")
                    return

                # Add current question to chat history
                response_window.chat_history.append({"role": "user", "content": question})

                # Get chat history
                history = response_window.chat_history.copy()

                # System instruction based on context (image vs text)
                if response_window.image:
                    system_instruction = (
                        "You are a helpful AI assistant specialized in image analysis and visual understanding. "
                        "Continue the conversation about the image, providing detailed and accurate responses. "
                        "Use clear, well-structured responses with markdown formatting when appropriate."
                    )
                else:
                    system_instruction = (
                        "You are a helpful AI assistant. Provide clear and direct responses, "
                        "maintaining the same format and style as your previous responses. "
                        "If appropriate, use Markdown formatting to make your response more readable."
                    )

                self._logger.debug("Sending request to AI provider")

                # Get image data if available
                image_data = None
                if response_window.image:
                    self._logger.debug(
                        f" 🖼️\u00a0 Processing follow-up with image - size: {response_window.image.width()}x{response_window.image.height()}"
                    )
                    image_data = self._qimage_to_base64(
                        response_window.image, use_physical_file=False
                    )
                    if image_data:
                        self._logger.debug(
                            f" 🖼️\u00a0 Follow-up image converted to base64 - length: {len(image_data)}"
                        )
                    else:
                        self._logger.error(" 🖼️\u00a0 Failed to convert follow-up image to base64")

                # Format conversation differently based on provider
                if self.current_provider and isinstance(self.current_provider, GeminiProvider):
                    # For Gemini, use the proper history format with roles
                    chat_messages = []

                    # Convert our roles to Gemini's expected roles and handle images
                    for i, msg in enumerate(history):
                        gemini_role = "model" if msg["role"] == "assistant" else "user"

                        # For the first user message with image, include the image
                        if (
                            i == 0
                            and msg["role"] == "user"
                            and image_data
                            and "Image analysis request" in msg["content"]
                        ):
                            # Create content with image for first message
                            content_parts = [
                                msg["content"],
                                {"inline_data": {"mime_type": "image/png", "data": image_data}},
                            ]
                            chat_messages.append({"role": gemini_role, "parts": content_parts})
                        else:
                            chat_messages.append({"role": gemini_role, "parts": msg["content"]})

                    # Start chat with history
                    if hasattr(self.current_provider, "model") and self.current_provider.model:
                        chat = self.current_provider.model.start_chat(
                            history=chat_messages[:-1]
                        )  # Exclude last question

                        # Send the latest question
                        response = chat.send_message(question)
                        response_text = response.text
                    else:
                        response_text = "Error: Provider model not available"

                elif self.current_provider and isinstance(self.current_provider, MistralProvider):
                    # For Mistral, prepare messages with system instruction and history
                    # Use Union type to handle both string and list content

                    messages: list[dict[str, Any]] = [
                        {"role": "system", "content": system_instruction}
                    ]

                    # Add history messages, handling images for Mistral
                    for i, msg in enumerate(history[:-1]):  # Exclude the just-added question
                        if (
                            i == 0
                            and msg["role"] == "user"
                            and image_data
                            and "Image analysis request" in msg["content"]
                        ):
                            # First message with image
                            user_content: list[dict[str, Any]] = [
                                {"type": "text", "text": msg["content"]},
                                {
                                    "type": "image_url",
                                    "image_url": f"data:image/png;base64,{image_data}",
                                },
                            ]
                            messages.append({"role": "user", "content": user_content})
                        else:
                            messages.append({"role": msg["role"], "content": msg["content"]})

                    # Add the current question
                    messages.append({"role": "user", "content": question})

                    # Get response from Mistral
                    response_text = self.current_provider.get_response(
                        system_instruction,
                        messages,
                        return_response=True,
                    )

                elif self.current_provider:
                    # For OpenAI/compatible providers, prepare messages array
                    # Use Union type to handle both string and list content

                    messages: list[dict[str, Any]] = [
                        {"role": "system", "content": system_instruction}
                    ]

                    # Add history messages (including latest question)
                    for i, msg in enumerate(history):
                        role = "assistant" if msg["role"] == "assistant" else "user"

                        # Handle image for first user message if present
                        if (
                            i == 0
                            and msg["role"] == "user"
                            and image_data
                            and "Image analysis request" in msg["content"]
                        ):
                            # OpenAI format for image
                            content: list[dict[str, Any]] = [
                                {"type": "text", "text": msg["content"]},
                                {
                                    "type": "image_url",
                                    "image_url": {"url": f"data:image/png;base64,{image_data}"},
                                },
                            ]
                            messages.append({"role": role, "content": content})
                        else:
                            messages.append({"role": role, "content": msg["content"]})

                    # Get response by passing the full messages array
                    response_text = self.current_provider.get_response(
                        system_instruction,
                        messages if isinstance(messages, str) else str(messages),
                        return_response=True,
                    )
                else:
                    response_text = "Error: No provider available"

                self._logger.debug(f"Got response of length: {len(response_text)}")

                # Add response to chat history
                response_window.chat_history.append({"role": "assistant", "content": response_text})

                # Emit response via signal
                self.followup_response_signal.emit(response_text)

            except Exception as e:
                self._logger.error(f"Error processing follow-up question: {e}", exc_info=True)

                if "Resource has been exhausted" in str(e):
                    self.show_message_signal.emit(
                        "Error - Rate Limit Hit",
                        "Whoops! You've hit the per-minute rate limit of the API. Please try again in a few moments.\n\nIf this happens often, try switching to a different model in Settings.",
                    )
                    self.followup_response_signal.emit(
                        "Sorry, an error occurred while processing your question."
                    )
                else:
                    self.show_message_signal.emit("Error", f"An error occurred: {e}")
                    self.followup_response_signal.emit(
                        "Sorry, an error occurred while processing your question."
                    )

        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()

    def show_settings(self, providers_only: bool = False, previous_window=None) -> None:
        """
        Show the settings window with debounce protection against rapid clicks.
        """
        import time

        current_time = time.time() * 1000  # Convert to milliseconds

        # Prevent rapid successive clicks that could accidentally open Settings
        # This fixes the bug where rapid right-clicks on tray icon open Settings accidentally
        if (
            hasattr(self, "last_tray_click_time")
            and (current_time - self.last_tray_click_time)
            < self.systray_manager.tray_click_debounce_ms
        ):
            self._logger.debug("Settings click ignored due to debounce protection")
            return

        self.last_tray_click_time = current_time

        self._logger.debug("Showing settings window")
        # Always create a new settings window to handle providers_only correctly
        self.settings_window = ui.SettingsWindow.SettingsWindow(self, providers_only=providers_only)

        # Set reference to previous window for navigation
        if previous_window:
            self.settings_window.previous_window = previous_window

        self.settings_window.close_signal.connect(self.exit_app)

        self.settings_window.retranslate_ui()
        self.settings_window.show()

    def show_about(self) -> None:
        """
        Show the about window.
        """
        self._logger.debug("Showing about window")
        if not self.about_window:
            self.about_window = ui.AboutWindow.AboutWindow(self)
        self.about_window.show()

    def show_help(self) -> None:
        """
        Show the help window.
        """
        self._logger.debug("Showing help window")
        if not self.help_window:
            self.help_window = ui.HelpWindow.HelpWindow(self)
        self.help_window.show()

    # ============================================================================
    # APPLICATION LIFECYCLE METHODS
    # ============================================================================

    def setup_ctrl_c_listener(self) -> None:
        """
        Listener for Ctrl+C to exit the app.
        """
        signal.signal(signal.SIGINT, lambda signum, frame: self.handle_sigint(signum, frame))
        # This empty timer is needed to make sure that the sigint handler gets checked inside the main loop:
        # without it, the sigint handle would trigger only when an event is triggered, either by a hotkey combination
        # or by another GUI event like spawning a new window. With this we trigger it every 100ms with an empy lambda
        # so that the signal handler gets checked regularly.
        self.ctrl_c_timer = QtCore.QTimer()
        self.ctrl_c_timer.start(100)
        self.ctrl_c_timer.timeout.connect(lambda: None)

    def handle_sigint(self, signum: int, frame: Optional[types.FrameType]) -> None:
        """
        Handle the SIGINT signal (Ctrl+C) to exit the app gracefully.

        Args:
            signum: Signal number (unused but required by signal handler interface)
            frame: Current stack frame (unused but required by signal handler interface)
        """
        del signum, frame  # Explicitly mark as unused
        self._logger.debug("Received SIGINT. Exiting...")
        self.exit_app()

    def exit_app(self) -> None:
        """
        Exit the application.
        """
        self._logger.debug("Stopping the listener")
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        self._logger.debug("Restoring default SIGINT handler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._logger.debug("Exiting application")
        self.quit()
