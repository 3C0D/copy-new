"""
Message Formatter - Formats conversation history for different AI providers.

This module contains the logic for formatting conversation history according
to the requirements of different AI providers (Gemini, OpenAI, Mistral, etc.).
"""

from typing import Any


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
    def format_for_openai(
        history: list[dict], system_instruction: str, image_data: str | None
    ) -> list[dict[str, Any]]:
        """Format messages for OpenAI/OpenAI-compatible providers."""
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_instruction}]

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
    def format_for_mistral(
        history: list[dict], system_instruction: str, image_data: str | None
    ) -> list[dict[str, Any]]:
        """Format messages for Mistral provider."""
        messages: list[dict[str, Any]] = [{"role": "system", "content": system_instruction}]

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
