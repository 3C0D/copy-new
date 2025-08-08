"""
AI Provider Architecture for Writing Tools
--------------------------------------------

This module handles different AI model providers (Gemini, OpenAI-compatible, Ollama) and manages their interactions
with the main application. It uses an abstract base class pattern for provider implementations.

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
    • OpenAICompatibleProvider - Connects to any OpenAI-compatible API (v1/chat/completions)
    • OllamaProvider - Connects to a locally running Ollama server (e.g. for llama.cpp)

Response Flow:
   • The main app calls get_response() with a system instruction and a prompt.
   • The provider formats and sends the request to its API endpoint.
   • For operations that require a window (e.g. Summary, Key Points), the provider returns the full text.
   • For direct text replacement, the provider emits the full text via the output_ready_signal.
   • Conversation history (for follow-up questions) is maintained by the main app.

Note: Streaming has been fully removed throughout the code.
"""

# Disable Pylance reportPrivateImportUsage for google.generativeai
# The library doesn't properly define __all__, causing false positives
# but all imports (configure, types.HarmCategory, etc.) work correctly at runtime
# pyright: reportPrivateImportUsage=false

import logging
import subprocess
import webbrowser
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Optional, Union, cast

if TYPE_CHECKING:
    from Windows_and_Linux.config.interfaces import ProviderConfig

# External libraries
try:
    import google.generativeai as genai
    from google.generativeai.types import HarmBlockThreshold, HarmCategory
except ImportError:
    # Fallback for type checking
    genai = None  # type: ignore
    HarmBlockThreshold = None  # type: ignore
    HarmCategory = None  # type: ignore

from ollama import Client as OllamaClient
from openai import OpenAI
from PySide6 import QtWidgets
from PySide6.QtWidgets import QVBoxLayout

from config.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    MISTRAL_MODELS,
    OPENAI_MODELS,
)
from config.data_operations import get_default_model_for_provider
from ui.ui_utils import colorMode

if TYPE_CHECKING:
    from Windows_and_Linux.WritingToolApp import WritingToolApp


class AIProviderSetting(ABC):
    """
    Abstract base class for a provider setting (e.g., API key, model selection).
    """

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
    ):
        self.name = name
        self.display_name = display_name if display_name else name
        self.default_value = default_value if default_value else ""
        self.description = description if description else ""

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout):
        """Render the setting widget(s) into the provided layout."""

    @abstractmethod
    def set_value(self, value):
        """Set the internal value from configuration."""

    @abstractmethod
    def get_value(self):
        """Return the current value from the widget."""


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).
    """

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.internal_value = default_value
        self.input: Optional[QtWidgets.QLineEdit] = None

    def render_to_layout(self, layout: QVBoxLayout):
        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if colorMode=='dark' else '#333333'};")
        row_layout.addWidget(label)
        self.input = QtWidgets.QLineEdit(self.internal_value)
        self.input.setStyleSheet(
            f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if colorMode=='dark' else 'white'};
            color: {'#ffffff' if colorMode=='dark' else '#000000'};
            border: 1px solid {'#666' if colorMode=='dark' else '#ccc'};
        """,
        )
        self.input.setPlaceholderText(self.description)
        row_layout.addWidget(self.input)
        layout.addLayout(row_layout)

    def set_value(self, value):
        self.internal_value = value

    def get_value(self):
        if self.input is not None:
            return self.input.text()
        return ""


class DropdownSetting(AIProviderSetting):
    """
    A dropdown setting (e.g., for selecting a model).
    """

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[list] = None,
        editable: bool = False,
    ):
        super().__init__(name, display_name, default_value, description)
        self.options = options or []
        self.internal_value = default_value
        self.dropdown: Optional[QtWidgets.QComboBox] = None
        self.editable = editable

    def render_to_layout(self, layout: QVBoxLayout):
        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.display_name)
        label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if colorMode=='dark' else '#333333'};")
        row_layout.addWidget(label)
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setEditable(self.editable)  # Allow custom input if editable
        self.dropdown.setStyleSheet(
            f"""
            font-size: 16px;
            padding: 5px;
            padding-right: 25px;
            background-color: {'#444' if colorMode=='dark' else 'white'};
            color: {'#ffffff' if colorMode=='dark' else '#000000'};
            border: 1px solid {'#666' if colorMode=='dark' else '#ccc'};
        """,
        )
        for option, value in self.options:
            self.dropdown.addItem(option, value)

        # Set current value
        if self.dropdown is not None:
            if self.editable:
                # For editable dropdowns, set the text directly
                self.dropdown.setCurrentText(str(self.internal_value) if self.internal_value is not None else "")
            else:
                # For non-editable dropdowns, find by data
                index = self.dropdown.findData(self.internal_value)
            if index != -1:
                self.dropdown.setCurrentIndex(index)
        row_layout.addWidget(self.dropdown)
        layout.addLayout(row_layout)

    def set_value(self, value):
        self.internal_value = value

    def get_value(self):
        if self.dropdown is None:
            return ""

        if self.editable:
            # For editable dropdowns, first check if current text matches a dropdown option
            current_text = self.dropdown.currentText()
            # Look for matching option and return its data value
            for i in range(self.dropdown.count()):
                if self.dropdown.itemText(i) == current_text:
                    return self.dropdown.itemData(i)
            # If no match found, return the text as-is (custom input)
            return current_text
        # For non-editable dropdowns, return the data
        return self.dropdown.currentData()


class AIProvider(ABC):
    """
    Abstract base class for AI providers.

    All providers must implement:
      • get_response(system_instruction, prompt) -> str
      • after_load() to create their client or model instance
      • before_load() to cleanup any existing client
      • cancel() to cancel an ongoing request
    """

    # Type annotations for dynamically created attributes
    api_key: str
    model_name: str
    api_base: str
    api_organisation: str
    api_project: str
    api_model: str
    keep_alive: str
    logo: Optional[str]

    def __init__(
        self,
        app: 'WritingToolApp',
        provider_name: str,
        settings: list[AIProviderSetting],
        description: str = "An unfinished AI provider!",
        internal_name: str = "",
        button_text: str = "Go to URL",
        button_action: Optional[Callable] = None,
        logo: Optional[str] = None,
    ):
        self.provider_name = provider_name
        self.internal_name = internal_name
        self.settings = settings
        self.app = app
        self.description = description if description else "An unfinished AI provider!"
        self.button_text = button_text
        self.button_action = button_action
        self.logo = logo

        # Initialize dynamic attributes with default values
        self.api_key = ""
        self.model_name = ""
        self.api_base = ""
        self.api_organisation = ""
        self.api_project = ""
        self.api_model = ""
        self.keep_alive = ""

    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str) -> str:
        """
        Send the given system instruction and prompt to the AI provider and return the full response text.
        """

    def load_config(self, config: dict):
        """
        Load configuration settings into the provider.
        """
        for setting in self.settings:
            if setting.name in config:
                setattr(self, setting.name, config[setting.name])
                setting.set_value(config[setting.name])
            else:
                setattr(self, setting.name, setting.default_value)
        self.after_load()

    def save_config(self):
        """
        Save provider configuration settings into the main config file.
        """
        config = {}
        for setting in self.settings:
            value = setting.get_value()
            # Clean whitespace and newlines from string values (especially API keys)
            if isinstance(value, str):
                value = value.strip()
            config[setting.name] = value

        # Store provider config in custom_data
        if not self.app.settings_manager.settings.custom_data:
            self.app.settings_manager.settings.custom_data = {}
        if "providers" not in self.app.settings_manager.settings.custom_data:
            self.app.settings_manager.providers = {}

        self.app.settings_manager.providers[self.internal_name] = cast('ProviderConfig', config)

        # Use settings_manager directly instead of going through app.save_settings()
        self.app.settings_manager.save_settings()

    @abstractmethod
    def after_load(self):
        """
        Called after configuration is loaded; create your API client here.
        """

    @abstractmethod
    def before_load(self):
        """
        Called before reloading configuration; cleanup your API client here.
        """

    @abstractmethod
    def cancel(self):
        """
        Cancel any ongoing API request.
        """


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API.

    Uses google.generativeai.GenerativeModel.generate_content() to generate text.
    Streaming is no longer offered so we always do a single-shot call.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = False
        self.model = None

        settings = [
            TextSetting(
                name="api_key",
                display_name="API Key",
                description="Paste your Gemini API key here",
            ),
            DropdownSetting(
                name="model_name",
                display_name="Model",
                default_value=get_default_model_for_provider("gemini"),
                description="Select Gemini model to use",
                options=GEMINI_MODELS,
            ),
        ]
        super().__init__(
            app,
            "Gemini (Recommended)",
            settings,
            "• Google’s Gemini is a powerful AI model available for free!\n"
            "• An API key is required to connect to Gemini on your behalf.\n"
            "• Click the button below to get your API key.",
            "gemini",
            "Get API Key",
            lambda: webbrowser.open("https://aistudio.google.com/app/apikey"),
            "gemini",
        )

    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False) -> str:
        """
        Generate content using Gemini.

        Always performs a single-shot request with streaming disabled.
        Returns the full response text if return_response is True,
        otherwise emits the text via the output_ready_signal.
        """
        self.close_requested = False

        # Check if model is configured
        if not self.model:
            error_msg = "Gemini API key not configured. Please add your API key in settings."
            logging.error(error_msg)
            if not return_response:
                # Show a user-friendly message box instead of just emitting to output
                self.app.show_message_signal.emit(
                    "API Key Missing",
                    "Your Gemini API key is not configured or invalid. Please go to Settings and add a valid API key.",
                )
                return ""
            return error_msg

        # Single-shot call with streaming disabled
        response = self.model.generate_content(contents=[system_instruction, prompt], stream=False)

        try:
            response_text = response.text.rstrip("\n")
            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)
                self.app.replace_text(response_text)
                return ""
            return response_text
        except Exception as e:
            error_str = str(e)
            logging.exception(f"Error processing Gemini response: {error_str}")

            # Handle specific Gemini API errors with user-friendly messages
            if "API_KEY_INVALID" in error_str or "invalid API key" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Invalid API Key",
                    "Your Gemini API key is invalid. Please check your API key in Settings and make sure it's correct.",
                )
            elif "quota exceeded" in error_str.lower() or "resource exhausted" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Quota Exceeded",
                    "You've exceeded your Gemini API quota. Please check your usage limits or try again later.",
                )
            elif "rate limit" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Rate Limit Hit",
                    "You're sending requests too quickly. Please wait a moment and try again.",
                )
            else:
                # Generic error with option to check settings
                self.app.show_message_signal.emit(
                    "API Error",
                    f"An error occurred with the Gemini API:\n\n{error_str}\n\nPlease check your API key and settings.",
                )
        finally:
            self.close_requested = False

        return ""

    def after_load(self):
        """
        Configure the google.generativeai client and create the generative model.
        """
        # Only configure if API key is provided and genai is available
        if (
            hasattr(self, "api_key")
            and self.api_key
            and self.api_key.strip()
            and genai is not None
            and HarmCategory is not None
            and HarmBlockThreshold is not None
        ):
            # Fix: Use try-except to handle the configure method
            try:
                genai.configure(api_key=self.api_key)
                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=1000,
                        temperature=0.5,
                    ),
                    safety_settings={
                        HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                        HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
                    },
                )
            except AttributeError as e:
                print(f"Error configuring Google Generative AI: {e}")
                self.model = None
        else:
            self.model = None

    def before_load(self):
        self.model = None

    def cancel(self):
        self.close_requested = True


class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = None
        self.client = None

        settings = [
            TextSetting(
                name="api_key",
                display_name="API Key",
                description="API key for the OpenAI-compatible API.",
            ),
            TextSetting(
                "api_base",
                "API Base URL",
                "https://api.openai.com/v1",
                "E.g. https://api.openai.com/v1",
            ),
            TextSetting(
                "api_organisation",
                "API Organisation",
                "",
                "Leave blank if not applicable.",
            ),
            TextSetting("api_project", "API Project", "", "Leave blank if not applicable."),
            DropdownSetting(
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("openai"),
                description="Select OpenAI model to use",
                options=OPENAI_MODELS,
            ),
        ]
        super().__init__(
            app,
            "OpenAI Compatible (For Experts)",
            settings,
            "• Connect to ANY OpenAI-compatible API (v1/chat/completions).\n"
            "• You must abide by the service's Terms of Service.",
            "openai",
            "Get OpenAI API Key",
            lambda: webbrowser.open("https://platform.openai.com/account/api-keys"),
            "openai",
        )

    @property
    def api_model(self) -> str:
        """Get the API model setting value."""
        for setting in self.settings:
            if setting.name == "api_model":
                value = setting.get_value()
                return str(value) if value is not None else ""
        return ""

    @api_model.setter
    def api_model(self, value: str):
        """Set the API model setting value."""
        for setting in self.settings:
            if setting.name == "api_model":
                setting.set_value(value)
                break

    def get_response(self, system_instruction: str, prompt: Union[str, list], return_response: bool = False) -> str:
        """
        Send a chat request to the OpenAI-compatible API.

        Always performs a non-streaming request.
        If prompt is not a list, builds a simple two-message conversation.
        Returns the response text if return_response is True,
        otherwise emits it via output_ready_signal.
        """
        self.close_requested = False

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ]

        try:
            if self.client is None:
                self.app.show_message_signal.emit(
                    "Error", "OpenAI client not initialized. Please check your API settings."
                )
                return ""

            response = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,  # type: ignore
                temperature=0.5,
                stream=False,
            )
            response_text = response.choices[0].message.content.strip()

            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)
            return response_text

        except Exception as e:
            error_str = str(e)
            logging.exception(f"Error while generating content: {error_str}")

            # Handle specific OpenAI API errors
            if "invalid api key" in error_str.lower() or "unauthorized" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Invalid API Key",
                    "Your OpenAI API key is invalid. Please check your API key in Settings and make sure it's correct.",
                )
            elif "exceeded" in error_str.lower() or "rate limit" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Rate Limit Hit",
                    "You've hit an API rate/usage limit. Please try again later or check your OpenAI usage limits.",
                )
            elif "insufficient_quota" in error_str.lower() or "quota" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Quota Exceeded",
                    "You've exceeded your OpenAI API quota. Please check your billing and usage limits.",
                )
            else:
                self.app.show_message_signal.emit(
                    "API Error",
                    f"An error occurred with the OpenAI API:\n\n{error_str}\n\nPlease check your API key and settings.",
                )
            return ""

    def after_load(self):
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.api_organisation,
            project=self.api_project,
        )

    def before_load(self):
        self.client = None

    def cancel(self):
        self.close_requested = True


def get_ollama_models():
    """
    Get list of installed Ollama models by running 'ollama list' command.
    Returns a list of tuples (display_name, model_name) for installed models.
    """
    try:
        result = subprocess.run(["ollama", "list"], check=False, capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            lines = result.stdout.strip().split("\n")
            models = []

            # Skip header line and parse model list
            for line in lines[1:]:
                if line.strip():
                    # Parse line format: "model_name:tag    id    size    modified"
                    parts = line.split()
                    if parts:
                        model_name = parts[0]
                        # Extract size info if available and format it properly
                        size_info = ""
                        if len(parts) >= 3:
                            size_raw = parts[2]
                            # Convert size to proper format (e.g., "5.6GB" -> "(5.6 Go)")
                            if size_raw.upper().endswith("GB"):
                                size_value = size_raw[:-2]
                                size_info = f" ({size_value} Go)"
                            elif size_raw.upper().endswith("MB"):
                                size_value = size_raw[:-2]
                                size_info = f" ({size_value} Mo)"
                            else:
                                size_info = f" ({size_raw})"

                        display_name = f"{model_name}{size_info}"
                        models.append((display_name, model_name))

            if models:
                return models
            # No models found, return message to install models
            return [("Veuillez d'abord installer des modèles Ollama", "")]
        logging.warning(f"Failed to get Ollama models: {result.stderr}")
        return [("Veuillez d'abord installer des modèles Ollama", "")]

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logging.warning(f"Could not run 'ollama list': {e}")
        return [("Ollama non disponible - Veuillez l'installer", "")]


class OllamaProvider(AIProvider):
    """
    Provider for connecting to an Ollama server.

    Uses the /chat endpoint of the Ollama server to generate a response.
    Streaming is not used.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = None
        self.client = None
        self.app = app

        # Get available Ollama models
        ollama_models = get_ollama_models()

        settings = [
            TextSetting(
                "api_base",
                "API Base URL",
                "http://localhost:11434",
                "E.g. http://localhost:11434",
            ),
            DropdownSetting(
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("ollama"),
                description="Select Ollama model to use (or type custom model name)",
                options=ollama_models,
                editable=True,  # Allow custom model names
            ),
            TextSetting(
                "keep_alive",
                "Time to keep the model loaded in memory in minutes",
                "5",
                "E.g. 5",
            ),
        ]
        super().__init__(
            app,
            "Ollama (For Experts)",
            settings,
            "• Connect to an Ollama server (local LLM).",
            "ollama",
            "Ollama Set-up Instructions",
            lambda: webbrowser.open(
                "https://github.com/theJayTea/WritingTools?tab=readme-ov-file#-optional-ollama-local-llm-instructions-for-windows-v7-onwards",
            ),
            "ollama",
        )

    @property
    def api_model(self) -> str:
        """Get the API model setting value."""
        for setting in self.settings:
            if setting.name == "api_model":
                value = setting.get_value()
                return str(value) if value is not None else ""
        return ""

    def get_response(self, system_instruction: str, prompt: Union[str, list], return_response: bool = False) -> str:
        """
        Send a chat request to the Ollama server.

        Always performs a non-streaming request.
        Returns the response text if return_response is True,
        otherwise emits it via output_ready_signal.
        """
        self.close_requested = False

        if isinstance(prompt, list):
            messages = prompt
        else:
            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": prompt},
            ]

        try:
            # Check if model is valid before making the request
            if not self.api_model or self.api_model.strip() == "":
                self.app.show_message_signal.emit(
                    "OllamaError",
                    "Aucun modèle Ollama sélectionné. Veuillez d'abord installer et sélectionner un modèle dans les paramètres.",
                )
                return ""

            if self.client is None:
                self.app.show_message_signal.emit("Error", "Ollama client not initialized. Please check your settings.")
                return ""

            logging.debug(f"Ollama using model: '{self.api_model}'")
            response = self.client.chat(model=self.api_model, messages=messages)
            response_text = response["message"]["content"].strip()
            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)
            return response_text
        except Exception as e:
            error_str = str(e)
            logging.exception(f"Error during Ollama chat: {error_str}")

            # Handle specific Ollama errors
            if "connection" in error_str.lower() or "refused" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Connection Error",
                    "Cannot connect to Ollama server. Please make sure Ollama is running and check your server URL in Settings.",
                )
            elif "model" in error_str.lower() and "not found" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Model Not Found",
                    "The specified Ollama model was not found. Please check your model name in Settings or download the model first.",
                )
            else:
                self.app.show_message_signal.emit(
                    "Ollama Error",
                    f"An error occurred with Ollama:\n\n{error_str}\n\nPlease check your Ollama server and settings.",
                )
            return ""

    def after_load(self):
        self.client = OllamaClient(host=self.api_base)

    def before_load(self):
        self.client = None

    def cancel(self):
        self.close_requested = True


class AnthropicProvider(AIProvider):
    """
    Anthropic (Claude) AI Provider for Writing Tools.
    Uses the Anthropic API to generate content with Claude models.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = None
        self.client = None
        self.app = app
        settings = [
            TextSetting(
                "api_key",
                "API Key",
                "",
                "Enter your Anthropic API key",
            ),
            DropdownSetting(
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("anthropic"),
                description="Select Claude model to use",
                options=ANTHROPIC_MODELS,
                editable=False,
            ),
        ]
        super().__init__(
            app,
            "Anthropic (Claude)",
            settings,
            "• Claude is Anthropic's powerful AI assistant.\n"
            "• An API key is required to connect to Claude on your behalf.\n"
            "• Click the button below to get your API key.",
            "anthropic",
            "Get API Key",
            lambda: webbrowser.open("https://console.anthropic.com/"),
            "anthropic",
        )

    def get_response(
        self,
        system_instruction,
        prompt,
        conversation_history=None,
        return_response=False,
    ):
        if self.close_requested:
            return ""

        try:
            # Initialize client if not already done
            if not self.client:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.anthropic.com/v1",
                    default_headers={
                        "anthropic-version": "2023-06-01",
                    },
                )

            # Prepare messages
            messages = []

            # Add system instruction if provided
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": prompt})

            # Make API call
            response = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,  # type: ignore
                max_tokens=4000,
                temperature=0.7,
            )

            if self.close_requested:
                return ""

            response_text = response.choices[0].message.content
            logging.debug(f"Anthropic API response: {response_text}")
            logging.debug(f"Anthropic response length: {len(response_text) if response_text else 0}")

            # Handle empty or None response
            if not response_text or response_text.strip() == "":
                error_msg = (
                    "Anthropic API returned an empty response. This might be due to insufficient credits or API limits."
                )
                logging.warning(error_msg)
                self.app.show_message_signal.emit(
                    "Empty Response",
                    error_msg,
                )
                return ""

            if return_response:
                return response_text
            # Emit the response via signal for direct replacement
            self.app.output_ready_signal.emit(response_text)
            return response_text

        except Exception as e:
            error_str = str(e)
            logging.exception(f"Anthropic API error: {error_str}")

            if "401" in error_str or "authentication" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Authentication Error",
                    "Invalid API key. Please check your Anthropic API key in settings.",
                )
            elif "429" in error_str or "rate limit" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Rate Limit",
                    "You've exceeded the rate limit. Please wait a moment and try again.",
                )
            else:
                self.app.show_message_signal.emit(
                    "Anthropic Error",
                    f"An error occurred with Anthropic:\n\n{error_str}\n\nPlease check your settings and try again.",
                )
            return ""

    def after_load(self):
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.anthropic.com/v1",
            default_headers={
                "anthropic-version": "2023-06-01",
            },
        )

    def before_load(self):
        self.client = None

    def cancel(self):
        self.close_requested = True


class MistralProvider(AIProvider):
    """
    Mistral AI Provider for Writing Tools.
    Uses the Mistral API to generate content with Mistral models.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = None
        self.client = None
        self.app = app
        settings = [
            TextSetting(
                "api_key",
                "API Key",
                "",
                "Enter your Mistral API key",
            ),
            DropdownSetting(
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("mistral"),
                description="Select Mistral model to use",
                options=MISTRAL_MODELS,
                editable=False,
            ),
        ]
        super().__init__(
            app,
            "Mistral AI",
            settings,
            "• Mistral AI provides powerful open-source language models.\n"
            "• An API key is required to connect to Mistral on your behalf.\n"
            "• Click the button below to get your API key.",
            "mistral",
            "Get API Key",
            lambda: webbrowser.open("https://console.mistral.ai/"),
            "mistral",
        )

    def get_response(
        self,
        system_instruction,
        prompt,
        conversation_history=None,
        return_response=False,
    ):
        logging.debug(f"MistralProvider.get_response called with return_response={return_response}")
        logging.debug(
            f"MistralProvider current config - api_key: {self.api_key[:10] if self.api_key else 'None'}..., api_model: {self.api_model}",
        )

        if self.close_requested:
            return ""

        try:
            import requests

            # Check if API key and model are configured
            if not self.api_key or self.api_key.strip() == "":
                error_msg = "Mistral API key not configured. Please add your API key in settings."
                logging.error(error_msg)
                self.app.show_message_signal.emit(
                    "API Key Missing",
                    error_msg,
                )
                return ""

            if not self.api_model or self.api_model.strip() == "":
                error_msg = "Mistral model not selected. Please select a model in settings."
                logging.error(error_msg)
                self.app.show_message_signal.emit(
                    "Model Missing",
                    error_msg,
                )
                return ""

            logging.debug(f"Mistral API call - Key: {self.api_key[:10]}..., Model: {self.api_model}")

            # Prepare messages using direct requests (like the working test code)
            url = "https://api.mistral.ai/v1/chat/completions"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            messages = []

            # Add system instruction as first message
            if system_instruction:
                messages.append({"role": "system", "content": system_instruction})

            # Add conversation history if provided
            if conversation_history:
                messages.extend(conversation_history)

            # Add current user message
            messages.append({"role": "user", "content": prompt})

            data = {
                "model": self.api_model,
                "messages": messages,
                "temperature": 0.7,
                "max_tokens": 4000,
            }

            logging.debug(f"Mistral request data: {data}")

            # Make API call using requests (like the working test code)
            response = requests.post(url, headers=headers, json=data, timeout=60)

            logging.debug(f"Mistral API status code: {response.status_code}")

            if self.close_requested:
                return ""

            if response.status_code == 200:
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    response_text = result["choices"][0]["message"]["content"]

                    logging.debug(f"Mistral API response: {response_text}")
                    logging.debug(f"Mistral response length: {len(response_text) if response_text else 0}")

                    # Handle empty or None response
                    if not response_text or response_text.strip() == "":
                        error_msg = "Mistral API returned an empty response. This might be due to insufficient credits or API limits."
                        logging.warning(error_msg)
                        self.app.show_message_signal.emit(
                            "Empty Response",
                            error_msg,
                        )
                        return ""

                    if return_response:
                        return response_text
                    # Emit the response via signal for direct replacement
                    self.app.output_ready_signal.emit(response_text)
                    return response_text
                error_msg = "Mistral API returned no content in response."
                logging.error(f"{error_msg} Full response: {result}")
                self.app.show_message_signal.emit(
                    "No Content",
                    error_msg,
                )
                return ""
            error_msg = f"Mistral API error {response.status_code}: {response.text}"
            logging.error(error_msg)

            if response.status_code == 401:
                self.app.show_message_signal.emit(
                    "Authentication Error",
                    "Invalid API key. Please check your Mistral API key in settings.",
                )
            elif response.status_code == 429:
                self.app.show_message_signal.emit(
                    "Rate Limit",
                    "You've exceeded the rate limit. Please wait a moment and try again.",
                )
            else:
                self.app.show_message_signal.emit(
                    "Mistral Error",
                    f"API error {response.status_code}: {response.text}",
                )
            return ""

        except Exception as e:
            error_str = str(e)
            logging.exception(f"Mistral API error: {error_str}")
            self.app.show_message_signal.emit(
                "Mistral Error",
                f"An error occurred with Mistral:\n\n{error_str}\n\nPlease check your settings and try again.",
            )
            return ""

    def after_load(self):
        # No client initialization needed - using requests directly
        pass

    def before_load(self):
        # No client cleanup needed
        pass

    def cancel(self):
        self.close_requested = True
