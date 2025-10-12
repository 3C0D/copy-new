"""
Provider setup module for Writing Tools application.

This module contains setup functions for the AI provider.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ...config.interfaces import ProviderConfig
    from ...writing_tools_app import WritingToolsApp


def initialize_ai_provider(app: "WritingToolsApp") -> None:
    """Initialize and configure the current AI provider."""
    logger = logging.getLogger(__name__)
    app.ai_processor.set_current_provider()

    if app.ai_processor.current_provider:
        logger.debug(f"Current provider: {app.ai_processor.current_provider.provider_name}")
        provider_config: ProviderConfig = app.ai_processor.get_provider_config(
            app.settings_manager.provider
        )
        logger.debug(f"Provider config: {provider_config}")
        app.ai_processor.current_provider.load_config(provider_config)
        logger.debug("Provider config loaded successfully")
