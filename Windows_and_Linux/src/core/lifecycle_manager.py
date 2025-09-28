"""
Lifecycle Manager - Manages application lifecycle events and initialization.

This module provides a LifecycleManager class that handles application startup,
shutdown, and lifecycle-related operations.
"""

import logging
import signal
import sys
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


class LifecycleManager:
    """
    Manager for application lifecycle operations.

    Handles initialization after onboarding, application exit, and mode detection.
    """

    def __init__(self, app: "WritingToolApp"):
        """
        Initialize the lifecycle manager.

        Args:
            app: Main application instance
        """
        self.app = app
        self._logger = logging.getLogger(__name__)

    def on_onboarding_closed(self) -> None:
        """
        Handle onboarding window being closed.
        Instead of exiting, continue with normal app initialization.
        """
        self._logger.debug("Onboarding window closed, continuing with app initialization")
        self.app.onboarding_window = None
        # Initialize the current provider with default settings
        self.app.ai_processor.set_current_provider()

        # Load provider-specific config from system settings
        if self.app.ai_processor.current_provider:
            provider_config = self.app.ai_processor.get_provider_config(
                self.app.settings_manager.provider
            )
            self.app.ai_processor.current_provider.load_config(provider_config)

        self.app._sync_autostart_settings()
        self.app._create_tray_icon_with_startup_delay()
        self.app.hotkey_manager.register_hotkey()

        # Set language from system settings
        self.app.language_manager.change_language(self.app.settings_manager.language or "en")

        # Initialize update checker
        from ..update_checker import UpdateChecker

        self.app.update_checker = UpdateChecker(self.app)
        self.app.update_checker.check_updates_async()

    def exit_app(self) -> None:
        """
        Exit the application.
        """
        self.app.hotkey_manager.cleanup()
        self._logger.debug("Restoring default SIGINT handler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
        self._logger.debug("Exiting application")
        self.app.quit()

    def _detect_running_mode(self) -> str:
        """
        Detect the operating mode based on the environment.

        Returns:
            str: "dev", "build-dev", or "build-final"
        """

        base_dir = Path(sys.executable).parent

        # dev
        if not getattr(sys, "frozen", False):
            self._logger.debug("Detected dev mode")
            return "dev"

        # build-dev
        elif base_dir.name == "dev":
            self._logger.debug("Detected build-dev mode")
            return "build-dev"

        # build-final
        else:
            self._logger.debug("Detected build-final mode")
            return "build-final"
