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
from typing import Optional

from PySide6.QtCore import QObject, QTimer, Signal

from ..ui.progress_window import OllamaInstallProgressWindow


class OllamaStateManager(QObject):
    """
    Singleton manager for Ollama state to avoid redundant checks.
    Uses caching and async operations to prevent UI blocking.
    """

    # Signals for async updates
    state_updated = Signal()
    models_updated = Signal(list)

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
            self._ollama_path: Optional[str] = None
            self._is_installed: Optional[bool] = None
            self._is_running: Optional[bool] = None
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

            # Timer for periodic checks
            self._check_timer = QTimer()
            self._check_timer.timeout.connect(self._periodic_check)
            self._check_timer.start(30000)  # Check every 30 seconds

    def _get_current_time(self) -> float:
        """Get current time in seconds."""
        import time

        return time.time()

    def _is_cache_valid(self, check_time: float, duration: float) -> bool:
        """Check if cached value is still valid."""
        return (self._get_current_time() - check_time) < duration

    def find_ollama_executable(self, force_refresh: bool = False) -> Optional[str]:
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

    def is_ollama_running(self, force_refresh: bool = False) -> bool:
        """
        Check if Ollama is running with short-term caching.
        """
        if (
            not force_refresh
            and self._is_running is not None
            and self._is_cache_valid(self._running_check_time, self.QUICK_CHECK_DURATION)
        ):
            return self._is_running

        # Use cached installation status to avoid redundant path finding
        if not self._is_installed:
            self._is_running = False
            self._running_check_time = self._get_current_time()
            return False

        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            self._is_running = False
            self._running_check_time = self._get_current_time()
            return False

        try:
            # Hide console window on Windows
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
                timeout=0.5,  # Reduced timeout for better performance
                startupinfo=startupinfo,
            )
            self._is_running = result.returncode == 0
        except (subprocess.TimeoutExpired, FileNotFoundError, Exception):
            self._is_running = False

        self._running_check_time = self._get_current_time()
        return self._is_running

    def get_ollama_models(self, force_refresh: bool = False) -> list[tuple[str, str]]:
        """
        Get list of installed Ollama models with caching.
        """
        if (
            not force_refresh
            and self._models_list
            and self._is_cache_valid(self._models_check_time, self.CACHE_DURATION)
        ):
            return self._models_list

        if not self.is_ollama_installed():
            self._models_list = [("Ollama not available - Please install it", "")]
            return self._models_list

        if not self.is_ollama_running():
            self._models_list = [("Ollama not running - Please start Ollama", "")]
            return self._models_list

        ollama_path = self.find_ollama_executable()
        if not ollama_path:
            self._models_list = [("Ollama not available", "")]
            return self._models_list

        try:
            # Hide console window on Windows
            startupinfo = None
            if os.name == "nt":
                startupinfo = subprocess.STARTUPINFO()
                startupinfo.dwFlags |= subprocess.STARTF_USESHOWWINDOW
                startupinfo.wShowWindow = subprocess.SW_HIDE

            result = subprocess.run(
                [ollama_path, "list"],
                check=False,
                capture_output=True,
                text=True,
                timeout=2.0,  # Longer timeout for list operation
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

                            # Add asterisk for models with vision support
                            vision_indicator = ""
                            if "vision" in model_name.lower() or "vl" in model_name.lower():
                                vision_indicator = "*"

                            display_name = f"{vision_indicator}{model_name}{size_info}"
                            models.append((display_name, model_name))

                if models:
                    self._models_list = models
                else:
                    self._models_list = [("Please install Ollama models first", "")]
            else:
                self._models_list = [("Please install Ollama models first", "")]

        except subprocess.TimeoutExpired:
            self._models_list = [("Ollama not running - Please start Ollama", "")]
        except Exception:
            self._models_list = [("", "")]

        self._models_check_time = self._get_current_time()
        return self._models_list

    def refresh_models_async(self):
        """
        Refresh models asynchronously without blocking the UI.
        """

        def _refresh():
            models = self.get_ollama_models(force_refresh=True)
            self.models_updated.emit(models)

        self._executor.submit(_refresh)

    def refresh_state_async(self):
        """
        Refresh Ollama state asynchronously.
        """

        def _refresh():
            self.is_ollama_installed(force_refresh=True)
            self.is_ollama_running(force_refresh=True)
            self.state_updated.emit()

        self._executor.submit(_refresh)

    def _periodic_check(self):
        """
        Periodic background check of Ollama state.
        """
        self.refresh_state_async()

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
                # Invalidate models cache
                self._models_check_time = 0
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

    def install_ollama(self, app, progress_callback=None) -> bool:
        """
        Install Ollama with progress updates.
        """
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
            self._path_check_time = 0
            self._running_check_time = 0
            self.refresh_state_async()

        return success

    def _install_ollama_windows(self, app, progress_callback) -> bool:
        """Windows installation implementation."""
        try:
            import requests

            ollama_url = "https://ollama.com/download/OllamaSetup.exe"

            with tempfile.NamedTemporaryFile(delete=False, suffix=".exe") as temp_file:
                temp_path = temp_file.name

                response = requests.get(ollama_url, stream=True, allow_redirects=True)
                response.raise_for_status()

                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        temp_file.write(chunk)
                    if progress_callback:
                        progress_callback("downloading")

            if progress_callback:
                progress_callback("installing")

            result = subprocess.run([temp_path], check=False)

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