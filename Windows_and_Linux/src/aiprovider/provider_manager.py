"""
provider_manager.py

Manages provider lifecycle: creation, switching, and configuration.
"""

import logging
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..aiprovider.aiprovider import AIProvider
    from ..writing_tools_app import WritingToolsApp

from ..core.ai_processor import PROVIDER_CLASSES


class ProviderManager:
    """Manages provider lifecycle and switching logic."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)

    def find_provider_by_name(self, internal_name: str) -> "AIProvider | None":
        """Create provider instance by internal name."""
        provider_class = PROVIDER_CLASSES.get(internal_name)
        if not provider_class:
            return None

        try:
            # Skip initial refresh for Ollama when switching providers
            # to avoid debug spam - refreshes will be handled by provider switching logic
            if internal_name == "ollama":
                return provider_class(self.app, skip_initial_refresh=True)
            else:
                return provider_class(self.app)
        except Exception as e:
            self._logger.error(f"Failed to create provider {internal_name}: {e}")
            return None

    def switch_provider(self, internal_name: str) -> "AIProvider | None":
        """
        Switch to a new provider.

        Returns the new provider instance or None if switch failed.
        """
        self._logger.debug(f"Switching to provider: {internal_name}")

        # Handle Ollama-specific checks
        if internal_name == "ollama":
            self._handle_ollama_selection()

        # Find new provider
        new_provider = self.find_provider_by_name(internal_name)
        if not new_provider:
            self._logger.warning(f"Provider {internal_name} not found")
            return None

        # Cleanup old provider
        if self.app.ai_processor.current_provider and hasattr(
            self.app.ai_processor.current_provider, "before_load"
        ):
            self.app.ai_processor.current_provider.before_load()

        # Update settings
        self.app.settings_manager.provider = internal_name

        # Reload config
        provider_config = self.app.settings_manager.providers.get(internal_name, {})
        new_provider.load_config(provider_config)

        # Update AI processor
        self.app.ai_processor.current_provider = new_provider

        self._logger.debug(f"Switched to provider: {internal_name}")
        return new_provider

    def refresh_provider_config(self, provider: "AIProvider") -> None:
        """Refresh provider configuration if supported."""
        if not hasattr(provider, "refresh_configuration"):
            return

        try:
            provider.refresh_configuration()
            self._logger.debug(f"Refreshed config: {provider.internal_name}")
        except Exception as e:
            self._logger.warning(f"Failed to refresh {provider.internal_name} config: {e}")

    def save_provider_settings(self, provider: "AIProvider") -> None:
        """Save settings for given provider."""
        provider.save_config()

        provider_config = self.app.settings_manager.providers.get(provider.internal_name, {})
        provider.load_config(provider_config)

        self._logger.debug(f"Saved settings: {provider.internal_name}")

    def _handle_ollama_selection(self) -> None:
        """
        Handle Ollama provider selection with status checks.
        Uses cached status to avoid redundant async operations.
        """
        from ..aiprovider.ollama import OllamaStateManager

        state_manager = OllamaStateManager()

        # Get cached status (non-blocking) - don't trigger async refresh here
        # to avoid debug spam when switching providers
        ollama_installed = state_manager.is_ollama_installed()

        # Only show message for installation issues
        if not ollama_installed:
            self.app.ui_manager.show_message_signal.emit(
                "Ollama Not Installed",
                "Ollama is not installed on your system.\n\n"
                "You can install it using the 'Install Ollama' button in the provider settings below.\n\n"
                "Once installed and running, Ollama will be ready to use.",
            )
