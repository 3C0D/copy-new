"""
WritingToolApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

import gettext
import logging
import os
import platform
import signal
import sys
import threading
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pyperclip
from pynput import keyboard as pykeyboard
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QLocale, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

import ui.AboutWindow
import ui.CustomPopupWindow
import ui.NonEditableModal
import ui.OnboardingWindow
import ui.SettingsWindow

if TYPE_CHECKING:
    from aiprovider import AIProvider
    from ui.ResponseWindow import ResponseWindow

from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)
from config.settings import SettingsManager
from ui.ResponseWindow import ResponseWindow
from ui.ui_utils import get_icon_path
from update_checker import UpdateChecker

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
            self._logger.error(
                f"Critical error during WritingToolApp initialization: {e}"
            )
            import traceback

            self._logger.error(f"Full traceback: {traceback.format_exc()}")
            raise

    def _setup_core_attributes(self) -> None:
        """Initialize core application attributes."""
        self.current_response_window: ResponseWindow | None = None
        self.current_provider: AIProvider | None = None
        self.output_queue = ""
        self.paused = False

    def _setup_signals(self) -> None:
        """Connect application signals to their handlers."""
        self.output_ready_signal.connect(self.replace_text)
        self.show_message_signal.connect(self.show_message_box)
        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)

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
        self.tray_menu = None
        self.settings_window = None
        self.about_window = None
        self.non_editable_modal = None
        self.toggle_action = None

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
        self._logger.debug(
            "First launch detected (no providers configured), showing onboarding"
        )
        self.show_onboarding()

    def _handle_normal_launch(self) -> None:
        """Handle normal application launch with configured providers."""
        self._logger.debug("Providers configured, setting up hotkey and tray icon")

        # IMPORTANT: Synchronize global colorMode with saved settings before UI setup
        # This prevents visual conflicts when data exists with a different color_mode
        saved_color_mode = self.settings_manager.color_mode or "auto"
        from ui.ui_utils import set_color_mode

        set_color_mode(saved_color_mode)
        self._logger.debug(
            f"Synchronized colorMode with saved setting: {saved_color_mode}"
        )

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
            logging.info(
                f"Startup delay detected - waiting {delay / 1000}s for system tray to be ready"
            )
            logging.debug(
                f"Detected potential startup scenario, delaying tray icon creation by {delay}ms"
            )
            QtCore.QTimer.singleShot(delay, self.create_tray_icon)
        else:
            self.create_tray_icon()

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
        logging.exception(f"Error during app initialization: {error}")
        logging.exception("Falling back to onboarding")
        import traceback

        logging.debug(f"Full traceback: {traceback.format_exc()}")
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

    def _update_translation_functions(
        self, translation: gettext.NullTranslations
    ) -> None:
        """Update translation functions for all UI components."""
        self._ = translation.gettext
        ui.AboutWindow._ = self._
        ui.SettingsWindow._ = self._
        ui.ResponseWindow._ = self._
        ui.OnboardingWindow._ = self._
        ui.CustomPopupWindow._ = self._

    def retranslate_ui(self) -> None:
        """Retranslate the user interface elements."""
        self.update_tray_menu()

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
                "base_url": self.settings_manager.ollama_base_url
                or "http://localhost:11434",
                "model": "",
                "keep_alive": self.settings_manager.ollama_keep_alive or "5",
            },
            ("Mistral", "Mistral AI"): {
                "api_key": "",
                "api_model": "",
                "base_url": self.settings_manager.mistral_base_url
                or "https://api.mistral.ai/v1",
            },
            ("Anthropic", "Anthropic (Claude)"): {"api_key": "", "model": ""},
            ("OpenAI", "OpenAI-Compatible"): {
                "api_key": "",
                "base_url": self.settings_manager.openai_base_url
                or "https://api.openai.com/v1",
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

        # IMPORTANT: Synchronize global colorMode with saved settings before showing onboarding
        # This prevents visual conflicts when data_dev.json exists with a different color_mode
        saved_color_mode = self.settings_manager.color_mode or "auto"
        from ui.ui_utils import set_color_mode

        set_color_mode(saved_color_mode)
        self._logger.debug(
            f"Synchronized colorMode with saved setting: {saved_color_mode}"
        )

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
            (
                provider
                for provider in self.providers
                if provider.internal_name == provider_name
            ),
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
                if self.paused:
                    return
                self._logger.debug("triggered hotkey")
                self.hotkey_triggered_signal.emit()  # Emit the signal when hotkey is pressed

            # Define the hotkey combination
            hotkey = pykeyboard.HotKey(pykeyboard.HotKey.parse(shortcut), on_activate)
            self.registered_hotkey = orig_shortcut

            # Helper function to standardize key event
            def for_canonical(f):
                return lambda k: f(
                    self.hotkey_listener.canonical(k)
                    if k is not None and self.hotkey_listener is not None
                    else k
                )

            # Create a listener and store it as an attribute to stop it later
            self.hotkey_listener = pykeyboard.Listener(
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
        self._logger.debug("Hotkey pressed")

        # Check for spam triggers
        if self.check_trigger_spam():
            self._logger.warning("Hotkey spam detected - quitting application")
            self.exit_app()
            return

        # Close existing non-editable modal if open
        if self.non_editable_modal is not None:
            self._logger.debug("Closing existing non-editable modal")
            self.non_editable_modal.close()
            self.non_editable_modal = None

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
        self._logger.debug("Showing popup window")
        # First attempt with default sleep
        selected_text = self.get_selected_text()

        # Retry with longer sleep if no text captured
        if not selected_text:
            self._logger.debug("No text captured, retrying with longer sleep")
            selected_text = self.get_selected_text(sleep_duration=0.5)

        clipboard_image = self.get_clipboard_image()
        self._logger.debug(f'Selected text: "{selected_text}"')
        self._logger.debug(f'Clipboard image: {clipboard_image is not None}')
        try:
            if self.popup_window is not None:
                self._logger.debug("Existing popup window found")
                if self.popup_window.isVisible():
                    self._logger.debug("Closing existing visible popup window")
                    self.popup_window.close()
                self.popup_window = None
            self._logger.debug("Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(
                self, selected_text, clipboard_image
            )

            # Set the window icon
            icon_path = get_icon_path("app_icon", with_theme=False)
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
        except Exception as e:
            self._logger.error(f"Error showing popup window: {e}", exc_info=True)

    def debug_clipboard_contents(self) -> None:
        """
        Debug method to analyze clipboard contents and available formats.
        Helps diagnose clipboard detection issues.
        """
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            self._logger.debug("=== CLIPBOARD DEBUG INFO ===")
            self._logger.debug(f"Platform: {platform.system()}")
            self._logger.debug(f"hasImage(): {mime_data.hasImage()}")
            self._logger.debug(f"hasText(): {mime_data.hasText()}")
            self._logger.debug(f"hasUrls(): {mime_data.hasUrls()}")

            # List all available formats
            formats = mime_data.formats()
            self._logger.debug(f"Available formats ({len(formats)}): {formats}")

            # Check specific image formats
            image_formats = [
                "image/png", "image/jpeg", "image/jpg", "image/bmp",
                "image/gif", "image/tiff", "image/dib", "CF_DIB",
                "CF_BITMAP", "application/x-qt-image"
            ]

            for fmt in image_formats:
                has_format = mime_data.hasFormat(fmt)
                if has_format:
                    data_size = len(mime_data.data(fmt))
                    self._logger.debug(f"Format '{fmt}': YES ({data_size} bytes)")
                else:
                    self._logger.debug(f"Format '{fmt}': NO")

            # Linux-specific format checks
            if platform.system() == "Linux":
                self._logger.debug("--- Linux-specific format checks ---")
                linux_formats = [
                    "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
                    "application/x-qt-image", "application/x-qt-pixmap",
                    "image/x-portable-pixmap", "image/x-portable-bitmap",
                    "image/x-portable-graymap", "image/x-portable-anymap"
                ]
                
                for fmt in linux_formats:
                    has_format = mime_data.hasFormat(fmt)
                    if has_format:
                        data_size = len(mime_data.data(fmt))
                        self._logger.debug(f"Linux format '{fmt}': YES ({data_size} bytes)")
                    else:
                        self._logger.debug(f"Linux format '{fmt}': NO")
                
                # Check for any format containing image-related keywords
                self._logger.debug("--- Checking for image-related formats ---")
                for fmt in formats:
                    if any(img_type in fmt.lower() for img_type in ['image', 'pixmap', 'bitmap', 'png', 'jpeg', 'jpg', 'gif', 'bmp', 'tiff']):
                        has_format = mime_data.hasFormat(fmt)
                        if has_format:
                            data_size = len(mime_data.data(fmt))
                            self._logger.debug(f"Image-related format '{fmt}': YES ({data_size} bytes)")
                        else:
                            self._logger.debug(f"Image-related format '{fmt}': NO")

            self._logger.debug("=== END CLIPBOARD DEBUG ===")

        except Exception as e:
            self._logger.error(f"Error debugging clipboard: {e}")

    def get_clipboard_image(self) -> Optional[QImage]:
        """
        Get the image currently stored in the clipboard using Qt6 with multiple detection methods.
        Returns the image if found, None otherwise.

        Uses multiple approaches to detect images:
        1. Standard hasImage() method
        2. Format-specific detection for various image types
        3. Raw data analysis for Windows clipboard formats
        4. Linux-specific clipboard formats and methods
        5. Direct image data access
        """
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            # Debug clipboard contents if in debug mode
            if self._logger.isEnabledFor(logging.DEBUG):
                self.debug_clipboard_contents()

            # Method 1: Standard Qt image detection
            if mime_data.hasImage():
                self._logger.debug("Method 1: hasImage() returned True")
                image = mime_data.imageData()
                if isinstance(image, QImage):
                    if not image.isNull():
                        self._logger.debug(f"Image found via hasImage(): {image.width()}x{image.height()}")
                        return image
                    else:
                        self._logger.debug("hasImage() returned null QImage")
                else:
                    # Convert QPixmap to QImage
                    try:
                        from PySide6.QtGui import QPixmap
                        if isinstance(image, QPixmap):
                            qimage = image.toImage()
                            if not qimage.isNull():
                                self._logger.debug(f"Image converted from QPixmap: {qimage.width()}x{qimage.height()}")
                                return qimage
                            else:
                                self._logger.debug("QPixmap conversion resulted in null QImage")
                    except Exception as e:
                        self._logger.debug(f"Error converting QPixmap: {e}")

            # Method 2: Format-specific detection
            image_formats = [
                "image/png", "image/jpeg", "image/jpg", "image/bmp",
                "image/gif", "image/tiff", "image/dib", "CF_DIB", "CF_BITMAP"
            ]

            for fmt in image_formats:
                if mime_data.hasFormat(fmt):
                    self._logger.debug(f"Method 2: Found format '{fmt}'")
                    try:
                        data = mime_data.data(fmt)
                        if data and not data.isEmpty():
                            # Try to load image from raw data
                            image = QImage()
                            if image.loadFromData(data):
                                if not image.isNull():
                                    self._logger.debug(f"Image loaded from format '{fmt}': {image.width()}x{image.height()}")
                                    return image
                                else:
                                    self._logger.debug(f"Format '{fmt}' data loaded but resulted in null image")
                            else:
                                self._logger.debug(f"Failed to load image from format '{fmt}' data")
                        else:
                            self._logger.debug(f"Format '{fmt}' has no data or empty data")
                    except Exception as e:
                        self._logger.debug(f"Error processing format '{fmt}': {e}")

            # Method 3: Windows-specific clipboard formats (for Print Screen)
            if platform.system() == "Windows":
                windows_formats = ["CF_DIB", "CF_BITMAP", "CF_DIBV5"]
                for fmt in windows_formats:
                    if mime_data.hasFormat(fmt):
                        self._logger.debug(f"Method 3: Found Windows format '{fmt}'")
                        try:
                            data = mime_data.data(fmt)
                            if data and not data.isEmpty():
                                # Try to create QImage from Windows DIB/Bitmap data
                                image = QImage()
                                if image.loadFromData(data):
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded from Windows format '{fmt}': {image.width()}x{image.height()}")
                                        return image
                                else:
                                    # Try alternative loading methods for Windows formats
                                    try:
                                        # Convert bytes to QByteArray and try different formats
                                        from PySide6.QtCore import QByteArray
                                        byte_array = QByteArray(data)

                                        # Try loading as different image formats
                                        for img_format in ["BMP", "PNG", "JPEG"]:
                                            image = QImage()
                                            if image.loadFromData(byte_array, img_format.encode()):
                                                if not image.isNull():
                                                    self._logger.debug(f"Image loaded from Windows format '{fmt}' as {img_format}: {image.width()}x{image.height()}")
                                                    return image
                                    except Exception as e:
                                        self._logger.debug(f"Alternative loading failed for '{fmt}': {e}")
                        except Exception as e:
                            self._logger.debug(f"Error processing Windows format '{fmt}': {e}")

            # Method 4: Linux-specific clipboard formats and methods
            if platform.system() == "Linux":
                self._logger.debug("Method 4: Checking Linux-specific clipboard formats")
                
                # Linux clipboard formats commonly used for images
                linux_formats = [
                    "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
                    "application/x-qt-image", "application/x-qt-pixmap",
                    "image/x-portable-pixmap", "image/x-portable-bitmap",
                    "image/x-portable-graymap", "image/x-portable-anymap"
                ]
                
                for fmt in linux_formats:
                    if mime_data.hasFormat(fmt):
                        self._logger.debug(f"Method 4: Found Linux format '{fmt}'")
                        try:
                            data = mime_data.data(fmt)
                            if data and not data.isEmpty():
                                # Try to load image from raw data
                                image = QImage()
                                if image.loadFromData(data):
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded from Linux format '{fmt}': {image.width()}x{image.height()}")
                                        return image
                                    else:
                                        self._logger.debug(f"Linux format '{fmt}' data loaded but resulted in null image")
                                else:
                                    self._logger.debug(f"Failed to load image from Linux format '{fmt}' data")
                        except Exception as e:
                            self._logger.debug(f"Error processing Linux format '{fmt}': {e}")
                
                # Try to get image data directly from clipboard (Linux-specific approach)
                try:
                    # Sometimes on Linux, the image data is available but not detected by hasImage()
                    image_data = mime_data.imageData()
                    if image_data is not None:
                        self._logger.debug("Method 4: Found imageData() directly on Linux")
                        if isinstance(image_data, QImage) and not image_data.isNull():
                            self._logger.debug(f"Direct imageData() successful on Linux: {image_data.width()}x{image_data.height()}")
                            return image_data
                        elif hasattr(image_data, 'toImage'):
                            # Try converting if it's a QPixmap
                            converted = image_data.toImage()
                            if not converted.isNull():
                                self._logger.debug(f"Direct imageData() converted on Linux: {converted.width()}x{converted.height()}")
                                return converted
                except Exception as e:
                    self._logger.debug(f"Linux-specific imageData() method failed: {e}")

            # Method 5: Try to get image data directly from clipboard (last resort)
            try:
                # Sometimes the image data is available but not detected by hasImage()
                image_data = mime_data.imageData()
                if image_data is not None:
                    self._logger.debug("Method 5: Found imageData() directly")
                    if isinstance(image_data, QImage) and not image_data.isNull():
                        self._logger.debug(f"Direct imageData() successful: {image_data.width()}x{image_data.height()}")
                        return image_data
                    elif hasattr(image_data, 'toImage'):
                        # Try converting if it's a QPixmap
                        converted = image_data.toImage()
                        if not converted.isNull():
                            self._logger.debug(f"Direct imageData() converted: {converted.width()}x{converted.height()}")
                            return converted
            except Exception as e:
                self._logger.debug(f"Method 5 failed: {e}")

            # Method 6: Try alternative clipboard access methods for Linux
            if platform.system() == "Linux":
                self._logger.debug("Method 6: Trying alternative Linux clipboard access")
                try:
                    # Try to access clipboard data in different ways
                    clipboard_data = clipboard.mimeData()
                    
                    # Check if there are any data formats that might contain image data
                    all_formats = clipboard_data.formats()
                    self._logger.debug(f"All available formats on Linux: {all_formats}")
                    
                    # Look for any format that might contain image data
                    for fmt in all_formats:
                        if any(img_type in fmt.lower() for img_type in ['image', 'pixmap', 'bitmap', 'png', 'jpeg', 'jpg']):
                            self._logger.debug(f"Method 6: Found potential image format '{fmt}'")
                            try:
                                data = clipboard_data.data(fmt)
                                if data and not data.isEmpty():
                                    # Try to load image from raw data
                                    image = QImage()
                                    if image.loadFromData(data):
                                        if not image.isNull():
                                            self._logger.debug(f"Image loaded from potential format '{fmt}': {image.width()}x{image.height()}")
                                            return image
                            except Exception as e:
                                self._logger.debug(f"Error processing potential format '{fmt}': {e}")
                                
                except Exception as e:
                    self._logger.debug(f"Alternative Linux clipboard access failed: {e}")

            self._logger.debug("No image found in clipboard using any method")

        except Exception as e:
            self._logger.error(f"Error getting clipboard image: {e}")

        return None

    def _get_image_from_linux_system_tools(self) -> Optional[QImage]:
        """
        Try to get image from clipboard using Linux system tools (xclip, xsel).
        This is a fallback method when Qt clipboard methods fail.
        """
        try:
            import subprocess
            import tempfile
            import os

            # Try xclip first (more common)
            try:
                # Check if xclip is available
                result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'TARGETS'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self._logger.debug("xclip is available, trying to get image")
                    
                    # Try to get image data from clipboard
                    img_result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], 
                                             capture_output=True, timeout=5)
                    if img_result.returncode == 0 and img_result.stdout:
                        # Create temporary file to save image data
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                            temp_file.write(img_result.stdout)
                            temp_file_path = temp_file.name
                        
                        try:
                            # Load image from temporary file
                            image = QImage(temp_file_path)
                            if not image.isNull():
                                self._logger.debug(f"Image loaded via xclip: {image.width()}x{image.height()}")
                                return image
                        finally:
                            # Clean up temporary file
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass
                    
                    # Try other image formats
                    for img_type in ['image/jpeg', 'image/bmp', 'image/gif']:
                        try:
                            img_result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', img_type, '-o'], 
                                                     capture_output=True, timeout=5)
                            if img_result.returncode == 0 and img_result.stdout:
                                with tempfile.NamedTemporaryFile(suffix=f'.{img_type.split("/")[1]}', delete=False) as temp_file:
                                    temp_file.write(img_result.stdout)
                                    temp_file_path = temp_file.name
                                
                                try:
                                    image = QImage(temp_file_path)
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded via xclip ({img_type}): {image.width()}x{image.height()}")
                                        return image
                                finally:
                                    try:
                                        os.unlink(temp_file_path)
                                    except:
                                        pass
                        except Exception as e:
                            self._logger.debug(f"xclip failed for {img_type}: {e}")
                            
            except FileNotFoundError:
                self._logger.debug("xclip not found, trying xsel")
            except Exception as e:
                self._logger.debug(f"xclip failed: {e}")

            # Try xsel as fallback
            try:
                # Check if xsel is available
                result = subprocess.run(['xsel', '--clipboard', '--type', 'TARGETS'], 
                                      capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    self._logger.debug("xsel is available, trying to get image")
                    
                    # Try to get image data from clipboard
                    img_result = subprocess.run(['xsel', '--clipboard', '--type', 'image/png', '--output'], 
                                             capture_output=True, timeout=5)
                    if img_result.returncode == 0 and img_result.stdout:
                        # Create temporary file to save image data
                        with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as temp_file:
                            temp_file.write(img_result.stdout)
                            temp_file_path = temp_file.name
                        
                        try:
                            # Load image from temporary file
                            image = QImage(temp_file_path)
                            if not image.isNull():
                                self._logger.debug(f"Image loaded via xsel: {image.width()}x{image.height()}")
                                return image
                        finally:
                            # Clean up temporary file
                            try:
                                os.unlink(temp_file_path)
                            except:
                                pass
                    
                    # Try other image formats
                    for img_type in ['image/jpeg', 'image/bmp', 'image/gif']:
                        try:
                            img_result = subprocess.run(['xsel', '--clipboard', '--type', img_type, '--output'], 
                                                     capture_output=True, timeout=5)
                            if img_result.returncode == 0 and img_result.stdout:
                                with tempfile.NamedTemporaryFile(suffix=f'.{img_type.split("/")[1]}', delete=False) as temp_file:
                                    temp_file.write(img_result.stdout)
                                    temp_file_path = temp_file.name
                                
                                try:
                                    image = QImage(temp_file_path)
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded via xsel ({img_type}): {image.width()}x{image.height()}")
                                        return image
                                finally:
                                    try:
                                        os.unlink(temp_file_path)
                                    except:
                                        pass
                        except Exception as e:
                            self._logger.debug(f"xsel failed for {img_type}: {e}")
                            
            except FileNotFoundError:
                self._logger.debug("Neither xclip nor xsel found")
            except Exception as e:
                self._logger.debug(f"xsel failed: {e}")

        except Exception as e:
            self._logger.debug(f"Linux system tools fallback failed: {e}")

        return None

    def get_selected_text(self, sleep_duration: float = 0.2) -> str:
        """
        Get the currently selected text from any application.
        Args:
            sleep_duration (float): Time to wait for clipboard update
        """
        # Backup the clipboard
        clipboard_backup = pyperclip.paste()
        self._logger.debug(
            f'Clipboard backup: "{clipboard_backup}" (sleep: {sleep_duration}s)'
        )

        # Clear the clipboard
        self.clear_clipboard()

        # Simulate Ctrl+C
        self._logger.debug("Simulating Ctrl+C")
        kbrd = pykeyboard.Controller()

        def press_ctrl_c():
            kbrd.press(pykeyboard.Key.ctrl.value)
            kbrd.press("c")
            kbrd.release("c")
            kbrd.release(pykeyboard.Key.ctrl.value)

        press_ctrl_c()

        # Wait for the clipboard to update
        time.sleep(sleep_duration)
        self._logger.debug(f"Waited {sleep_duration}s for clipboard")

        # Get the selected text
        selected_text = pyperclip.paste()

        # Clean the selected text (remove leading/trailing whitespace and newlines)
        if selected_text:
            selected_text = selected_text.strip()

        # Restore the clipboard
        pyperclip.copy(clipboard_backup)

        return selected_text



    def clear_clipboard(self) -> None:
        """
        Clear the system clipboard.
        """
        try:
            pyperclip.copy("")
        except Exception as e:
            self._logger.error(f"Error clearing clipboard: {e}")

    def process_option(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str] = None,
        force_chat: bool = False,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Process the selected writing option in a separate thread.

        Args:
            option: The action option to process
            selected_text: The text selected by the user
            custom_change: Custom instruction for "Custom" option
            force_chat: If True, force response to open in ResponseWindow (chat mode)
        """
        self._logger.debug(f"Processing option: {option}")
        self._logger.debug(f"Selected text: {selected_text}")
        self._logger.debug(f"Custom change: {custom_change}")
        self._logger.debug(f"Force chat: {force_chat}")
        self._logger.debug(f"Image: {image is not None}")

        action_config = self.settings_manager.actions.get(option)
        if not action_config:
            self._logger.error(f"Action not found: {option}")
            return

        should_setup_window = self._should_display_in_window(
            option, selected_text, action_config, force_chat, image
        )

        if should_setup_window:
            is_empty_custom = option == "Custom" and not selected_text.strip()
            self._setup_response_window(is_empty_custom, option, selected_text, image)
        elif hasattr(self, "current_response_window"):
            delattr(self, "current_response_window")

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, custom_change, image),
            daemon=True,
        ).start()

    def _setup_response_window(
        self,
        is_empty_custom: bool,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None,
    ) -> None:
        # For images, always use "Chat" as title and force chat mode
        if image is not None:
            window_title = "Image Analysis"
            self._logger.debug("Setting up response window for image analysis")
        else:
            window_title = "Chat" if is_empty_custom else option

        self.current_response_window = self.show_response_window(
            window_title, selected_text
        )

        # Initialize chat history inline
        self.current_response_window.chat_history = (
            []
            if is_empty_custom
            else [
                {
                    "role": "user",
                    "content": f"Original text to {option.lower()}:\n\n{selected_text}",
                },
            ]
        )

        # If there's an image, add it to chat history and enable force chat
        if image is not None:
            # Add image to chat history
            if self.current_response_window.chat_history:
                # Add image after the text
                self.current_response_window.chat_history.append({
                    "role": "user",
                    "content": "[Image from clipboard]",
                    "image": image
                })
            else:
                # Only image, no text
                self.current_response_window.chat_history.append({
                    "role": "user",
                    "content": "[Image from clipboard]",
                    "image": image
                })

            # Automatically enable force chat for images
            if hasattr(self.current_response_window, 'force_chat_toggle'):
                self.current_response_window.force_chat_toggle.setChecked(True)
                # Also lock it to prevent accidental disabling
                if hasattr(self.current_response_window, 'force_chat_lock'):
                    self.current_response_window.force_chat_lock.setChecked(True)

    # ============================================================================
    # AI PROCESSING METHODS
    # ============================================================================

    def process_option_thread(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str] = None,
        force_chat: bool = False,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Thread function to process the selected writing option using the AI model.

        Args:
            option: The selected writing option (e.g., "Summary", "Custom", "Proofread")
            selected_text: The text selected by the user
            custom_change: Optional custom change description for Custom option
        """
        self._logger.debug(f"Starting processing thread for option: {option}")

        try:
            prompt_data = self._prepare_prompt_data(
                option, selected_text, custom_change, image
            )
            if not prompt_data:
                return

            self.output_queue = ""
            should_open_window = self._should_display_in_window(
                option, selected_text, prompt_data["action_config"], force_chat, image
            )

            if should_open_window:
                self._process_window_response(
                    option, selected_text, custom_change, prompt_data, image
                )
            else:
                self._process_direct_replacement(prompt_data)

        except Exception as e:
            self._handle_processing_error(e)

    def _prepare_prompt_data(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str] = None,
        image: QtGui.QImage | None = None,
    ) -> Optional[dict]:
        """
        Prepare prompt data for AI processing.

        Returns:
            dict: Contains prompt, system_instruction, and action_config, or None if invalid
        """
        has_selected_text = selected_text.strip() != ""
        is_custom_option = option == "Custom"

        if not has_selected_text and image is None:
            return self._handle_no_text_selected(is_custom_option, custom_change, image)
        else:
            return self._handle_text_selected(
                option, selected_text, custom_change, is_custom_option, image
            )

    def _handle_no_text_selected(
        self,
        is_custom_option: bool,
        custom_change: Optional[str],
        image: QtGui.QImage | None = None,
    ) -> Optional[dict]:
        """Handle case where no text is selected."""
        if is_custom_option:
            return {
                "prompt": custom_change,
                "system_instruction": "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                "action_config": {},
                "image": image,
            }
        else:
            self.show_message_signal.emit(
                "Error", "Please select text to use this option."
            )
            return None

    def _handle_text_selected(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str],
        is_custom_option: bool,
        image: QtGui.QImage | None = None,
    ) -> Optional[dict]:
        """Handle case where text is selected."""
        action_config = self.settings_manager.actions.get(option)
        if not action_config:
            self._logger.error(f"Action not found: {option}")
            return None

        prompt_prefix = action_config.get("prefix", "")
        system_instruction = action_config.get("instruction", "")

        if is_custom_option:
            prompt = f"{prompt_prefix}Described change: {custom_change}\n\nText: {selected_text}"
        else:
            prompt = f"{prompt_prefix}{selected_text}"

        return {
            "prompt": prompt,
            "system_instruction": system_instruction,
            "action_config": action_config,
            "image": image,
        }

    def _should_display_in_window(
        self,
        option: str,
        selected_text: str,
        action_config: dict,
        force_chat: bool,
        image: QtGui.QImage | None = None,
    ) -> bool:
        """Determine if response should be displayed in a window."""
        has_selected_text = selected_text.strip() != ""
        is_custom_option = option == "Custom"

        # If there's an image, always open in window (force chat mode)
        if image is not None:
            self._logger.debug("Image detected - forcing window display")
            return True

        # Normal logic for text-based operations
        return (
            (is_custom_option and not has_selected_text)
            or (has_selected_text and action_config.get("open_in_window", False))
            or (force_chat and has_selected_text)
        )

    def _process_window_response(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str],
        prompt_data: dict,
        image: QtGui.QImage | None = None,
    ) -> None:
        """Process AI response for window display."""
        if not self.current_provider:
            return

        self._logger.debug("Getting response for window display")

        # Check if we have an image to process
        image = prompt_data.get("image")
        if image:
            # For images, we need to use a special prompt format
            prompt = f"Analyze this image and respond to the following request: {prompt_data['prompt']}"
            # Convert image to base64 for the provider
            import base64
            import io

            buffer = io.BytesIO()
            image.save(buffer, "PNG")
            image_base64 = base64.b64encode(buffer.getvalue()).decode()

            response = self.current_provider.get_response(
                prompt_data["system_instruction"],
                prompt,
                return_response=True,
                image_data=image_base64,
            )
        else:
            response = self.current_provider.get_response(
                prompt_data["system_instruction"],
                str(prompt_data["prompt"]),
                return_response=True,
            )
        self._logger.debug(f"Got response of length: {len(response) if response else 0}")

        self._update_chat_history_if_needed(option, selected_text, custom_change, image)
        self._update_response_window(response)

    def _update_chat_history_if_needed(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str],
        image: QtGui.QImage | None = None,
    ) -> None:
        """Update chat history for custom prompts without text."""
        is_custom_option = option == "Custom"
        has_selected_text = selected_text.strip() != ""

        if is_custom_option and not has_selected_text and self.current_response_window:
            self.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or "", "image": image},
            )

    def _update_response_window(self, response: str) -> None:
        """Update response window with AI response (thread-safe)."""
        if self.current_response_window:
            QtCore.QMetaObject.invokeMethod(
                self.current_response_window,
                "set_text",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response),
            )
            self._logger.debug("Invoked set_text on response window")

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
        msg_box.setWindowFlags(
            msg_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Add standard 'OK' button
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        # For API errors, add a button to open settings
        settings_button = None
        if any(
            keyword in title.lower()
            for keyword in ["api", "key", "quota", "rate limit", "connection"]
        ):
            settings_button = msg_box.addButton(
                "Open Settings", QMessageBox.ButtonRole.ActionRole
            )

        # Show the message box
        msg_box.exec()

        # If settings button was clicked, open settings
        if settings_button and msg_box.clickedButton() == settings_button:
            self.show_settings()

    def show_response_window(
        self, option: str, text: str
    ) -> ui.ResponseWindow.ResponseWindow:
        """
        Show the response in a new window instead of pasting it.
        """
        response_window = ui.ResponseWindow.ResponseWindow(self, f"{option} Result")
        response_window.selected_text = text  # Store the text for regeneration
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
        error_message = "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"

        # Confirm new_text exists and is a string
        if new_text and isinstance(new_text, str):
            self.output_queue += new_text
            current_output = self.output_queue.strip()  # Strip whitespace for comparison

            # If the new text is the error message, show a message box
            if current_output == error_message:
                self.show_message_signal.emit(
                    "Error", "The text is incompatible with the requested change."
                )
                return

            # Check if we're building up to the error message (to prevent partial pasting)
            if len(current_output) <= len(error_message):
                clean_current = "".join(current_output.split())
                clean_error = "".join(error_message.split())
                if clean_current == clean_error[: len(clean_current)]:
                    return

            logging.debug("Processing output text")
            try:
                # For Summary and Key Points, show in response window
                if (
                    hasattr(self, "current_response_window")
                    and self.current_response_window
                ):
                    # Use chat_area.add_message instead of append_text
                    if (
                        hasattr(self.current_response_window, "chat_area")
                        and self.current_response_window.chat_area
                    ):
                        self.current_response_window.chat_area.add_message(new_text)

                    # If this is the initial response, add it to chat history
                    if (
                        len(self.current_response_window.chat_history) == 1
                    ):  # Only original text exists
                        self.current_response_window.chat_history.append(
                            {
                                "role": "assistant",
                                "content": self.output_queue.rstrip("\n"),
                            },
                        )
                else:
                    # For other options, try clipboard-based replacement with fallback
                    clipboard_backup = pyperclip.paste()
                    cleaned_text = self.output_queue.rstrip("\n")

                    # Get current selection before attempting paste
                    original_selection = self.get_selected_text(sleep_duration=0.1)

                    pyperclip.copy(cleaned_text)

                    kbrd = pykeyboard.Controller()

                    def press_ctrl_v():
                        kbrd.press(pykeyboard.Key.ctrl.value)
                        kbrd.press("v")
                        kbrd.release("v")
                        kbrd.release(pykeyboard.Key.ctrl.value)

                    press_ctrl_v()
                    time.sleep(0.2)

                    # Check if selection changed (indicating successful paste)
                    new_selection = self.get_selected_text(sleep_duration=0.1)

                    # If selection is the same, paste failed (non-editable page)
                    if original_selection == new_selection and original_selection.strip():
                        logging.debug(
                            "Paste failed - showing modal window for non-editable page"
                        )
                        # noinspection PyTypeChecker
                        QtCore.QMetaObject.invokeMethod(
                            self,
                            "_show_non_editable_modal",
                            QtCore.Qt.ConnectionType.QueuedConnection,
                            QtCore.Q_ARG(str, cleaned_text),
                        )

                    pyperclip.copy(clipboard_backup)

                if not hasattr(self, "current_response_window"):
                    self.output_queue = ""

            except Exception as e:
                logging.exception(f"Error processing output: {e}")
        else:
            logging.debug("No new text to process")

    @QtCore.Slot(str)
    def _show_non_editable_modal(self, transformed_text: str) -> None:
        """
        Show a modal window with the transformed text when pasting fails (non-editable page).
        """
        logging.debug("Showing non-editable modal window")
        try:
            # Close existing modal if any
            if self.non_editable_modal is not None:
                self.non_editable_modal.close()
                self.non_editable_modal = None

            # Create and show the modal window
            self.non_editable_modal = ui.NonEditableModal.NonEditableModal(
                self, transformed_text
            )

            # Connect close event to clean up reference
            self.non_editable_modal.finished.connect(self._on_modal_closed)

            # Show the modal (use exec() to make it truly modal and keep it open)
            self.non_editable_modal.exec()

        except Exception as e:
            logging.error(f"Error showing non-editable modal: {e}", exc_info=True)

    @QtCore.Slot()
    def _on_modal_closed(self) -> None:
        """Clean up modal reference when it's closed"""
        self.non_editable_modal = None

    def create_tray_icon(self) -> None:
        """
        Create the system tray icon for the application.
        """
        if self.tray_icon:
            logging.debug("Tray icon already exists")
            return

        logging.debug("Creating system tray icon")

        # Check if system tray is available with retry mechanism for startup
        if not self._is_system_tray_available_with_retry():
            logging.error("System tray is not available on this system after retries")
            return

        icon_path = get_icon_path("app_icon", with_theme=False)
        logging.debug(f"Icon path resolved to: {icon_path}")

        if not icon_path.exists():
            logging.warning(f"Tray icon not found at {icon_path}")
            # Use a default icon if not found
            self.tray_icon = QSystemTrayIcon(self)
        else:
            logging.debug(f"Loading icon from: {icon_path}")
            icon = QtGui.QIcon(icon_path.as_posix())
            if icon.isNull():
                logging.warning(f"Failed to load icon from {icon_path}")
            self.tray_icon = QSystemTrayIcon(icon, self)
        # Set the tooltip (hover name) for the tray icon
        self.tray_icon.setToolTip("WritingTools")
        self.tray_menu = QMenu()
        self.tray_icon.setContextMenu(self.tray_menu)

        # Timer to prevent rapid successive clicks that could accidentally trigger menu items
        # This prevents the bug where rapid right-clicks open Settings accidentally
        self.last_tray_click_time = 0
        self.tray_click_debounce_ms = 300  # 300ms debounce period

        self.update_tray_menu()
        self.tray_icon.show()
        logging.debug("Tray icon show() called")

        # Verify if it's actually visible with retry
        self._verify_tray_icon_visibility()

        logging.debug("Tray icon setup completed")

    def _is_system_tray_available_with_retry(
        self, max_retries: int = 5, delay_ms: int = 1000
    ) -> bool:
        """
        Check if system tray is available with retry mechanism.
        This is especially important during Windows startup when the system tray
        might not be immediately available.

        Args:
            max_retries: Maximum number of retry attempts
            delay_ms: Delay between retries in milliseconds

        Returns:
            bool: True if system tray becomes available, False otherwise
        """
        for attempt in range(max_retries):
            if QSystemTrayIcon.isSystemTrayAvailable():
                if attempt > 0:
                    logging.info(
                        f"System tray became available after {attempt + 1} attempts"
                    )
                return True

            if attempt < max_retries - 1:  # Don't wait after the last attempt
                logging.debug(
                    f"System tray not available, attempt {attempt + 1}/{max_retries}, retrying in {delay_ms}ms..."
                )
                QtCore.QTimer.singleShot(delay_ms, lambda: None)
                self.processEvents()  # Process pending events
                time.sleep(delay_ms / 1000.0)  # Convert to seconds

        logging.warning(f"System tray not available after {max_retries} attempts")
        return False

    def _verify_tray_icon_visibility(
        self, max_retries: int = 2, delay_ms: int = 250
    ) -> None:
        """
        Verify that the tray icon is actually visible with retry mechanism.

        Args:
            max_retries: Maximum number of retry attempts
            delay_ms: Delay between retries in milliseconds
        """
        for attempt in range(max_retries):
            if self.tray_icon and self.tray_icon.isVisible():
                logging.debug(f"Tray icon confirmed visible after {attempt + 1} attempts")
                return

            if attempt < max_retries - 1:  # Don't wait after the last attempt
                logging.debug(
                    f"Tray icon not visible, attempt {attempt + 1}/{max_retries}, retrying..."
                )
                QtCore.QTimer.singleShot(delay_ms, lambda: None)
                self.processEvents()  # Process pending events
                time.sleep(delay_ms / 1000.0)  # Convert to seconds
                if self.tray_icon:
                    self.tray_icon.show()  # Try showing again

        if self.tray_icon and not self.tray_icon.isVisible():
            logging.warning("Tray icon reports as NOT visible after retries")
        else:
            logging.debug("Tray icon visibility verification completed")

    def update_tray_menu(self) -> None:
        """
        Update the tray menu with all menu items, including pause functionality
        and proper translations.
        """
        if self.tray_menu is None:
            return

        self.tray_menu.clear()

        # Apply dark mode styles using darkdetect
        self.apply_dark_mode_styles(self.tray_menu)

        # Settings menu item
        settings_action = self.tray_menu.addAction(self._("Settings"))
        settings_action.triggered.connect(self.show_settings)

        # Pause/Resume toggle action
        self.toggle_action = self.tray_menu.addAction(
            self._("Resume") if self.paused else self._("Pause")
        )
        self.toggle_action.triggered.connect(self.toggle_paused)

        # About menu item
        about_action = self.tray_menu.addAction(self._("About"))
        about_action.triggered.connect(self.show_about)

        # Exit menu item
        exit_action = self.tray_menu.addAction(self._("Exit"))
        exit_action.triggered.connect(self.exit_app)

    def toggle_paused(self) -> None:
        """Toggle the paused state of the application."""
        logging.debug("Toggle paused state")
        self.paused = not self.paused
        if self.toggle_action is not None:
            self.toggle_action.setText(
                self._("Resume") if self.paused else self._("Pause")
            )
        logging.debug("App is paused" if self.paused else "App is resumed")

    @staticmethod
    def apply_dark_mode_styles(menu) -> None:
        """
        Apply styles to the tray menu based on current color mode.
        """
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        is_dark_mode = current_mode == "dark"
        palette = menu.palette()

        if is_dark_mode:
            logging.debug("Tray icon dark")
            # Dark mode colors
            palette.setColor(
                QtGui.QPalette.ColorRole.Window, QtGui.QColor("#2d2d2d")
            )  # Dark background
            palette.setColor(
                QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#ffffff")
            )  # White text
        else:
            logging.debug("Tray icon light")
            # Light mode colors
            palette.setColor(
                QtGui.QPalette.ColorRole.Window, QtGui.QColor("#ffffff")
            )  # Light background
            palette.setColor(
                QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#000000")
            )  # Black text

        menu.setPalette(palette)

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

    def process_followup_question(
        self, response_window: ResponseWindow, question: str
    ) -> None:
        """
        Process a follow-up question in the chat window.
        """
        logging.debug(f"Processing follow-up question: {question}")

        def process_thread():
            logging.debug("Starting follow-up processing thread")
            try:
                if not response_window.chat_history:
                    logging.error("No chat history found")
                    self.show_message_signal.emit("Error", "Chat history not found")
                    return

                # Add current question to chat history
                response_window.chat_history.append({"role": "user", "content": question})

                # Get chat history
                history = response_window.chat_history.copy()

                # System instruction based on original option
                system_instruction = "You are a helpful AI assistant. Provide clear and direct responses, maintaining the same format and style as your previous responses. If appropriate, use Markdown formatting to make your response more readable."

                logging.debug("Sending request to AI provider")

                # Format conversation differently based on provider
                if self.current_provider and isinstance(
                    self.current_provider, GeminiProvider
                ):
                    # For Gemini, use the proper history format with roles
                    chat_messages = []

                    # Convert our roles to Gemini's expected roles
                    for msg in history:
                        gemini_role = "model" if msg["role"] == "assistant" else "user"
                        chat_messages.append(
                            {"role": gemini_role, "parts": msg["content"]}
                        )

                    # Start chat with history
                    if (
                        hasattr(self.current_provider, "model")
                        and self.current_provider.model
                    ):
                        chat = self.current_provider.model.start_chat(
                            history=chat_messages
                        )

                        # Get response using the chat
                        response = chat.send_message(question)
                        if response and hasattr(response, 'parts') and response.parts:
                            response_text = response.text
                        else:
                            response_text = "Error: No valid response generated"
                    else:
                        response_text = "Error: Provider model not available"

                elif self.current_provider and isinstance(
                    self.current_provider, OllamaProvider
                ):
                    # For Ollama, prepare messages with system instruction and history
                    messages = [{"role": "system", "content": system_instruction}]

                    for msg in history:
                        messages.append({"role": msg["role"], "content": msg["content"]})

                    # Get response from Ollama
                    response_text = self.current_provider.get_response(
                        system_instruction,
                        messages,
                        return_response=True,
                    )

                elif self.current_provider:
                    # For OpenAI/compatible providers, prepare messages array, add system message
                    messages = [{"role": "system", "content": system_instruction}]

                    # Add history messages (including latest question)
                    for msg in history:
                        # Convert 'assistant' role to 'assistant' for OpenAI
                        role = "assistant" if msg["role"] == "assistant" else "user"
                        messages.append({"role": role, "content": msg["content"]})

                    # Get response by passing the full messages array
                    response_text = self.current_provider.get_response(
                        system_instruction,
                        messages if isinstance(messages, str) else str(messages),
                        return_response=True,
                    )
                else:
                    response_text = "Error: No provider available"

                logging.debug(f"Got response of length: {len(response_text)}")

                # Add response to chat history
                response_window.chat_history.append(
                    {"role": "assistant", "content": response_text}
                )

                # Emit response via signal
                self.followup_response_signal.emit(response_text)

            except Exception as e:
                logging.error(f"Error processing follow-up question: {e}", exc_info=True)

                if "Resource has been exhausted" in str(e):
                    self.show_message_signal.emit(
                        "Error - Rate Limit Hit",
                        "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
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
            and (current_time - self.last_tray_click_time) < self.tray_click_debounce_ms
        ):
            logging.debug("Settings click ignored due to debounce protection")
            return

        self.last_tray_click_time = current_time

        logging.debug("Showing settings window")
        # Always create a new settings window to handle providers_only correctly
        self.settings_window = ui.SettingsWindow.SettingsWindow(
            self, providers_only=providers_only
        )

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
        logging.debug("Showing about window")
        if not self.about_window:
            self.about_window = ui.AboutWindow.AboutWindow()
        self.about_window.show()

    # ============================================================================
    # APPLICATION LIFECYCLE METHODS
    # ============================================================================

    def setup_ctrl_c_listener(self) -> None:
        """
        Listener for Ctrl+C to exit the app.
        """
        signal.signal(
            signal.SIGINT, lambda signum, frame: self.handle_sigint(signum, frame)
        )
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
        logging.info("Received SIGINT. Exiting...")
        self.exit_app()

    def exit_app(self) -> None:
        """
        Exit the application.
        """
        logging.debug("Stopping the listener")
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        logging.debug("Restoring default SIGINT handler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        logging.debug("Exiting application")
        self.quit()
