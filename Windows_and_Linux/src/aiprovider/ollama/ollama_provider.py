"""
Ollama Provider - AI provider implementation for Ollama local LLM server.

This module contains the OllamaProvider class that handles:
- Communication with Ollama API
- Model management and selection
- Message formatting for Ollama
- Installation and state management integration
"""

import logging
from typing import TYPE_CHECKING

from ollama import Client as OllamaClient
from PySide6.QtCore import QObject, QTimer, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QDialog,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
)

from ...ui.progress_window import OllamaInstallProgressWindow
from .. import AIProvider, DropdownSetting, TextSetting
from .ollama_state import OllamaStateManager

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


class OllamaInstallationHandler(QObject):
    """
    Separate QObject for managing Ollama installation signals.
    Required because AIProvider does not inherit from QObject.
    """

    installation_finished = Signal(bool)  # True if success, False otherwise


class OllamaProvider(AIProvider):
    """
    Optimized Ollama provider with async operations and state caching.
    """

    def __init__(self, app: "WritingToolsApp", skip_initial_refresh: bool = False):
        self.app = app
        self.client: OllamaClient | None = None
        self._logger = logging.getLogger(self.__class__.__name__)

        # Use the singleton state manager
        self.state_manager = OllamaStateManager()

        # Connect to state updates
        # Refresh config when Ollama installation state changes
        self.state_manager.state_updated.connect(self._on_state_updated)
        # Update model dropdown when model list changes
        self.state_manager.models_updated.connect(self._on_models_updated)
        # Refresh models when Ollama starts running
        self.state_manager.running_status_updated.connect(self._on_running_status_updated)

        # Installation finished callback will be called via QMetaObject.invokeMethod

        # Variables for cleanup (accessible by callbacks)
        self._update_timer = None
        self._progress_window = None

        # Installation signal handler (separate QObject for signals)
        self._install_handler = OllamaInstallationHandler()
        self._install_handler.installation_finished.connect(self._on_installation_finished)
        self._installation_result = None

        # Get initial state (using cached values if available)
        ollama_installed = self.state_manager.is_ollama_installed()

        # Get models without blocking
        if ollama_installed:
            # Trigger async check to see if Ollama is running and get models
            # Skip if we're just switching providers (refreshes will be handled elsewhere)
            if not skip_initial_refresh:
                self.state_manager.refresh_state_async()
                self.state_manager.refresh_models_async()
            ollama_models = self.state_manager.get_ollama_models()
        else:
            # Not installed - show appropriate message
            ollama_models = [("Ollama not installed", "")]

        # Set default model
        default_ollama_model = ""
        if ollama_models and ollama_models[0][1] and "not" not in ollama_models[0][0].lower():
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

        # No automatic refresh here - already done above

    @Slot(bool)
    def _on_installation_finished(self, success: bool):
        """Handle installation completion in main thread."""
        try:
            if self._update_timer:
                self._update_timer.stop()
                self._update_timer = None
            if self._progress_window:
                self._progress_window.close()
                self._progress_window = None
        except Exception as e:
            self._logger.error(f"Cleanup error: {e}")

        # Show result message
        if success:
            self.app.ui_manager.show_message_signal.emit(
                "Installation Successful", "Ollama has been installed successfully!"
            )
            # Refresh UI
            self.refresh_configuration()
            if hasattr(self.app, "settings_window") and self.app.systray_manager.settings_window:
                self.app.systray_manager.settings_window._on_provider_changed()
        else:
            self.app.ui_manager.show_message_signal.emit(
                "Installation Failed",
                "Ollama installation failed. Please try again or install manually.",
            )

    @Slot()
    def _on_state_updated(self):
        """Handle state updates from the state manager."""
        self.refresh_configuration()
        # Update button text in settings window if it's open
        if self.app.systray_manager.settings_window:
            self.app.systray_manager.settings_window.update_provider_button_text()

    @Slot(bool)
    def _on_running_status_updated(self, is_running: bool):
        """Handle running status updates."""
        self._logger.debug(f"Ollama running status updated: {is_running}")
        if is_running:
            # Ollama just started - refresh models
            self.state_manager.refresh_models_async()

    @Slot(list)
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
        """
        Refresh models - called when user clicks on dropdown.
        Always trigger async refresh to get fresh data.
        """
        self._logger.debug("Manual model refresh requested")
        # Always refresh when user explicitly requests it
        self.state_manager.refresh_models_async()

    def _install_ollama_async(self):
        """Install Ollama asynchronously."""

        self._progress_window = OllamaInstallProgressWindow(self.app)
        self._progress_window.show()
        self._progress_window.start_animation()

        # Timer to force regular UI updates
        self._update_timer = QTimer()
        self._update_timer.timeout.connect(lambda: QApplication.processEvents())
        self._update_timer.start(100)  # Every 100ms

        def progress_callback(status):
            if self._progress_window:
                if status == "downloading":
                    self._progress_window.set_downloading()
                elif status == "installing":
                    self._progress_window.set_installing()
                elif status == "finishing":
                    self._progress_window.set_finishing()

            # Always force UI update
            QApplication.processEvents()

        def install_thread():
            success = False
            try:
                success = self.state_manager.install_ollama(self.app, progress_callback)
            except Exception as e:
                self._logger.error(f"Installation error: {e}")
                success = False
            finally:
                # Emit signal to handle cleanup in main thread
                # This prevents "killTimer from another thread" error
                self._install_handler.installation_finished.emit(success)

        # Run installation in a separate thread
        import threading

        thread = threading.Thread(target=install_thread)
        thread.daemon = True
        thread.start()

    def refresh_configuration(self):
        """Refresh configuration based on current state."""
        ollama_installed = self.state_manager.is_ollama_installed()

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

        # Trigger async model refresh if installed and running
        if ollama_installed:
            # Check if running first (non-blocking)
            ollama_running = self.state_manager.is_ollama_running()
            if ollama_running:
                self.state_manager.refresh_models_async()
            else:
                # Not running - trigger state check in background
                self.state_manager.refresh_state_async()

    def _delete_model(self):
        """Delete model implementation."""
        # Get models from state manager (cached values)
        all_models = self.state_manager.get_ollama_models()

        # Filter out invalid models
        valid_models = [
            (display, model)
            for display, model in all_models
            if model
            and model.strip()
            and "not" not in display.lower()
            and "click" not in display.lower()
        ]

        if not valid_models:
            self.app.ui_manager.show_message_signal.emit(
                "No Models Available",
                "No Ollama models are available to delete.\n\nPlease ensure Ollama is running and has models installed.",
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
                    self.app.ui_manager.show_message_signal.emit("Model Deleted", message)
                else:
                    self.app.ui_manager.show_message_signal.emit("Deletion Failed", message)

    def _get_response_impl(
        self,
        system_instruction: str,
        prompt: str | list,
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
            self.app.ui_manager.show_message_signal.emit(error_msg[0], error_msg[1])
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
            self.app.ui_manager.show_message_signal.emit(error_msg[0], error_msg[1])
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
                self.app.ui_manager.show_message_signal.emit(
                    "Ollama Error", "No Ollama model selected."
                )
                return ""

            if self.client is None:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Ollama client not initialized."
                )
                return ""

            response = self.client.chat(model=self.api_model, messages=messages)
            response_text = response["message"]["content"].rstrip("\n")

            if not return_response and self.app.current_response_window is None:
                self.app.text_processor.output_ready_signal.emit(response_text)

            return response_text

        except Exception as e:
            error_str = str(e)
            self._logger.exception(f"Error during Ollama chat: {error_str}")

            if "connection" in error_str.lower() or "refused" in error_str.lower():
                self.app.ui_manager.show_message_signal.emit(
                    "Connection Error", "Cannot connect to Ollama server."
                )
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Ollama Error", f"An error occurred: {error_str}"
                )
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
