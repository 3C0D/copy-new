"""
Update Manager - Manages application updates and version checking.

This module provides an UpdateManager class that handles checking for updates
from GitHub and managing update availability.
"""

import logging
import threading
import time
from typing import TYPE_CHECKING
from urllib.error import HTTPError, URLError
from urllib.request import urlopen

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp

CURRENT_VERSION = 7
UPDATE_CHECK_URL = "https://raw.githubusercontent.com/theJayTea/WritingTools/main/Windows_and_Linux/Latest_Version_for_Update_Check.txt"
UPDATE_DOWNLOAD_URL = "https://github.com/theJayTea/WritingTools/releases"


class UpdateManager:
    """
    Manager for application update checking and management.
    """

    def __init__(self, app: "WritingToolsApp"):
        """
        Initialize the update manager.

        Args:
            app: Main application instance
        """
        self.app = app
        self._logger = logging.getLogger(__name__)

    def _fetch_latest_version(self):
        """
        Fetch the latest version number from GitHub.
        Returns the version number or None if failed.
        """
        try:
            with urlopen(UPDATE_CHECK_URL, timeout=5) as response:
                data = response.read().decode("utf-8").strip()
                try:
                    return int(data)
                except ValueError:
                    self._logger.warning(f"Invalid version number format: {data}")
                    return None
        except (URLError, HTTPError) as e:
            self._logger.warning(f"Failed to fetch version info: {e}")
            return None
        except Exception as e:
            self._logger.exception(f"Unexpected error checking for updates: {e}")
            return None

    def _retry_fetch_version(self):
        """
        Attempt to fetch version with one retry.
        """
        result = self._fetch_latest_version()
        if result is None:
            # Wait 2 seconds before retry
            time.sleep(2)
            result = self._fetch_latest_version()
        return result

    def check_updates(self):
        """
        Check if an update is available.
        Always checks against cloud value and updates config accordingly.
        Returns True if an update is available.
        """
        latest_version = self._retry_fetch_version()

        if latest_version is None:
            return False

        update_available = latest_version > CURRENT_VERSION

        # Always update settings with fresh status
        # Store update status in system settings
        self.app.settings_manager.update_available = update_available

        return update_available

    def check_updates_async(self):
        """
        Perform the update check in a background thread.
        """

        def check_thread():
            self.check_updates()

        thread = threading.Thread(target=check_thread, daemon=True)
        thread.start()
