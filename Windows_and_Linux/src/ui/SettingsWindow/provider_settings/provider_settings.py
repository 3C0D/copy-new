"""
Main provider settings widget (orchestration only).
Delegates to specialized components.
"""

import logging
import weakref
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6.QtWidgets import (
    QComboBox,
    QLabel,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from ....aiprovider.aiprovider import AIProvider
    from ....writing_tools_app import WritingToolsApp
    from ..settings_window import SettingsWindow

from ....aiprovider.provider_manager import ProviderManager
from ....config.constants import PROVIDER_DISPLAY_NAMES
from ....config.data_operations import get_provider_display_name
from ....core.ai_processor import PROVIDER_CLASSES
from .button_manager import ProviderButtonManager
from .components.provider_model_fetcher import ProviderModelFetcher
from .components.provider_preset_manager import ProviderPresetManager
from .components.provider_ui_builder import ProviderUIBuilder


def _(x):
    return x


class ProviderSettings(QWidget):
    """Main widget for AI provider selection and configuration."""

    def __init__(self, app: "WritingToolsApp", parent: "SettingsWindow"):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent
        self._logger = logging.getLogger(__name__)

        # Managers
        self.button_manager = ProviderButtonManager(app)
        self.provider_manager = ProviderManager(app)
        self.ui_builder = ProviderUIBuilder(app)
        self.preset_manager = ProviderPresetManager(app)
        self.model_fetcher = ProviderModelFetcher()

        # State
        self.current_provider_layout = None
        self._current_provider_ref = None
        self._signal_connections = []
        self._changing_preset = False

        # UI components
        self.provider_label = None
        self.provider_dropdown = None
        self.provider_container = None
        self.provider_name_label = None
        self.description_label = None
        self.vision_comment = None

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
            provider_instance = self.provider_manager.find_provider_by_name(current_internal_name)

            if not provider_instance:
                # Fallback to first available provider
                default_provider_name = list(PROVIDER_CLASSES.keys())[0]
                provider_class = PROVIDER_CLASSES.get(default_provider_name)
                if provider_class:
                    try:
                        provider_instance = provider_class(self.app)
                    except Exception as e:
                        self._logger.error(
                            f"Failed to create default provider {default_provider_name}: {e}"
                        )
                        provider_instance = None

            if provider_instance:
                self.app.ai_processor.current_provider = provider_instance
                self.init_provider_ui(provider_instance, self.provider_container)

        # Connect provider change - TRACK CONNECTION
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)
        self._signal_connections.append(
            (self.provider_dropdown, "currentIndexChanged", self._on_provider_changed)
        )

        # Vision comment - only show for providers that use dropdown models
        current_provider = self.app.ai_processor.current_provider
        if current_provider and current_provider.internal_name != "openai-compatible":
            self.vision_comment = QLabel(_("* Models with vision support"))
            self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")
            layout.addWidget(self.vision_comment)
        else:
            self.vision_comment = None

    def init_provider_ui(self, provider: "AIProvider", layout: QVBoxLayout) -> None:
        """Initialize UI for a specific provider."""
        # Refresh config
        self._refresh_provider_config(provider)

        # Clean up old UI
        self._cleanup_provider_layout()
        from ...ui_utils import ui_utils

        ui_utils.clear_layout(layout)

        # Store weakref
        self._current_provider_ref = weakref.ref(provider)
        self.current_provider_layout = QVBoxLayout()

        # Build UI components
        self.provider_name_label, self.description_label = self.ui_builder.build_provider_header(
            provider, self.current_provider_layout
        )

        # Buttons
        button_widget = self.button_manager.create_button_layout(provider)
        if button_widget:
            self.current_provider_layout.addWidget(
                button_widget,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

        # Preset UI (OpenAI-compatible)
        if provider.internal_name == "openai-compatible":
            self.preset_manager.build_preset_ui(
                provider,
                self.current_provider_layout,
                self._on_preset_selected,
                self._on_save_preset,
                self._on_delete_preset,
            )

        # Settings
        self.ui_builder.build_settings_ui(
            provider,
            self.current_provider_layout,
            self._on_credential_changed,
        )

        layout.addLayout(self.current_provider_layout)

        # Disable dropdown scroll
        self.ui_builder.disable_dropdown_scroll(self.current_provider_layout)

        # Auto-fetch models for OpenAI-compatible
        self._auto_fetch_models_if_needed(provider)

        self._logger.debug(f"Provider UI initialized: {provider.internal_name}")

    # Header and description methods moved to ProviderUIBuilder

    # Settings method moved to ProviderUIBuilder

    def _refresh_provider_config(self, provider: "AIProvider") -> None:
        """Refresh provider configuration if supported."""
        self.provider_manager.refresh_provider_config(provider)

    def _cleanup_provider_layout(self) -> None:
        """Clean up previous provider layout with complete cleanup."""
        if not self.current_provider_layout:
            return

        # Clean all callbacks from previous provider settings
        if self._current_provider_ref:
            old_provider = self._current_provider_ref()
            if old_provider:
                for setting in old_provider.settings:
                    # Reset callback to release references
                    setting.set_auto_save_callback(lambda: None)

        parent = self.current_provider_layout.parent()
        if parent and hasattr(parent, "removeItem"):
            # Cast to QLayout to access removeItem method
            from PySide6.QtWidgets import QLayout

            if isinstance(parent, QLayout):
                parent.removeItem(self.current_provider_layout)

        self.current_provider_layout.setParent(None)
        from ...ui_utils import ui_utils

        ui_utils.clear_layout(self.current_provider_layout)
        self.current_provider_layout.deleteLater()

        # Clear weakref
        self._current_provider_ref = None

    # Moved to ProviderUIBuilder

    def _on_provider_changed(self) -> None:
        """Handle provider change."""
        if not self.provider_dropdown:
            return

        current_internal_name = self.provider_dropdown.currentData()
        if not current_internal_name:
            return

        self._logger.debug(f"Provider changed to: {current_internal_name}")

        # Use ProviderManager to switch provider
        new_provider = self.provider_manager.switch_provider(current_internal_name)
        if not new_provider:
            self._logger.warning(f"Provider {current_internal_name} not found")
            return

        # Rebuild UI
        if self.provider_container is not None:
            self.init_provider_ui(new_provider, self.provider_container)

        # Update vision comment visibility
        self._update_vision_comment_visibility(new_provider)

    def _update_vision_comment_visibility(self, provider: "AIProvider") -> None:
        """Update the visibility of the vision comment based on provider type."""
        # Remove existing vision comment if it exists
        if self.vision_comment:
            self.vision_comment.hide()
            self.vision_comment.setParent(None)
            self.vision_comment = None

        # Add vision comment only for providers that use dropdown models (not openai-compatible)
        if provider.internal_name != "openai-compatible":
            self.vision_comment = QLabel(_("* Models with vision support"))
            self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")
            # Insert before the stretch at the end of the layout
            parent_layout = self.layout()
            if parent_layout:
                parent_layout.addWidget(self.vision_comment)

    def update_provider_button_text(self) -> None:
        """Update main button text when provider state changes."""
        # This method can be called from outside to update button text
        pass

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

        # Main button styling moved to button manager

        # Update provider labels in layout
        if self.current_provider_layout:
            self._update_provider_labels()

        # Update buttons
        if self.current_provider_layout:
            self.button_manager.update_button_styles(self.current_provider_layout)

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

    def refresh_language(self) -> None:
        """Refresh language for all components."""
        if self.provider_dropdown:
            self.provider_dropdown.blockSignals(True)

        try:
            if self.provider_label:
                self.provider_label.setText(_("Choose AI Provider:"))

            if self.vision_comment:
                self.vision_comment.setText(_("* Models with vision support"))

            # Update main button (moved to button manager)

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

    def _disconnect_all_signals(self) -> None:
        """Explicitly disconnect all tracked signals."""
        for widget, signal_name, slot in self._signal_connections:
            try:
                # Get signal by name
                signal = getattr(widget, signal_name, None)
                if signal:
                    signal.disconnect(slot)
                    self._logger.debug(f"Disconnected signal: {signal_name}")
            except Exception as e:
                self._logger.debug(f"Error disconnecting signal {signal_name}: {e}")

        self._signal_connections.clear()

    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        self._logger.debug("ProviderSettings closing, cleaning up...")

        # Disconnect all signals
        self._disconnect_all_signals()

        # Clean provider layout
        self._cleanup_provider_layout()

        # Call parent closeEvent
        super().closeEvent(event)

    # Preset methods moved to ProviderPresetManager

    # Preset UI moved to ProviderPresetManager

    def _on_preset_selected(self, dropdown: QComboBox) -> None:
        """Load selected preset."""
        preset_data = dropdown.currentData()
        if not preset_data:
            return

        provider = self.app.ai_processor.current_provider
        if not provider or provider.internal_name != "openai-compatible":
            return

        self._changing_preset = True

        try:
            # Load preset
            self.preset_manager.load_preset(provider, preset_data)

            # Auto-update has_vision based on preset model
            preset_model = preset_data.get("api_model", "")
            vision_info = {"has_vision": False, "auto_detected": False}

            if preset_model and hasattr(provider, "get_model_metadata"):
                try:
                    vision_info = getattr(provider, "get_model_metadata")(preset_model)
                except AttributeError:
                    pass

            # Update has_vision setting
            for setting in provider.settings:
                if setting.name == "has_vision":
                    setting.set_value(vision_info.get("has_vision", False))

                    # Update read_only based on auto_detection
                    if hasattr(setting, 'set_read_only'):
                        getattr(setting, 'set_read_only')(vision_info.get("auto_detected", False))

                    break

            # Update main api_model to match preset
            config = self.app.settings_manager.providers["openai-compatible"]
            if preset_model:
                config["api_model"] = preset_model
                config["has_vision"] = vision_info.get("has_vision", False)
                self.app.settings_manager.save()

            # Rebuild UI
            if self.provider_container:
                self.init_provider_ui(provider, self.provider_container)

            # Fetch models with new credentials
            api_base = preset_data.get("api_base", "")
            api_key = preset_data.get("api_key", "")

            if api_base and api_key:
                self._fetch_models(provider, api_base, api_key)

        finally:
            self._changing_preset = False

    def _on_save_preset(self) -> None:
        """Save current config as preset."""
        provider = self.app.ai_processor.current_provider
        if provider and self.preset_manager.save_preset(provider):
            self._refresh_preset_ui()

    def _on_delete_preset(self) -> None:
        """Delete current preset."""
        provider = self.app.ai_processor.current_provider
        if provider and self.preset_manager.delete_preset(provider):
            self._refresh_preset_ui()

    def _refresh_preset_ui(self) -> None:
        """Refresh preset UI after save/delete."""
        provider = self.app.ai_processor.current_provider
        if provider and provider.internal_name == "openai-compatible":
            if self.provider_container:
                self.init_provider_ui(provider, self.provider_container)

    def _refresh_additional_buttons(self) -> None:
        """Refresh text for additional buttons."""
        if not self.current_provider_layout:
            return

        from typing import cast

        from PySide6.QtWidgets import QPushButton

        button_index = 0
        for i in range(self.current_provider_layout.count()):
            item = self.current_provider_layout.itemAt(i)
            if not item or not item.widget():
                continue

            widget = item.widget()
            if not hasattr(widget, "layout") or not widget.layout():
                continue

            for j in range(widget.layout().count()):
                sub_item = widget.layout().itemAt(j)
                if not sub_item or not sub_item.widget():
                    continue

                if isinstance(sub_item.widget(), QPushButton):
                    button = cast(QPushButton, sub_item.widget())
                    provider = self.app.ai_processor.current_provider
                    if (
                        provider
                        and hasattr(provider, "additional_buttons")
                        and provider.additional_buttons
                        and button_index < len(provider.additional_buttons)
                    ):
                        config = provider.additional_buttons[button_index]
                        button.setText(config["text"])
                        button_index += 1

    # Deprecated methods removed - functionality moved to ProviderUIBuilder

    def _auto_fetch_models_if_needed(self, provider: "AIProvider") -> None:
        """Auto-fetch models for OpenAI-compatible if credentials exist."""
        if provider.internal_name != "openai-compatible":
            return

        provider_config = self.app.settings_manager.providers.get(provider.internal_name, {})
        api_base = provider_config.get("api_base", "")
        api_key = provider_config.get("api_key", "")

        if api_base and api_key:
            self._logger.debug("Auto-fetching models on provider UI init")
            QtCore.QTimer.singleShot(
                100,
                lambda: self._fetch_models(provider, api_base, api_key),
            )

    def _on_credential_changed(self, setting, provider_ref) -> None:
        """Handle credential change (api_base or api_key)."""
        if self._changing_preset:
            return

        provider = provider_ref()
        if not provider:
            return

        # Save first
        if hasattr(setting, "auto_save_callback") and setting.auto_save_callback:
            setting.auto_save_callback()

        # Fetch models
        config = self.app.settings_manager.providers.get(provider.internal_name, {})
        api_base = config.get("api_base", "")
        api_key = config.get("api_key", "")

        if api_base and api_key:
            self._fetch_models(provider, api_base, api_key)

    def _fetch_models(self, provider: "AIProvider", api_base: str, api_key: str) -> None:
        """Fetch models and update UI."""
        from ....aiprovider.openAI_compatible import OpenAICompatibleProvider

        if not isinstance(provider, OpenAICompatibleProvider):
            return

        def on_success(models):
            if self.current_provider_layout:
                self.ui_builder.replace_model_setting_with_dropdown(
                    provider,
                    self.current_provider_layout,
                    models,  # Pass full model dicts, not just IDs
                    self._on_model_changed,
                )

        def on_failure(error_msg):
            pass  # Keep TextSetting on failure

        self.model_fetcher.fetch_models(
            provider,
            api_base,
            api_key,
            on_success,
            on_failure,
        )

    def _on_model_changed(self) -> None:
        """Handle model selection change."""
        # Could add logic here if needed
        pass

    # Model replacement moved to ProviderUIBuilder
