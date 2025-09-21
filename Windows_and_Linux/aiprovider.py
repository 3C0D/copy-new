"""
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

"""

# Disable Pylance reportPrivateImportUsage for google.generativeai
# pyright: reportPrivateImportUsage=false

# Standard library imports
import copy
import io
import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
import webbrowser
from abc import ABC, abstractmethod
from concurrent.futures import CancelledError, ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Any, Callable, Optional, Union, cast

import requests

# Third-party imports (with fallbacks for optional dependencies)
from ollama import Client as OllamaClient
from openai import OpenAI
from PIL import Image as PILImage

# PySide6 imports
from PySide6 import QtCore
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
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
from config.constants import ANTHROPIC_MODELS, GEMINI_MODELS, MISTRAL_MODELS, OPENAI_MODELS
from config.data_operations import get_default_model_for_provider
from ui.ProgressWindow import OllamaInstallProgressWindow

# Type checking imports
if TYPE_CHECKING:
    from config.interfaces import ProviderConfig
    from WritingToolApp import WritingToolApp


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
        app: "WritingToolApp",
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
        app: "WritingToolApp",
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
                option, value, _ = option_tuple
                self.dropdown.addItem(option, value)
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

            # Clear and repopulate dropdown
            self.dropdown.clear()
            self.options = new_options

            for option_tuple in self.options:
                if len(option_tuple) == 2:
                    option, value = option_tuple
                    self.dropdown.addItem(option, value)
                elif len(option_tuple) == 3:
                    option, value, _ = option_tuple
                    self.dropdown.addItem(option, value)
                    # Store metadata (vision support) if necessary
                else:
                    self._logger.warning(f"Unexpected option format: {option_tuple}")

            # Restore selection if possible
            if current_value:
                index = self.dropdown.findData(current_value)
                if index != -1:
                    self.dropdown.setCurrentIndex(index)
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
        app: "WritingToolApp",
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
        self, system_instruction: str, prompt: str, return_response: bool = False, **kwargs
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
        self, system_instruction: str, prompt: str, return_response: bool = False, **kwargs
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


class GeminiProvider(AIProvider):
    """
    Provider for Google's Gemini API.

    Uses google.generativeai.GenerativeModel.generate_content() to generate text.
    Streaming is no longer offered so we always do a single-shot call.
    Handles safety settings to allow less restricted content.
    """

    def __init__(self, app: "WritingToolApp"):
        self.model: Any = None

        settings = [
            TextSetting(
                app,
                name="api_key",
                display_name="API Key",
                description="Paste your Gemini API key here",
            ),
            DropdownSetting(
                app,
                name="api_model",
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

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: str,
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Generate content using Gemini.
        Includes retry logic for safety filter blocks.
        """
        image_data: str | None = kwargs.get("image_data")
        # DEBUG: Log the incoming request
        self._logger.debug("🔥 GeminiProvider.get_response called")
        self._logger.debug(f"🔥 system_instruction length: {len(system_instruction)}")
        self._logger.debug(f"🔥 prompt length: {len(prompt)}")
        self._logger.debug(f"🔥 prompt preview:\n{prompt[:200]}...")
        self._logger.debug(f"🔥 return_response: {return_response}")
        self._logger.debug(f"🔥 image_data present: {image_data is not None}")

        # Check if model is configured
        if not self.model:
            error_msg = "Gemini API key not configured. Please add your API key in settings."
            self._logger.error(error_msg)
            if not return_response:
                self.app.show_message_signal.emit(
                    "API Key Missing",
                    "Your Gemini API key is not configured or invalid. Please go to Settings and add a valid API key.",
                )
                return ""
            return error_msg

        # Retry logic for safety filters - up to 3 attempts
        max_retries = 3
        for attempt in range(max_retries):
            attempt_num = attempt + 1
            self._logger.debug(f"Gemini API call - Attempt {attempt_num}/{max_retries}")

            try:
                # Prepare content for Gemini
                if image_data:
                    # Convert base64 to PIL Image like in gemini_integration.py
                    self._logger.debug(
                        f"🖼️\u00a0 GeminiProvider: Converting base64 to PIL Image - length: {len(image_data)}"
                    )
                    if PILImage is not None and io is not None:
                        try:
                            import base64

                            # Decode base64 to bytes
                            image_bytes = base64.b64decode(image_data)
                            # Create PIL Image from bytes
                            pil_image = PILImage.open(io.BytesIO(image_bytes))
                            self._logger.debug(
                                f" 🖼️\u00a0 GeminiProvider: PIL Image created - size: {pil_image.size}, mode: {pil_image.mode}"
                            )

                            # For image analysis, create content with PIL Image and text
                            contents = [system_instruction, pil_image, prompt]
                        except Exception as img_error:
                            self._logger.error(
                                f" 🖼️\u00a0 GeminiProvider: Failed to convert base64 to PIL Image: {img_error}"
                            )
                            # Fallback to inline_data format
                            contents = [
                                system_instruction,
                                {"inline_data": {"mime_type": "image/png", "data": image_data}},
                                prompt,
                            ]
                    else:
                        self._logger.warning(
                            " 🖼️\u00a0 GeminiProvider: PIL not available, using inline_data format"
                        )
                        # Fallback to inline_data format when PIL is not available
                        contents = [
                            system_instruction,
                            {"inline_data": {"mime_type": "image/png", "data": image_data}},
                            prompt,
                        ]
                else:
                    # For text-only requests
                    contents = [system_instruction, prompt]

                # Single-shot call with streaming disabled
                response = self.model.generate_content(contents=contents, stream=False)

                # Check if response was blocked by safety filters
                if not response.candidates:
                    error_detail = "🔥 No candidates in response - empty response"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        error_msg = "Gemini blocked the request due to safety concerns. Try rephrasing your request."
                        self._logger.error("Gemini response blocked - no candidates returned")
                        self.app.show_message_signal.emit(
                            "Content Blocked",
                            "Your request has been blocked by Gemini's safety filters. Please try rephrasing your request to be more neutral.",
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
                    error_detail = f"🔥 Safety filter activated (code {candidate.finish_reason})"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        error_msg = "Gemini blocked the response due to safety filters. Try rephrasing your request to be more neutral."
                        self._logger.warning(
                            f"Gemini safety filter triggered. Finish reason: {candidate.finish_reason}"
                        )
                        self.app.show_message_signal.emit(
                            "Content Blocked by Safety Filters",
                            error_msg,
                        )
                        return ""
                elif candidate.finish_reason == 3:  # RECITATION - No retry for copyright issues
                    error_detail = f"🔥 Copyright filter activated (code {candidate.finish_reason})"
                    self._logger.warning(
                        f"🔥 Attempt {attempt_num}: {error_detail} - No retry for copyright issues"
                    )
                    error_msg = "Gemini blocked the response due to potential copyright concerns. Try a more original request."
                    self._logger.warning(
                        f"Gemini recitation filter triggered. Finish reason: {candidate.finish_reason}"
                    )
                    self.app.show_message_signal.emit(
                        "Content Blocked - Copyright Concern",
                        error_msg,
                    )
                    return ""
                elif candidate.finish_reason not in [
                    1,
                    None,
                ]:  # Not STOP or unset - No retry for other issues
                    error_detail = f"🔥 Unexpected error code (code {candidate.finish_reason})"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail} - No retry")
                    error_msg = f"Gemini could not complete the response (reason code: {candidate.finish_reason}). Please try again."
                    self._logger.warning(f"Gemini unusual finish reason: {candidate.finish_reason}")
                    self.app.show_message_signal.emit(
                        "Response Incomplete",
                        error_msg,
                    )
                    return ""

                # Check if response has content parts
                if not candidate.content or not candidate.content.parts:
                    error_detail = "🔥 Empty response - no content parts"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.show_message_signal.emit(
                            "Empty Response",
                            "Gemini returned an empty response. Please try rephrasing your request.",
                        )
                        return ""

                # Extract response text with proper error handling
                response_text = self._extract_response_text(response, candidate)
                self._logger.debug(f"Response text: {response_text}")

                if not response_text:
                    error_detail = "🔥 Could not extract text from response"
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.show_message_signal.emit(
                            "Response Processing Error",
                            "Could not process the response from Gemini. Please try again.",
                        )
                        return ""

                # Check if response text indicates safety filter (in case finish_reason doesn't show it)
                if self._contains_safety_filter_message(response_text):
                    error_detail = f"🔥 Safety filter message detected: {response_text[:100]}..."
                    self._logger.warning(f"🔥 Attempt {attempt_num}: {error_detail}")
                    if attempt < max_retries - 1:
                        self._logger.warning(f"🔥 Attempt {attempt_num} failed, retrying...")
                        continue
                    else:
                        self._logger.warning(
                            f"🔥 Final failure after {max_retries} attempts: {error_detail}"
                        )
                        self.app.show_message_signal.emit(
                            "Content Blocked by Safety Filters",
                            response_text,
                        )
                        return ""

                # If we get here, we have a valid response - log success and return it
                if attempt > 0:
                    self._logger.debug(f"Gemini response obtained after {attempt_num} attempt(s)")

                self._logger.debug(f"Gemini response length: {len(response_text)}")

                # Direct replacement
                if not return_response and not hasattr(self.app, "current_response_window"):
                    self._logger.debug(
                        f"🔥 Gemini emitting signal with response_text length: {len(response_text)}"
                    )
                    self._logger.debug(
                        f"🔥 Gemini response_text preview: '{response_text[:200]}...'"
                    )
                    self.app.output_ready_signal.emit(response_text)
                    self._logger.debug("🔥 Gemini signal emitted, returning empty string")
                    return ""
                # Response window
                return response_text

            except Exception as e:
                error_str = str(e)
                self._logger.exception(f"Error processing Gemini response: {error_str}")

                # Handle specific Gemini API errors with user-friendly messages
                if "API_KEY_INVALID" in error_str or "invalid API key" in error_str.lower():
                    self.app.show_message_signal.emit(
                        "Invalid API Key",
                        "Your Gemini API key is invalid. Please check your API key in Settings and make sure it's correct.",
                    )
                    return ""
                elif (
                    "quota exceeded" in error_str.lower()
                    or "resource exhausted" in error_str.lower()
                ):
                    self.app.show_message_signal.emit(
                        "Quota Exceeded",
                        "You've exceeded your Gemini API quota. Please check your usage limits or try again later.",
                    )
                    return ""
                elif "rate limit" in error_str.lower():
                    self.app.show_message_signal.emit(
                        "Rate Limit Hit",
                        "You're sending requests too quickly. Please wait a moment and try again.",
                    )
                    return ""
                elif "finish_reason" in error_str.lower() and "safety" in error_str.lower():
                    self.app.show_message_signal.emit(
                        "Content Blocked",
                        "Gemini blocked the request due to safety concerns. Try rephrasing your request to be more neutral.",
                    )
                    return ""
                else:
                    # For other errors, if we have retries left, continue
                    if attempt < max_retries - 1:
                        self._logger.warning(
                            f"Gemini API error on attempt {attempt + 1}/{max_retries}: {error_str}, retrying..."
                        )
                        continue
                    else:
                        # Generic error with option to check settings
                        self.app.show_message_signal.emit(
                            "API Error",
                            f"An error occurred with the Gemini API:\n\n{error_str}\n\nPlease check your API key and settings.",
                        )
                        return ""

        return ""

    def _extract_response_text(self, response, candidate) -> str:
        """Extract text from Gemini response with fallback."""
        try:
            return response.text.rstrip("\n")
        except ValueError as text_error:
            # Fallback: manually extract text from parts
            self._logger.warning(f"🔥 Gemini ValueError in response.text: {text_error}")
            text_parts = []
            for part in candidate.content.parts:
                if hasattr(part, "text") and part.text:
                    text_parts.append(part.text)

            if text_parts:
                response_text = "".join(text_parts).rstrip("\n")
                self._logger.debug(f"🔥 Gemini fallback response_text: '{response_text}'")
                return response_text
            else:
                self._logger.warning(f"🔥 Unable to extract text: {str(text_error)}")
                return ""

    def _contains_safety_filter_message(self, text: str) -> bool:
        """Check if text contains safety filter messages."""
        safety_filter_messages = [
            "Content Blocked by Safety Filters",
            "Gemini blocked the response due to safety filters",
        ]
        return any(msg.lower() in text.lower() for msg in safety_filter_messages)

    def after_load(self) -> None:
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
                try:
                    civic_integrity_category = getattr(
                        HarmCategory, "HARM_CATEGORY_CIVIC_INTEGRITY", None
                    )
                    if civic_integrity_category is not None:
                        safety_settings[civic_integrity_category] = (
                            HarmBlockThreshold.BLOCK_ONLY_HIGH
                        )
                except (AttributeError, TypeError):
                    # Handle cases where HarmCategory might be None or attribute doesn't exist
                    pass

                self.model = genai.GenerativeModel(
                    model_name=self.api_model,
                    generation_config=genai.types.GenerationConfig(
                        candidate_count=1,
                        max_output_tokens=1000,
                        temperature=0.5,
                    ),
                    safety_settings=safety_settings,
                )

                # Log the safety configuration for debugging
                self._logger.debug(
                    f"Gemini model initialized with BLOCK_ONLY_HIGH safety settings for model: {self.api_model}"
                )

            except AttributeError as e:
                self._logger.error(f"Error configuring Google Generative AI: {e}")
                self.model = None
            except Exception as e:
                # Handle potential API key or configuration errors
                self._logger.error(f"Failed to initialize Gemini model: {e}")
                self.model = None
        else:
            self.model = None

    def before_load(self) -> None:
        """Clean up model instance before reloading."""
        self.model = None


class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed. Supports APIs with organization
    and project authentication.
    """

    def __init__(self, app: "WritingToolApp"):
        self.client: Any = None

        settings = [
            TextSetting(
                app,
                name="api_key",
                display_name="API Key",
                description="API key for the OpenAI-compatible API.",
            ),
            TextSetting(
                app,
                "api_base",
                "API Base URL",
                "https://api.openai.com/v1",
                "E.g. https://api.openai.com/v1",
            ),
            TextSetting(
                app,
                "api_organisation",
                "API Organisation",
                "",
                "Leave blank if not applicable.",
            ),
            TextSetting(app, "api_project", "API Project", "", "Leave blank if not applicable."),
            DropdownSetting(
                app,
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

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Send a chat request to the OpenAI-compatible API.

        Always performs a non-streaming request.
        If prompt is not a list, builds a simple two-message conversation.
        Supports image analysis if image_data is provided.
        Returns the response text if return_response is True,
        otherwise emits it via output_ready_signal.
        """
        image_data = kwargs.get("image_data")
        if isinstance(prompt, list):
            messages = prompt
        else:
            # Handle image data if provided
            if image_data:
                user_content = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            else:
                user_content = prompt

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ]

        try:
            self._logger.debug("🔄 OpenAICompatibleProvider._get_response_impl called")
            self._logger.debug(f"🔄 Client instance exists: {self.client is not None}")
            self._logger.debug(f"🔄 API key configured: {bool(self.api_key)}")
            self._logger.debug(f"🔄 API model configured: {bool(self.api_model)}")

            if self.client is None:
                self._logger.error("❌ OpenAI client is None - provider not properly initialized")
                self.app.show_message_signal.emit(
                    "Error",
                    "OpenAI client not initialized. Please check your API settings.",
                )
                return ""

            self._logger.debug(f"🔄 Making API call to model: {self.api_model}")
            self._logger.debug(f"🔄 Messages count: {len(messages)}")

            response = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,  # type: ignore
                temperature=0.5,
                stream=False,
            )

            self._logger.debug("🔄 API call completed successfully")
            self._logger.debug(
                f"🔄 Response choices count: {len(response.choices) if response.choices else 0}"
            )

            if response.choices and len(response.choices) > 0:
                response_text = response.choices[0].message.content.rstrip("\n")
                self._logger.debug(
                    f"🔄 Response text length: {len(response_text) if response_text else 0}"
                )
            else:
                self._logger.error("❌ No choices in API response")
                response_text = ""

            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)
            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Error while generating content: {error_str}")

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

    def after_load(self) -> None:
        """Initialize OpenAI client with configured settings."""
        if OpenAI is not None:
            try:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url=self.api_base,
                    organization=self.api_organisation,
                    project=self.api_project,
                )
            except Exception as e:
                self._logger.error(f"Failed to create OpenAI client: {e}")
                self.client = None
        else:
            self.client = None

    def before_load(self) -> None:
        """Clean up client before reloading."""
        self._logger.debug("🧹 OpenAICompatibleProvider.before_load called - cleaning up client")
        self.client = None


class OllamaStateManager(QObject):
    """
    Singleton manager for Ollama state to avoid redundant checks.
    Uses caching and async operations to prevent UI blocking.
    """

    # Signals for async updates
    state_updated = Signal()
    models_updated = Signal(list)

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.initialized = True
            self._logger = logging.getLogger(self.__class__.__name__)

            # Cache states
            self._ollama_path: Optional[str] = None
            self._is_installed: Optional[bool] = None
            self._is_running: Optional[bool] = None
            self._models_list: list[tuple[str, str]] = []

            # Cache timestamps (in seconds)
            self._path_check_time = 0
            self._running_check_time = 0
            self._models_check_time = 0

            # Cache duration in seconds
            self.CACHE_DURATION = 30  # 30 seconds cache
            self.QUICK_CHECK_DURATION = 5  # 5 seconds for running status

            # Thread executor for async operations
            self._executor = ThreadPoolExecutor(max_workers=2)

            # Timer for periodic checks
            self._check_timer = QTimer()
            self._check_timer.timeout.connect(self._periodic_check)
            self._check_timer.start(30000)  # Check every 30 seconds

    def _get_current_time(self) -> float:
        """Get current time in seconds."""
        import time

        return time.time()

    def _is_cache_valid(self, check_time: float, duration: float) -> bool:
        """Check if cached value is still valid."""
        return (self._get_current_time() - check_time) < duration

    def find_ollama_executable(self, force_refresh: bool = False) -> Optional[str]:
        """
        Find the Ollama executable with caching.
        """
        if (
            not force_refresh
            and self._ollama_path
            and self._is_cache_valid(self._path_check_time, self.CACHE_DURATION)
        ):
            return self._ollama_path

        # First try to find ollama in env PATH
        ollama_path = shutil.which("ollama")
        if ollama_path:
            self._ollama_path = ollama_path
            self._path_check_time = self._get_current_time()
            return ollama_path

        # Check standard installation locations
        system = platform.system().lower()
        possible_paths = []

        if system == "windows":
            possible_paths = [
                Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe",
                Path("C:") / "Program Files" / "Ollama" / "ollama.exe",
                Path("C:") / "Program Files (x86)" / "Ollama" / "ollama.exe",
            ]
        elif system == "linux":
            possible_paths = [
                Path("/usr/local/bin/ollama"),
                Path("/usr/bin/ollama"),
                Path.home() / ".local" / "bin" / "ollama",
            ]

        for path in possible_paths:
            if path.is_file() and os.access(path, os.X_OK):
                self._ollama_path = str(path)
                self._path_check_time = self._get_current_time()
                return self._ollama_path

        self._ollama_path = None
        self._path_check_time = self._get_current_time()
        return None

    def is_ollama_installed(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama is installed with caching.
        """
        if (
            not force_refresh
            and self._is_installed is not None
            and self._is_cache_valid(self._path_check_time, self.CACHE_DURATION)
        ):
            return self._is_installed

        ollama_path = self.find_ollama_executable(force_refresh)
        self._is_installed = ollama_path is not None
        return self._is_installed

    def is_ollama_running(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama is running with short-term caching.
        """
        if (
            not force_refresh
            and self._is_running is not None
            and self._is_cache_valid(self._running_check_time, self.QUICK_CHECK_DURATION)
        ):
            return self._is_running

        # Use cached installation status to avoid redundant path finding
        if not self._is_installed:
            self._is_running = False
            self._running_check_time = self._get_current_time()
            return False

        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            self._is_running = False
            self._running_check_time = self._get_current_time()
            return False

        try:
            result = subprocess.run(
                [ollama_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=0.5,  # Reduced timeout for better performance
            )
            self._is_running = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._is_running = False

        self._running_check_time = self._get_current_time()
        return self._is_running

    def get_ollama_models(self, force_refresh: bool = False) -> list[tuple[str, str]]:
        """
        Get list of installed Ollama models with caching.
        """
        if (
            not force_refresh
            and self._models_list
            and self._is_cache_valid(self._models_check_time, self.CACHE_DURATION)
        ):
            return self._models_list

        if not self.is_ollama_installed():
            self._models_list = [("Ollama not available - Please install it", "")]
            return self._models_list

        if not self.is_ollama_running():
            self._models_list = [("Ollama not running - Please start Ollama", "")]
            return self._models_list

        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            self._models_list = [("Ollama not available", "")]
            return self._models_list

        try:
            result = subprocess.run(
                [ollama_path, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,  # Longer timeout for list operation
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                models = []

                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_name = parts[0]
                            size_info = ""
                            if len(parts) >= 3:
                                size_raw = parts[2]
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
                    self._models_list = models
                else:
                    self._models_list = [("Please install Ollama models first", "")]
            else:
                self._models_list = [("Please install Ollama models first", "")]

        except subprocess.TimeoutExpired:
            self._models_list = [("Ollama not running - Please start Ollama", "")]
        except Exception:
            self._models_list = [("", "")]

        self._models_check_time = self._get_current_time()
        return self._models_list

    def refresh_models_async(self):
        """
        Refresh models asynchronously without blocking the UI.
        """

        def _refresh():
            models = self.get_ollama_models(force_refresh=True)
            self.models_updated.emit(models)

        self._executor.submit(_refresh)

    def refresh_state_async(self):
        """
        Refresh Ollama state asynchronously.
        """

        def _refresh():
            self.is_ollama_installed(force_refresh=True)
            self.is_ollama_running(force_refresh=True)
            self.state_updated.emit()

        self._executor.submit(_refresh)

    def _periodic_check(self):
        """
        Periodic background check of Ollama state.
        """
        self.refresh_state_async()

    def remove_ollama_model(self, model_name: str) -> tuple[bool, str]:
        """
        Remove an Ollama model.
        """
        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            return False, "Ollama not available - Please install it"

        try:
            result = subprocess.run(
                [ollama_path, "rm", model_name],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
            )

            if result.returncode == 0:
                # Invalidate models cache
                self._models_check_time = 0
                self.refresh_models_async()
                return True, f"Model '{model_name}' removed successfully"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "not found" in error_msg.lower():
                    return False, f"Model '{model_name}' not found"
                elif "in use" in error_msg.lower():
                    return False, f"Model '{model_name}' is currently in use"
                else:
                    return False, f"Failed to remove model '{model_name}': {error_msg}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout while removing model '{model_name}'"
        except Exception as e:
            return False, f"Error removing model '{model_name}': {str(e)}"

    def install_ollama(self, app, progress_callback=None) -> bool:
        """
        Install Ollama with progress updates.
        """
        system = platform.system().lower()

        if system == "windows":
            success = self._install_ollama_windows(app, progress_callback)
        elif system == "linux":
            success = self._install_ollama_linux(app, progress_callback)
        else:
            app.show_message_signal.emit(
                "Unsupported platform",
                f"Automatic installation is not supported on {system}.\n\n"
                f"Please install manually from https://ollama.com",
            )
            return False

        if success:
            # Invalidate all caches after installation
            self._ollama_path = None
            self._is_installed = None
            self._is_running = None
            self._path_check_time = 0
            self._running_check_time = 0
            self.refresh_state_async()

        return success

    def _install_ollama_windows(self, app, progress_callback) -> bool:
        """Windows installation implementation."""
        # Implementation similar to your existing install_ollama_windows
        # but using the progress_callback for updates
        try:
            import requests

            ollama_url = "https://ollama.com/download/OllamaSetup.exe"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
                temp_path = temp_file.name

                response = requests.get(ollama_url, stream=True, allow_redirects=True)
                response.raise_for_status()

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                    if progress_callback:
                        progress_callback("downloading")

            if progress_callback:
                progress_callback("installing")

            result = subprocess.run([temp_path], check=False)

            try:
                os.unlink(temp_path)
            except OSError:
                pass

            return result.returncode == 0

        except Exception as e:
            self._logger.exception(f"Error installing Ollama: {e}")
            return False

    def _install_ollama_linux(self, app, progress_callback) -> bool:
        """Linux installation implementation."""
        try:
            if progress_callback:
                progress_callback("installing")

            install_command = "curl -fsSL https://ollama.com/install.sh | sh"
            result = subprocess.run(
                install_command, shell=True, check=False, capture_output=True, text=True
            )

            return result.returncode == 0

        except Exception as e:
            self._logger.exception(f"Error installing Ollama on Linux: {e}")
            return False


class OllamaProvider(AIProvider):
    """
    Optimized Ollama provider with async operations and state caching.
    """

    def __init__(self, app: "WritingToolApp"):
        self.app = app
        self.client: Optional[OllamaClient] = None
        self._logger = logging.getLogger(self.__class__.__name__)

        # Use the singleton state manager
        self.state_manager = OllamaStateManager()

        # Connect to state updates
        self.state_manager.state_updated.connect(self._on_state_updated)
        self.state_manager.models_updated.connect(self._on_models_updated)

        # Get initial state (using cached values if available)
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_models = self.state_manager.get_ollama_models()

        # Set default model
        default_ollama_model = ""
        if ollama_models and ollama_models[0][1]:
            default_ollama_model = ollama_models[0][1]

        settings = [
            TextSetting(
                app,
                "api_base",
                "API Base URL",
                "http://localhost:11434",
                "E.g. http://localhost:11434",
            ),
            DropdownSetting(
                app,
                name="api_model",
                display_name="API Model (detected automatically)",
                default_value=default_ollama_model,
                description="Models are automatically detected from your Ollama installation",
                options=ollama_models,
                refresh_callback=self._refresh_models,
            ),
            TextSetting(
                app,
                "keep_alive",
                "Time to keep the model loaded in memory in minutes",
                "5",
                "E.g. 5",
            ),
        ]

        # Determine initial UI state and button text
        if ollama_installed:
            description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is installed and ready to use."
            )
            button_text = "Update Ollama"
        else:
            description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is not installed. Click the button to install it."
            )
            button_text = "Install Ollama"

        super().__init__(
            app,
            "Ollama",
            settings,
            description,
            "ollama",
            button_text,
            lambda: self._install_ollama_async(),
            "ollama",
        )

        # Add additional buttons if Ollama is installed
        if ollama_installed:
            self.add_button("🗑️ Delete Model", self._delete_model, "secondary")

        # Start async refresh on initialization
        self.state_manager.refresh_state_async()

    def _on_state_updated(self):
        """Handle state updates from the state manager."""
        self.refresh_configuration()
        # Update button text in settings window if it's open
        if hasattr(self.app, "settings_window") and self.app.settings_window:
            self.app.settings_window.update_provider_button_text()

    def _on_models_updated(self, models: list[tuple[str, str]]):
        """Handle model list updates."""
        for setting in self.settings:
            if setting.name == "api_model" and isinstance(setting, DropdownSetting):
                setting.refresh_options(models)
                # Update selection if needed
                current_value = setting.get_value() if hasattr(setting, "get_value") else ""
                if models and models[0][1] and not current_value:
                    setting.set_value(models[0][1])
                break

    def _refresh_models(self):
        """Refresh models asynchronously."""
        self.state_manager.refresh_models_async()

    def _install_ollama_async(self):
        """Install Ollama asynchronously."""

        progress_window = OllamaInstallProgressWindow(self.app)
        progress_window.show()
        progress_window.start_animation()

        def progress_callback(status):
            if status == "downloading":
                QApplication.processEvents()
            elif status == "installing":
                progress_window.set_installing()
                QApplication.processEvents()
            elif status == "finishing":
                progress_window.set_finishing()
                QApplication.processEvents()

        def install_thread():
            success = self.state_manager.install_ollama(self.app, progress_callback)
            progress_window.close()

            if success:
                self.app.show_message_signal.emit(
                    "Installation Successful", "Ollama has been installed successfully!"
                )
                # Refresh UI
                self.refresh_configuration()
                if hasattr(self.app, "settings_window") and self.app.settings_window:
                    self.app.settings_window._on_provider_changed()
            else:
                self.app.show_message_signal.emit(
                    "Installation Failed",
                    "Ollama installation failed. Please try again or install manually.",
                )

        # Run installation in a separate thread
        import threading

        thread = threading.Thread(target=install_thread)
        thread.start()

    def refresh_configuration(self):
        """Refresh configuration based on current state."""
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_running = self.state_manager.is_ollama_running() if ollama_installed else False

        if ollama_installed:
            self.description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is installed and ready to use."
            )
            self.button_text = "Update Ollama"
        else:
            self.description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is not installed. Click the button to install it."
            )
            self.button_text = "Install Ollama"

        # Update additional buttons
        self.additional_buttons = []
        if ollama_installed:
            self.add_button("🗑️ Delete Model", self._delete_model, "secondary")

        # Refresh models if installed and running
        if ollama_installed and ollama_running:
            self._refresh_models()

    def _delete_model(self):
        """Delete model implementation - same as before but using state_manager."""
        # Get models from state manager
        valid_models = [
            (display, model)
            for display, model in self.state_manager.get_ollama_models()
            if model and model.strip()
        ]

        if not valid_models:
            self.app.show_message_signal.emit(
                "No Models Available", "No Ollama models are available to delete."
            )
            return

        # Create selection dialog (same as before)
        dialog = QDialog()
        dialog.setWindowTitle("Delete Ollama Model")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        warning_label = QLabel("⚠️ Warning: This will permanently delete the selected model.")
        layout.addWidget(warning_label)

        model_label = QLabel("Select model to delete:")
        layout.addWidget(model_label)

        model_combo = QComboBox()
        for display_name, model_name in valid_models:
            model_combo.addItem(display_name, model_name)
        layout.addWidget(model_combo)

        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        delete_button = QPushButton("Delete Model")
        delete_button.clicked.connect(dialog.accept)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_model = model_combo.currentData()
            if selected_model:
                success, message = self.state_manager.remove_ollama_model(selected_model)

                if success:
                    self.app.show_message_signal.emit("Model Deleted", message)
                else:
                    self.app.show_message_signal.emit("Deletion Failed", message)

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """Send request to Ollama server."""
        # Check Ollama status before attempting to send request
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_running = self.state_manager.is_ollama_running()

        if not ollama_installed:
            error_msg = (
                "Ollama Not Installed",
                "Ollama is not installed on your system.\n\n"
                "Please go to Settings and use the 'Install Ollama' button to install it.\n\n"
                "Once installed, you can use Ollama for AI responses.",
            )
            self.app.show_message_signal.emit(error_msg[0], error_msg[1])
            return ""

        if not ollama_running:
            error_msg = (
                "Ollama Not Running",
                "Ollama is installed but not currently running.\n\n"
                "Please start Ollama using your system's Ollama application.\n"
                "On Windows: Click the Ollama icon in your system tray or start menu.\n"
                "On Linux: Run 'ollama serve' in a terminal.\n\n"
                "Or go to Settings to manage Ollama.",
            )
            self.app.show_message_signal.emit(error_msg[0], error_msg[1])
            return ""

        # Implementation remains the same as your original
        image_data = kwargs.get("image_data")
        if isinstance(prompt, list):
            messages = prompt
        else:
            if image_data:
                user_content = [
                    {"type": "text", "text": prompt},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
            else:
                user_content = prompt

            messages = [
                {"role": "system", "content": system_instruction},
                {"role": "user", "content": user_content},
            ]

        try:
            if not self.api_model or self.api_model.strip() == "":
                self.app.show_message_signal.emit("Ollama Error", "No Ollama model selected.")
                return ""

            if self.client is None:
                self.app.show_message_signal.emit("Error", "Ollama client not initialized.")
                return ""

            response = self.client.chat(model=self.api_model, messages=messages)
            response_text = response["message"]["content"].rstrip("\n")

            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)

            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Error during Ollama chat: {error_str}")

            if "connection" in error_str.lower() or "refused" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Connection Error", "Cannot connect to Ollama server."
                )
            else:
                self.app.show_message_signal.emit("Ollama Error", f"An error occurred: {error_str}")
            return ""

    def after_load(self):
        """Initialize Ollama client."""
        if OllamaClient is not None and self.state_manager.is_ollama_installed():
            try:
                self.client = OllamaClient(host=self.api_base)
                self._logger.debug("Ollama client initialized successfully")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Ollama client: {e}")
                self.client = None
        else:
            self.client = None

    def before_load(self):
        """Clean up client before reloading."""
        self.client = None


class AnthropicProvider(AIProvider):
    """
    Anthropic (Claude) AI Provider for Writing Tools.

    Uses the Anthropic API to generate content with Claude models.
    Implements authentication via API key and supports different Claude models.
    """

    def __init__(self, app: "WritingToolApp"):
        self.client: Any = None
        self.app: WritingToolApp = app
        self._logger = logging.getLogger(__name__)
        settings = [
            TextSetting(
                app,
                "api_key",
                "API Key",
                "",
                "Enter your Anthropic API key",
            ),
            DropdownSetting(
                app,
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("anthropic"),
                description="Select Claude model to use",
                options=ANTHROPIC_MODELS,
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

    def _get_response_impl(
        self, system_instruction: str, prompt: str, return_response: bool = False, **kwargs
    ) -> str:
        """
        Generate response using Anthropic's Claude API.

        Supports conversation history for multi-turn interactions.
        Uses Anthropic's OpenAI-compatible endpoint for simplicity.
        """
        conversation_history = kwargs.get("conversation_history")
        self._logger.debug(
            f"AnthropicProvider.get_response called with return_response={return_response}"
        )
        self._logger.debug(
            f"AnthropicProvider current config - api_key: {self.api_key[:10] if self.api_key else 'None'}..., api_model: {self.api_model}"
        )

        try:
            # Initialize client if not already done
            if not self.client and OpenAI is not None:
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
            # Ensure client is initialized before use
            if self.client is None and OpenAI is not None:
                self.client = OpenAI(
                    api_key=self.api_key,
                    base_url="https://api.anthropic.com/v1",
                    default_headers={
                        "anthropic-version": "2023-06-01",
                    },
                )

            if self.client is None:
                error_msg = (
                    "Anthropic client could not be initialized. Please check your API settings."
                )
                self._logger.error(error_msg)
                self.app.show_message_signal.emit(
                    "Initialization Error",
                    error_msg,
                )
                return ""

            response = self.client.chat.completions.create(
                model=self.api_model,
                messages=messages,  # type: ignore
                max_tokens=4000,
                temperature=0.4,
            )

            response_text = response.choices[0].message.content.rstrip("\n")
            self._logger.debug(f"Anthropic API response: {response_text}")
            self._logger.debug(
                f"Anthropic response length: {len(response_text) if response_text else 0}"
            )

            # Handle empty or None response
            if not response_text or response_text.strip() == "":
                error_msg = "Anthropic API returned an empty response. This might be due to insufficient credits or API limits."
                self._logger.warning(error_msg)
                self.app.show_message_signal.emit(
                    "Empty Response",
                    error_msg,
                )
                return ""

            if return_response:
                self._logger.debug(
                    f"AnthropicProvider: Returning response text (length: {len(response_text)})"
                )
                return response_text
            # Emit the response via signal for direct replacement
            self._logger.debug(
                f"AnthropicProvider: Emitting output_ready_signal with text (length: {len(response_text)})"
            )
            self.app.output_ready_signal.emit(response_text)
            self._logger.debug("AnthropicProvider: Signal emitted successfully")
            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Anthropic API error: {error_str}")

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

    def after_load(self) -> None:
        """Initialize Anthropic client with proper authentication."""
        if OpenAI is not None:
            self.client = OpenAI(
                api_key=self.api_key,
                base_url="https://api.anthropic.com/v1",
                default_headers={
                    "anthropic-version": "2023-06-01",
                },
            )

    def before_load(self) -> None:
        """Clean up client before reloading."""
        self.client = None


class MistralProvider(AIProvider):
    """
    Mistral AI Provider for Writing Tools.

    Uses the Mistral API to generate content with Mistral models.
    Uses direct HTTP requests for better control and reliability.
    """

    def __init__(self, app: "WritingToolApp"):
        self.client: Any = None
        self.app: WritingToolApp = app
        settings = [
            TextSetting(
                app,
                "api_key",
                "API Key",
                "",
                "Enter your Mistral API key",
            ),
            DropdownSetting(
                app,
                name="api_model",
                display_name="API Model",
                default_value=get_default_model_for_provider("mistral"),
                description="Select Mistral model to use",
                options=MISTRAL_MODELS,
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

    def _get_response_impl(
        self,
        system_instruction,
        prompt,
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """
        Generate response using Mistral API.

        Uses direct HTTP requests via requests library for maximum control
        over request format and error handling.
        """
        image_data: str | None = kwargs.get("image_data")
        conversation_history: list[dict[str, str]] | None = kwargs.get("conversation_history")

        self._logger.debug(
            f"MistralProvider.get_response called with return_response={return_response}"
        )
        self._logger.debug(
            f"MistralProvider current config - api_key: {self.api_key[:10] if self.api_key else 'None'}..., api_model: {self.api_model}",
        )

        # Log request details for debugging
        self._logger.debug(f"Mistral request - system: {len(system_instruction)} chars, prompt: {len(prompt)} chars, image: {image_data is not None}")

        try:
            # Check if requests library is available
            if requests is None:
                raise ImportError("requests library not available")

            # Check if API key and model are configured
            if not self.api_key or self.api_key.strip() == "":
                error_msg = "Mistral API key not configured. Please add your API key in settings."
                self._logger.error(error_msg)
                self.app.show_message_signal.emit(
                    "API Key Missing",
                    error_msg,
                )
                return ""
            if not self.api_model or self.api_model.strip() == "":
                error_msg = "Mistral model not selected. Please select a model in settings."
                self._logger.error(error_msg)
                self.app.show_message_signal.emit(
                    "Model Missing",
                    error_msg,
                )
                return ""

            self._logger.debug(
                f"Mistral API call - Key: {self.api_key[:10]}..., Model: {self.api_model}"
            )

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

            # Handle image data if provided for Mistral
            if image_data:
                # Check if current model supports vision
                vision_models = [
                    "pixtral-12b-2409",
                    "mistral-small-2503",
                    "mistral-medium-2505",
                    "pixtral-large-2411",
                    "mistral-small-latest",  # Keep for backward compatibility
                ]

                if self.api_model not in vision_models:
                    error_msg = f"The selected model '{self.api_model}' does not support image analysis. Please choose a vision-capable model like pixtral-12b-2409 or mistral-small-2503."
                    self._logger.error(error_msg)
                    self.app.show_message_signal.emit(
                        "Model Incompatible",
                        error_msg,
                    )
                    return ""

                user_content = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": f"data:image/png;base64,{image_data}"},
                ]
            else:
                user_content = prompt

            # Add current user message
            messages.append({"role": "user", "content": user_content})

            data = {
                "model": self.api_model,
                "messages": messages,
                "temperature": 0.4,
                "max_tokens": 4000,
            }

            # to avoid very long logs because of image urls
            data_for_logs = copy.deepcopy(data)
            for message in data_for_logs["messages"]:
                if isinstance(message["content"], list):
                    for content_item in message["content"]:
                        if (
                            isinstance(content_item, dict)
                            and content_item.get("type") == "image_url"
                        ):
                            image_url = content_item["image_url"]
                            truncated = image_url[:60] + "..."
                            content_item["image_url"] = truncated
                elif isinstance(message["content"], str):
                    text = message["content"]
                    message["content"] = (text[:100] + "...") if len(text) > 100 else text

            self._logger.debug(f"Mistral request data: {data_for_logs}")

            # Make API call using requests (like the working test code)
            response = requests.post(url, headers=headers, json=data, timeout=60)

            self._logger.debug(f"Mistral API status code: {response.status_code}")

            if response.status_code == 200:
                result = response.json()

                if "choices" in result and len(result["choices"]) > 0:
                    response_text = result["choices"][0]["message"]["content"].strip("\n")

                    self._logger.debug(f"Mistral API response: {response_text}")
                    self._logger.debug(
                        f"Mistral response length: {len(response_text) if response_text else 0}"
                    )

                    # Handle empty or None response
                    if not response_text or response_text.strip() == "":
                        error_msg = "Mistral API returned an empty response. This might be due to insufficient credits or API limits."
                        self._logger.warning(error_msg)
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
                self._logger.error(f"{error_msg} Full response: {result}")
                self.app.show_message_signal.emit(
                    "No Content",
                    error_msg,
                )
                return ""
            error_msg = f"Mistral API error {response.status_code}: {response.text}"
            self._logger.error(error_msg)

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
            self._logger.error(error_msg)
            self.app.show_message_signal.emit(
                "Missing Library",
                "The 'requests' library is required for Mistral API. Please install it using: pip install requests",
            )
            return ""
        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Mistral API error: {error_str}")
            self.app.show_message_signal.emit(
                "Mistral Error",
                f"An error occurred with Mistral:\n\n{error_str}\n\nPlease check your settings and try again.",
            )
            return ""

    def after_load(self) -> None:
        """No client initialization needed - using requests directly."""
        pass

    def before_load(self) -> None:
        """No client cleanup needed."""
        pass
