"""
provider_settings.py

AI Provider settings component with dynamic UI generation.
"""

import logging
from typing import TYPE_CHECKING, cast

from PySide6 import QtCore
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLayout,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from ...aiprovider.aiprovider import AIProvider
    from ...writing_tools_app import WritingToolsApp
    from .settings_window import SettingsWindow

from ...aiprovider.anthropic import AnthropicProvider
from ...aiprovider.gemini import GeminiProvider
from ...aiprovider.mistral import MistralProvider
from ...aiprovider.ollama import OllamaProvider
from ...aiprovider.openAI import OpenAIProvider
from ...aiprovider.openAI_compatible import OpenAICompatibleProvider
from ...config.constants import PROVIDER_DISPLAY_NAMES
from ...config.data_operations import get_provider_display_name
from ..ui_utils import ui_utils

# Mapping of internal provider names to their classes
PROVIDER_CLASSES = {
    "gemini": GeminiProvider,
    "ollama": OllamaProvider,
    "anthropic": AnthropicProvider,
    "mistral": MistralProvider,
    "openAIcompatible": OpenAICompatibleProvider,
    "openAI": OpenAIProvider,
}


def _(x):
    return x


class ProviderSettings(QWidget):
    """Widget for AI provider selection and configuration."""

    def __init__(self, app: "WritingToolsApp", parent: "SettingsWindow"):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent
        self._logger = logging.getLogger(__name__)

        self.current_provider_layout = None

        # UI components
        self.provider_label = None
        self.provider_dropdown = None
        self.provider_container = None
        self.provider_name_label = None
        self.description_label = None
        self.vision_comment = None
        self.main_button = None

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize provider settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Provider selection
        self.provider_label = QLabel(_("Choose AI Provider:"))
        self.provider_label.setStyleSheet(self.app.styles["label"])
        layout.addWidget(self.provider_label)

        self.provider_dropdown = QComboBox()
        self.provider_dropdown.setStyleSheet(self.app.styles["dropdown"])
        self.provider_dropdown.wheelEvent = lambda e: e.ignore()

        current_provider = self.app.settings_manager.provider

        # Populate dropdown
        for internal_name, display_name in PROVIDER_DISPLAY_NAMES.items():
            self.provider_dropdown.addItem(display_name, internal_name)

        # Set current selection
        current_display_name = get_provider_display_name(current_provider)
        current_index = self.provider_dropdown.findText(current_display_name)

        if current_index != -1:
            self.provider_dropdown.setCurrentIndex(current_index)
        else:
            self.provider_dropdown.setCurrentIndex(0)
            self._logger.warning("Current provider not found, defaulting to first item")

        layout.addWidget(self.provider_dropdown)

        # Provider UI container
        self.provider_container = QVBoxLayout()
        layout.addLayout(self.provider_container)

        # Initial provider UI - use ai_processor's current provider
        if self.app.ai_processor.current_provider:
            self.init_provider_ui(self.app.ai_processor.current_provider, self.provider_container)
        else:
            # Fallback if no provider is set
            current_internal_name = self.provider_dropdown.currentData()
            provider_instance = self._find_provider_by_name(current_internal_name)

            if not provider_instance:
                # Fallback to first available provider
                default_provider_name = list(PROVIDER_CLASSES.keys())[0]
                provider_class = PROVIDER_CLASSES.get(default_provider_name)
                if provider_class:
                    try:
                        provider_instance = provider_class(self.app)
                    except Exception as e:
                        self._logger.error(f"Failed to create default provider {default_provider_name}: {e}")
                        provider_instance = None

            if provider_instance:
                self.app.ai_processor.current_provider = provider_instance
                self.init_provider_ui(provider_instance, self.provider_container)

        # Connect provider change
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)

        # Vision comment
        self.vision_comment = QLabel(_("* Models with vision support"))
        self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")
        layout.addWidget(self.vision_comment)

    def init_provider_ui(self, provider: "AIProvider", layout: QVBoxLayout) -> None:
        """Initialize UI for a specific provider."""
        # Refresh provider configuration
        self._refresh_provider_config(provider)

        # Clean up old UI
        self._cleanup_provider_layout()
        ui_utils.clear_layout(layout)

        self.current_provider_layout = QVBoxLayout()

        # Provider header (logo + name)
        provider_header_layout = QHBoxLayout()
        provider_header_layout.setSpacing(10)
        provider_header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Logo
        if provider.logo:
            logo_path = ui_utils.get_icon_path(
                self.app, f"provider_{provider.logo}", with_theme=False
            )
            if logo_path.exists():
                targetPixmap = ui_utils.resize_and_round_image(QImage(logo_path), 30, 15)
                logo_label = QLabel()
                logo_label.setPixmap(targetPixmap)
                logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                provider_header_layout.addWidget(logo_label)

        # Name
        self.provider_name_label = QLabel(provider.provider_name)
        self.provider_name_label.setStyleSheet(
            f"{self.app.styles['label_title']}; font-size: 18px;"
        )
        self.provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(self.provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

        # Description
        if provider.description:
            self.description_label = QLabel(provider.description)
            self.description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")
            self.description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(self.description_label)

        # Buttons
        self._add_provider_buttons(provider)

        # Initialize provider settings
        if not self.app.settings_manager.providers:
            self.app.settings_manager.providers = {}

        if provider.internal_name not in self.app.settings_manager.providers:
            self.app.settings_manager.providers[provider.internal_name] = {}

        # Build settings UI
        provider_config = self.app.settings_manager.providers[provider.internal_name]
        for setting in provider.settings:
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)
            setting.set_auto_save_callback(self.save_current_provider_settings)
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

        # Disable dropdown scroll interference
        self._disable_dropdown_scroll(self.current_provider_layout)

        self._logger.debug(f"Provider UI initialized: {provider.internal_name}")

    def _refresh_provider_config(self, provider: "AIProvider") -> None:
        """Refresh provider configuration if supported."""
        if not hasattr(provider, "refresh_configuration"):
            return

        if provider.internal_name == "ollama":
            from ...aiprovider.ollama import OllamaStateManager

            state_manager = OllamaStateManager()
            if state_manager.is_ollama_installed():
                try:
                    provider.refresh_configuration()
                    self._logger.debug(f"Refreshed config: {provider.internal_name}")
                except Exception as e:
                    self._logger.warning(f"Failed to refresh Ollama config: {e}")
            else:
                self._logger.debug("Skipped Ollama refresh - not installed")
        else:
            provider.refresh_configuration()
            self._logger.debug(f"Refreshed config: {provider.internal_name}")

    def _cleanup_provider_layout(self) -> None:
        """Clean up previous provider layout."""
        if not self.current_provider_layout:
            return

        parent = self.current_provider_layout.parent()
        if parent and hasattr(parent, "removeItem") and isinstance(parent, QLayout):
            parent.removeItem(self.current_provider_layout)

        self.current_provider_layout.setParent(None)
        ui_utils.clear_layout(self.current_provider_layout)
        self.current_provider_layout.deleteLater()

    def _add_provider_buttons(self, provider: "AIProvider") -> None:
        """Add provider action buttons."""
        if not provider.button_text and not (
            hasattr(provider, "additional_buttons") and provider.additional_buttons
        ):
            return

        button_container = QHBoxLayout()
        button_container.setSpacing(10)

        # Main button
        if provider.button_text:
            self.main_button = QPushButton(provider.button_text)
            self.main_button.setStyleSheet(self.app.styles["primary_button"])
            self.main_button.clicked.connect(provider.button_action)
            button_container.addWidget(self.main_button)

        # Additional buttons
        if hasattr(provider, "additional_buttons"):
            for button_config in provider.additional_buttons:
                additional_button = QPushButton(button_config["text"])

                if button_config.get("style") == "secondary":
                    additional_button.setStyleSheet(self.app.styles["secondary_button"])
                else:
                    additional_button.setStyleSheet(self.app.styles["primary_button"])

                additional_button.clicked.connect(button_config["action"])
                button_container.addWidget(additional_button)

        # Center button container
        button_widget = QWidget()
        button_widget.setLayout(button_container)
        if self.current_provider_layout is not None:
            self.current_provider_layout.addWidget(
                button_widget,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

    def _disable_dropdown_scroll(self, layout: QLayout) -> None:
        """Disable wheel events on dropdowns to prevent scroll interference."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QComboBox):
                item.widget().wheelEvent = lambda event: event.ignore()
            elif item.layout():
                self._disable_dropdown_scroll(item.layout())

    def _on_provider_changed(self) -> None:
        """Handle provider change."""
        if not self.provider_dropdown:
            return

        current_internal_name = self.provider_dropdown.currentData()
        if not current_internal_name:
            return

        # Ollama-specific handling
        if current_internal_name == "ollama":
            self._handle_ollama_selection()

        # Find new provider
        new_provider = self._find_provider_by_name(current_internal_name)
        if not new_provider:
            self._logger.warning(f"Provider {current_internal_name} not found")
            return

        # Cleanup old provider
        if self.app.ai_processor.current_provider and hasattr(self.app.ai_processor.current_provider, "before_load"):
            self.app.ai_processor.current_provider.before_load()
        self.app.settings_manager.provider = current_internal_name

        # Reload config
        provider_config = self.app.settings_manager.providers.get(current_internal_name, {})
        new_provider.load_config(provider_config)

        # Update AI processor with the same instance
        self.app.ai_processor.current_provider = new_provider

        # Rebuild UI
        if self.provider_container is not None:
            self.init_provider_ui(new_provider, self.provider_container)

        self._logger.debug(f"Switched to provider: {current_internal_name}")

    def _handle_ollama_selection(self) -> None:
        """Handle Ollama provider selection with status checks."""
        from ...aiprovider.ollama import OllamaStateManager

        state_manager = OllamaStateManager()
        ollama_installed = state_manager.is_ollama_installed()
        ollama_running = state_manager.is_ollama_running()

        if not ollama_installed:
            self.app.ui_manager.show_message_signal.emit(
                "Ollama Not Installed",
                "Ollama is not installed on your system.\n\n"
                "You can install it using the 'Install Ollama' button in the provider settings below.\n\n"
                "Once installed and running, Ollama will be ready to use.",
            )
        elif not ollama_running:
            self.app.ui_manager.show_message_signal.emit(
                "Ollama Not Running",
                "Ollama is installed but not currently running.\n\n"
                "Please start Ollama from the command line with: ollama serve\n\n"
                "Or use the provider interface to manage Ollama.",
            )

    def _find_provider_by_name(self, internal_name: str) -> "AIProvider | None":
        """Create provider instance by internal name."""
        provider_class = PROVIDER_CLASSES.get(internal_name)
        if provider_class:
            try:
                return provider_class(self.app)
            except Exception as e:
                self._logger.error(f"Failed to create provider {internal_name}: {e}")
                return None
        return None

    def save_current_provider_settings(self) -> None:
        """Save settings for current provider."""
        if not self.app.ai_processor.current_provider:
            return

        self.app.ai_processor.current_provider.save_config()

        provider_config = self.app.settings_manager.providers.get(
            self.app.ai_processor.current_provider.internal_name, {}
        )
        self.app.ai_processor.current_provider.load_config(provider_config)

        self._logger.debug(f"Saved settings: {self.app.ai_processor.current_provider.internal_name}")

    def update_provider_button_text(self) -> None:
        """Update main button text when provider state changes."""
        if hasattr(self, "main_button") and self.main_button and self.app.ai_processor.current_provider:
            self.main_button.setText(self.app.ai_processor.current_provider.button_text)

    def refresh_theme(self) -> None:
        """Refresh theme for all components."""
        if self.provider_label:
            self.provider_label.setStyleSheet(self.app.styles["label"])
        if self.provider_dropdown:
            self.provider_dropdown.setStyleSheet(self.app.styles["dropdown"])

        if self.provider_name_label:
            self.provider_name_label.setStyleSheet(
                f"{self.app.styles['label_title']}; font-size: 18px;"
            )

        if self.description_label:
            self.description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")

        if self.vision_comment:
            self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")

        if self.main_button:
            self.main_button.setStyleSheet(self.app.styles["primary_button"])

        # Update provider labels in layout
        if self.current_provider_layout:
            self._update_provider_labels()

        # Update buttons
        self._update_provider_buttons()

        # Refresh provider styles
        if self.app.ai_processor.current_provider:
            self.app.ai_processor.current_provider.refresh_styles()

    def _update_provider_labels(self) -> None:
        """Update labels in provider layout."""
        if self.current_provider_layout is None:
            return

        for i in range(self.current_provider_layout.count()):
            item = self.current_provider_layout.itemAt(i)
            if not item or not item.widget():
                continue

            widget = item.widget()
            if not isinstance(widget, QLabel):
                continue

            # Skip name and description
            if widget in [self.provider_name_label, self.description_label]:
                continue

            # Update field labels
            if widget.text() and len(widget.text()) <= 50:
                widget.setStyleSheet(self.app.styles["label"])

    def _update_provider_buttons(self) -> None:
        """Update button styles in provider layout."""
        if not self.current_provider_layout:
            return

        def update_buttons(layout):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QPushButton):
                    button = item.widget()
                    button_text = button.text().lower() if button.text() else ""

                    # Determine button type
                    secondary_keywords = ["cancel", "reset", "clear", "remove", "delete"]
                    if any(kw in button_text for kw in secondary_keywords):
                        button.setStyleSheet(self.app.styles["secondary_button"])
                    else:
                        button.setStyleSheet(self.app.styles["primary_button"])

                elif item.layout():
                    update_buttons(item.layout())

        update_buttons(self.current_provider_layout)

    def refresh_language(self) -> None:
        """Refresh language for all components."""
        if self.provider_dropdown:
            self.provider_dropdown.blockSignals(True)

        try:
            if self.provider_label:
                self.provider_label.setText(_("Choose AI Provider:"))

            if self.vision_comment:
                self.vision_comment.setText(_("* Models with vision support"))

            # Update main button
            if self.main_button and self.app.ai_processor.current_provider:
                if hasattr(self.app.ai_processor.current_provider, "button_text"):
                    self.main_button.setText(self.app.ai_processor.current_provider.button_text)

            # Update additional buttons
            if (
                self.app.ai_processor.current_provider
                and hasattr(self.app.ai_processor.current_provider, "additional_buttons")
                and self.app.ai_processor.current_provider.additional_buttons
            ):
                self._refresh_additional_buttons()

        finally:
            if self.provider_dropdown:
                self.provider_dropdown.blockSignals(False)

    def _refresh_additional_buttons(self) -> None:
        """Refresh text for additional buttons."""
        if not self.current_provider_layout:
            return

        button_index = 0
        for i in range(self.current_provider_layout.count()):
            item = self.current_provider_layout.itemAt(i)
            if not item or not item.widget():
                continue

            widget = item.widget()
            if not hasattr(widget, "layout") or not widget.layout():
                continue

            # Look for buttons in nested layouts
            for j in range(widget.layout().count()):
                sub_item = widget.layout().itemAt(j)
                if not sub_item or not sub_item.widget():
                    continue

                if isinstance(sub_item.widget(), QPushButton):
                    button = cast(QPushButton, sub_item.widget())
                    if (
                        self.app.ai_processor.current_provider is not None
                        and hasattr(self.app.ai_processor.current_provider, "additional_buttons")
                        and self.app.ai_processor.current_provider.additional_buttons
                        and button_index < len(self.app.ai_processor.current_provider.additional_buttons)
                    ):
                        config = self.app.ai_processor.current_provider.additional_buttons[button_index]
                        button.setText(config["text"])
                        button_index += 1
