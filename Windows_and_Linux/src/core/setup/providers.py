"""
Providers setup module for Writing Tools application.

This module contains setup functions for AI providers.
"""

import logging


def initialize_ai_provider(app) -> None:
    """Initialize and configure the current AI provider."""
    logger = logging.getLogger(__name__)
    app.ai_processor.set_current_provider()

    if app.ai_processor.current_provider:
        logger.debug(f"Current provider: {app.ai_processor.current_provider.provider_name}")
        provider_config = app.ai_processor.get_provider_config(app.settings_manager.provider)
        logger.debug(f"Provider config: {provider_config}")
        app.ai_processor.current_provider.load_config(provider_config)
        logger.debug("Provider config loaded successfully")
