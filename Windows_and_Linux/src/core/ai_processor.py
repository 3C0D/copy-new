"""
AI Processor - Handles AI request processing and response management.

This module contains the logic for processing AI requests, handling prompts,
managing responses, and coordinating with different AI providers.
"""

import logging
import threading
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject

from ..aiprovider.anthropic import AnthropicProvider
from ..aiprovider.gemini import GeminiProvider
from ..aiprovider.mistral import MistralProvider
from ..aiprovider.ollama import OllamaProvider
from ..aiprovider.openAI import OpenAIProvider
from ..aiprovider.openAI_compatible import OpenAICompatibleProvider
from ..config.constants import DEFAULT_PROVIDER, DEFAULT_PROVIDER_CONFIGS, SYSTEM_INSTRUCTIONS
from ..config.interfaces import ActionConfig, ProviderConfig

# Mapping of internal provider names to their classes
PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
    "mistral": MistralProvider,
    "openAIcompatible": OpenAICompatibleProvider,
    "openAI": OpenAIProvider,
}

if TYPE_CHECKING:
    from ..aiprovider.aiprovider import AIProvider
    from ..ui.response_window import ResponseWindow


class MessageFormatter:
    """Formats conversation history for different AI providers."""

    @staticmethod
    def format_for_gemini(history: list[dict], image_data: str | None) -> list[dict]:
        """Format messages for Gemini provider."""
        chat_messages = []

        # Convert our roles to Gemini's expected roles and handle images
        for i, msg in enumerate(history):
            gemini_role = "model" if msg["role"] == "assistant" else "user"

            # For the first user message with image, include the image
            if (
                i == 0
                and msg["role"] == "user"
                and image_data
                and "Image analysis request" in msg["content"]
            ):
                # Create content with image for first message
                content_parts = [
                    msg["content"],
                    {"inline_data": {"mime_type": "image/png", "data": image_data}},
                ]
                chat_messages.append({"role": gemini_role, "parts": content_parts})
            else:
                chat_messages.append({"role": gemini_role, "parts": msg["content"]})

        return chat_messages

    @staticmethod
    def format_for_openai(history: list[dict], system_instruction: str, image_data: str | None) -> list[dict[str, Any]]:
        """Format messages for OpenAI/OpenAI-compatible providers."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

        # Add history messages (including latest question)
        for i, msg in enumerate(history):
            role = "assistant" if msg["role"] == "assistant" else "user"

            # Handle image for first user message if present
            if (
                i == 0
                and msg["role"] == "user"
                and image_data
                and "Image analysis request" in msg["content"]
            ):
                # OpenAI format for image
                content: list[dict[str, Any]] = [
                    {"type": "text", "text": msg["content"]},
                    {
                        "type": "image_url",
                        "image_url": {"url": f"data:image/png;base64,{image_data}"},
                    },
                ]
                messages.append({"role": role, "content": content})
            else:
                messages.append({"role": role, "content": msg["content"]})

        return messages

    @staticmethod
    def format_for_mistral(history: list[dict], system_instruction: str, image_data: str | None) -> list[dict[str, Any]]:
        """Format messages for Mistral provider."""
        messages: list[dict[str, Any]] = [
            {"role": "system", "content": system_instruction}
        ]

        # Add history messages, handling images for Mistral
        for i, msg in enumerate(history[:-1]):  # Exclude the just-added question
            if (
                i == 0
                and msg["role"] == "user"
                and image_data
                and "Image analysis request" in msg["content"]
            ):
                # First message with image
                user_content: list[dict[str, Any]] = [
                    {"type": "text", "text": msg["content"]},
                    {
                        "type": "image_url",
                        "image_url": f"data:image/png;base64,{image_data}",
                    },
                ]
                messages.append({"role": "user", "content": user_content})
            else:
                messages.append({"role": msg["role"], "content": msg["content"]})

        return messages


class AIProcessor(QObject):
    """
    Handles AI request processing and response management.
    """

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.current_provider: AIProvider | None = None
        self.output_queue = ""

    def set_current_provider(self) -> None:
        """Set the current provider and save settings."""
        provider_name: str = self.app.settings_manager.provider or DEFAULT_PROVIDER

        # Create provider instance
        provider_class = PROVIDER_CLASSES.get(provider_name)
        if provider_class:
            try:
                self.current_provider = provider_class(self.app)  # instance
                if self.current_provider is not None:
                    self.app.settings_manager.provider = self.current_provider.internal_name
            except Exception as e:
                self._logger.error(f"Failed to create provider {provider_name}: {e}")
                # Fallback to default provider
                default_class = PROVIDER_CLASSES.get(DEFAULT_PROVIDER)
                if default_class and default_class != provider_class:
                    try:
                        self.current_provider = default_class(self.app)  # instance
                        if self.current_provider is not None:
                            self.app.settings_manager.provider = self.current_provider.internal_name
                    except Exception as e2:
                        self._logger.error(
                            f"Failed to create default provider {DEFAULT_PROVIDER}: {e2}"
                        )
                        self.current_provider = None
                else:
                    self.current_provider = None
        else:
            self._logger.error(f"Unknown provider: {provider_name}")
            self.current_provider = None

    def get_current_model(self, provider_name: str) -> str:
        """Get the current API model for a specific provider."""
        provider = self.app.settings_manager.providers.get(provider_name, {})
        return provider.get("api_model", "")

    def get_provider_config(self, provider_name: str) -> ProviderConfig:
        """
        Extract provider-specific configuration from custom_data.

        Args:
            provider_name: Name of the provider

        Returns:
            dict: Provider-specific configuration
        """
        if not provider_name:
            raise ValueError("Provider name cannot be empty or None")

        # Default configuration based on provider type
        default_configs = DEFAULT_PROVIDER_CONFIGS

        # Find the default config
        config: ProviderConfig = {}
        for provider_names, default_config in default_configs.items():
            if provider_name in provider_names:
                config = default_config.copy()
                break

        # Override with saved config
        saved_config = self.app.settings_manager.providers.get(provider_name, {})
        if saved_config:
            config.update(saved_config)

        return config

    def process_option(
        self,
        option: str,
        selected_text: str | None,
        force_chat: bool = False,
        custom_change: str | None = None,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Process the selected writing option.

        Args:
            option: The action option to process
            selected_text: The text selected by the user
            force_chat: If True, force response to open in ResponseWindow (chat mode)
            custom_change: Optional custom instruction text entered by the user in the input field
            image: Optional image copied from the clipboard
        """
        message = f"Processing option: {option}{' - force chat' if force_chat else ''}"
        self._logger.debug(message)

        if self.current_provider is not None and not self.current_provider.validate_connection():
            return

        has_image = image is not None
        # Get action config from appropriate dictionary based on context
        if has_image and option in self.app.settings_manager.image_actions:
            action_config = self.app.settings_manager.image_actions.get(option, {})
        else:
            action_config = self.app.settings_manager.actions.get(option, {})

        should_setup_response_window = self._should_display_in_window(
            option, selected_text, action_config, has_image, force_chat
        )

        self._logger.debug(f"should_setup_response_window: {should_setup_response_window}")
        self._logger.debug(f"has_image: {has_image}")

        if should_setup_response_window:
            self._setup_response_window(option, selected_text, image)
        elif hasattr(self.app, "current_response_window"):
            delattr(self.app, "current_response_window")

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, image, custom_change, force_chat),
            daemon=True,
        ).start()

    def _setup_response_window(
        self, option: str, selected_text: str | None, image: QtGui.QImage | None
    ) -> None:
        """
        Set up the response window for the selected writing option.
        """
        is_custom = option == "Custom"
        window_title = "Chat" if not is_custom else option
        self.app.current_response_window = self.app.ui_manager.show_response_window(
            window_title, selected_text
        )

        # Handle chat history based on content type
        if image is not None:
            # Image mode - no selected text
            # Get the actual prompt text for the action to put in history
            is_custom = option == "Custom"
            if is_custom:
                # For custom, the prompt is the custom_change (handled later)
                history_content = f"Image analysis request: {option.lower()}"
            else:
                # For predefined actions, use the action's prefix as the user-visible request
                action_config = self.app.settings_manager.image_actions.get(option, {})
                history_content = action_config.get(
                    "prefix", f"Image analysis request: {option.lower()}"
                )  # !!! à voir comment on fait une fois le system compris

            self.app.current_response_window.chat_history = [
                {"role": "user", "content": history_content}
            ]
        elif is_custom and not selected_text:
            # Custom mode without text
            self.app.current_response_window.chat_history = []
        else:
            # Text mode
            self.app.current_response_window.chat_history = (
                []
                if not is_custom
                else [
                    {
                        "role": "user",
                        "content": f"Original text to {option.lower()}:\n\n{selected_text}",
                    },
                ]
            )

        self._logger.debug(f"💬📜 Chat history: {self.app.current_response_window.chat_history}")

    def process_option_thread(
        self,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None = None,
        custom_change: str | None = None,
        force_chat: bool = False,
    ) -> None:
        """
        Thread function to process the selected writing option using the AI model.
        Enhanced to support image processing.

        Args:
            option: The selected writing option (e.g., "Summary", "Custom", "Proofread")
            selected_text: The text selected by the user
            image: Optional image copied from the clipboard
            custom_change: Optional custom change description for Custom option
            force_chat: If True, force response to open in ResponseWindow (chat mode)
        """
        self._logger.debug(f"Starting processing thread for option: {option}")

        try:
            prompt_data = self._prepare_prompt_data(option, selected_text, image, custom_change)
            if not prompt_data:
                return

            self.output_queue = ""
            should_open_window = self._should_display_in_window(
                option, selected_text, prompt_data["action_config"], image is not None, force_chat
            )

            if should_open_window:
                self._process_window_response(option, selected_text, custom_change, prompt_data)
            else:
                self._process_direct_replacement(prompt_data)

            # Clean up image resources
            self.app.popup_manager.clean_image()

        except Exception as e:
            self._handle_processing_error(e)

    def _prepare_prompt_data(
        self,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None,
        custom_change: str | None,
    ) -> dict | None:
        """
        Prepare prompt data for AI processing including image support.

        Args:
            option: The selected writing option (e.g., "Summary", "Custom", "Proofread")
            selected_text: The text selected by the user
            image: The image copied from the clipboard
            custom_change: The custom instruction text entered by the user in the input field

        Returns:
            dict: Contains prompt, system_instruction, action_config, and image_data, or None if invalid
        """
        has_selected_text = selected_text and selected_text.strip() != ""
        is_custom_option = option == "Custom"
        has_image = image is not None

        if not has_selected_text and not has_image:
            return self._handle_no_text_selected(is_custom_option, custom_change)
        else:
            return self._handle_text_or_image_selected(
                option, selected_text, image, is_custom_option, custom_change
            )

    def _handle_no_text_selected(
        self, is_custom_option: bool, custom_change: str | None
    ) -> dict | None:
        """Handle case where no text is selected."""
        if custom_change is None:
            custom_change = ""

        if is_custom_option:
            return {
                "prompt": custom_change,
                "system_instruction": SYSTEM_INSTRUCTIONS["chat_no_text"],
                "action_config": {},
            }
        else:
            self.app.ui_manager.show_message_signal.emit(
                "Error", "Please select text to use this option."
            )
            return None

    def _handle_text_or_image_selected(
        self,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None,
        is_custom_option: bool,
        custom_change: str | None,
    ) -> dict | None:
        """Handle case where text is selected or image is available."""
        # Get action config from appropriate dictionary based on context
        has_image = image is not None
        if has_image and option in self.app.settings_manager.image_actions:
            action_config: ActionConfig = self.app.settings_manager.image_actions.get(option, {})
        else:
            action_config: ActionConfig = self.app.settings_manager.actions.get(option, {})

        # For image analysis, use a specialized system instruction
        if image is not None:
            if is_custom_option:
                system_instruction = SYSTEM_INSTRUCTIONS["image_custom"]
                prompt = custom_change or "Please analyze this image and describe what you see."
            else:
                if not action_config:
                    self._logger.error(f"Handle image - Action not found: {option}")
                    return None

                # For pre-defined actions with images, adapt the instruction
                system_instruction = SYSTEM_INSTRUCTIONS["image_action"].format(
                    action_instruction=action_config.get("instruction", "")
                )
                prompt = action_config.get("prefix", "") + (custom_change or "")
        else:
            # Text-based processing
            if not action_config:
                self._logger.error(f"Action not found: {option}")
                return None

            prompt_prefix = action_config.get("prefix", "")
            system_instruction = action_config.get("instruction", "")

            if is_custom_option:
                prompt = (
                    f"{prompt_prefix}Described change: {custom_change}\nText: {selected_text}\n"
                )
            else:
                prompt = f"{prompt_prefix}{selected_text}\n"

        # Convert QImage to base64 if present
        image_data = None
        if image:
            self._logger.debug(
                f" 🖼️  Processing image in _handle_text_or_image_selected - image size: {image.width()}x{image.height()}"
            )
            image_data = self.app.image_processor.qimage_to_base64(image, use_physical_file=False)
            if image_data:
                self._logger.debug(
                    f" 🖼️  Image converted to base64 successfully - length: {len(image_data)}"
                )
            else:
                self._logger.error(" 🖼️  Failed to convert image to base64")

        return {
            "prompt": prompt,
            "system_instruction": system_instruction,
            "action_config": action_config,
            "image_data": image_data,
        }

    def _should_display_in_window(
        self,
        option: str,
        selected_text: str | None,
        action_config: ActionConfig,
        has_image: bool,
        force_chat: bool,
    ) -> bool:
        """Determine if response should be displayed in a window."""
        is_custom_option = option == "Custom"
        has_selected_text = bool(selected_text and selected_text.strip() != "")

        return (
            has_image
            or force_chat
            and has_selected_text
            or is_custom_option
            and not has_selected_text
            or bool(action_config.get("open_in_window", True))
        )

    def _process_window_response(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        prompt_data: dict,
    ) -> None:
        """Process AI response for window display with image support."""
        if not self.current_provider:
            return

        self._logger.debug("Getting response for window display")

        # Extract image data from prompt_data
        image_data = prompt_data.get("image_data")

        if image_data:
            self._logger.debug(f" 🖼️  Passing image data to provider - length: {len(image_data)}")
            self._logger.debug(f" 🖼️  Image data preview: {image_data[:100]}...")
        else:
            self._logger.debug(" 🖼️  No image data to pass to provider")

        response = self.current_provider.get_response(
            prompt_data["system_instruction"],
            str(prompt_data["prompt"]),
            return_response=True,
            image_data=image_data,  # Pass image data to provider
        )
        self._logger.debug(f"Got response of length: {len(response) if response else 0}")

        self._update_chat_history_if_needed(option, selected_text, custom_change, image_data)
        self._update_response_window(response)

    def _update_chat_history_if_needed(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        image_data: str | None = None,
    ) -> None:
        """Update chat history for custom prompts, including image context."""
        is_custom_option = option == "Custom"
        has_image = image_data is not None

        if (
            not hasattr(self.app, "current_response_window")
            or not self.app.current_response_window
            or not is_custom_option
        ):
            return

        if has_image:
            # Image analysis request
            self.app.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or "Analyze this image"},
            )
        else:
            # Text-only custom request
            self.app.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or ""},
            )

        self._logger.debug(
            f"💬📜 Chat history updated to: {self.app.current_response_window.chat_history}"
        )

    def _update_response_window(self, response: str) -> None:
        """Update response window with AI response (thread-safe)."""
        if hasattr(self.app, "current_response_window") and self.app.current_response_window:
            QtCore.QMetaObject.invokeMethod(
                self.app.current_response_window,
                "set_text",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response),
            )
            self._logger.debug("🆕🪟  Invoked set_text on response window")
        else:
            self._logger.warning("No current_response_window to update")

    def _process_direct_replacement(self, prompt_data: dict) -> None:
        """Process AI response for direct text replacement."""
        if not self.current_provider:
            return

        self._logger.debug("Getting response for direct replacement")
        prompt_str = str(prompt_data["prompt"])
        self.current_provider.get_response(prompt_data["system_instruction"], prompt_str)
        self._logger.debug("Response processed")

    def _handle_processing_error(self, error: Exception) -> None:
        """Handle errors during AI processing."""
        self._logger.error(f"An error occurred: {error}", exc_info=True)

        if "Resource has been exhausted" in str(error):
            self.app.ui_manager.show_message_signal.emit(
                "Error - Rate Limit Hit",
                "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
            )
        else:
            self.app.ui_manager.show_message_signal.emit("Error", f"An error occurred: {error}")

    def process_followup_question(self, response_window: "ResponseWindow", question: str) -> None:
        """
        Process a follow-up question in the chat window, with image support.

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

        b) OpenAi/OpenAI-compatible:
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
        self._logger.debug(f"Processing follow-up question: {question}")

        def process_thread():
            self._logger.debug("Starting follow-up processing thread")
            try:
                if not response_window.chat_history:
                    self.app.ui_manager.show_message_signal.emit("Error", "Chat history not found")
                    return

                # Add current question to chat history
                response_window.chat_history.append({"role": "user", "content": question})

                # Get chat history
                history = response_window.chat_history.copy()

                # System instruction based on context (image vs text)
                if response_window.image:
                    system_instruction = SYSTEM_INSTRUCTIONS["response_window_image"]
                else:
                    system_instruction = SYSTEM_INSTRUCTIONS["response_window_text"]

                self._logger.debug("Sending request to AI provider")

                # Get image data if available
                image_data = None
                if response_window.image:
                    self._logger.debug(
                        f" 🖼️  Processing follow-up with image - size: {response_window.image.width()}x{response_window.image.height()}"
                    )
                    image_data = self.app.image_processor.qimage_to_base64(
                        response_window.image, use_physical_file=False
                    )
                    if image_data:
                        self._logger.debug(
                            f" 🖼️  Follow-up image converted to base64 - length: {len(image_data)}"
                        )
                    else:
                        self._logger.error(" 🖼️  Failed to convert follow-up image to base64")

                # Format conversation based on provider
                if self.current_provider and isinstance(self.current_provider, GeminiProvider):
                    chat_messages = MessageFormatter.format_for_gemini(history, image_data)

                    # Start chat with history
                    if hasattr(self.current_provider, "model") and self.current_provider.model:
                        chat = self.current_provider.model.start_chat(
                            history=chat_messages[:-1]
                        )  # Exclude last question

                        # Send the latest question
                        response = chat.send_message(question)
                        response_text = response.text
                    else:
                        response_text = "Error: Provider model not available"

                elif self.current_provider and isinstance(self.current_provider, MistralProvider):
                    messages = MessageFormatter.format_for_mistral(history, system_instruction, image_data)
                    messages.append({"role": "user", "content": question})

                    # Get response from Mistral
                    response_text = self.current_provider.get_response(
                        "",  # system_instruction already in messages
                        messages,
                        return_response=True,
                        image_data=image_data,
                    )

                elif self.current_provider:
                    messages = MessageFormatter.format_for_openai(history, system_instruction, image_data)

                    # Get response by passing the full messages array
                    response_text = self.current_provider.get_response(
                        "",  # system_instruction already in messages
                        messages,
                        return_response=True,
                    )
                else:
                    response_text = "Error: No provider available"

                self._logger.debug(f"Got response of length: {len(response_text)}")

                # Add response to chat history
                response_window.chat_history.append({"role": "assistant", "content": response_text})

                # Emit response via signal
                self.app.current_response_window.followup_response_signal.emit(response_text)

            except Exception as e:
                self._logger.error(f"Error processing follow-up question: {e}", exc_info=True)

                if "Resource has been exhausted" in str(e):
                    self.app.ui_manager.show_message_signal.emit(
                        "Error - Rate Limit Hit",
                        "Whoops! You've hit the per-minute rate limit of the API. Please try again in a few moments.\n\nIf this happens often, try switching to a different model in Settings.",
                    )
                    self.app.current_response_window.followup_response_signal.emit(
                        "Sorry, an error occurred while processing your question."
                    )
                else:
                    self.app.ui_manager.show_message_signal.emit("Error", f"An error occurred: {e}")
                    self.app.current_response_window.followup_response_signal.emit(
                        "Sorry, an error occurred while processing your question."
                    )

        # Start the thread
        threading.Thread(target=process_thread, daemon=True).start()
