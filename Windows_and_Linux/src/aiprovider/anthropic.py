import logging
import webbrowser
from typing import TYPE_CHECKING, Any, Union

from openai import OpenAI

from ..aiprovider.aiprovider import AIProvider, DropdownSetting, TextSetting
from ..config.constants import ANTHROPIC_MODELS
from ..config.data_operations import get_default_model_for_provider

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


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
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
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
