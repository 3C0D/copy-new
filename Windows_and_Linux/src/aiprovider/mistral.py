import copy
import webbrowser
from typing import TYPE_CHECKING, Any, Union

import requests

from ..config.constants import MISTRAL_MODELS
from ..config.data_operations import get_default_model_for_provider
from .aiprovider import AIProvider, DropdownSetting, TextSetting

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class MistralProvider(AIProvider):
    """
    Mistral AI Provider for Writing Tools.

    Uses the Mistral API to generate content with Mistral models.
    Uses direct HTTP requests for better control and reliability.
    """

    def __init__(self, app: "WritingToolsApp"):
        self.client: Any = None
        self.app: WritingToolsApp = app
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
        prompt: Union[str, list],
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
        self._logger.debug(
            f"Mistral request - system: {len(system_instruction)} chars, prompt: {len(prompt) if isinstance(prompt, str) else 'list'} chars, image: {image_data is not None}"
        )

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

            # Check if prompt is already a list of messages
            if isinstance(prompt, list):
                messages = prompt
            else:
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
