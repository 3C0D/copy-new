"""
UI construction logic for provider settings.
"""

import logging
import weakref
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from .....aiprovider.aiprovider import AIProvider
    from .....writing_tools_app import WritingToolsApp

from .....aiprovider.settings import DropdownSetting, TextSetting
from ....ui_utils import ui_utils


def _(x):
    return x


class ProviderUIBuilder:
    """Handles UI construction for provider settings."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)

    def build_provider_header(
        self, provider: "AIProvider", layout: QVBoxLayout
    ) -> tuple[QLabel, QLabel | None]:
        """Build provider header (logo + name).

        Returns:
            Tuple of (name_label, description_label)
        """
        header_layout = QHBoxLayout()
        header_layout.setSpacing(10)
        header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

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
                header_layout.addWidget(logo_label)

        # Name
        name_label = QLabel(provider.provider_name)
        name_label.setStyleSheet(f"{self.app.styles['label_title']}; font-size: 18px;")
        name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        header_layout.addWidget(name_label)

        layout.addLayout(header_layout)

        # Description
        description_label = None
        if provider.description:
            description_label = QLabel(provider.description)
            description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")
            description_label.setWordWrap(True)
            layout.addWidget(description_label)

        return name_label, description_label

    def build_settings_ui(
        self,
        provider: "AIProvider",
        layout: QVBoxLayout,
        on_setting_changed_callback,
    ) -> None:
        """Build settings controls for a provider.

        Args:
            provider: The AI provider instance
            layout: Layout to add settings to
            on_setting_changed_callback: Callback for when settings change
        """
        if provider.internal_name not in self.app.settings_manager.providers:
            self.app.settings_manager.providers[provider.internal_name] = {}

        provider_config = self.app.settings_manager.providers[provider.internal_name]
        provider_ref = weakref.ref(provider)

        for setting in provider.settings:
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)

            # Auto-save callback with preset sync for OpenAI-compatible
            def create_auto_save_callback(p_ref, setting_name):
                def auto_save():
                    provider_obj = p_ref()
                    if not provider_obj:
                        return

                    # Save config
                    provider_obj.save_config()
                    updated_config = self.app.settings_manager.providers.get(
                        provider_obj.internal_name, {}
                    )
                    provider_obj.load_config(updated_config)

                    # Sync with recorded preset if OpenAI-compatible and model changed
                    if (
                        provider_obj.internal_name == "openai-compatible"
                        and setting_name == "api_model"
                    ):
                        self._sync_model_to_preset(provider_obj, updated_config)

                return auto_save

            setting.set_auto_save_callback(create_auto_save_callback(provider_ref, setting.name))
            setting.render_to_layout(layout)

            # Connect credential changes for OpenAI-compatible
            if provider.internal_name == "openai-compatible" and setting.name in [
                "api_base",
                "api_key",
            ]:
                if hasattr(setting, "input"):
                    getattr(setting, "input").editingFinished.connect(
                        lambda s=setting, p_ref=provider_ref: on_setting_changed_callback(s, p_ref)
                    )

    def _sync_model_to_preset(self, provider: "AIProvider", config) -> None:
        """Sync api_model value to the current preset in recorded."""
        api_base = config.get("api_base", "")
        if not api_base:
            return

        # Extract preset key
        from urllib.parse import urlparse

        parsed = urlparse(api_base)
        preset_key = parsed.netloc or "unknown"

        # Update recorded preset if exists
        if "recorded" in config and preset_key in config["recorded"]:
            new_model = config.get("api_model", "")
            config["recorded"][preset_key]["api_model"] = new_model
            self.app.settings_manager.save()
            self._logger.debug(f"Synced api_model '{new_model}' to preset '{preset_key}'")

    def replace_model_setting_with_dropdown(
        self,
        provider: "AIProvider",
        layout: QVBoxLayout,
        models: list[str],
        on_model_changed_callback,
        searchable: bool = True,
        search_placeholder: str = "Search models...",
    ) -> bool:
        """Replace api_model TextSetting with DropdownSetting.

        Returns:
            True if replacement was successful
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
            return False

        # Already a dropdown? Just update options and selection
        if isinstance(old_setting, DropdownSetting):
            self._logger.debug("api_model is already a DropdownSetting, updating options")

            # Update searchable status if needed
            if searchable and not old_setting.searchable:
                # Need to recreate dropdown as searchable
                old_setting.searchable = True
                old_setting.search_placeholder = search_placeholder
                # Force re-render by temporarily removing and re-adding
                if old_setting.dropdown:
                    old_setting.dropdown.deleteLater()
                    old_setting.dropdown = None

            old_setting.refresh_options([(m, m) for m in models])

            # Update selection to match current api_model
            provider_config = self.app.settings_manager.providers.get(provider.internal_name, {})
            current_model = self._get_preset_model_or_default(provider_config, models)
            if current_model:
                old_setting.set_value(current_model)

            # Ensure scroll is disabled
            if old_setting.dropdown:
                old_setting.dropdown.wheelEvent = lambda e: e.ignore()

            return True

        provider_config = self.app.settings_manager.providers.get(provider.internal_name, {})
        current_model = self._get_preset_model_or_default(provider_config, models)

        # Sync main config with preset model if different
        if current_model and current_model != provider_config.get("api_model", ""):
            provider_config["api_model"] = current_model
            self._update_preset_model(provider_config, current_model)
            provider.save_config()
        elif not current_model and models:
            # Auto-select first model if no valid model found
            current_model = models[0]
            provider_config["api_model"] = current_model
            self._update_preset_model(provider_config, current_model)
            provider.save_config()

        # Create dropdown with search capability
        options = [(model, model) for model in models]
        dropdown_setting = DropdownSetting(
            self.app,
            name="api_model",
            display_name="API Model",
            default_value=current_model,
            description="Select a model",
            options=options,
            searchable=searchable,  # Enable search
            search_placeholder=_(
                "Enter search terms to narrow down options (e.g. 'gemini free' or ':free')..."
            ),  # Better placeholder
        )

        # Set callback with preset sync
        provider_ref = weakref.ref(provider)

        def auto_save():
            provider_obj = provider_ref()
            if provider_obj:
                provider_obj.save_config()
                updated_config = self.app.settings_manager.providers.get(
                    provider_obj.internal_name, {}
                )
                provider_obj.load_config(updated_config)
                # Sync to preset
                self._sync_model_to_preset(provider_obj, updated_config)

        dropdown_setting.set_auto_save_callback(auto_save)

        # Replace in list
        provider.settings[model_setting_index] = dropdown_setting

        # Find and replace in layout
        result = self._replace_setting_in_layout(
            layout, old_setting, dropdown_setting, model_setting_index
        )

        # Disable scroll on the new dropdown
        self.disable_dropdown_scroll(layout)

        return result

    def _get_preset_model_or_default(self, config, available_models: list[str]) -> str:
        """Get model from current preset if available, fallback to main config."""
        api_base = config.get("api_base", "")
        if not api_base:
            return config.get("api_model", "")

        # Extract preset key
        from urllib.parse import urlparse

        parsed = urlparse(api_base)
        preset_key = parsed.netloc or "unknown"

        # Check if preset exists and has a valid model
        if "recorded" in config and preset_key in config["recorded"]:
            preset_model = config["recorded"][preset_key].get("api_model", "")
            if preset_model and preset_model in available_models:
                self._logger.debug(f"Using preset model: {preset_model}")
                return preset_model

        # Fallback to main config
        return config.get("api_model", "")

    def _update_preset_model(self, config, new_model: str) -> None:
        """Update model in current preset."""
        api_base = config.get("api_base", "")
        if not api_base:
            return

        from urllib.parse import urlparse

        parsed = urlparse(api_base)
        preset_key = parsed.netloc or "unknown"

        if "recorded" in config and preset_key in config["recorded"]:
            config["recorded"][preset_key]["api_model"] = new_model
            self._logger.debug(f"Updated preset '{preset_key}' model to: {new_model}")

    def _replace_setting_in_layout(
        self,
        layout: QVBoxLayout,
        old_setting,
        new_setting,
        setting_index: int,
    ) -> bool:
        """Replace old setting widget with new one in layout."""
        old_layout_item = None
        old_layout_item_index = -1

        # Find old setting in layout
        if isinstance(old_setting, TextSetting) and hasattr(old_setting, "input"):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item and item.layout():
                    sub_layout = item.layout()
                    for j in range(sub_layout.count()):
                        widget_item = sub_layout.itemAt(j)
                        if widget_item and widget_item.widget() == old_setting.input:
                            old_layout_item = item
                            old_layout_item_index = i
                            break
                    if old_layout_item:
                        break

        # Replace or append
        if old_layout_item and old_layout_item_index >= 0:
            layout.removeItem(old_layout_item)
            old_layout = old_layout_item.layout()
            if old_layout:
                ui_utils.clear_layout(old_layout)
                old_layout.deleteLater()

            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            temp_layout.setContentsMargins(0, 0, 0, 0)
            new_setting.render_to_layout(temp_layout)
            layout.insertWidget(old_layout_item_index, temp_widget)
            return True
        else:
            # Fallback: append at end
            self._logger.warning("Could not find old setting widget, appending at end")
            temp_widget = QWidget()
            temp_layout = QVBoxLayout(temp_widget)
            temp_layout.setContentsMargins(0, 0, 0, 0)
            new_setting.render_to_layout(temp_layout)
            layout.addWidget(temp_widget)
            return False

    def disable_dropdown_scroll(self, layout: QLayout) -> None:
        """Disable wheel events on dropdowns to prevent scroll interference."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QComboBox):
                item.widget().wheelEvent = lambda event: event.ignore()
            elif item.layout():
                self.disable_dropdown_scroll(item.layout())
