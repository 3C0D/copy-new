import logging
from typing import TYPE_CHECKING, Any, cast

from openai import OpenAI
from PySide6 import QtCore
from PySide6.QtCore import QThread, Signal

from . import AIProvider, TextSetting
from .settings import AIProviderSetting, CheckboxSetting

# Local imports

# Type checking imports
if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class ModelFetchThread(QThread):
    """Thread for fetching models without blocking UI"""

    models_fetched = Signal(list)  # Emits list of model IDs
    fetch_failed = Signal(str)  # Emits error message

    def __init__(self, api_base: str, api_key: str):
        super().__init__()
        self.api_base = api_base
        self.api_key = api_key
        self._logger = logging.getLogger(__name__)

    def run(self):
        """Execute fetch in background thread"""
        try:
            import requests

            api_base = self.api_base.rstrip("/")
            models_url = f"{api_base}/models"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            self._logger.debug(f"Fetching models from: {models_url}")
            response = requests.get(models_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict) and "data" in data:
                    # Extract full model data including architecture
                    models = []
                    for model in data["data"]:
                        if "id" in model:
                            model_info = {
                                "id": model.get("id"),
                                "architecture": model.get("architecture"),
                                "has_vision": self._detect_vision_support(model),
                            }
                            models.append(model_info)

                    self._logger.debug(f"Successfully fetched {len(models)} models")
                    self.models_fetched.emit(models)
                else:
                    self._logger.warning(f"Unexpected response format: {data}")
                    self.fetch_failed.emit("Unexpected response format")
            else:
                self._logger.warning(f"Failed to fetch models: {response.status_code}")
                self.fetch_failed.emit(f"HTTP {response.status_code}")

        except Exception as e:
            self._logger.error(f"Error fetching models: {e}")
            self.fetch_failed.emit(str(e))

    def _detect_vision_support(self, model_data: dict) -> bool:
        """
        Detect if a model supports vision/image analysis.

        Checks the 'architecture' field for presence of 'image' in input_modalities.

        Args:
            model_data: Model data dict from API

        Returns:
            True if model supports image input
        """
        architecture = model_data.get("architecture")
        if not architecture:
            return False

        input_modalities = architecture.get("input_modalities")
        if not input_modalities:
            return False

        if isinstance(input_modalities, list):
            return "image" in input_modalities

        return False


class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed. Supports APIs with organization
    and project authentication.
    """

    def __init__(self, app: "WritingToolsApp"):
        self.client: Any = None
        self._fetched_models: list[dict] = []  # Store fetched models with metadata

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
            TextSetting(
                app,
                name="api_project",
                display_name="API Project",
                default_value="",
                description="Leave blank if not applicable.",
            ),
            TextSetting(
                app,
                name="api_model",
                display_name="API Model",
                default_value="",
                description="Add a custom model name",
            ),
            CheckboxSetting(
                app,
                name="has_vision",
                display_name="Has Vision (auto-detected)",
                default_value=False,
                description="Automatically detected based on model capabilities",
                read_only=True,
            ),
        ]
        super().__init__(
            app,
            "OpenAI Compatible",
            cast(list[AIProviderSetting], settings),
            "• Connect to any OpenAI-compatible API (v1/chat/completions).\n"
            "• An API key is required for authentication.",
            "openai-compatible",
        )

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: str | list,
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

            if not self.api_model or not self.api_model.strip():
                self.app.ui_manager.show_message_signal.emit(
                    "Model Not Configured",
                    "Please enter a model name in the 'Added Model' field in OpenAI Compatible settings.",
                )
                return ""

            if self.client is None:
                self.app.ui_manager.show_message_signal.emit(
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

            if not return_response and self.app.current_response_window is None:
                self.app.text_processor.output_ready_signal.emit(response_text)
            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Error while generating content: {error_str}")

            # Handle specific OpenAI API errors
            if "invalid api key" in error_str.lower() or "unauthorized" in error_str.lower():
                self.app.ui_manager.show_message_signal.emit(
                    "Invalid API Key",
                    "Your OpenAI API key is invalid. Please check your API key in Settings and make sure it's correct.",
                )
            elif "exceeded" in error_str.lower() or "rate limit" in error_str.lower():
                # Close response window on rate limit errors (thread-safe)
                if self.app.current_response_window:
                    QtCore.QMetaObject.invokeMethod(
                        self.app.current_response_window,
                        "close",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                    )
                self.app.ui_manager.show_message_signal.emit(
                    "Rate Limit Hit",
                    "You've hit an API rate/usage limit. Please try again later or check your OpenAI usage limits.",
                )
            elif "insufficient_quota" in error_str.lower() or "quota" in error_str.lower():
                self.app.ui_manager.show_message_signal.emit(
                    "Quota Exceeded",
                    "You've exceeded your OpenAI API quota. Please check your billing and usage limits.",
                )
            else:
                self.app.ui_manager.show_message_signal.emit(
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

    @property
    def supports_vision(self) -> bool:
        """Check if this provider instance has vision support enabled."""
        return bool(getattr(self, "has_vision", False))

    def before_load(self) -> None:
        """Clean up client before reloading."""
        self._logger.debug("🧹 OpenAICompatibleProvider.before_load called - cleaning up client")
        self.client = None

    def fetch_models_async(
        self, callback_success=None, callback_failure=None, api_base=None, api_key=None
    ):
        """
        Fetch available models asynchronously.

        Args:
            callback_success: Function to call with list of models on success
            callback_failure: Function to call with error message on failure
            api_base: Optional explicit api_base (uses self.api_base if None)
            api_key: Optional explicit api_key (uses self.api_key if None)
        """
        # Use explicit values if provided, otherwise fall back to instance attributes
        base_url = api_base if api_base is not None else getattr(self, "api_base", "")
        key = api_key if api_key is not None else getattr(self, "api_key", "")

        if not base_url or not key:
            self._logger.debug("Cannot fetch models: missing api_base or api_key")
            if callback_failure:
                callback_failure("Missing API credentials")
            return

        self._logger.debug(f"Starting async fetch with api_base: {base_url}")

        # Create and start thread with explicit values
        self._fetch_thread = ModelFetchThread(base_url, key)

        if callback_success:
            self._fetch_thread.models_fetched.connect(
                lambda models: self._on_models_fetched(models, callback_success)
            )

        if callback_failure:
            self._fetch_thread.fetch_failed.connect(callback_failure)

        self._fetch_thread.start()

    def _on_models_fetched(self, models, callback):
        """Store fetched models and execute callback"""
        self._fetched_models = models
        callback(models)

    def fetch_models(self) -> list[str]:
        """
        Fetch available models from the API endpoint.

        Returns:
            List of model IDs if successful, empty list otherwise.
        """
        if not self.api_base or not self.api_key:
            self._logger.debug("Cannot fetch models: missing api_base or api_key")
            return []

        try:
            import requests

            # Normalize api_base
            api_base = self.api_base.rstrip("/")
            models_url = f"{api_base}/models"

            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }

            self._logger.debug(f"Fetching models from: {models_url}")
            response = requests.get(models_url, headers=headers, timeout=10)

            if response.status_code == 200:
                data = response.json()
                # Handle OpenAI-style response format
                if isinstance(data, dict) and "data" in data:
                    models = []
                    for model in data["data"]:
                        if "id" in model:
                            model_info = {
                                "id": model.get("id"),
                                "architecture": model.get("architecture"),
                                "has_vision": self._detect_vision_support(model),
                            }
                            models.append(model_info)

                    self._logger.debug(f"Successfully fetched {len(models)} models")
                    self._fetched_models = models
                    return models
                else:
                    self._logger.warning(f"Unexpected response format: {data}")
                    return []
            else:
                self._logger.warning(f"Failed to fetch models: {response.status_code}")
                return []

        except Exception as e:
            self._logger.error(f"Error fetching models: {e}")
            return []

    def _detect_vision_support(self, model_data: dict) -> bool:
        """
        Detect if a model supports vision/image analysis.

        Checks the 'architecture' field for presence of 'image' in input_modalities.

        Args:
            model_data: Model data dict from API

        Returns:
            True if model supports image input
        """
        architecture = model_data.get("architecture")
        if not architecture:
            return False

        input_modalities = architecture.get("input_modalities")
        if not input_modalities:
            return False

        if isinstance(input_modalities, list):
            return "image" in input_modalities

        return False

    def get_model_metadata(self, model_id: str) -> dict:
        """
        Get metadata for a specific model.

        Args:
            model_id: ID of the model

        Returns:
            Dict with metadata including has_vision
        """
        for model in self._fetched_models:
            if model.get("id") == model_id:
                return model
        return {"id": model_id, "has_vision": False}

    def get_fetched_models(self) -> list[str]:
        """Get the list of fetched models."""
        return [model["id"] for model in self._fetched_models]
