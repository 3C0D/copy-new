"""
AI Provider Architecture for Writing Tools
--------------------------------------------

This module handles different AI model providers (Gemini, OpenAI, OpenAI-compatible, Ollama, Anthropic, Mistral)
and manages their interactions with the main application. It uses an abstract base class pattern for
provider implementations.

Key Components:
1. AIProviderSetting - Base class for provider settings (e.g. API keys, model names)
    • TextSetting      - A simple text input for settings
    • DropdownSetting  - A dropdown selection setting

2. AIProvider - Abstract base class that all providers implement.
   It defines the interface for:
      • Getting a response from the AI model
      • Loading and saving configuration settings
      • Cancelling an ongoing request

3. Provider Implementations:
    • GeminiProvider - Uses Google’s Generative AI API (Gemini) to generate content.
    • OpenAIProvider - Connects to the official OpenAI API.
    • OpenAICompatibleProvider - Connects to any OpenAI-compatible API (v1/chat/completions)
    • OllamaProvider - Connects to a locally running Ollama server (e.g. for llama.cpp)
    • AnthropicProvider - Uses Anthropic's Claude API
    • MistralProvider - Uses Mistral AI API

Response Flow:
   • The main app calls get_response() with a system instruction and a prompt.
   • The provider formats and sends the request to its API endpoint.
   • For operations that require a window (e.g. Summary, Key Points), the provider returns the full text.
   • For direct text replacement, the provider emits the full text via the output_ready_signal.
   • Conversation history (for follow-up questions) is maintained by the main app.

"""

# Disable Pylance reportPrivateImportUsage for google.generativeai
# pyright: reportPrivateImportUsage=false

# Standard library imports
import logging
from abc import ABC, abstractmethod
from concurrent.futures import CancelledError, ThreadPoolExecutor
from typing import TYPE_CHECKING, Callable, Union, cast

# Third-party imports (with fallbacks for optional dependencies)
# PySide6 imports
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

# Google Generative AI imports (with fallbacks)
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmBlockThreshold, HarmCategory
except ImportError:
    # Fallback for type checking
    genai = None  # type: ignore
    HarmBlockThreshold = None  # type: ignore
    HarmCategory = None  # type: ignore

# Local imports

# Type checking imports
if TYPE_CHECKING:
    from ..config.interfaces import ProviderConfig
    from ..writing_tools_app import WritingToolsApp


class AIProviderSetting(ABC):
    """
    Abstract base class for a provider setting (e.g., API key, model selection).

    Each setting has a name, display name, default value and description.
    Subclasses must implement UI rendering and value management.

    Attributes:
        name: Internal identifier for the setting
        display_name: Human-readable name shown in UI
        default_value: Default value if none is set
        description: Optional description text
        auto_save_callback: Optional callback for value changes
    """

    def __init__(
        self,
        name: str,
        display_name: str | None = None,
        default_value: str | None = None,
        description: str | None = None,
    ):
        self.name: str = name
        self._logger = logging.getLogger(__name__)
        self.display_name: str = display_name or name
        self.default_value: str = default_value or ""
        self.description: str = description or ""
        # Callback function (no args, no return) or None
        self.auto_save_callback: Callable[[], None] | None = None

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Render the setting widget(s) into the provided layout."""

    @abstractmethod
    def set_value(self, value: str) -> None:
        """Set the internal value from configuration."""

    @abstractmethod
    def get_value(self) -> str:
        """Return the current value from the widget."""

    def refresh_styles(self) -> None:
        """Optional: reapply the styles if the widget exists."""
        pass

    def set_auto_save_callback(self, callback: Callable) -> None:
        """Set callback function for auto-saving when value changes."""
        self.auto_save_callback = callback


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).

    Uses a QLineEdit to allow free text input, and its label shown before.
    Value is stored internally until widget rendering.
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        name: str,
        display_name: str | None = None,
        default_value: str | None = None,
        description: str | None = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.app = app
        self.internal_value: str | None = default_value
        self.input: QLineEdit | None = None
        self.label: QLabel | None = None

    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Create and add the QLineEdit with its label to the layout."""
        row_layout = QHBoxLayout()
        self.label = QLabel(self.display_name)
        self.label.setStyleSheet(self.app.styles["label"])
        row_layout.addWidget(self.label)
        self.input = QLineEdit(self.internal_value)
        self.input.setStyleSheet(self.app.styles["input"])
        self.input.setPlaceholderText(self.description)
        # Connect auto-save if callback is set
        if self.auto_save_callback:
            self.input.editingFinished.connect(self.auto_save_callback)
        row_layout.addWidget(self.input)
        layout.addLayout(row_layout)

    def refresh_styles(self):
        # Update input style
        if self.input:
            self.input.setStyleSheet(self.app.styles["input"])

        # Update label style
        if hasattr(self, "label") and self.label:
            self.label.setStyleSheet(self.app.styles["label"])

    def set_value(self, value: str) -> None:
        """Store value internally and update widget if it exists."""
        self.internal_value = value
        if self.input is not None:
            try:
                # Only update if the value has actually changed to avoid triggering textChanged
                current_text = self.input.text()
                if str(value) != current_text:
                    self.input.setText(str(value))
            except RuntimeError:
                # Widget has been deleted, just store the value
                pass

    def get_value(self) -> str:
        """Return widget value or empty string if not yet rendered."""
        if self.input is not None:
            try:
                return self.input.text()
            except RuntimeError:
                # Widget has been deleted, return stored value or empty string
                return getattr(self, "internal_value", "")
        return getattr(self, "internal_value", "")


class DropdownSetting(AIProviderSetting):
    """
    A dropdown setting (e.g., for selecting a model).

    Uses a non-editable QComboBox.
    Options are stored as tuples (display_name, value).
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        name: str,
        display_name: str | None = None,
        default_value: str | None = None,
        description: str | None = None,
        options: list | None = None,
        refresh_callback: Callable | None = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.app = app
        self.options = options or []
        self.internal_value = default_value
        self.dropdown: QComboBox | None = None
        self.label: QLabel | None = None
        self.refresh_callback = refresh_callback

    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Create and configure the QComboBox with available options."""
        row_layout = QHBoxLayout()
        self.label = QLabel(self.display_name)
        self.label.setStyleSheet(self.app.styles["label"])
        row_layout.addWidget(self.label)
        self.dropdown = QComboBox()
        # Ensure dropdown can receive focus and clicks properly
        self.dropdown.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.dropdown.setStyleSheet(self.app.styles["dropdown"])

        for option_tuple in self.options:
            if len(option_tuple) == 2:
                option, value = option_tuple
                self.dropdown.addItem(option, value)
            elif len(option_tuple) == 3:
                option, value, metadata = option_tuple
                # Add asterisk for vision support
                if metadata.get("vision", False):
                    display_option = f"* {option}"
                else:
                    display_option = option
                self.dropdown.addItem(display_option, value)
                # Store metadata (vision support) if necessary
            else:
                self._logger.warning(f"Unexpected option format: {option_tuple}")

        # Set current value
        if self.dropdown is not None:
            index = self.dropdown.findData(self.internal_value)
            if index != -1:
                self.dropdown.setCurrentIndex(index)

        # Connect auto-save if callback is set
        if self.auto_save_callback:
            self.dropdown.currentIndexChanged.connect(self.auto_save_callback)

        # Connect refresh callback when dropdown is about to be shown
        if self.refresh_callback:
            # Override showPopup to call refresh before showing
            # QComboBox doesn't have aboutToShow signal, so we override showPopup
            original_show_popup = self.dropdown.showPopup

            def show_popup_with_refresh():
                if callable(self.refresh_callback):
                    self.refresh_callback()
                original_show_popup()

            self.dropdown.showPopup = show_popup_with_refresh

        row_layout.addWidget(self.dropdown)
        layout.addLayout(row_layout)

    def set_value(self, value: str) -> None:
        """Store value for selection during rendering and update widget if it exists."""
        self.internal_value = value
        if self.dropdown is not None:
            try:
                # Check if the value is already selected to avoid triggering currentIndexChanged
                current_data = self.dropdown.currentData()
                if current_data != value:
                    # Find and select the matching option
                    for i in range(self.dropdown.count()):
                        if self.dropdown.itemData(i) == value:
                            self.dropdown.setCurrentIndex(i)
                            return
            except RuntimeError:
                # Widget has been deleted, just store the value
                pass

    def refresh_styles(self):
        # Update dropdown style
        if self.dropdown:
            self.dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update label style
        if hasattr(self, "label") and self.label:
            self.label.setStyleSheet(self.app.styles["label"])

    def get_value(self) -> str:
        """Return selected value from the dropdown."""
        if self.dropdown is None:
            return getattr(self, "internal_value", "")

        try:
            return self.dropdown.currentData()
        except RuntimeError:
            # Widget has been deleted, return stored value or empty string
            return getattr(self, "internal_value", "")

    def refresh_options(self, new_options: list) -> None:
        """Refresh the dropdown options dynamically."""
        if self.dropdown is None:
            self.options = new_options
            return

        try:
            # Save current selection
            current_value = self.get_value()
            initial_index = self.dropdown.currentIndex()

            # Block signals during refresh to prevent unwanted auto-save triggers
            self.dropdown.blockSignals(True)

            # Clear and repopulate dropdown
            self.dropdown.clear()
            self.options = new_options

            for option_tuple in self.options:
                if len(option_tuple) == 2:
                    option, value = option_tuple
                    self.dropdown.addItem(option, value)
                elif len(option_tuple) == 3:
                    option, value, metadata = option_tuple
                    # Add asterisk for vision support
                    if metadata.get("vision", False):
                        display_option = f"* {option}"
                    else:
                        display_option = option
                    self.dropdown.addItem(display_option, value)
                    # Store metadata (vision support) if necessary
                else:
                    self._logger.warning(f"Unexpected option format: {option_tuple}")

            # Restore selection if possible
            final_index = initial_index
            if current_value:
                index = self.dropdown.findData(current_value)
                if index != -1:
                    self.dropdown.setCurrentIndex(index)
                    final_index = index

            # Unblock signals
            self.dropdown.blockSignals(False)

            # Only trigger auto-save if the effective selection actually changed
            if final_index != initial_index and self.auto_save_callback:
                self.auto_save_callback()

        except RuntimeError:
            # Widget has been deleted, just update the options
            self.options = new_options


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers must implement:
      • get_response(system_instruction, prompt) -> str
      • after_load() to create their client or model instance
      • before_load() to cleanup any existing client
      • cancel() to cancel an ongoing request

    The class also handles configuration loading/saving and UI interface.
    Dynamic attributes are created via setattr() during configuration loading.
    """

    # Type annotations for dynamically created attributes
    api_key: str
    api_model: str
    api_base: str
    api_organisation: str
    api_project: str
    keep_alive: str
    logo: str | None

    def __init__(
        self,
        app: "WritingToolsApp",
        provider_name: str,
        settings: list[AIProviderSetting],
        description: str = "An unfinished AI provider!",
        internal_name: str = "",
        button_text: str = "Go to URL",
        button_action: Callable | None = None,
        logo: str | None = None,
    ):
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.provider_name = provider_name
        self.internal_name = internal_name
        self.settings = settings
        self.description = description if description else "An unfinished AI provider!"
        self.button_text = button_text
        self.button_action = button_action
        self.logo = logo
        self.executor = ThreadPoolExecutor(max_workers=1)
        self.current_future = None

        # Support for multiple buttons (for providers that need refresh functionality)
        self.additional_buttons = []

    def add_button(self, text: str, action: Callable, style: str = "secondary") -> None:
        """Add an additional button to the provider UI."""
        self.additional_buttons.append({"text": text, "action": action, "style": style})

    def refresh_configuration(self) -> None:
        """
        Refresh the provider configuration dynamically.
        This method should be overridden by providers that need dynamic reconfiguration.
        """
        pass

    def refresh_styles(self):
        for setting in self.settings:
            if hasattr(setting, "refresh_styles"):
                setting.refresh_styles()

    # Suppression of the getter/setter for model_name, we use api_model directly
    # which will be created by setattr() in load_config()

    def get_response(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Public interface to get a response from the AI provider.

        Automatically handles cancellation and threading for all providers.
        """
        # Cancel the previous request if it exists
        if self.current_future and not self.current_future.done():
            self.current_future.cancel()
            logging.debug(f"Cancelled previous {self.provider_name} request")

        # Launch the new query in a thread
        self.current_future = self.executor.submit(
            self._get_response_impl, system_instruction, prompt, return_response, **kwargs
        )

        try:
            # Wait for the result
            return self.current_future.result()
        except CancelledError:
            logging.debug(f"{self.provider_name} request was cancelled")
            return ""
        except Exception as e:
            logging.error(f"Error in {self.provider_name} request: {e}")
            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(
                    "An error occurred while processing the response."
                )
            return ""

    @abstractmethod
    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Concrete implementation of get_response for each provider.

        This method runs in a separate thread and can be cancelled.
        Providers implement this method instead of get_response.

        Send the given system instruction and prompt to the AI provider and return the full response text.

        This method must handle:
        - Formatting the request according to the API's expected format
        - Sending the request and waiting for the response
        - Error handling and displaying appropriate user messages
        - Emitting the output_ready_signal for direct text replacement
        - Processing images if image_data is provided
        """

    def load_config(self, config: "ProviderConfig") -> None:
        """
        Load configuration settings into the provider.

        Updates dynamic attributes and setting values,
        then calls after_load() to initialize the API client.
        """
        for setting in self.settings:
            if setting.name in config:
                setattr(self, setting.name, config[setting.name])
                setting.set_value(config[setting.name])
            else:
                setattr(self, setting.name, setting.default_value)

        self.after_load()

    def save_config(self) -> None:
        """
        Save provider configuration settings into the main config file.

        Retrieves current values from UI widgets, cleans whitespace,
        and stores them in the settings_manager's custom_data.providers section.
        """
        config = {}
        for setting in self.settings:
            value = setting.get_value()
            # Clean whitespace and newlines from string values (especially API keys)
            if isinstance(value, str):
                value = value.strip()
            config[setting.name] = value

        self.app.settings_manager.providers[self.internal_name] = cast("ProviderConfig", config)

        success = self.app.settings_manager.save()
        if not success:
            self._logger.error("Failed to save provider configuration")
            return

    @abstractmethod
    def after_load(self) -> None:
        """
        Called after configuration is loaded; create your API client here.

        This method should initialize any clients or connections needed
        using the loaded settings (api_key, api_base, etc.).
        """

    @abstractmethod
    def before_load(self) -> None:
        """
        Called before reloading configuration; cleanup your API client here.

        This method should release resources and close connections
        before a new configuration is loaded.
        """

    def cancel(self) -> None:
        """
        Cancel any ongoing API request.

        Default implementation that works for all providers.
        """
        if self.current_future and not self.current_future.done():
            cancelled = self.current_future.cancel()
            if cancelled:
                logging.debug(f"Successfully cancelled {self.provider_name} request")
            else:
                logging.debug(f"Could not cancel {self.provider_name} request (already started)")

    def __del__(self):
        """Cleanup of the ThreadPoolExecutor on destruction."""
        try:
            if hasattr(self, "executor") and self.executor:
                self.executor.shutdown(wait=False)
        except Exception:
            # Ignore errors during cleanup
            pass

    def validate_connection(self) -> bool:
        """
        Validate the provider configuration before processing. Used from process_option().

        Returns:
            bool: True if the provider is properly configured, False otherwise
        """
        # Check for API key
        if hasattr(self, "api_key") and not (self.api_key and self.api_key.strip()):
            self.app.show_message_signal.emit(
                "Configuration Error",
                f"API key is required for {self.provider_name}. Please configure your API key in settings.",
            )
            return False

        # Check for model
        if hasattr(self, "api_model") and not (self.api_model and self.api_model.strip()):
            self.app.show_message_signal.emit(
                "Configuration Error",
                f"Model selection is required for {self.provider_name}. Please select a model in settings.",
            )
            return False

        return True
