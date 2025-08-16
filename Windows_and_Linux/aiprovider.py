"""
revoir les import anarchiques dans le code et les rendre compatible avec win and linux. Aussi peutêtre voir dans tout Les modules les imports Pour qu'il respecte la même règle Que ça ça importe sous Windows ou Linux parce que y a eu des méthodes différentes J'ai vu Donc il faudrait homogénéiser ça Et mettre la plus efficace.



AI Provider Architecture for Writing Tools
--------------------------------------------

This module handles different AI model providers (Gemini, OpenAI-compatible, Ollama, Anthropic, Mistral)
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

Note: Streaming has been fully removed throughout the code.
"""

# Disable Pylance reportPrivateImportUsage for google.generativeai
# The library doesn't properly define __all__, causing false positives
# but all imports (configure, types.HarmCategory, etc.) work correctly at runtime
# pyright: reportPrivateImportUsage=false

import logging
import os
import platform
import subprocess
import tempfile
import webbrowser
from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, Callable, Optional, Union, cast

try:
    import requests
except ImportError:
    requests = None

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
from PySide6 import QtWidgets, QtCore
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

    Each setting has a name, display name, default value and description.
    Subclasses must implement UI rendering and value management.
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
        self.auto_save_callback: Optional[Callable] = None

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout):
        """Render the setting widget(s) into the provided layout."""

    @abstractmethod
    def set_value(self, value):
        """Set the internal value from configuration."""

    @abstractmethod
    def get_value(self):
        """Return the current value from the widget."""

    def set_auto_save_callback(self, callback: Callable):
        """Set callback function for auto-saving when value changes."""
        self.auto_save_callback = callback


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).

    Uses a QLineEdit to allow free text input.
    Value is stored internally until widget rendering.
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
        """Create and add the QLineEdit with its label to the layout."""
        from ui.ui_utils import get_effective_color_mode

        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.display_name)
        current_mode = get_effective_color_mode()
        label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if current_mode=='dark' else '#333333'};")
        row_layout.addWidget(label)
        self.input = QtWidgets.QLineEdit(self.internal_value)
        self.input.setStyleSheet(
            f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if current_mode=='dark' else 'white'};
            color: {'#ffffff' if current_mode=='dark' else '#000000'};
            border: 1px solid {'#666' if current_mode=='dark' else '#ccc'};
        """,
        )
        self.input.setPlaceholderText(self.description)
        # Connect auto-save if callback is set
        if self.auto_save_callback:
            self.input.textChanged.connect(self.auto_save_callback)
        row_layout.addWidget(self.input)
        layout.addLayout(row_layout)

    def set_value(self, value):
        """Store value internally for future rendering."""
        self.internal_value = value

    def get_value(self):
        """Return widget value or empty string if not yet rendered."""
        if self.input is not None:
            return self.input.text()
        return ""


class DropdownSetting(AIProviderSetting):
    """
    A dropdown setting (e.g., for selecting a model).

    Uses a QComboBox that can be editable or not.
    Options are stored as tuples (display_name, value).
    """

    def __init__(
        self,
        name: str,
        display_name: Optional[str] = None,
        default_value: Optional[str] = None,
        description: Optional[str] = None,
        options: Optional[list] = None,
        editable: bool = False,
        refresh_callback: Optional[Callable] = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.options = options or []
        self.internal_value = default_value
        self.dropdown: Optional[QtWidgets.QComboBox] = None
        self.editable = editable
        self.refresh_callback = refresh_callback

    def render_to_layout(self, layout: QVBoxLayout):
        """Create and configure the QComboBox with available options."""
        from ui.ui_utils import get_effective_color_mode

        row_layout = QtWidgets.QHBoxLayout()
        label = QtWidgets.QLabel(self.display_name)
        current_mode = get_effective_color_mode()
        label.setStyleSheet(f"font-size: 16px; color: {'#ffffff' if current_mode=='dark' else '#333333'};")
        row_layout.addWidget(label)
        self.dropdown = QtWidgets.QComboBox()
        self.dropdown.setEditable(self.editable)  # Allow custom input if editable
        # Ensure dropdown can receive focus and clicks properly
        self.dropdown.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.dropdown.setStyleSheet(
            f"""
            font-size: 16px;
            padding: 5px;
            padding-right: 25px;
            background-color: {'#444' if current_mode=='dark' else 'white'};
            color: {'#ffffff' if current_mode=='dark' else '#000000'};
            border: 1px solid {'#666' if current_mode=='dark' else '#ccc'};
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

        # Connect auto-save if callback is set
        if self.auto_save_callback:
            if self.editable:
                self.dropdown.currentTextChanged.connect(self.auto_save_callback)
            else:
                self.dropdown.currentIndexChanged.connect(self.auto_save_callback)

        # Connect refresh callback when dropdown is about to be shown
        if self.refresh_callback:
            # Use a custom event filter to detect when dropdown is about to open
            def on_dropdown_about_to_show():
                self.refresh_callback()

            # Connect to the aboutToShow signal if available, or use showPopup override
            if hasattr(self.dropdown, 'aboutToShow'):
                self.dropdown.aboutToShow.connect(on_dropdown_about_to_show)
            else:
                # Override showPopup to call refresh before showing
                original_show_popup = self.dropdown.showPopup

                def show_popup_with_refresh():
                    self.refresh_callback()
                    original_show_popup()

                self.dropdown.showPopup = show_popup_with_refresh

        row_layout.addWidget(self.dropdown)
        layout.addLayout(row_layout)

    def set_value(self, value):
        """Store value for selection during rendering."""
        self.internal_value = value

    def get_value(self):
        """Return selected or entered value from the dropdown."""
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

    def refresh_options(self, new_options: list):
        """Refresh the dropdown options dynamically."""
        if self.dropdown is None:
            self.options = new_options
            return

        # Save current selection
        current_value = self.get_value()

        # Clear and repopulate dropdown
        self.dropdown.clear()
        self.options = new_options

        for option, value in self.options:
            self.dropdown.addItem(option, value)

        # Restore selection if possible
        if current_value:
            if self.editable:
                self.dropdown.setCurrentText(str(current_value))
            else:
                index = self.dropdown.findData(current_value)
                if index != -1:
                    self.dropdown.setCurrentIndex(index)


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
    model_name: str
    api_base: str
    api_organisation: str
    api_project: str
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

        # Support for multiple buttons (for providers that need refresh functionality)
        self.additional_buttons = []

        # Initialize dynamic attributes based on provider settings
        # These attributes will be updated during configuration loading
        self._initialize_dynamic_attributes()

    def add_button(self, text: str, action: Callable, style: str = "secondary"):
        """Add an additional button to the provider UI."""
        self.additional_buttons.append({"text": text, "action": action, "style": style})

    def refresh_configuration(self):
        """
        Refresh the provider configuration dynamically.
        This method should be overridden by providers that need dynamic reconfiguration.
        """
        pass

    def _initialize_dynamic_attributes(self):
        """Initialize all dynamic attributes based on provider settings."""
        for setting in self.settings:
            setattr(self, setting.name, setting.default_value or "")

    @property
    def api_model(self) -> str:
        """Generic getter for the api_model attribute."""
        return getattr(self, '_api_model', '')

    @api_model.setter
    def api_model(self, value: str):
        """Generic setter for the api_model attribute."""
        self._api_model = value
        # Also update the corresponding setting if it exists
        for setting in self.settings:
            if setting.name == "api_model":
                setting.set_value(value)
                break

    @abstractmethod
    def get_response(self, system_instruction: str, prompt: str, return_response: bool = False) -> str:
        """
        Send the given system instruction and prompt to the AI provider and return the full response text.

        This method must handle:
        - Formatting the request according to the API's expected format
        - Sending the request and waiting for the response
        - Error handling and displaying appropriate user messages
        - Emitting the output_ready_signal for direct text replacement
        """

    def load_config(self, config: dict):
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

    def save_config(self):
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

        This method should initialize any clients or connections needed
        using the loaded settings (api_key, api_base, etc.).
        """

    @abstractmethod
    def before_load(self):
        """
        Called before reloading configuration; cleanup your API client here.

        This method should release resources and close connections
        before a new configuration is loaded.
        """

    @abstractmethod
    def cancel(self):
        """
        Cancel any ongoing API request.

        This method should set cancellation flags and interrupt
        ongoing operations safely.
        """


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API.

    Uses google.generativeai.GenerativeModel.generate_content() to generate text.
    Streaming is no longer offered so we always do a single-shot call.
    Handles safety settings to allow less restricted content.
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
            "• Google's Gemini is a powerful AI model available for free!\n"
            "• An API key is required to connect to Gemini on your behalf.\n"
            "• Safety filters are set to 'Block Only High' (most permissive setting available).\n"
            "• If content is still blocked, try rephrasing your request more neutrally.\n"
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

        try:
            # Single-shot call with streaming disabled
            response = self.model.generate_content(contents=[system_instruction, prompt], stream=False)

            # Check if response was blocked by safety filters
            if not response.candidates:
                error_msg = "Gemini blocked the request due to safety concerns. Try rephrasing your request."
                logging.warning("Gemini response blocked - no candidates returned")
                self.app.show_message_signal.emit(
                    "Content Blocked",
                    error_msg,
                )
                return ""

            # Check the finish reason of the first candidate
            candidate = response.candidates[0]

            # Finish reason meanings:
            # 1: STOP (normal completion)
            # 2: SAFETY (blocked by safety filters)
            # 3: RECITATION (blocked due to recitation)
            # 4: OTHER (other reason)
            if candidate.finish_reason == 2:  # SAFETY
                error_msg = (
                    "Gemini blocked the response due to safety filters. Try rephrasing your request to be more neutral."
                )
                logging.warning(f"Gemini safety filter triggered. Finish reason: {candidate.finish_reason}")
                self.app.show_message_signal.emit(
                    "Content Blocked by Safety Filters",
                    error_msg,
                )
                return ""
            elif candidate.finish_reason == 3:  # RECITATION
                error_msg = (
                    "Gemini blocked the response due to potential copyright concerns. Try a more original request."
                )
                logging.warning(f"Gemini recitation filter triggered. Finish reason: {candidate.finish_reason}")
                self.app.show_message_signal.emit(
                    "Content Blocked - Copyright Concern",
                    error_msg,
                )
                return ""
            elif candidate.finish_reason not in [1, None]:  # Not STOP or unset
                error_msg = f"Gemini could not complete the response (reason code: {candidate.finish_reason}). Please try again."
                logging.warning(f"Gemini unusual finish reason: {candidate.finish_reason}")
                self.app.show_message_signal.emit(
                    "Response Incomplete",
                    error_msg,
                )
                return ""

            # Check if response has content parts
            if not candidate.content or not candidate.content.parts:
                error_msg = "Gemini returned an empty response. Please try rephrasing your request."
                logging.warning("Gemini returned no content parts")
                self.app.show_message_signal.emit(
                    "Empty Response",
                    error_msg,
                )
                return ""

            # Safely extract text from response
            try:
                response_text = response.text.rstrip("\n")
            except ValueError as text_error:
                # Fallback: manually extract text from parts
                text_parts = []
                for part in candidate.content.parts:
                    if hasattr(part, 'text') and part.text:
                        text_parts.append(part.text)

                if text_parts:
                    response_text = "".join(text_parts).rstrip("\n")
                else:
                    error_msg = f"Could not extract text from Gemini response: {str(text_error)}"
                    logging.error(error_msg)
                    self.app.show_message_signal.emit(
                        "Response Processing Error",
                        "Could not process the response from Gemini. Please try again.",
                    )
                    return ""

            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)
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
            elif "finish_reason" in error_str.lower() and "safety" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Content Blocked",
                    "Gemini blocked the request due to safety concerns. Try rephrasing your request to be more neutral.",
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

        Only initialize model if API key is provided and genai is available.
        Uses BLOCK_ONLY_HIGH instead of BLOCK_NONE due to 2025 API restrictions.
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
            # Use try-except to handle the configure method
            try:
                genai.configure(api_key=self.api_key)

                # Updated safety settings for 2025 - BLOCK_NONE is now restricted
                # Use BLOCK_ONLY_HIGH for maximum permissiveness without special access
                safety_settings = {
                    HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                    HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_ONLY_HIGH,
                }

                # Check if CIVIC_INTEGRITY category exists (may vary by API version)
                if hasattr(HarmCategory, 'HARM_CATEGORY_CIVIC_INTEGRITY'):
                    safety_settings[HarmCategory.HARM_CATEGORY_CIVIC_INTEGRITY] = HarmBlockThreshold.BLOCK_ONLY_HIGH

                self.model = genai.GenerativeModel(
                    model_name=self.model_name,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=1000,
                        temperature=0.5,
                    ),
                    safety_settings=safety_settings,
                )

                # Log the safety configuration for debugging
                logging.info(
                    f"Gemini model initialized with BLOCK_ONLY_HIGH safety settings for model: {self.model_name}"
                )

            except AttributeError as e:
                logging.error(f"Error configuring Google Generative AI: {e}")
                self.model = None
            except Exception as e:
                # Handle potential API key or configuration errors
                logging.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None

    def before_load(self):
        """Clean up model instance before reloading."""
        self.model = None

    def cancel(self):
        """Set cancellation flag to interrupt operations."""
        self.close_requested = True


class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed. Supports APIs with organization
    and project authentication.
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
        """Initialize OpenAI client with configured settings."""
        self.client = OpenAI(
            api_key=self.api_key,
            base_url=self.api_base,
            organization=self.api_organisation,
            project=self.api_project,
        )

    def before_load(self):
        """Clean up client before reloading."""
        self.client = None

    def cancel(self):
        """Set cancellation flag."""
        self.close_requested = True


def find_ollama_executable():
    """
    Find the Ollama executable in standard installation locations.
    Returns the path to ollama executable or None if not found.
    """
    import shutil

    # First try to find ollama in PATH
    ollama_path = shutil.which("ollama")
    if ollama_path:
        return ollama_path

    # If not found in PATH, check standard installation locations
    system = platform.system().lower()

    if system == "windows":
        # Standard Windows installation locations
        possible_paths = [
            os.path.expanduser("~\\AppData\\Local\\Programs\\Ollama\\ollama.exe"),
            "C:\\Program Files\\Ollama\\ollama.exe",
            "C:\\Program Files (x86)\\Ollama\\ollama.exe",
        ]
    elif system == "linux":
        # Standard Linux installation locations
        possible_paths = [
            "/usr/local/bin/ollama",
            "/usr/bin/ollama",
            os.path.expanduser("~/.local/bin/ollama"),
        ]
    else:
        return None

    # Check each possible path
    for path in possible_paths:
        if os.path.isfile(path) and os.access(path, os.X_OK):
            return path

    return None


def is_ollama_installed():
    """
    Check if Ollama is installed and available on the system.
    Returns True if Ollama is installed, False otherwise.
    """
    ollama_path = find_ollama_executable()
    if not ollama_path:
        return False

    try:
        result = subprocess.run([ollama_path, "--version"], check=False, capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
        return False


def install_ollama_auto(app):
    """
    Automatically detect platform and install Ollama.
    """
    system = platform.system().lower()

    if system == "windows":
        return install_ollama_windows(app)
    elif system == "linux":
        return install_ollama_linux(app)
    else:
        app.show_message_signal.emit(
            "Plateforme non supportée",
            f"L'installation automatique n'est pas supportée sur {system}.\n\nVeuillez installer manuellement depuis https://ollama.com",
        )
        return False


def install_ollama_windows(app):
    """
    Download and install Ollama on Windows automatically.
    Shows a progress window with animated loading dots during the process.
    """
    from ui.ProgressWindow import OllamaInstallProgressWindow
    from PySide6.QtWidgets import QApplication

    # Create and show progress window
    progress_window = OllamaInstallProgressWindow()
    progress_window.show()
    progress_window.start_animation()

    # Process events to show the window
    QApplication.processEvents()

    cancelled = False

    def on_cancel():
        nonlocal cancelled
        cancelled = True

    progress_window.cancelled.connect(on_cancel)

    try:
        # Import requests here to avoid issues if not available
        import requests

        if cancelled:
            return False

        # Download Ollama installer
        ollama_url = "https://ollama.com/download/OllamaSetup.exe"

        with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
            temp_path = temp_file.name

            response = requests.get(ollama_url, stream=True, allow_redirects=True)
            response.raise_for_status()

            total_size = int(response.headers.get('content-length', 0))
            downloaded = 0

            for chunk in response.iter_content(chunk_size=8192):
                if cancelled:
                    progress_window.close()
                    try:
                        os.unlink(temp_path)
                    except:
                        pass
                    return False

                if chunk:
                    temp_file.write(chunk)
                    downloaded += len(chunk)

                # Process events to keep UI responsive
                QApplication.processEvents()

        if cancelled:
            progress_window.close()
            try:
                os.unlink(temp_path)
            except:
                pass
            return False

        # Switch to installing state
        progress_window.set_installing()
        QApplication.processEvents()

        # Run installer with elevated privileges
        result = subprocess.run([temp_path], check=False)

        # Switch to finishing state
        progress_window.set_finishing()
        QApplication.processEvents()

        # Clean up temp file
        try:
            os.unlink(temp_path)
        except:
            pass

        progress_window.close()

        if result.returncode == 0:
            app.show_message_signal.emit(
                "Installation réussie",
                "Ollama a été installé avec succès ! Vous pouvez maintenant télécharger des modèles.",
            )
            return True
        else:
            app.show_message_signal.emit("Installation annulée", "L'installation d'Ollama a été annulée ou a échoué.")
            return False

    except ImportError:
        progress_window.close()
        app.show_message_signal.emit(
            "Erreur", "La bibliothèque 'requests' n'est pas disponible. Installation manuelle requise."
        )
        return False
    except Exception as e:
        progress_window.close()
        logging.exception(f"Error installing Ollama: {e}")
        app.show_message_signal.emit(
            "Erreur d'installation",
            f"Erreur lors de l'installation d'Ollama: {str(e)}\n\nVeuillez installer manuellement depuis https://ollama.com",
        )
        return False


def install_ollama_linux(app):
    """
    Install Ollama on Linux using the official installation script.
    """
    from ui.ProgressWindow import OllamaInstallProgressWindow
    from PySide6.QtWidgets import QApplication

    # Create and show progress window
    progress_window = OllamaInstallProgressWindow()
    progress_window.show()
    progress_window.start_animation()

    # Process events to show the window
    QApplication.processEvents()

    cancelled = False

    def on_cancel():
        nonlocal cancelled
        cancelled = True

    progress_window.cancelled.connect(on_cancel)

    try:
        if cancelled:
            return False

        # Use the official Ollama installation script for Linux
        install_command = "curl -fsSL https://ollama.com/install.sh | sh"

        progress_window.set_installing()
        QApplication.processEvents()

        # Run the installation command
        result = subprocess.run(install_command, shell=True, check=False, capture_output=True, text=True)

        if cancelled:
            progress_window.close()
            return False

        progress_window.set_finishing()
        QApplication.processEvents()

        progress_window.close()

        if result.returncode == 0:
            app.show_message_signal.emit(
                "Installation réussie",
                "Ollama a été installé avec succès ! Vous pouvez maintenant télécharger des modèles.",
            )
            return True
        else:
            error_msg = result.stderr if result.stderr else "Erreur inconnue"
            app.show_message_signal.emit(
                "Erreur d'installation",
                f"L'installation d'Ollama a échoué:\n\n{error_msg}\n\nVeuillez installer manuellement depuis https://ollama.com",
            )
            return False

    except Exception as e:
        progress_window.close()
        logging.exception(f"Error installing Ollama on Linux: {e}")
        app.show_message_signal.emit(
            "Erreur d'installation",
            f"Erreur lors de l'installation d'Ollama: {str(e)}\n\nVeuillez installer manuellement depuis https://ollama.com",
        )
        return False


def get_ollama_models():
    """
    Get list of installed Ollama models by running 'ollama list' command.
    Returns a list of tuples (display_name, model_name) for installed models.

    Parses the command output to extract model names and sizes.
    Handles error cases (Ollama not installed, no models, etc.).
    """
    # Find Ollama executable
    ollama_path = find_ollama_executable()
    if not ollama_path:
        return [("Ollama not available - Please install it", "")]

    try:
        result = subprocess.run([ollama_path, "list"], check=False, capture_output=True, text=True, timeout=10)

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
                            # Convert size to proper format (e.g., "5.6GB" -> "(5.6 GB)")
                            if size_raw.upper().endswith("GB"):
                                size_value = size_raw[:-2]
                                size_info = f" ({size_value} GB)"
                            elif size_raw.upper().endswith("MB"):
                                size_value = size_raw[:-2]
                                size_info = f" ({size_value} MB)"
                            else:
                                size_info = f" ({size_raw})"

                        display_name = f"{model_name}{size_info}"
                        models.append((display_name, model_name))

            if models:
                return models
            # No models found, return message to install models
            return [("Please install Ollama models first", "")]
        logging.warning(f"Failed to get Ollama models: {result.stderr}")
        return [("Please install Ollama models first", "")]

    except (subprocess.TimeoutExpired, FileNotFoundError, Exception) as e:
        logging.warning(f"Could not run 'ollama list': {e}")
        return [("Ollama not available - Please install it", "")]


class OllamaProvider(AIProvider):
    """
    Provider for connecting to an Ollama server.

    Uses the /chat endpoint of the Ollama server to generate a response.
    Streaming is not used. Supports configuration of model keep-alive time
    and custom models.
    """

    def __init__(self, app: 'WritingToolApp'):
        self.close_requested = None
        self.client = None
        self.app = app

        # Get available Ollama models
        ollama_models = get_ollama_models()

        # Set default model to first available model or empty string
        default_ollama_model = ""
        if ollama_models and ollama_models[0][1]:  # Check if first model has a valid value
            default_ollama_model = ollama_models[0][1]

        settings = [
            TextSetting(
                "api_base",
                "API Base URL",
                "http://localhost:11434",
                "E.g. http://localhost:11434",
            ),
            DropdownSetting(
                name="api_model",
                display_name="API Model (detected automatically)",
                default_value=default_ollama_model,
                description="Models are automatically detected from your Ollama installation",
                options=ollama_models,
                editable=False,  # Don't allow custom model names for Ollama
                refresh_callback=self._refresh_models,
            ),
            TextSetting(
                "keep_alive",
                "Time to keep the model loaded in memory in minutes",
                "5",
                "E.g. 5",
            ),
        ]

        # Determine button text and action based on Ollama installation status
        if is_ollama_installed():
            button_text = "Instructions d'installation"
            button_action = lambda: webbrowser.open(
                "https://github.com/theJayTea/WritingTools?tab=readme-ov-file#-optional-ollama-local-llm-instructions-for-windows-v7-onwards"
            )
            description = "• Connect to an Ollama server (local LLM).\n• Ollama est installé et prêt à utiliser."
        else:
            button_text = "Installer Ollama automatiquement"
            button_action = lambda: self._install_ollama()
            description = "• Connect to an Ollama server (local LLM).\n• Ollama n'est pas installé. Cliquez sur le bouton pour l'installer automatiquement."

        super().__init__(
            app,
            "Ollama (For Experts)",
            settings,
            description,
            "ollama",
            button_text,
            button_action,
            "ollama",
        )

        # Add refresh button for updating the interface after installation
        self.add_button("🔄 Actualiser", self._refresh_ui, "secondary")

    def _refresh_models(self):
        """Refresh the list of available Ollama models."""
        ollama_models = get_ollama_models()
        for setting in self.settings:
            if setting.name == "api_model" and hasattr(setting, 'refresh_options'):
                setting.refresh_options(ollama_models)
                break

    def refresh_configuration(self):
        """Refresh the Ollama provider configuration based on current installation status."""
        # Re-detect Ollama installation status and update configuration
        if is_ollama_installed():
            self.button_text = "Instructions d'installation"
            self.button_action = lambda: webbrowser.open(
                "https://github.com/theJayTea/WritingTools?tab=readme-ov-file#-optional-ollama-local-llm-instructions-for-windows-v7-onwards"
            )
            self.description = "• Connect to an Ollama server (local LLM).\n• Ollama est installé et prêt à utiliser."
        else:
            self.button_text = "Installer Ollama automatiquement"
            self.button_action = lambda: self._install_ollama()
            self.description = "• Connect to an Ollama server (local LLM).\n• Ollama n'est pas installé. Cliquez sur le bouton pour l'installer automatiquement."

        # Update model list and settings
        ollama_models = get_ollama_models()
        for setting in self.settings:
            if setting.name == "api_model" and hasattr(setting, 'refresh_options'):
                # Refresh the dropdown options
                setting.refresh_options(ollama_models)
                # Update default value if models are available and current value is empty
                current_value = setting.get_value() if hasattr(setting, 'get_value') else ""
                if ollama_models and ollama_models[0][1] and not current_value:
                    setting.set_value(ollama_models[0][1])
                break

    def _refresh_ui(self):
        """Refresh the UI to reflect current Ollama installation status."""
        # Use the refresh_configuration method to update the provider
        self.refresh_configuration()

        # Refresh the provider UI
        if hasattr(self.app, 'settings_window') and self.app.settings_window:
            self.app.settings_window._on_provider_changed()

    def _install_ollama(self):
        """Handle Ollama installation and UI refresh."""
        success = install_ollama_auto(self.app)
        if success:
            # Automatically refresh UI after successful installation
            self._refresh_ui()

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
                    "Ollama Error",
                    "No Ollama model selected. Please install and select a model in settings first.",
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
        """Initialize Ollama client with configured base URL."""
        self.client = OllamaClient(host=self.api_base)

    def before_load(self):
        """Clean up client before reloading."""
        self.client = None

    def cancel(self):
        """Set cancellation flag."""
        self.close_requested = True


class AnthropicProvider(AIProvider):
    """
    Anthropic (Claude) AI Provider for Writing Tools.

    Uses the Anthropic API to generate content with Claude models.
    Implements authentication via API key and supports different Claude models.
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
        """
        Generate response using Anthropic's Claude API.

        Supports conversation history for multi-turn interactions.
        Uses Anthropic's OpenAI-compatible endpoint for simplicity.
        """
        logging.debug(f"AnthropicProvider.get_response called with return_response={return_response}")
        logging.debug(
            f"AnthropicProvider current config - api_key: {self.api_key[:10] if self.api_key else 'None'}..., api_model: {self.api_model}"
        )

        # Reset cancellation flag at start of new request (like other providers)
        self.close_requested = False

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
                logging.debug(f"AnthropicProvider: Returning response text (length: {len(response_text)})")
                return response_text
            # Emit the response via signal for direct replacement
            logging.debug(f"AnthropicProvider: Emitting output_ready_signal with text (length: {len(response_text)})")
            self.app.output_ready_signal.emit(response_text)
            logging.debug("AnthropicProvider: Signal emitted successfully")
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
        """Initialize Anthropic client with proper authentication."""
        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.anthropic.com/v1",
            default_headers={
                "anthropic-version": "2023-06-01",
            },
        )

    def before_load(self):
        """Clean up client before reloading."""
        self.client = None

    def cancel(self):
        """Set cancellation flag."""
        self.close_requested = True


class MistralProvider(AIProvider):
    """
    Mistral AI Provider for Writing Tools.

    Uses the Mistral API to generate content with Mistral models.
    Uses direct HTTP requests for better control and reliability.
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
        """
        Generate response using Mistral API.

        Uses direct HTTP requests via requests library for maximum control
        over request format and error handling.
        """
        logging.debug(f"MistralProvider.get_response called with return_response={return_response}")
        logging.debug(
            f"MistralProvider current config - api_key: {self.api_key[:10] if self.api_key else 'None'}..., api_model: {self.api_model}",
        )

        # Reset cancellation flag at start of new request (like other providers)
        self.close_requested = False

        if self.close_requested:
            return ""

        try:
            # Check if requests library is available
            if requests is None:
                raise ImportError("requests library not available")

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

        except ImportError as e:
            error_msg = f"Missing required library: {e}. Please install 'requests' library."
            logging.error(error_msg)
            self.app.show_message_signal.emit(
                "Missing Library",
                "The 'requests' library is required for Mistral API. Please install it using: pip install requests",
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
        """No client initialization needed - using requests directly."""
        pass

    def before_load(self):
        """No client cleanup needed."""
        pass

    def cancel(self):
        """Set cancellation flag."""
        self.close_requested = True
