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

            # Auto-save callback
            def create_auto_save_callback(p_ref):
                def auto_save():
                    provider_obj = p_ref()
                    if provider_obj:
                        provider_obj.save_config()
                        updated_config = self.app.settings_manager.providers.get(
                            provider_obj.internal_name, {}
                        )
                        provider_obj.load_config(updated_config)

                return auto_save

            setting.set_auto_save_callback(create_auto_save_callback(provider_ref))
            setting.render_to_layout(layout)

            # Connect credential changes for OpenAI-compatible
            if provider.internal_name == "openai-compatible" and setting.name in [
                "api_base",
                "api_key",
            ]:
                if hasattr(setting, "input"):
                    getattr(setting, "input").editingFinished.connect(
                        lambda s=setting, p_ref=provider_ref: on_setting_changed_callback(
                            s, p_ref
                        )
                    )

    def replace_model_setting_with_dropdown(
        self,
        provider: "AIProvider",
        layout: QVBoxLayout,
        models: list[str],
        on_model_changed_callback,
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

        # Already a dropdown? Just update options
        if isinstance(old_setting, DropdownSetting):
            self._logger.debug("api_model is already a DropdownSetting, updating options")
            old_setting.refresh_options([(m, m) for m in models])
            return True

        provider_config = self.app.settings_manager.providers.get(
            provider.internal_name, {}
        )
        current_model = provider_config.get("api_model", "")

        # Auto-select first model if needed
        if (not current_model or current_model not in models) and models:
            current_model = models[0]
            provider_config["api_model"] = current_model
            provider.save_config()

        # Create dropdown
        options = [(model, model) for model in models]
        dropdown_setting = DropdownSetting(
            self.app,
            name="api_model",
            display_name="API Model",
            default_value=current_model,
            description="Select a model",
            options=options,
        )

        # Set callback
        provider_ref = weakref.ref(provider)

        def auto_save():
            provider_obj = provider_ref()
            if provider_obj:
                provider_obj.save_config()
                updated_config = self.app.settings_manager.providers.get(
                    provider_obj.internal_name, {}
                )
                provider_obj.load_config(updated_config)

        dropdown_setting.set_auto_save_callback(auto_save)

        # Replace in list
        provider.settings[model_setting_index] = dropdown_setting

        # Find and replace in layout
        return self._replace_setting_in_layout(
            layout, old_setting, dropdown_setting, model_setting_index
        )

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