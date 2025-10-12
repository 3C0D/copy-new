import webbrowser
from typing import TYPE_CHECKING, Any, cast

from openai import OpenAI

from . import AIProvider, AIProviderSetting, TextSetting

# Local imports

# Type checking imports
if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


class OpenAICompatibleProvider(AIProvider):
    """
    Provider for OpenAI-compatible APIs.

    Uses self.client.chat.completions.create() to obtain a response.
    Streaming is fully removed. Supports APIs with organization
    and project authentication.
    """

    def __init__(self, app: "WritingToolsApp"):
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
        ]
        super().__init__(
            app,
            "OpenAI Compatible",
            cast(list[AIProviderSetting], settings),
            "• Connect to any OpenAI-compatible API (v1/chat/completions).\n"
            "• An API key is required for authentication.\n"
            "• You must abide by the service's Terms of Service.",
            "openai-compatible",
            "Get OpenAI API Key",
            lambda: webbrowser.open("https://platform.openai.com/account/api-keys"),
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

    def before_load(self) -> None:
        """Clean up client before reloading."""
        self._logger.debug("🧹 OpenAICompatibleProvider.before_load called - cleaning up client")
        self.client = None
