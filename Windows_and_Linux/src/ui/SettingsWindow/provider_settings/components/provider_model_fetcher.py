"""
Async model fetching for OpenAI-compatible providers.
"""

import logging
from collections.abc import Callable
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .....aiprovider.openAI_compatible import OpenAICompatibleProvider


class ProviderModelFetcher:
    """Handles async model fetching for OpenAI-compatible providers."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._is_fetching = False

    def fetch_models(
        self,
        provider: "OpenAICompatibleProvider",
        api_base: str,
        api_key: str,
        on_success: Callable[[list[str]], None],
        on_failure: Callable[[str], None],
    ) -> None:
        """Fetch models asynchronously.

        Args:
            provider: OpenAI-compatible provider instance
            api_base: API base URL
            api_key: API key
            on_success: Callback with list of models
            on_failure: Callback with error message
        """
        if self._is_fetching:
            self._logger.debug("Already fetching models, skipping")
            return

        if not api_base or not api_key:
            self._logger.debug("Missing credentials, skipping fetch")
            return

        self._is_fetching = True
        self._logger.debug(f"Fetching models with api_base: {api_base}")

        def success_wrapper(models):
            self._is_fetching = False
            if not models:
                self._logger.debug("No models returned from fetch")
                return
            on_success(models)

        def failure_wrapper(error_msg):
            self._is_fetching = False
            self._logger.warning(f"Failed to fetch models: {error_msg}")
            on_failure(error_msg)

        provider.fetch_models_async(
            success_wrapper,
            failure_wrapper,
            api_base=api_base,
            api_key=api_key,
        )

    @property
    def is_fetching(self) -> bool:
        """Check if currently fetching models."""
        return self._is_fetching
