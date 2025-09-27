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
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from pynput import keyboard as keyboard
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QLocale, Signal, Slot
from PySide6.QtWidgets import QApplication, QMessageBox

from .aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)

# ResponseWindow already imported above
# Removed duplicate imports
from .AutostartManager import AutostartManager
from .config.settings import SettingsManager
from .core.ai_processor import AIProcessor
from .core.image_processor import ImageProcessor
from .core.popup_manager import PopupManager
from .systray import SystrayManager
from .ui import (
    AboutWindow,
    CustomPopupWindow,
    HelpWindow,
    NonEditableModal,
    OnboardingWindow,
    SettingsWindow,
)
from .ui.LanguageManager import LanguageManager
from .ui.ResponseWindow import ResponseWindow
from .ui.ThemeManager import ThemeManager
from .update_checker import UpdateChecker

if TYPE_CHECKING:
    from .aiprovider import AIProvider

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
            self._setup_hotkey_system()

            self._logger.debug("Setting up AI providers...")
            self._setup_ai_providers()

            self._logger.debug("Setting up spam protection...")
            self._setup_spam_protection()

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
        self.current_provider: AIProvider | None = None
        self.output_queue = ""
        self.ai_processor = AIProcessor(self)
        self.systray_manager = SystrayManager(self)
        self.image_processor = ImageProcessor(self._logger)
        self.popup_manager = PopupManager(self, self._logger)

    def _setup_signals(self) -> None:
        """Connect application signals to their handlers."""
        self.output_ready_signal.connect(self.replace_text)
        self.show_message_signal.connect(self.show_message_box)
        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)

    def _setup_settings(self) -> None:
        """Initialize settings manager and load configuration."""
        mode = self._detect_running_mode()
        self._logger.debug(f"Running mode: {mode}")
        self.settings_manager = SettingsManager(mode=mode)
        self.load_settings()

    def _setup_ui_components(self) -> None:
        """Initialize UI component references."""
        self.onboarding_window = None
        self.tray_icon = None
        self.settings_window = None
        self.non_editable_modal = None
        self.theme_manager = ThemeManager(self)
        self.language_manager = LanguageManager(self)
        self.styles = self.theme_manager.get_styles()

    def _setup_hotkey_system(self) -> None:
        """Initialize hotkey and keyboard listener system."""
        self.hotkey_listener = None
        self.ctrl_c_timer = None
        self.setup_ctrl_c_listener()

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
        self.ai_processor.set_current_provider()

        if self.ai_processor.current_provider:
            self._logger.debug(
                f"Current provider: {self.ai_processor.current_provider.provider_name}"
            )
            provider_config = self.ai_processor.get_provider_config(self.settings_manager.provider)
            self._logger.debug(f"Provider config: {provider_config}")
            self.ai_processor.current_provider.load_config(provider_config)
            self._logger.debug("Provider config loaded successfully")

        # Keep the reference for compatibility
        self.current_provider = self.ai_processor.current_provider

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

    def setup_translations(self, lang=None) -> None:
        """Setup application translations for the specified language."""
        if not lang:
            lang = QLocale.system().name().split("_")[0]

        try:
            locales_dir = Path(__file__).parent.parent / "locales"
            translation = gettext.translation(
                "messages",
                localedir=str(locales_dir),
                languages=[lang],
            )
        except FileNotFoundError:
            translation = gettext.NullTranslations()

        translation.install()
        self._update_translation_functions(translation)

    def _update_translation_functions(self, translation: gettext.NullTranslations) -> None:
        """Update translation functions for all UI components."""
        self._ = translation.gettext
        AboutWindow._ = self._
        SettingsWindow._ = self._
        ResponseWindow._ = self._  # type: ignore
        OnboardingWindow._ = self._
        CustomPopupWindow._ = self._
        HelpWindow._ = self._

    def retranslate_ui(self) -> None:
        """Retranslate the user interface elements."""
        self.systray_manager.update_tray_menu()

    def change_language(self, lang: str) -> None:
        """Change the application language and update all UI elements."""
        self.language_manager.change_language(lang)

    def _update_widget_translations(self) -> None:
        """Update translations for all top-level widgets."""
        for widget in QApplication.topLevelWidgets():
            if widget != self and hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()  # type: ignore

    def load_settings(self) -> None:
        """Load unified settings using the SettingsManager."""
        self.settings_manager.load_settings()
        self._logger.debug("Unified settings loaded successfully")

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

    def show_onboarding(self) -> None:
        """
        Show the onboarding window for first-time users.
        """
        self._logger.debug("Showing onboarding window")

        self.onboarding_window = OnboardingWindow.OnboardingWindow(self)
        self.onboarding_window.close_signal.connect(self.on_onboarding_closed)
        self.onboarding_window.show()

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
        self.register_hotkey()

        # Set language from system settings
        lang = self.settings_manager.language or "en"
        self.change_language(lang if lang != "en" else "en")

        # Initialize update checker
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()

    def get_current_model(self, provider_name: str) -> str:
        provider = self.settings_manager.providers.get(provider_name, {})
        return provider.get("api_model", "")

    # ============================================================================
    # HOTKEY MANAGEMENT METHODS
    # ============================================================================

    def start_hotkey_listener(self) -> None:
        """
        Create listener for hotkeys on Linux/Mac.
        """
        orig_shortcut = self.settings_manager.hotkey or "ctrl+space"

        # Parse the shortcut string, for example ctrl+alt+h -> <ctrl>+<alt>+<h>. Space are removed.
        shortcut = "+".join([f"<{t.strip()}>" for t in orig_shortcut.split("+")])

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
        if hasattr(self, "popup_manager") and self.popup_manager.popup_window is not None:
            self._logger.debug("Closing existing popup window")
            self.popup_manager.popup_window.close()
            self.popup_manager.popup_window = None

        # Close existing response window if open
        if hasattr(self, "current_response_window") and self.current_response_window is not None:
            self._logger.debug("Closing existing response window")
            self.current_response_window.close()
            self.current_response_window = None

        # Original hotkey handling continues...
        if self.ai_processor.current_provider:
            self._logger.debug("Cancelling current provider's request")
            self.ai_processor.current_provider.cancel()
            self.ai_processor.output_queue = ""

        # noinspection PyTypeChecker
        QtCore.QMetaObject.invokeMethod(
            self.popup_manager, "show_popup", QtCore.Qt.ConnectionType.QueuedConnection
        )

    def process_option(
        self,
        option: str,
        selected_text: str | None,
        force_chat: bool = False,
        custom_change: str | None = None,
        image: QtGui.QImage | None = None,
    ) -> None:
        """Delegate to AI processor."""
        self.ai_processor.process_option(option, selected_text, force_chat, custom_change, image)

    # ============================================================================
    # AI PROCESSING METHODS
    # ============================================================================

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
        if self.popup_manager.has_image and self.popup_manager.image:
            response_window.image = self.popup_manager.image
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
                new_selection = self.popup_manager.get_selected_text(sleep_duration=0.1)

                # If selection is the same, paste failed (non-editable page)
                if (
                    self.popup_manager.original_selection == new_selection
                    and self.popup_manager.original_selection
                    and self.popup_manager.original_selection.strip()
                ):
                    # Fallback to modal window for non-editable pages
                    cleaned_text = self.output_queue.rstrip("\n")
                    QtCore.QMetaObject.invokeMethod(
                        self,
                        "_show_non_editable_modal",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, cleaned_text),
                    )
                self.popup_manager.original_selection = None
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
            self.non_editable_modal = NonEditableModal.NonEditableModal(self, transformed_text)
            self.non_editable_modal.close_signal.connect(self._on_non_editable_modal_closed)
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
        """Delegate to AI processor."""
        self.ai_processor.process_followup_question(response_window, question)

    def show_settings(self, providers_only: bool = False, previous_window=None) -> None:
        """
        Show the settings window with debounce protection against rapid clicks.
        """
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

        if self.settings_window:
            self.settings_window.close()

        # Always create a new settings window to handle providers_only correctly
        self.settings_window = SettingsWindow.SettingsWindow(self, providers_only=providers_only)

        # Set reference to previous window for navigation
        if previous_window:
            self.settings_window.previous_window = previous_window

        self.settings_window.close_signal.connect(self.exit_app)
        self.settings_window.retranslate_ui()
        self.settings_window.show()

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
