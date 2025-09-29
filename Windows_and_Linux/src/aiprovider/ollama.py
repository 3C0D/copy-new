import logging
import os
import platform
import shutil
import subprocess
import tempfile
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Optional, Union

from ollama import Client as OllamaClient

# PySide6 imports
from PySide6.QtCore import QObject, QTimer, Signal
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ..aiprovider.aiprovider import AIProvider, DropdownSetting, TextSetting
from ..ui.ProgressWindow import OllamaInstallProgressWindow

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


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
            app.show_message_signal.emit(
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
        # Implementation similar to your existing install_ollama_windows
        # but using the progress_callback for updates
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


class OllamaProvider(AIProvider):
    """
    Optimized Ollama provider with async operations and state caching.
    """

    def __init__(self, app: "WritingToolApp"):
        self.app = app
        self.client: Optional[OllamaClient] = None
        self._logger = logging.getLogger(self.__class__.__name__)

        # Use the singleton state manager
        self.state_manager = OllamaStateManager()

        # Connect to state updates
        self.state_manager.state_updated.connect(self._on_state_updated)
        self.state_manager.models_updated.connect(self._on_models_updated)

        # Get initial state (using cached values if available)
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_models = self.state_manager.get_ollama_models()

        # Set default model
        default_ollama_model = ""
        if ollama_models and ollama_models[0][1]:
            default_ollama_model = ollama_models[0][1]

        settings = [
            TextSetting(
                app,
                "api_base",
                "API Base URL",
                "http://localhost:11434",
                "E.g. http://localhost:11434",
            ),
            DropdownSetting(
                app,
                name="api_model",
                display_name="API Model (detected automatically)",
                default_value=default_ollama_model,
                description="Models are automatically detected from your Ollama installation",
                options=ollama_models,
                refresh_callback=self._refresh_models,
            ),
            TextSetting(
                app,
                "keep_alive",
                "Time to keep the model loaded in memory in minutes",
                "5",
                "E.g. 5",
            ),
        ]

        # Determine initial UI state and button text
        if ollama_installed:
            description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is installed and ready to use."
            )
            button_text = "Update Ollama"
        else:
            description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is not installed. Click the button to install it."
            )
            button_text = "Install Ollama"

        super().__init__(
            app,
            "Ollama",
            settings,
            description,
            "ollama",
            button_text,
            lambda: self._install_ollama_async(),
            "ollama",
        )

        # Add additional buttons if Ollama is installed
        if ollama_installed:
            self.add_button("🗑️ Delete Model", self._delete_model, "secondary")

        # Start async refresh on initialization
        self.state_manager.refresh_state_async()

    def _on_state_updated(self):
        """Handle state updates from the state manager."""
        self.refresh_configuration()
        # Update button text in settings window if it's open
        if hasattr(self.app, "settings_window") and self.app.settings_window:
            self.app.settings_window.update_provider_button_text()

    def _on_models_updated(self, models: list[tuple[str, str]]):
        """Handle model list updates."""
        for setting in self.settings:
            if setting.name == "api_model" and isinstance(setting, DropdownSetting):
                setting.refresh_options(models)
                # Update selection if needed
                current_value = setting.get_value() if hasattr(setting, "get_value") else ""
                if models and models[0][1] and not current_value:
                    setting.set_value(models[0][1])
                break

    def _refresh_models(self):
        """Refresh models asynchronously if cache is stale."""
        if not self.state_manager._is_cache_valid(
            self.state_manager._models_check_time, self.state_manager.CACHE_DURATION
        ):
            self.state_manager.refresh_models_async()
        else:
            # Cache is valid, emit current cached models to update UI if needed
            self.state_manager.models_updated.emit(self.state_manager.get_ollama_models())

    def _install_ollama_async(self):
        """Install Ollama asynchronously."""

        progress_window = OllamaInstallProgressWindow(self.app)
        progress_window.show()
        progress_window.start_animation()

        def progress_callback(status):
            if status == "downloading":
                QApplication.processEvents()
            elif status == "installing":
                progress_window.set_installing()
                QApplication.processEvents()
            elif status == "finishing":
                progress_window.set_finishing()
                QApplication.processEvents()

        def install_thread():
            success = self.state_manager.install_ollama(self.app, progress_callback)
            progress_window.close()

            if success:
                self.app.show_message_signal.emit(
                    "Installation Successful", "Ollama has been installed successfully!"
                )
                # Refresh UI
                self.refresh_configuration()
                if hasattr(self.app, "settings_window") and self.app.settings_window:
                    self.app.settings_window._on_provider_changed()
            else:
                self.app.show_message_signal.emit(
                    "Installation Failed",
                    "Ollama installation failed. Please try again or install manually.",
                )

        # Run installation in a separate thread
        import threading

        thread = threading.Thread(target=install_thread)
        thread.start()

    def refresh_configuration(self):
        """Refresh configuration based on current state."""
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_running = self.state_manager.is_ollama_running() if ollama_installed else False

        if ollama_installed:
            self.description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is installed and ready to use."
            )
            self.button_text = "Update Ollama"
        else:
            self.description = (
                "• Connect to an Ollama server (local LLM).\n"
                "• Ollama is not installed. Click the button to install it."
            )
            self.button_text = "Install Ollama"

        # Update additional buttons
        self.additional_buttons = []
        if ollama_installed:
            self.add_button("🗑️ Delete Model", self._delete_model, "secondary")

        # Refresh models if installed and running
        if ollama_installed and ollama_running:
            self._refresh_models()

    def _delete_model(self):
        """Delete model implementation - same as before but using state_manager."""
        # Get models from state manager
        valid_models = [
            (display, model)
            for display, model in self.state_manager.get_ollama_models()
            if model and model.strip()
        ]

        if not valid_models:
            self.app.show_message_signal.emit(
                "No Models Available", "No Ollama models are available to delete."
            )
            return

        # Create selection dialog (same as before)
        dialog = QDialog()
        dialog.setWindowTitle("Delete Ollama Model")
        dialog.setModal(True)
        dialog.resize(400, 200)

        layout = QVBoxLayout(dialog)

        warning_label = QLabel("⚠️ Warning: This will permanently delete the selected model.")
        layout.addWidget(warning_label)

        model_label = QLabel("Select model to delete:")
        layout.addWidget(model_label)

        model_combo = QComboBox()
        for display_name, model_name in valid_models:
            model_combo.addItem(display_name, model_name)
        layout.addWidget(model_combo)

        button_layout = QHBoxLayout()

        cancel_button = QPushButton("Cancel")
        cancel_button.clicked.connect(dialog.reject)
        button_layout.addWidget(cancel_button)

        delete_button = QPushButton("Delete Model")
        delete_button.clicked.connect(dialog.accept)
        button_layout.addWidget(delete_button)

        layout.addLayout(button_layout)

        if dialog.exec() == QDialog.DialogCode.Accepted:
            selected_model = model_combo.currentData()
            if selected_model:
                success, message = self.state_manager.remove_ollama_model(selected_model)

                if success:
                    self.app.show_message_signal.emit("Model Deleted", message)
                else:
                    self.app.show_message_signal.emit("Deletion Failed", message)

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: Union[str, list],
        return_response: bool = False,
        **kwargs,
    ) -> str:
        """Send request to Ollama server."""
        # Check Ollama status before attempting to send request
        ollama_installed = self.state_manager.is_ollama_installed()
        ollama_running = self.state_manager.is_ollama_running()

        if not ollama_installed:
            error_msg = (
                "Ollama Not Installed",
                "Ollama is not installed on your system.\n\n"
                "Please go to Settings and use the 'Install Ollama' button to install it.\n\n"
                "Once installed, you can use Ollama for AI responses.",
            )
            self.app.show_message_signal.emit(error_msg[0], error_msg[1])
            return ""

        if not ollama_running:
            error_msg = (
                "Ollama Not Running",
                "Ollama is installed but not currently running.\n\n"
                "Please start Ollama using your system's Ollama application.\n"
                "On Windows: Click the Ollama icon in your system tray or start menu.\n"
                "On Linux: Run 'ollama serve' in a terminal.\n\n"
                "Or go to Settings to manage Ollama.",
            )
            self.app.show_message_signal.emit(error_msg[0], error_msg[1])
            return ""

        # Implementation for Ollama message format
        image_data = kwargs.get("image_data")
        if isinstance(prompt, list):
            # Chat history format - messages are already structured
            messages = []

            for msg in prompt:
                ollama_msg = {"role": msg["role"], "content": ""}

                # Handle content that can be string or list (OpenAI format)
                content = msg.get("content", "")
                if isinstance(content, list):
                    # OpenAI format: extract text and images
                    text_parts = []
                    images = []

                    for part in content:
                        if part.get("type") == "text":
                            text_parts.append(part.get("text", ""))
                        elif part.get("type") == "image_url":
                            # Extract base64 from data URL
                            image_url = part.get("image_url", {})
                            if isinstance(image_url, dict):
                                url = image_url.get("url", "")
                            else:
                                url = str(image_url)

                            if url.startswith("data:image/"):
                                # Extract base64 part
                                base64_data = url.split(",", 1)[1] if "," in url else ""
                                if base64_data:
                                    images.append(base64_data)

                    ollama_msg["content"] = " ".join(text_parts)
                    if images:
                        ollama_msg["images"] = images
                else:
                    # Simple string content
                    ollama_msg["content"] = str(content)

                messages.append(ollama_msg)

            # Add system instruction at the beginning if not present
            if not messages or messages[0].get("role") != "system":
                messages.insert(0, {"role": "system", "content": system_instruction})
        else:
            if image_data:
                # Ollama format for images: content is text, images is separate field
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt, "images": [image_data]},
                ]
            else:
                messages = [
                    {"role": "system", "content": system_instruction},
                    {"role": "user", "content": prompt},
                ]

        try:
            if not self.api_model or self.api_model.strip() == "":
                self.app.show_message_signal.emit("Ollama Error", "No Ollama model selected.")
                return ""

            if self.client is None:
                self.app.show_message_signal.emit("Error", "Ollama client not initialized.")
                return ""

            response = self.client.chat(model=self.api_model, messages=messages)
            response_text = response["message"]["content"].rstrip("\n")

            if not return_response and not hasattr(self.app, "current_response_window"):
                self.app.output_ready_signal.emit(response_text)

            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Error during Ollama chat: {error_str}")

            if "connection" in error_str.lower() or "refused" in error_str.lower():
                self.app.show_message_signal.emit(
                    "Connection Error", "Cannot connect to Ollama server."
                )
            else:
                self.app.show_message_signal.emit("Ollama Error", f"An error occurred: {error_str}")
            return ""

    def after_load(self):
        """Initialize Ollama client."""
        if OllamaClient is not None and self.state_manager.is_ollama_installed():
            try:
                self.client = OllamaClient(host=self.api_base)
                self._logger.debug("Ollama client initialized successfully")
            except Exception as e:
                self._logger.warning(f"Failed to initialize Ollama client: {e}")
                self.client = None
        else:
            self.client = None

    def before_load(self):
        """Clean up client before reloading."""
        self.client = None
