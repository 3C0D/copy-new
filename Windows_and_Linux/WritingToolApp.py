import gettext
import logging
import os
import signal
import sys
import threading
import time

import darkdetect
import pyperclip
from pynput import keyboard as pykeyboard
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import QLocale, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication
from PySide6.QtWidgets import QApplication, QMessageBox

import ui.AboutWindow
import ui.CustomPopupWindow
import ui.NonEditableModal
import ui.OnboardingWindow
import ui.ResponseWindow
import ui.SettingsWindow
from aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)
from config.settings import SettingsManager
from ui.ui_utils import get_icon_path
from update_checker import UpdateChecker

_ = gettext.gettext


class WritingToolApp(QtWidgets.QApplication):
    """
    The main application class for Writing Tools.
    """

    output_ready_signal = Signal(str)
    show_message_signal = Signal(str, str)  # a signal for showing message boxes
    hotkey_triggered_signal = Signal()
    followup_response_signal = Signal(str)

    def __init__(self, argv, theme_override=None):
        super().__init__(argv)
        self.current_response_window = None
        self.theme_override = theme_override
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing WritingToolApp")

        # Apply theme override if specified
        if theme_override and theme_override != "auto":
            self._apply_theme_override(theme_override)
        self.output_ready_signal.connect(self.replace_text)
        self.show_message_signal.connect(self.show_message_box)
        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)

        # Initialize unified settings manager with mode detection
        mode = self._detect_mode()
        self.settings_manager = SettingsManager(mode=mode)
        self.load_settings()

        self.onboarding_window = None
        self.popup_window = None
        self.tray_icon = None
        self.tray_menu = None
        self.settings_window = None
        self.about_window = None
        self.registered_hotkey = None
        self.output_queue = ""
        self.last_replace = 0
        self.hotkey_listener = None
        self.paused = False
        self.toggle_action = None
        self.non_editable_modal = None  # Keep reference to modal window

        self._ = gettext.gettext

        # Initialize the ctrl+c hotkey listener
        self.ctrl_c_timer = None
        self.setup_ctrl_c_listener()

        # Setup available AI providers
        self.providers = [
            GeminiProvider(self),
            OpenAICompatibleProvider(self),
            OllamaProvider(self),
            AnthropicProvider(self),
            MistralProvider(self),
        ]

        # Check if this is a first launch (no providers configured)
        if not self.settings_manager.has_providers_configured():
            self._logger.debug("First launch detected (no providers configured), showing onboarding")
            self.show_onboarding()
        else:
            self._logger.debug("Providers configured, setting up hotkey and tray icon")

            # else pylance is not happy
            assert self.settings_manager.settings

            try:
                # Initialize the current provider, defaulting to Gemini
                provider_name = self.settings_manager.settings.system.get("provider", "gemini")
                self._logger.debug(f"Selected provider: {provider_name}")

                # # Map provider names to actual provider_name in classes
                # provider_mapping = {
                #     "Gemini": "Gemini (Recommended)",
                #     "OpenAI": "OpenAI-Compatible",
                #     "Ollama": "Ollama (Local)",
                #     "Anthropic": "Anthropic (Claude)",
                #     "Mistral": "Mistral AI",
                # }

                # actual_provider_name = provider_mapping.get(
                #     provider_name, provider_name
                # )
                # self._logger.debug(f"Mapped provider name: {actual_provider_name}")

                self.current_provider = next(
                    (
                        provider
                        for provider in self.providers
                        # if provider.provider_name == actual_provider_name
                        if provider.provider_name == provider_name
                    ),
                    None,
                )
                if not self.current_provider:
                    self._logger.warning(f"Provider {provider_name} not found. Using default provider.")
                    self.current_provider = self.providers[0]

                self._logger.debug(f"Current provider: {self.current_provider.provider_name}")

                # Load provider-specific config from system settings
                provider_config = self._get_provider_config(provider_name)
                self._logger.debug(f"Provider config: {provider_config}")
                self.current_provider.load_config(provider_config)
                self._logger.debug("Provider config loaded successfully")

                self.create_tray_icon()
                self.register_hotkey()

                # Set language from system settings
                lang = self.settings_manager.settings.system.get("language","en")
                self.change_language(lang if lang != "en" else None)

                # Initialize update checker
                self.update_checker = UpdateChecker(self)
                self.update_checker.check_updates_async()

            except Exception as e:
                logging.exception(f"Error during app initialization: {e}")
                logging.exception("Falling back to onboarding")
                import traceback

                logging.debug(f"Full traceback: {traceback.format_exc()}")
                # If there's an error, show onboarding as fallback (silent recovery)
                self.show_onboarding()

        self.recent_triggers = []  # Track recent hotkey triggers
        self.TRIGGER_WINDOW = 1.5  # Time window in seconds
        self.MAX_TRIGGERS = 3  # Max allowed triggers in window

    def _apply_theme_override(self, theme):
        """Apply theme override to the application"""
        from ui.ui_utils import set_color_mode

        set_color_mode(theme)

    def _detect_mode(self) -> str:
        """
        Detect the operating mode based on the environment.

        Returns:
            str: "dev", "build-dev", or "build-final"
        """
        if not getattr(sys, "frozen", False):
            # Running as script
            return "dev"
        # Running as compiled executable
        # Check if data.json exists in the same directory (build-final)
        # or if data_dev.json exists (build-dev)
        base_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(base_dir, "data.json")):
            return "build-final"
        if os.path.exists(os.path.join(base_dir, "data_dev.json")):
            return "build-dev"
        return "build-dev"  # fallback

    def setup_translations(self, lang=None):
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
        # Update the translation function for all UI components.
        self._ = translation.gettext
        ui.AboutWindow._ = self._
        ui.SettingsWindow._ = self._
        ui.ResponseWindow._ = self._
        ui.OnboardingWindow._ = self._
        ui.CustomPopupWindow._ = self._

    def retranslate_ui(self):
        self.update_tray_menu()

    def change_language(self, lang):
        self.setup_translations(lang)
        self.retranslate_ui()

        # Update all other windows
        for widget in QApplication.topLevelWidgets():
            if widget != self and hasattr(widget, "retranslate_ui"):
                widget.retranslate_ui()  # type: ignore

    def check_trigger_spam(self):
        """
        Check if hotkey is being triggered too frequently (3+ times in 1.5 seconds).
        Returns True if spam is detected.
        """
        current_time = time.time()

        # Add current trigger
        self.recent_triggers.append(current_time)

        # Remove old triggers outside the window
        self.recent_triggers = [t for t in self.recent_triggers if current_time - t <= self.TRIGGER_WINDOW]

        # Check if we have too many triggers in the window
        return len(self.recent_triggers) >= self.MAX_TRIGGERS

    def load_settings(self):
        """
        Load unified settings using the SettingsManager.
        Handles migration from legacy config.json and options.json files.
        """
        # Load the unified settings (no legacy migration needed)
        self.settings_manager.load_settings()
        self._logger.debug("Unified settings loaded successfully")

    def save_settings(self):
        """
        Save the current unified settings.
        """
        return self.settings_manager.save_settings()

    def _get_provider_config(self, provider_name: str) -> dict:
        """
        Extract provider-specific configuration from custom_data.

        Args:
            provider_name: Name of the provider

        Returns:
            dict: Provider-specific configuration
        """
        if self.settings_manager.settings is None:
            return {}

        system = self.settings_manager.settings.system
        if system is None:
            return {}

        # Check if there's saved provider config in custom_data
        custom_data = self.settings_manager.settings.custom_data
        providers_data = custom_data.get("providers", {})
        saved_config = providers_data.get(provider_name, {})

        # Provide default config based on provider type with system settings where applicable
        if provider_name in {"Gemini", "Gemini (Recommended)"}:
            config = {"api_key": "", "model": system.get("model", "")}
        elif provider_name in {"Ollama", "Ollama (Local)", "Ollama (For Experts)"}:
            config = {
                "base_url": system.get("ollama_base_url", "http://localhost:11434"),
                "model": "",
                "keep_alive": system.get("ollama_keep_alive", "5"),
            }
        elif provider_name in {"Mistral", "Mistral AI"}:
            config = {
                "api_key": "",
                "api_model": "",
                "base_url": system.get("mistral_base_url", "https://api.mistral.ai/v1"),
            }
        elif provider_name in {"Anthropic", "Anthropic (Claude)"}:
            config = {"api_key": "", "model": ""}
        elif provider_name in {"OpenAI", "OpenAI-Compatible"}:
            config = {
                "api_key": "",
                "base_url": system.get("openai_base_url", "https://api.openai.com/v1"),
                "model": "",
            }
        else:
            config = {}

        # Override with saved config
        config.update(saved_config)
        return config

    def show_onboarding(self):
        """
        Show the onboarding window for first-time users.
        """
        self._logger.debug("Showing onboarding window")
        self.onboarding_window = ui.OnboardingWindow.OnboardingWindow(self)
        self.onboarding_window.close_signal.connect(self.on_onboarding_closed)
        self.onboarding_window.show()

    def on_onboarding_closed(self):
        """
        Handle onboarding window being closed.
        Instead of exiting, continue with normal app initialization.
        """
        self._logger.debug("Onboarding window closed, continuing with app initialization")

        # Initialize the current provider with default settings
        if self.settings_manager.settings is None or self.settings_manager.settings.system is None:
            provider_name = "Gemini"
        else:
            # Use safe access for TypedDict
            provider_name = self.settings_manager.settings.system.get("provider", "gemini")

        if not provider_name or provider_name.strip() == "":
            # Default to Gemini if no provider is set
            provider_name = "Gemini"
            self.settings_manager.update_system_setting("provider", provider_name)

        # Map provider names to actual provider_name in classes
        provider_mapping = {
            "Gemini": "Gemini (Recommended)",
            "OpenAI": "OpenAI-Compatible",
            "Ollama": "Ollama (Local)",
            "Anthropic": "Anthropic (Claude)",
            "Mistral": "Mistral AI",
        }
        actual_provider_name = provider_mapping.get(provider_name, provider_name)

        self.current_provider = next(
            (provider for provider in self.providers if provider.provider_name == actual_provider_name),
            self.providers[0],  # Default to first provider
        )

        # Load provider-specific config from system settings
        provider_config = self._get_provider_config(provider_name)
        self.current_provider.load_config(provider_config)

        self.create_tray_icon()
        self.register_hotkey()

        # Set language from system settings
        if self.settings_manager.settings is not None and self.settings_manager.settings.system is not None:
            lang = self.settings_manager.settings.system.get("language", "en")
            self.change_language(lang if lang != "en" else None)

        # Initialize update checker
        self.update_checker = UpdateChecker(self)
        self.update_checker.check_updates_async()

    def start_hotkey_listener(self):
        """
        Create listener for hotkeys on Linux/Mac.
        """
        if self.settings_manager.settings is None or self.settings_manager.settings.system is None:
            return

        orig_shortcut = self.settings_manager.settings.system.get("hotkey", "ctrl+space")
        # Parse the shortcut string, for example ctrl+alt+h -> <ctrl>+<alt>+<h>. Space are removed.
        shortcut = "+".join(
            [f"{t}" if len(t) <= 1 else f"<{t}>" for t in [part.strip() for part in orig_shortcut.split("+")]],
        )
        self._logger.debug(f"Registering global hotkey for shortcut: {shortcut}")
        try:
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()

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
                return lambda k: f(self.hotkey_listener.canonical(k))

            # Create a listener and store it as an attribute to stop it later
            self.hotkey_listener = pykeyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release),
            )

            # Start the listener
            self.hotkey_listener.start()
        except Exception as e:
            self._logger.error(f"Failed to register hotkey: {e}")

    def register_hotkey(self):
        """
        Register the global hotkey for activating Writing Tools.
        """
        self._logger.debug("Registering hotkey")
        self.start_hotkey_listener()
        self._logger.debug("Hotkey registered")

    def on_hotkey_pressed(self):
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
        QtCore.QMetaObject.invokeMethod(self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection)

    @Slot()
    def _show_popup(self):
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

        self._logger.debug(f'Selected text: "{selected_text}"')
        try:
            if self.popup_window is not None:
                self._logger.debug("Existing popup window found")
                if self.popup_window.isVisible():
                    self._logger.debug("Closing existing visible popup window")
                    self.popup_window.close()
                self.popup_window = None
            self._logger.debug("Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self, selected_text)

            # Set the window icon
            icon_path = get_icon_path("app_icon", with_theme=False)
            if os.path.exists(icon_path):
                self.setWindowIcon(QtGui.QIcon(icon_path))
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

    def get_selected_text(self, sleep_duration=0.2):
        """
        Get the currently selected text from any application.
        Args:
            sleep_duration (float): Time to wait for clipboard update
        """
        # Backup the clipboard
        clipboard_backup = pyperclip.paste()
        self._logger.debug(f'Clipboard backup: "{clipboard_backup}" (sleep: {sleep_duration}s)')

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

    @staticmethod
    def clear_clipboard():
        """
        Clear the system clipboard.
        """
        try:
            pyperclip.copy("")
        except Exception as e:
            self._logger.error(f"Error clearing clipboard: {e}")

    def process_option(self, option, selected_text, custom_change=None):
        """
        Process the selected writing option in a separate thread.
        """
        self._logger.debug(f"Processing option: {option}")

        action_config = self.settings_manager.settings.actions.get(option)
        if not action_config:
            self._logger.error(f"Action not found: {option}")
            return

        if (is_empty_custom := option == "Custom" and not selected_text.strip()) or action_config.open_in_window:
            self._setup_response_window(is_empty_custom, option, selected_text)
        elif hasattr(self, "current_response_window"):
            delattr(self, "current_response_window")

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, custom_change),
            daemon=True,
        ).start()

    def _setup_response_window(self, is_empty_custom, option, selected_text):
        window_title = "Chat" if is_empty_custom else option
        self.current_response_window = self.show_response_window(window_title, selected_text)

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

    def process_option_thread(self, option, selected_text, custom_change=None):
        """
        Thread function to process the selected writing option using the AI model.

        Args:
            option: The selected writing option
            selected_text: The text selected by the user
            custom_change: Optional custom change description
        """
        self._logger.debug(f"Starting processing thread for option: {option}")

        try:
            # Initialize variables
            has_selected_text = selected_text.strip() != ""
            is_custom_option = option == "Custom"

            # Handle case where no text is selected
            if not has_selected_text:
                if is_custom_option:
                    # Custom option without text: use custom_change as prompt
                    prompt = custom_change
                    system_instruction = "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable."
                else:
                    # Non-custom option requires selected text
                    self.show_message_signal.emit("Error", "Please select text to use this option.")
                    return
            else:
                # Text is selected: get action configuration
                action_config = self.settings_manager.settings.actions.get(option)
                if not action_config:
                    self._logger.error(f"Action not found: {option}")
                    return

                # Build prompt based on option type
                prompt_prefix = action_config.prefix
                system_instruction = action_config.instruction

                if is_custom_option:
                    prompt = f"{prompt_prefix}Described change: {custom_change}\n\nText: {selected_text}"
                else:
                    prompt = f"{prompt_prefix}{selected_text}"

            # Initialize output queue
            self.output_queue = ""

            # Get action config for window display check

            # if has_selected_text:
            action_config = self.settings_manager.settings.actions.get(option)
            if not action_config:
                self._logger.error(f"Action not found: {option}")
                return

            # Determine if response should be displayed in window
            should_open_window = (is_custom_option and not has_selected_text) or (
                has_selected_text and action_config.open_in_window
            )

            self._logger.debug(f"Getting response from provider for option: {option}")

            if should_open_window:
                # Get response for window display
                self._logger.debug("Getting response for window display")
                response = self.current_provider.get_response(system_instruction, prompt, return_response=True)
                self._logger.debug(f"Got response of length: {len(response) if response else 0}")

                # Add user message to chat history for custom prompts without text
                if is_custom_option and not has_selected_text:
                    self.current_response_window.chat_history.append({"role": "user", "content": custom_change})

                # Update window with response (thread-safe)
                if hasattr(self, "current_response_window"):
                    QtCore.QMetaObject.invokeMethod(
                        self.current_response_window,
                        "set_text",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        QtCore.Q_ARG(str, response),
                    )
                    self._logger.debug("Invoked set_text on response window")
            else:
                # Get response for direct text replacement
                self._logger.debug("Getting response for direct replacement")
                self.current_provider.get_response(system_instruction, prompt)
                self._logger.debug("Response processed")

        except Exception as e:
            self._logger.error(f"An error occurred: {e}", exc_info=True)

            # Handle specific error types
            if "Resource has been exhausted" in str(e):
                self.show_message_signal.emit(
                    "Error - Rate Limit Hit",
                    "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
                )
            else:
                self.show_message_signal.emit("Error", f"An error occurred: {e}")

    @Slot(str, str)
    def show_message_box(self, title, message):
        """
        Show a message box with the given title and message.
        For API errors, adds a button to open settings.
        """
        msg_box = QMessageBox(None)
        msg_box.setWindowFlags(msg_box.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Add standard 'OK' button
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        # For API errors, add a button to open settings
        settings_button = None
        if any(keyword in title.lower() for keyword in ["api", "key", "quota", "rate limit", "connection"]):
            settings_button = msg_box.addButton("Open Settings", QMessageBox.ButtonRole.ActionRole)

        # Show the message box
        msg_box.exec()

        # If settings button was clicked, open settings
        if settings_button and msg_box.clickedButton() == settings_button:
            self.show_settings()

    def show_response_window(self, option, text):
        """
        Show the response in a new window instead of pasting it.
        """
        response_window = ui.ResponseWindow.ResponseWindow(self, f"{option} Result")
        response_window.selected_text = text  # Store the text for regeneration
        response_window.show()
        return response_window

    @Slot(str)
    def replace_text(self, new_text):
        """
        Replaces the text by pasting in the LLM generated text. With "Key Points" and "Summary", invokes a window with the output instead.
        If pasting fails (non-editable page), shows the text in a modal window.
        """
        error_message = "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"

        # Confirm new_text exists and is a string
        if new_text and isinstance(new_text, str):
            self.output_queue += new_text
            current_output = self.output_queue.strip()  # Strip whitespace for comparison

            # If the new text is the error message, show a message box
            if current_output == error_message:
                self.show_message_signal.emit("Error", "The text is incompatible with the requested change.")
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
                if hasattr(self, "current_response_window"):
                    self.current_response_window.append_text(new_text)

                    # If this is the initial response, add it to chat history
                    if len(self.current_response_window.chat_history) == 1:  # Only original text exists
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
                        logging.debug("Paste failed - showing modal window for non-editable page")
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
    def _show_non_editable_modal(self, transformed_text):
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
            self.non_editable_modal = ui.NonEditableModal.NonEditableModal(self, transformed_text)

            # Connect close event to clean up reference
            self.non_editable_modal.finished.connect(self._on_modal_closed)

            # Show the modal (use exec() to make it truly modal and keep it open)
            self.non_editable_modal.exec()

        except Exception as e:
            logging.error(f"Error showing non-editable modal: {e}", exc_info=True)

    @QtCore.Slot()
    def _on_modal_closed(self):
        """Clean up modal reference when it's closed"""
        self.non_editable_modal = None

    # def process_text_with_option(self, option, text):
    #     """
    #     Process text with the given option. Used by NonEditableModal for chaining actions.
    #     """
    #     try:
    #         logging.debug(f"Processing text with option: {option}")
    #         # Store the text as selected text
    #         self.selected_text = text

    #         # Process the text with the selected option
    #         if option in ["Key Points", "Summary"]:
    #             # For these options, show response window
    #             self.show_response_window(option, text)
    #         else:
    #             # For other options, process normally
    #             self.process_text(option)

    #     except Exception as e:
    #         logging.error(f"Error processing text with option {option}: {e}")

    def create_tray_icon(self):
        """
        Create the system tray icon for the application.
        """
        if self.tray_icon:
            logging.debug("Tray icon already exists")
            return

        logging.debug("Creating system tray icon")

        icon_path = get_icon_path("app_icon", with_theme=False)
        if not os.path.exists(icon_path):
            logging.warning(f"Tray icon not found at {icon_path}")
            # Use a default icon if not found
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)
        else:
            self.tray_icon = QtWidgets.QSystemTrayIcon(QtGui.QIcon(icon_path), self)
        # Set the tooltip (hover name) for the tray icon
        self.tray_icon.setToolTip("WritingTools")
        self.tray_menu = QtWidgets.QMenu()
        self.tray_icon.setContextMenu(self.tray_menu)

        self.update_tray_menu()
        self.tray_icon.show()
        logging.debug("Tray icon displayed")

    def update_tray_menu(self):
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
        self.toggle_action = self.tray_menu.addAction(self._("Resume") if self.paused else self._("Pause"))
        self.toggle_action.triggered.connect(self.toggle_paused)

        # About menu item
        about_action = self.tray_menu.addAction(self._("About"))
        about_action.triggered.connect(self.show_about)

        # Exit menu item
        exit_action = self.tray_menu.addAction(self._("Exit"))
        exit_action.triggered.connect(self.exit_app)

    def toggle_paused(self):
        """Toggle the paused state of the application."""
        logging.debug("Toggle paused state")
        self.paused = not self.paused
        if self.toggle_action is not None:
            self.toggle_action.setText(self._("Resume") if self.paused else self._("Pause"))
        logging.debug("App is paused" if self.paused else "App is resumed")

    @staticmethod
    def apply_dark_mode_styles(menu):
        """
        Apply styles to the tray menu based on system theme using darkdetect.
        """
        is_dark_mode = darkdetect.isDark()
        palette = menu.palette()

        if is_dark_mode:
            logging.debug("Tray icon dark")
            # Dark mode colors
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#2d2d2d"))  # Dark background
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#ffffff"))  # White text
        else:
            logging.debug("Tray icon light")
            # Light mode colors
            palette.setColor(QtGui.QPalette.ColorRole.Window, QtGui.QColor("#ffffff"))  # Light background
            palette.setColor(QtGui.QPalette.ColorRole.WindowText, QtGui.QColor("#000000"))  # Black text

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

    def process_followup_question(self, response_window, question):
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
                if isinstance(self.current_provider, GeminiProvider):
                    # For Gemini, use the proper history format with roles
                    chat_messages = []

                    # Convert our roles to Gemini's expected roles
                    for msg in history:
                        gemini_role = "model" if msg["role"] == "assistant" else "user"
                        chat_messages.append({"role": gemini_role, "parts": msg["content"]})

                    # Start chat with history
                    chat = self.current_provider.model.start_chat(history=chat_messages)

                    # Get response using the chat
                    response = chat.send_message(question)
                    response_text = response.text

                elif isinstance(self.current_provider, OllamaProvider):
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

                else:
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
                        messages,  # Pass messages array directly
                        return_response=True,
                    )

                logging.debug(f"Got response of length: {len(response_text)}")

                # Add response to chat history
                response_window.chat_history.append({"role": "assistant", "content": response_text})

                # Emit response via signal
                self.followup_response_signal.emit(response_text)

            except Exception as e:
                logging.error(f"Error processing follow-up question: {e}", exc_info=True)

                if "Resource has been exhausted" in str(e):
                    self.show_message_signal.emit(
                        "Error - Rate Limit Hit",
                        "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
                    )
                    self.followup_response_signal.emit("Sorry, an error occurred while processing your question.")
                else:
                    self.show_message_signal.emit("Error", f"An error occurred: {e}")
                    self.followup_response_signal.emit("Sorry, an error occurred while processing your question.")

        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()

    def show_settings(self, providers_only=False, previous_window=None):
        """
        Show the settings window.
        """
        logging.debug("Showing settings window")
        # Always create a new settings window to handle providers_only correctly
        self.settings_window = ui.SettingsWindow.SettingsWindow(self, providers_only=providers_only)

        # Set reference to previous window for navigation
        if previous_window:
            self.settings_window.previous_window = previous_window

        self.settings_window.close_signal.connect(self.exit_app)
        self.settings_window.retranslate_ui()
        self.settings_window.show()

    def show_about(self):
        """
        Show the about window.
        """
        logging.debug("Showing about window")
        if not self.about_window:
            self.about_window = ui.AboutWindow.AboutWindow()
        self.about_window.show()

    def setup_ctrl_c_listener(self):
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

    def handle_sigint(self, signum, frame):
        """
        Handle the SIGINT signal (Ctrl+C) to exit the app gracefully.
        """
        logging.info("Received SIGINT. Exiting...")
        self.exit_app()

    def exit_app(self):
        """
        Exit the application.
        """
        logging.debug("Stopping the listener")
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        logging.debug("Exiting application")
        self.quit()
