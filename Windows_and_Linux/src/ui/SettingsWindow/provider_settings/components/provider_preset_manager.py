"""
Preset management for OpenAI-compatible providers.
"""

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout

if TYPE_CHECKING:
    from .....aiprovider.aiprovider import AIProvider
    from .....writing_tools_app import WritingToolsApp


class ProviderPresetManager:
    """Manages presets for OpenAI-compatible providers."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)

    def extract_provider_key(self, api_base: str) -> str:
        """Extract domain from API base URL as unique key."""
        parsed = urlparse(api_base)
        return parsed.netloc or "unknown"

    def save_preset(self, provider: "AIProvider") -> bool:
        """Save current config as preset.

        Returns:
            True if saved successfully
        """
        if provider.internal_name != "openai-compatible":
            return False

        config = self.app.settings_manager.providers.get("openai-compatible", {})
        api_base = config.get("api_base", "")

        if not api_base:
            return False

        key = self.extract_provider_key(api_base)

        # Initialize recorded as dict
        if "recorded" not in config:
            config["recorded"] = {}

        # Save preset
        config["recorded"][key] = {
            "api_key": config.get("api_key", ""),
            "api_base": api_base,
            "api_model": config.get("api_model", ""),
            "api_organisation": config.get("api_organisation", ""),
            "api_project": config.get("api_project", ""),
            "has_vision": config.get("has_vision", False),
        }

        self.app.settings_manager.save()
        return True

    def delete_preset(self, provider: "AIProvider") -> bool:
        """Delete current preset.

        Returns:
            True if deleted successfully
        """
        if provider.internal_name != "openai-compatible":
            return False

        config = self.app.settings_manager.providers.get("openai-compatible", {})
        api_base = config.get("api_base", "")

        if not api_base or "recorded" not in config:
            return False

        key = self.extract_provider_key(api_base)

        if key in config["recorded"]:
            del config["recorded"][key]
            self.app.settings_manager.save()
            return True

        return False

    def load_preset(self, provider: "AIProvider", preset_data: dict) -> None:
        """Load preset data into provider config."""
        if provider.internal_name != "openai-compatible":
            return

        config = self.app.settings_manager.providers["openai-compatible"]
        config.update(preset_data)
        provider.load_config(config)

    def build_preset_ui(
        self,
        provider: "AIProvider",
        layout: QVBoxLayout,
        on_preset_selected,
        on_save,
        on_delete,
    ) -> QComboBox | None:
        """Build preset UI (dropdown + buttons).

        Returns:
            Preset dropdown if created, None otherwise
        """
        if provider.internal_name != "openai-compatible":
            return None

        config = self.app.settings_manager.providers.get("openai-compatible", {})
        recorded = config.get("recorded", {})

        # Convert legacy list format to dict
        if isinstance(recorded, list):
            recorded = self._convert_legacy_presets(recorded)
            config["recorded"] = recorded

        # Dropdown (only if presets exist)
        preset_dropdown = None
        if len(recorded) > 0:
            preset_dropdown = QComboBox()
            preset_dropdown.setStyleSheet(self.app.styles["dropdown"])
            preset_dropdown.wheelEvent = lambda e: e.ignore()

            current_base = config.get("api_base", "")
            current_key = self.extract_provider_key(current_base) if current_base else ""

            # Add presets
            for key, preset_data in recorded.items():
                preset_dropdown.addItem(key, preset_data)

            # Set selection
            current_index = preset_dropdown.findText(current_key)
            if current_index != -1:
                preset_dropdown.setCurrentIndex(current_index)

            preset_dropdown.currentIndexChanged.connect(
                lambda: on_preset_selected(preset_dropdown)
            )
            layout.addWidget(preset_dropdown)

        # Buttons
        buttons_layout = QHBoxLayout()

        save_btn = QPushButton("Save")
        save_btn.setStyleSheet(self.app.styles["primary_button"])
        save_btn.clicked.connect(on_save)

        delete_btn = QPushButton("Delete")
        delete_btn.setStyleSheet(self.app.styles["secondary_button"])
        delete_btn.clicked.connect(on_delete)

        buttons_layout.addWidget(save_btn)
        buttons_layout.addWidget(delete_btn)
        layout.addLayout(buttons_layout)

        return preset_dropdown

    def _convert_legacy_presets(self, preset_list: list) -> dict:
        """Convert legacy list format to dict format."""
        new_recorded = {}
        for preset in preset_list:
            key = preset.get("key", "")
            if key:
                preset_copy = preset.copy()
                preset_copy.pop("key", None)
                new_recorded[key] = preset_copy
        return new_recorded