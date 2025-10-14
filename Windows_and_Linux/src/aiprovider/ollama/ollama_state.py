"""
Ollama State Manager - Singleton manager for Ollama state and operations.

This module contains the OllamaStateManager class that handles:
- Ollama installation detection and management
- Model listing and management
- State caching and async operations
- Installation procedures for Windows and Linux
"""

import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

from PySide6.QtCore import QObject, Signal


class OllamaStateManager(QObject):
    """
    Singleton manager for Ollama state to avoid redundant checks.
    Uses caching and async operations to prevent UI blocking.
    """

    # Signals for async updates
    state_updated = Signal()
    models_updated = Signal(list)
    running_status_updated = Signal(bool)

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not hasattr(self, "initialized"):
            super().__init__()
            self.initialized = True
            self._logger = logging.getLogger(self.__class__.__name__)

            # Cache states
            self._ollama_path: str | None = None
            self._is_installed: bool | None = None
            self._is_running: bool | None = None
            self._models_list: list[tuple[str, str]] = []

            # Cache timestamps (in seconds)
            self._path_check_time = 0
            self._running_check_time = 0
            self._models_check_time = 0

            # Cache duration in seconds
            self.CACHE_DURATION = 30  # 30 seconds cache
            self.QUICK_CHECK_DURATION = 5  # 5 seconds for running status

            # Thread executor for async operations
            self._executor = ThreadPoolExecutor(max_workers=2)

    def _get_current_time(self) -> float:
        """Get current time in seconds."""
        import time

        return time.time()

    def _is_cache_valid(self, check_time: float, duration: float) -> bool:
        """Check if cached value is still valid."""
        return (self._get_current_time() - check_time) < duration

    def find_ollama_executable(self, force_refresh: bool = False) -> str | None:
        """
        Find the Ollama executable with caching.
        """
        if (
            not force_refresh
            and self._ollama_path
            and self._is_cache_valid(self._path_check_time, self.CACHE_DURATION)
        ):
            return self._ollama_path

        # First try to find ollama in env PATH
        ollama_path = shutil.which("ollama")
        if ollama_path:
            self._ollama_path = ollama_path
            self._path_check_time = self._get_current_time()
            return ollama_path

        # Check standard installation locations
        system = platform.system().lower()
        possible_paths = []

        if system == "windows":
            possible_paths = [
                Path.home() / "AppData" / "Local" / "Programs" / "Ollama" / "ollama.exe",
                Path("C:") / "Program Files" / "Ollama" / "ollama.exe",
                Path("C:") / "Program Files (x86)" / "Ollama" / "ollama.exe",
            ]
        elif system == "linux":
            possible_paths = [
                Path("/usr/local/bin/ollama"),
                Path("/usr/bin/ollama"),
                Path.home() / ".local" / "bin" / "ollama",
            ]

        for path in possible_paths:
            # Check if file exists and is executable
            if path.is_file() and os.access(path, os.X_OK):
                self._ollama_path = str(path)
                self._path_check_time = self._get_current_time()
                return self._ollama_path

        self._ollama_path = None
        self._path_check_time = self._get_current_time()
        return None

    def is_ollama_installed(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama is installed with caching.
        """
        if (
            not force_refresh
            and self._is_installed is not None
            and self._is_cache_valid(self._path_check_time, self.CACHE_DURATION)
        ):
            return self._is_installed

        ollama_path = self.find_ollama_executable(force_refresh)
        self._is_installed = ollama_path is not None
        return self._is_installed

    def _check_running_sync(self) -> bool:
        """
        Synchronous check if Ollama is running.
        INTERNAL USE ONLY - should be called from worker thread.
        """
        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            return False

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self._logger.debug("Checking if Ollama is running: ollama --version")
            result = subprocess.run(
                [ollama_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=1.0,
                startupinfo=startupinfo,
            )
            is_running = result.returncode == 0
            self._logger.debug(f"Ollama running status: {is_running}")
            return is_running
        except subprocess.TimeoutExpired:
            self._logger.debug("Ollama check timeout - assuming not running")
            return False
        except (FileNotFoundError, Exception) as e:
            self._logger.debug(f"Ollama check failed: {e}")
            return False

    def refresh_running_status_async(self):
        """
        Refresh running status asynchronously without blocking the UI.
        """

        def _refresh():
            try:
                is_running = self._check_running_sync()
                self._is_running = is_running
                self._running_check_time = self._get_current_time()
                self.running_status_updated.emit(is_running)
            except Exception as e:
                self._logger.error(f"Error in async running status refresh: {e}")

        self._executor.submit(_refresh)

    def is_ollama_running(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama is running with short-term caching.
        Returns cached value immediately - use refresh_running_status_async() to update in background.
        """
        if (
            not force_refresh
            and self._is_running is not None
            and self._is_cache_valid(self._running_check_time, self.QUICK_CHECK_DURATION)
        ):
            return self._is_running

        # If not installed, definitely not running
        if not self._is_installed:
            self._is_running = False
            self._running_check_time = self._get_current_time()
            return False

        # Return cached value or False if no cache
        # Trigger async refresh if cache is stale
        if self._is_running is None:
            self._is_running = False
            self.refresh_running_status_async()

        return self._is_running

    def _get_models_sync(self) -> list[tuple[str, str]]:
        """
        Synchronous get models list.
        INTERNAL USE ONLY - should be called from worker thread.
        """
        if not self.is_ollama_installed():
            return [("Ollama not available - Please install it", "")]

        # Don't try to get models if we know Ollama isn't running
        # This prevents auto-starting Ollama
        if not self._check_running_sync():
            return [("Ollama not running - Please start Ollama", "")]

        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            return [("Ollama not available", "")]

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            self._logger.debug("Getting Ollama models list: ollama list")
            result = subprocess.run(
                [ollama_path, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5.0,  # Increased timeout
                startupinfo=startupinfo,
            )

            if result.returncode == 0:
                lines = result.stdout.strip().split("\n")
                models = []

                for line in lines[1:]:  # Skip header
                    if line.strip():
                        parts = line.split()
                        if parts:
                            model_name = parts[0]
                            size_info = ""
                            if len(parts) >= 3:
                                size_raw = parts[2]
                                if size_raw.upper().endswith("GB"):
                                    size_value = size_raw[:-2]
                                    size_info = f" ({size_value} GB)"
                                elif size_raw.upper().endswith("MB"):
                                    size_value = size_raw[:-2]
                                    size_info = f" ({size_value} MB)"
                                else:
                                    size_info = f" ({size_raw})"

                            vision_indicator = ""
                            if "vision" in model_name.lower() or "vl" in model_name.lower():
                                vision_indicator = "* "

                            display_name = f"{vision_indicator}{model_name}{size_info}"
                            models.append((display_name, model_name))

                if models:
                    self._logger.debug(f"Found {len(models)} Ollama models")
                    return models
                else:
                    return [("Please install Ollama models first", "")]
            else:
                error_output = result.stderr.strip() if result.stderr else "Unknown error"
                self._logger.warning(f"Failed to get models: {error_output}")
                return [("Please install Ollama models first", "")]

        except subprocess.TimeoutExpired:
            self._logger.warning("Timeout getting Ollama models")
            return [("Ollama not responding - Please check Ollama", "")]
        except Exception as e:
            self._logger.warning(f"Error getting models: {e}")
            return [("Error getting models", "")]

    def get_ollama_models(self, force_refresh: bool = False) -> list[tuple[str, str]]:
        """
        Get list of installed Ollama models with caching.
        Returns cached value immediately - use refresh_models_async() to update in background.
        """
        if (
            not force_refresh
            and self._models_list
            and self._is_cache_valid(self._models_check_time, self.CACHE_DURATION)
        ):
            return self._models_list

        # Return cached value or placeholder
        if not self._models_list:
            return [("Click to refresh models", "")]

        return self._models_list

    def refresh_models_async(self):
        """
        Refresh models asynchronously without blocking the UI.
        """

        def _refresh():
            try:
                self._logger.debug("Starting async model refresh")
                models = self._get_models_sync()  # Use sync method
                self._models_list = models
                self._models_check_time = self._get_current_time()
                self.models_updated.emit(models)
                self._logger.debug(f"Model refresh complete: {len(models)} models")
            except Exception as e:
                self._logger.error(f"Error in async model refresh: {e}")

        self._executor.submit(_refresh)

    def refresh_state_async(self):
        """
        Refresh Ollama state asynchronously.
        Checks installation status and running status without blocking UI.
        """

        def _refresh():
            try:
                self._logger.debug("Starting async state refresh")
                # Check installation (no subprocess)
                self.is_ollama_installed(force_refresh=True)

                # Check if running (subprocess in thread)
                self._is_running = self._check_running_sync()
                self._running_check_time = self._get_current_time()

                self.state_updated.emit()
                self._logger.debug(
                    f"State refresh complete: installed={self._is_installed}, running={self._is_running}"
                )
            except Exception as e:
                self._logger.error(f"Error in async state refresh: {e}")

        self._executor.submit(_refresh)

    def get_current_ollama_version(self) -> str | None:
        """
        Get the current installed Ollama version.
        Returns None if Ollama is not installed or version cannot be determined.
        """
        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            return None

        try:
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                [ollama_path, "--version"],
                check=False,
                capture_output=True,
                text=True,
                timeout=5,
                startupinfo=startupinfo,
            )

            if result.returncode == 0:
                version_line = result.stdout.strip()
                if "version" in version_line.lower():
                    return version_line.split()[-1]
        except Exception as e:
            self._logger.debug(f"Error getting Ollama version: {e}")

        return None

    def get_latest_ollama_version(self) -> str | None:
        """
        Get the latest Ollama version from GitHub releases.
        Returns None if unable to fetch version.
        """
        try:
            import requests

            response = requests.get(
                "https://api.github.com/repos/ollama/ollama/releases/latest", timeout=10
            )

            if response.status_code == 200:
                data = response.json()
                if data and isinstance(data, dict):
                    tag_name = data.get("tag_name", "")
                    if tag_name and isinstance(tag_name, str):
                        if tag_name.startswith("v"):
                            return tag_name[1:]  # Remove 'v' prefix
                        return tag_name
        except Exception as e:
            self._logger.debug(f"Error fetching latest Ollama version: {e}")

        return None

    def is_update_needed(self) -> bool:
        """
        Check if Ollama update is needed by comparing current and latest versions.
        Returns True if update is needed or if versions cannot be determined.
        """
        current = self.get_current_ollama_version()
        latest = self.get_latest_ollama_version()

        self._logger.debug(f"Version check - Current: {current}, Latest: {latest}")

        if not current or not latest:
            self._logger.debug("Cannot determine versions, assuming update might be needed")
            return True  # If we can't determine versions, assume update might be needed

        try:
            from packaging import version

            result = version.parse(current) < version.parse(latest)
            self._logger.debug(f"Version comparison result: {result}")
            return result
        except ImportError:
            # Fallback to string comparison if packaging is not available
            result = current < latest
            self._logger.debug(f"String comparison result: {result}")
            return result
        except Exception as e:
            self._logger.debug(f"Version comparison error: {e}, assuming update needed")
            return True  # If comparison fails, assume update needed

    def remove_ollama_model(self, model_name: str) -> tuple[bool, str]:
        """
        Remove an Ollama model.
        """
        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            return False, "Ollama not available - Please install it"

        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                [ollama_path, "rm", model_name],
                check=False,
                capture_output=True,
                text=True,
                timeout=30,
                startupinfo=startupinfo,
            )

            if result.returncode == 0:
                # Invalidate models cache and refresh
                self._models_check_time = 0
                self._models_list = []
                self.refresh_models_async()
                return True, f"Model '{model_name}' removed successfully"
            else:
                error_msg = result.stderr.strip() if result.stderr else "Unknown error"
                if "not found" in error_msg.lower():
                    return False, f"Model '{model_name}' not found"
                elif "in use" in error_msg.lower():
                    return False, f"Model '{model_name}' is currently in use"
                else:
                    return False, f"Failed to remove model '{model_name}': {error_msg}"

        except subprocess.TimeoutExpired:
            return False, f"Timeout while removing model '{model_name}'"
        except Exception as e:
            return False, f"Error removing model '{model_name}': {str(e)}"

    def install_ollama(self, app, progress_callback=None) -> bool | None:
        """
        Install or update Ollama with progress updates.
        Checks if update is needed before proceeding with installation.

        Returns:
            True if installation/update was successful
            False if installation/update failed
            None if no installation was needed (already up to date)
        """
        # Check if Ollama is already installed and up to date
        if self.is_ollama_installed():
            current_version = self.get_current_ollama_version()
            if not self.is_update_needed():
                app.ui_manager.show_message_signal.emit(
                    "Already Up to Date",
                    f"Ollama is already at the latest version ({current_version}).\n\n"
                    "No installation needed.",
                )
                return None  # No installation needed

            # Show update message
            latest_version = self.get_latest_ollama_version()
            app.ui_manager.show_message_signal.emit(
                "Updating Ollama",
                f"Current version: {current_version}\n"
                f"Latest version: {latest_version}\n\n"
                "Updating Ollama...",
            )

        system = platform.system().lower()

        if system == "windows":
            success = self._install_ollama_windows(app, progress_callback)
        elif system == "linux":
            success = self._install_ollama_linux(app, progress_callback)
        else:
            app.ui_manager.show_message_signal.emit(
                "Unsupported platform",
                f"Automatic installation is not supported on {system}.\n\n"
                f"Please install manually from https://ollama.com",
            )
            return False

        if success:
            # Invalidate all caches after installation
            self._ollama_path = None
            self._is_installed = None
            self._is_running = None
            self._models_list = []
            self._path_check_time = 0
            self._running_check_time = 0
            self._models_check_time = 0
            self.refresh_state_async()

        return success

    def _install_ollama_windows(self, app, progress_callback) -> bool:
        """Windows installation implementation."""
        try:
            import time

            import requests

            ollama_url = "https://ollama.com/download/OllamaSetup.exe"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
                temp_path = temp_file.name

                response = requests.get(ollama_url, stream=True, allow_redirects=True)
                response.raise_for_status()

                downloaded = 0
                last_progress_time = time.time()

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                        downloaded += len(chunk)

                        # Update progress every 500ms
                        current_time = time.time()
                        if current_time - last_progress_time >= 0.5:
                            last_progress_time = current_time
                            if progress_callback:
                                progress_callback("downloading")
                                # Force UI update
                                from PySide6.QtWidgets import QApplication

                                QApplication.processEvents()

                # Final download update
                if progress_callback:
                    progress_callback("downloading")

            if progress_callback:
                progress_callback("installing")
                # Force UI update
                from PySide6.QtWidgets import QApplication

                QApplication.processEvents()

            # Run installer
            result = subprocess.run([temp_path], check=False)

            # Finishing phase
            if progress_callback:
                progress_callback("finishing")
                # Force UI update
                from PySide6.QtWidgets import QApplication

                QApplication.processEvents()

            try:
                os.unlink(temp_path)
            except OSError:
                pass

            return result.returncode == 0

        except Exception as e:
            self._logger.exception(f"Error installing Ollama: {e}")
            return False

    def _install_ollama_linux(self, app, progress_callback) -> bool:
        """Linux installation implementation."""
        try:
            if progress_callback:
                progress_callback("installing")

            install_command = "curl -fsSL https://ollama.com/install.sh | sh"
            result = subprocess.run(
                install_command, shell=True, check=False, capture_output=True, text=True
            )

            return result.returncode == 0

        except Exception as e:
            self._logger.exception(f"Error installing Ollama on Linux: {e}")
            return False
