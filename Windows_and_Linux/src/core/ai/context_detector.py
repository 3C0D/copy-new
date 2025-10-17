"""
Context Detector - Determines the context and system instruction for AI requests.

This module contains the logic for determining appropriate system instructions
based on the context of AI requests (text vs image, custom vs predefined, etc.).
"""

from ...config.constants import SYSTEM_INSTRUCTIONS
from ...config.interfaces import ActionConfig


class ContextDetector:
    """Determines the context and system instruction for AI requests."""

    @staticmethod
    def get_system_instruction(
        has_image: bool,
        is_custom: bool,
        action_config: ActionConfig,
        context: str = "initial",  # "initial" or "followup"
    ) -> str:
        """
        Get appropriate system instruction based on context.

        Determines the right AI system prompt based on:
        - Content type (text vs image)
        - Request type (custom vs predefined action)
        - Conversation context (initial request vs followup)
        """
        if context == "followup":
            return (
                SYSTEM_INSTRUCTIONS["response_window_image"]
                if has_image
                else SYSTEM_INSTRUCTIONS["response_window_text"]
            )

        if has_image:
            if is_custom:
                return SYSTEM_INSTRUCTIONS["image_custom"]
            else:
                return SYSTEM_INSTRUCTIONS["image_action"].format(
                    action_instruction=action_config.get("instruction", "")
                )

        if is_custom:
            return SYSTEM_INSTRUCTIONS["chat_no_text"]

        return action_config.get("instruction", "")
