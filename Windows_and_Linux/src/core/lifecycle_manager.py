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

    Handles application exit and mode detection.
    """

    def __init__(self, app: "WritingToolApp"):
        """
        Initialize the lifecycle manager.

        Args:
            app: Main application instance
        """
        self.app = app
        self._logger = logging.getLogger(__name__)


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
