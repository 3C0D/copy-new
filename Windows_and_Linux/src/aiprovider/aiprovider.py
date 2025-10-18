"""
AI Provider Architecture for Writing Tools
--------------------------------------------

This module handles different AI model providers (Gemini, OpenAI, OpenAI-compatible, Ollama, Anthropic, Mistral)
and manages their interactions with the main application. It uses an abstract base class pattern for
provider implementations.

Key Components:
# Moved to settings.py
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

# Standard library imports
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from concurrent.futures import CancelledError, ThreadPoolExecutor
from typing import TYPE_CHECKING, cast

# Disable Pylance reportPrivateImportUsage for google.generativeai
# pyright: reportPrivateImportUsage=false

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
from PySide6 import QtCore

from ..ui.custom_popup.vision_support_validator import VisionSupportValidator
from .settings import AIProviderSetting

# Type checking imports
if TYPE_CHECKING:
    from ..config.interfaces import ProviderConfig
    from ..writing_tools_app import WritingToolsApp


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
        logging.getLogger("PIL").setLevel(logging.WARNING)
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

    def refresh_styles(self) -> None:
        """Refresh the styles for all settings in this provider."""
        for setting in self.settings:
            if hasattr(setting, "refresh_styles"):
                setting.refresh_styles()

    # Suppression of the getter/setter for model_name, we use api_model directly
    # which will be created by setattr() in load_config()

    def get_response(
        self,
        system_instruction: str,
        prompt: str | list,
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

            # Handle rate limit errors specially - close response window and show message
            if (
                "429" in str(e)
                or "RateLimitError" in str(e)
                or "Resource has been exhausted" in str(e)
            ):
                if self.app.current_response_window:
                    QtCore.QMetaObject.invokeMethod(
                        self.app.current_response_window,
                        "close",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                    )
                self.app.ui_manager.show_message_signal.emit(
                    "Error - Rate Limit Hit",
                    "You've hit an API rate/usage limit. Please try again later or check your API usage limits.",
                )
                return ""

            # For other errors, show generic message only if not in response window mode
            if not return_response and self.app.current_response_window is None:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "An error occurred while processing the response."
                )
            return ""

    @abstractmethod
    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: str | list,
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
                # Create dynamic attribute on provider instance for code access (e.g., self.api_key)
                setattr(self, setting.name, config[setting.name])
                # Update the UI widget and internal storage of the setting object
                setting.set_value(config[setting.name])
            else:
                setattr(self, setting.name, setting.default_value)

        self.after_load()

    def save_config(self) -> None:
        """
        Save provider configuration settings into the main config file.

        Retrieves current values from UI widgets, cleans whitespace,
        and stores them in the settings_manager's custom_data.providers section.
        Preserves existing data like 'recorded' presets.
        """
        # Get existing config to preserve non-setting data
        existing_config = self.app.settings_manager.providers.get(self.internal_name, {})

        # Update with current setting values
        config = existing_config.copy()
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

    def validate_connection(self, has_image: bool = False) -> bool:
        """
        Validate the provider configuration before processing. Used from process_option().

        Args:
            has_image: Whether the request includes an image that requires vision support

        Returns:
            bool: True if the provider is properly configured, False otherwise
        """
        # Check for API key
        if hasattr(self, "api_key") and not (self.api_key and self.api_key.strip()):
            self.app.ui_manager.show_message_signal.emit(
                "Configuration Error",
                f"API key is required for {self.provider_name}. Please configure your API key in settings.",
            )
            return False

        # Check for model
        if hasattr(self, "api_model") and not (self.api_model and self.api_model.strip()):
            self.app.ui_manager.show_message_signal.emit(
                "Configuration Error",
                f"Model selection is required for {self.provider_name}. Please select a model in settings.",
            )
            return False

        # Check vision support if image is being processed
        if has_image and not self._supports_vision():
            self.app.ui_manager.show_message_signal.emit(
                "Vision Not Supported",
                f"The selected model '{self.api_model}' does not support image processing.\n\n"
                f"Please select a vision-capable model in {self.provider_name} settings.",
            )
            return False

        return True

    def _supports_vision(self) -> bool:
        """
        Check if the current model supports vision/image processing.

        Returns:
            bool: True if the model supports vision, False otherwise
        """
        if not hasattr(self, "api_model") or not self.api_model:
            return False

        return VisionSupportValidator.has_vision_support(
            self.internal_name, self.api_model, provider_instance=self
        )
