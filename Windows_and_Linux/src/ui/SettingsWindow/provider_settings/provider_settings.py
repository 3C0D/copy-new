"""
provider_settings.py

AI Provider settings component with dynamic UI generation and improved memory management.
"""

import logging
import weakref
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
    from ....aiprovider.aiprovider import AIProvider
    from ....writing_tools_app import WritingToolsApp
    from ..settings_window import SettingsWindow

from ....aiprovider.provider_manager import ProviderManager
from ....aiprovider.settings import AIProviderSetting, DropdownSetting, TextSetting
from ....config.constants import PROVIDER_DISPLAY_NAMES
from ....config.data_operations import get_provider_display_name
from ....core.ai_processor import PROVIDER_CLASSES
from ...ui_utils import ui_utils
from .button_manager import ProviderButtonManager


def _(x):
    return x


class ProviderSettings(QWidget):
    """Widget for AI provider selection and configuration with improved memory management."""

    def __init__(self, app: "WritingToolsApp", parent: "SettingsWindow"):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent
        self._logger = logging.getLogger(__name__)
        self.button_manager = ProviderButtonManager(app)
        self.provider_manager = ProviderManager(app)

        self.current_provider_layout = None

        # Tracking signal/slot connections for proper cleanup
        self._signal_connections = []

        # Weakref to current provider to avoid cycles
        self._current_provider_ref = None

        # UI components
        self.provider_label = None
        self.provider_dropdown = None
        self.provider_container = None
        self.provider_name_label = None
        self.description_label = None
        self.vision_comment = None
        self.main_button = None

        # Add flag to prevent fetch loop
        self._is_fetching_models = False

        # Add flag to prevent automatic fetch during preset change
        self._changing_preset = False

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
        # Refresh provider configuration
        self._refresh_provider_config(provider)

        # Clean up old UI (with complete cleanup)
        self._cleanup_provider_layout()
        ui_utils.clear_layout(layout)

        # Store weakref to current provider
        self._current_provider_ref = weakref.ref(provider)

        self.current_provider_layout = QVBoxLayout()

        # UI Components
        self._add_provider_header(provider)
        self._add_provider_description(provider)

        # Buttons
        button_widget = self.button_manager.create_button_layout(provider)
        if button_widget and self.current_provider_layout is not None:
            self.current_provider_layout.addWidget(
                button_widget,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

        # Add settings FIRST
        self._add_provider_settings(provider)

        layout.addLayout(self.current_provider_layout)

        # Disable dropdown scroll interference
        self._disable_dropdown_scroll(self.current_provider_layout)

        # THEN auto-fetch models for openai-compatible if credentials exist
        # This ensures settings are rendered before we try to replace them
        if provider.internal_name == "openai-compatible" and not self._is_fetching_models:
            provider_config = self.app.settings_manager.providers.get(provider.internal_name, {})
            api_base = provider_config.get("api_base", "")
            api_key = provider_config.get("api_key", "")

            if api_base and api_key:
                self._logger.debug("Auto-fetching models on provider UI init")
                # Use QTimer to defer fetch until after UI is fully rendered
                QtCore.QTimer.singleShot(100, lambda: self._fetch_and_update_models_async(provider, provider_config))

        self._logger.debug(f"Provider UI initialized: {provider.internal_name}")

    def _add_provider_header(self, provider: "AIProvider") -> None:
        """Add provider header (logo + name)."""
        if self.current_provider_layout is None:
            return

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

    def _add_provider_description(self, provider: "AIProvider") -> None:
        """Add provider description."""
        if self.current_provider_layout is None:
            return

        if provider.description:
            self.description_label = QLabel(provider.description)
            self.description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")
            self.description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(self.description_label)

    def _add_provider_settings(self, provider: "AIProvider") -> None:
        """Add provider settings controls with weakref-based callback."""
        if self.current_provider_layout is None:
            return

        if not self.app.settings_manager.providers:
            self.app.settings_manager.providers = {}

        if provider.internal_name not in self.app.settings_manager.providers:
            self.app.settings_manager.providers[provider.internal_name] = {}

        provider_config = self.app.settings_manager.providers[provider.internal_name]

        # Add preset UI for openai-compatible
        if provider.internal_name == "openai-compatible":
            self._add_preset_ui(provider, provider_config)

        # Use weakref to avoid reference cycles
        provider_ref = weakref.ref(provider)
        provider_manager_ref = weakref.ref(self.provider_manager)

        for setting in provider.settings:
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)

            # Callback with weakref to avoid cycle - create separate function for each setting
            def create_auto_save_callback(p_ref, pm_ref):
                def auto_save_callback():
                    provider_obj = p_ref()
                    provider_manager_obj = pm_ref()
                    if provider_obj is not None and provider_manager_obj is not None:
                        # Only save the specific setting, don't overwrite the entire config
                        provider_obj.save_config()
                        # Reload config to preserve recorded data
                        updated_config = self.app.settings_manager.providers.get(provider_obj.internal_name, {})
                        provider_obj.load_config(updated_config)
                    else:
                        self._logger.debug("Provider or manager was garbage collected")

                return auto_save_callback

            setting.set_auto_save_callback(
                create_auto_save_callback(provider_ref, provider_manager_ref)
            )
            setting.render_to_layout(self.current_provider_layout)

            # Connect api_base AND api_key changes to fetch models
            # BUT skip if we're changing presets
            if provider.internal_name == "openai-compatible" and setting.name in ["api_base", "api_key"]:
                def create_fetch_callback(p_ref, s_name):
                    def on_credential_changed():
                        # Skip auto-fetch if we're changing presets
                        if self._changing_preset:
                            return

                        provider_obj = p_ref()
                        if provider_obj is not None:
                            # Save first
                            if s_name == "api_base":
                                if hasattr(setting, 'auto_save_callback') and setting.auto_save_callback:
                                    setting.auto_save_callback()

                            # Then fetch
                            config = self.app.settings_manager.providers.get(provider_obj.internal_name, {})
                            self._fetch_and_update_models_async(provider_obj, config)
                    return on_credential_changed

                # Connect to editingFinished for TextSetting
                if hasattr(setting, 'input'):
                    getattr(setting, 'input').editingFinished.connect(
                        create_fetch_callback(provider_ref, setting.name)
                    )

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
        if parent and hasattr(parent, "removeItem") and isinstance(parent, QLayout):
            parent.removeItem(self.current_provider_layout)

        self.current_provider_layout.setParent(None)
        ui_utils.clear_layout(self.current_provider_layout)
        self.current_provider_layout.deleteLater()

        # Clear weakref
        self._current_provider_ref = None

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
        if (
            hasattr(self, "main_button")
            and self.main_button
            and self.app.ai_processor.current_provider
        ):
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

    def _extract_provider_key(self, api_base: str) -> str:
        """Extract domain from API base URL as unique key (e.g., 'api.groq.com')"""
        from urllib.parse import urlparse

        parsed = urlparse(api_base)
        return parsed.netloc or "unknown"

    def _on_save_preset(self) -> None:
        """Save current config to recorded presets"""
        provider = self.app.ai_processor.current_provider
        if not provider or provider.internal_name != "openai-compatible":
            return

        config = self.app.settings_manager.providers.get("openai-compatible", {})
        api_base = config.get("api_base", "")

        if not api_base:
            return

        key = self._extract_provider_key(api_base)

        # Initialize recorded as dict if needed
        if "recorded" not in config:
            config["recorded"] = {}

        # Save current config under this key
        config["recorded"][key] = {
            "api_key": config.get("api_key", ""),
            "api_base": api_base,
            "api_model": config.get("api_model", ""),
            "api_organisation": config.get("api_organisation", ""),
            "api_project": config.get("api_project", ""),
            "has_vision": config.get("has_vision", False),
        }

        self.app.settings_manager.save()
        self._refresh_preset_dropdown()

    def _on_delete_preset(self) -> None:
        """Delete current preset from recorded"""
        provider = self.app.ai_processor.current_provider
        if not provider or provider.internal_name != "openai-compatible":
            return

        config = self.app.settings_manager.providers.get("openai-compatible", {})
        api_base = config.get("api_base", "")

        if not api_base or "recorded" not in config:
            return

        key = self._extract_provider_key(api_base)

        # Remove this key from recorded dict
        if key in config["recorded"]:
            del config["recorded"][key]

        self.app.settings_manager.save()
        self._refresh_preset_dropdown()

    def _add_preset_ui(self, provider, provider_config):
        """Add preset dropdown and save/delete buttons"""
        if self.current_provider_layout is None:
            return

        recorded = provider_config.get("recorded", {})

        # Handle backward compatibility: if recorded is a list, convert to dict
        if isinstance(recorded, list):
            new_recorded = {}
            for preset in recorded:
                key = preset.get("key", "")
                if key:
                    # Remove the key from preset data since it's now the dict key
                    preset_copy = preset.copy()
                    preset_copy.pop("key", None)
                    new_recorded[key] = preset_copy
            recorded = new_recorded
            provider_config["recorded"] = recorded

        # Show dropdown only if there are saved presets
        if len(recorded) > 0:
            # Dropdown
            preset_dropdown = QComboBox()
            preset_dropdown.setStyleSheet(self.app.styles["dropdown"])
            preset_dropdown.wheelEvent = lambda e: e.ignore()

            current_base = provider_config.get("api_base", "")
            current_key = self._extract_provider_key(current_base) if current_base else ""

            # Add all saved presets (keys from dict)
            for key, _ in recorded.items():
                preset_dropdown.addItem(key, recorded[key])

            # Set current selection
            current_index = -1
            for i in range(preset_dropdown.count()):
                if preset_dropdown.itemText(i) == current_key:
                    current_index = i
                    break

            if current_index != -1:
                preset_dropdown.setCurrentIndex(current_index)

            preset_dropdown.currentIndexChanged.connect(
                lambda: self._on_preset_selected(preset_dropdown)
            )
            self.current_provider_layout.addWidget(preset_dropdown)

        # Buttons row (always visible for openai-compatible)
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self.app.styles["primary_button"])
        save_btn.clicked.connect(self._on_save_preset)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self.app.styles["secondary_button"])
        delete_btn.clicked.connect(self._on_delete_preset)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(delete_btn)
        self.current_provider_layout.addLayout(buttons_layout)

    def _on_preset_selected(self, dropdown: QComboBox) -> None:
        """Load selected preset into current config"""
        preset_data = dropdown.currentData()
        if not preset_data:
            return

        provider = self.app.ai_processor.current_provider
        if not provider or provider.internal_name != "openai-compatible":
            return

        # Set flag to prevent automatic fetch during preset change
        self._changing_preset = True

        try:
            # Update config with preset data
            config = self.app.settings_manager.providers["openai-compatible"]
            config.update(preset_data)

            # Reload provider with new config (updates self.api_base, self.api_key, etc.)
            provider.load_config(config)

            # Rebuild UI to show new values
            if self.provider_container is not None:
                self.init_provider_ui(provider, self.provider_container)

            # Now manually trigger fetch with the NEW api_base/api_key
            new_api_base = preset_data.get("api_base", "")
            new_api_key = preset_data.get("api_key", "")

            if new_api_base and new_api_key:
                self._logger.debug(f"Fetching models for preset with api_base: {new_api_base}")
                # Fetch using updated config
                updated_config = self.app.settings_manager.providers.get("openai-compatible", {})
                self._fetch_and_update_models_async(provider, updated_config)

        finally:
            # Reset flag
            self._changing_preset = False

    def _refresh_preset_dropdown(self) -> None:
        """Rebuild UI to show updated presets"""
        provider = self.app.ai_processor.current_provider
        if (
            provider
            and provider.internal_name == "openai-compatible"
            and self.provider_container is not None
        ):
            self.init_provider_ui(provider, self.provider_container)

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
                        and button_index
                        < len(self.app.ai_processor.current_provider.additional_buttons)
                    ):
                        config = self.app.ai_processor.current_provider.additional_buttons[
                            button_index
                        ]
                        button.setText(config["text"])
                        button_index += 1

    def _remove_setting_widget(self, setting: AIProviderSetting) -> None:
        """Remove a setting's widget from the current layout - DEPRECATED, see _replace_model_setting_with_dropdown"""
        # This method is no longer used but kept for compatibility
        pass

    def _render_setting_at_position(self, setting: AIProviderSetting, position: int) -> None:
        """Render a setting at a specific position in the layout - DEPRECATED"""
        # This method is no longer used but kept for compatibility
        pass

    def _fetch_and_update_models_async(self, provider: "AIProvider", provider_config) -> None:
        """
        Fetch models asynchronously and update UI when complete.
        """
        from ....aiprovider.openAI_compatible import OpenAICompatibleProvider

        if not isinstance(provider, OpenAICompatibleProvider):
            return

        # Prevent multiple simultaneous fetches
        if self._is_fetching_models:
            self._logger.debug("Already fetching models, skipping")
            return

        # Get current api_base and api_key from provider config
        api_base = provider_config.get("api_base", "")
        api_key = provider_config.get("api_key", "")

        if not api_base or not api_key:
            self._logger.debug("Missing api_base or api_key, skipping fetch")
            return

        self._is_fetching_models = True

        # Log to verify we're using the correct api_base
        self._logger.debug(f"Fetching models with api_base: {api_base}")

        def on_success(models):
            """Callback when models are successfully fetched"""
            self._is_fetching_models = False

            if not models:
                self._logger.debug("No models returned from fetch")
                return

            self._replace_model_setting_with_dropdown(provider, provider_config, models)

        def on_failure(error_msg):
            """Callback when fetch fails"""
            self._is_fetching_models = False
            self._logger.warning(f"Failed to fetch models: {error_msg}")
            # Keep TextSetting on failure

        # Pass api_base and api_key explicitly to avoid using stale values
        provider.fetch_models_async(on_success, on_failure, api_base=api_base, api_key=api_key)

    def _replace_model_setting_with_dropdown(
        self, provider: "AIProvider", provider_config: dict, models: list[str]
    ) -> None:
        """
        Replace the api_model TextSetting with a DropdownSetting.
        Updates the setting in-place and re-renders only that setting.
        """
        # Find model setting
        model_setting_index = None
        old_setting = None
        for i, setting in enumerate(provider.settings):
            if setting.name == "api_model":
                model_setting_index = i
                old_setting = setting
                break

        if model_setting_index is None or old_setting is None:
            self._logger.warning("Could not find api_model setting")
            return

        # Check if already a dropdown to avoid redundant replacement
        if isinstance(old_setting, DropdownSetting):
            self._logger.debug("api_model is already a DropdownSetting, updating options")
            old_setting.refresh_options([(m, m) for m in models])
            return

        self._logger.debug(f"Replacing TextSetting with DropdownSetting for {len(models)} models")

        # Get current model value
        current_model = provider_config.get("api_model", "")

        # If no model is selected or current model not in list, select the first one
        if (not current_model or current_model not in models) and models:
            current_model = models[0]
            provider_config["api_model"] = current_model
            provider.save_config()

        # Create DropdownSetting
        options = [(model, model) for model in models]

        dropdown_setting = DropdownSetting(
            self.app,
            name="api_model",
            display_name="API Model",
            default_value=current_model,
            description="Select a model",
            options=options,
        )

        # Set up auto-save callback
        provider_ref = weakref.ref(provider)
        provider_manager_ref = weakref.ref(self.provider_manager)

        def create_auto_save_callback(p_ref, pm_ref):
            def auto_save_callback():
                provider_obj = p_ref()
                provider_manager_obj = pm_ref()
                if provider_obj is not None and provider_manager_obj is not None:
                    provider_obj.save_config()
                    updated_config = self.app.settings_manager.providers.get(provider_obj.internal_name, {})
                    provider_obj.load_config(updated_config)
                else:
                    self._logger.debug("Provider or manager was garbage collected")
            return auto_save_callback

        dropdown_setting.set_auto_save_callback(
            create_auto_save_callback(provider_ref, provider_manager_ref)
        )

        # Replace the setting in the list
        provider.settings[model_setting_index] = dropdown_setting

        # Find and remove the old widget's layout item
        old_layout_item = None
        old_layout_item_index = -1

        if self.current_provider_layout and isinstance(old_setting, TextSetting) and hasattr(old_setting, 'input'):
            for i in range(self.current_provider_layout.count()):
                item = self.current_provider_layout.itemAt(i)
                if item and item.layout():
                    # Check if this layout contains the old setting's input widget
                    sub_layout = item.layout()
                    for j in range(sub_layout.count()):
                        widget_item = sub_layout.itemAt(j)
                        if widget_item and widget_item.widget() == old_setting.input:
                            old_layout_item = item
                            old_layout_item_index = i
                            self._logger.debug(f"Found old setting at layout index {i}")
                            break
                    if old_layout_item:
                        break

        if old_layout_item and old_layout_item_index >= 0 and self.current_provider_layout:
            # Remove the old layout item
            self.current_provider_layout.removeItem(old_layout_item)

            # Clean up the old layout
            old_layout = old_layout_item.layout()
            if old_layout:
                ui_utils.clear_layout(old_layout)
                old_layout.deleteLater()

            self._logger.debug(f"Removed old setting layout at index {old_layout_item_index}")

            # Create a temporary parent for the new widget
            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            temp_layout.setContentsMargins(0, 0, 0, 0)

            # Render the new dropdown setting
            dropdown_setting.render_to_layout(temp_layout)

            # Insert the new layout at the same position
            self.current_provider_layout.insertWidget(old_layout_item_index, temp_widget)

            self._logger.debug(f"Inserted new dropdown at index {old_layout_item_index}")
        else:
            self._logger.warning(f"Could not find old setting widget in layout (is TextSetting: {isinstance(old_setting, TextSetting)}, has input: {hasattr(old_setting, 'input')})")
            # Fallback: just append at the end
            if self.current_provider_layout:
                temp_widget = QWidget()
                temp_layout = QVBoxLayout(temp_widget)
                temp_layout.setContentsMargins(0, 0, 0, 0)
                dropdown_setting.render_to_layout(temp_layout)
                self.current_provider_layout.addWidget(temp_widget)

        self._logger.debug(f"Successfully replaced api_model with dropdown")
