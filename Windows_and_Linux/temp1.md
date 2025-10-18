Bon, j'ai proposé une refactorisation à LLM Voici sa réponse Et les recommandations à suivre

Voici ma proposition de **refactorisation complète** de `provider_settings.py` :

## 📋 Résumé de la refactorisation

Le fichier original de **~700 lignes** est divisé en **4 modules spécialisés** :

### 1️⃣ **`provider_ui_builder.py`** (~200 lignes)
- Construction de l'interface (header, settings, dropdowns)
- Remplacement dynamique du TextSetting par DropdownSetting
- Gestion de la désactivation du scroll sur les dropdowns

### 2️⃣ **`provider_preset_manager.py`** (~150 lignes)
- Gestion des presets pour OpenAI-compatible
- Sauvegarde/suppression/chargement des presets
- Conversion du format legacy (liste → dict)
- Construction de l'UI des presets

### 3️⃣ **`provider_model_fetcher.py`** (~80 lignes)
- Récupération asynchrone des modèles
- Gestion du flag `_is_fetching` pour éviter les appels multiples
- Callbacks de succès/échec

### 4️⃣ **`provider_settings.py`** (~250 lignes - **simplifié**)
- **Orchestration uniquement**
- Délégation aux composants spécialisés
- Gestion du cycle de vie (init, cleanup, signals)

## 🎯 Avantages

✅ **Séparation des responsabilités** - chaque classe a un rôle unique  
✅ **Testabilité** - modules indépendants faciles à tester  
✅ **Maintenabilité** - modifications localisées sans impact sur le reste  
✅ **Réutilisabilité** - `ProviderModelFetcher` peut être utilisé ailleurs  
✅ **Lisibilité** - fichiers courts (~200 lignes max) faciles à comprendre  
✅ **Extensibilité** - ajout de nouvelles fonctionnalités simplifié  

## 📦 Structure des fichiers

```
gui/components/settings/provider/
├── __init__.py
├── provider_settings.py          # Main orchestrator (250 lignes)
├── provider_ui_builder.py        # UI construction (200 lignes)
├── provider_preset_manager.py    # Preset management (150 lignes)
├── provider_model_fetcher.py     # Async model fetching (80 lignes)
└── button_manager.py             # Existing
```

Voulez-vous que je crée les fichiers individuels pour faciliter l'implémentation ?

"""
Proposed refactoring for provider_settings.py

Split into multiple focused modules:
1. provider_settings.py - Main widget (orchestration)
2. provider_ui_builder.py - UI construction
3. provider_preset_manager.py - Preset management (OpenAI-compatible)
4. provider_model_fetcher.py - Async model fetching
"""

# ============================================================================
# provider_ui_builder.py
# ============================================================================
"""UI construction logic for provider settings."""

import logging
import weakref
from typing import TYPE_CHECKING

from PySide6 import QtCore
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QComboBox, QHBoxLayout, QLabel, QLayout, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ....aiprovider.aiprovider import AIProvider
    from ....writing_tools_app import WritingToolsApp

from ....aiprovider.settings import DropdownSetting, TextSetting
from ...ui_utils import ui_utils


class ProviderUIBuilder:
    """Handles UI construction for provider settings."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)

    def build_provider_header(
        self, provider: "AIProvider", layout: QVBoxLayout
    ) -> tuple[QLabel, QLabel]:
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


# ============================================================================
# provider_preset_manager.py
# ============================================================================
"""Preset management for OpenAI-compatible providers."""

import logging
from typing import TYPE_CHECKING
from urllib.parse import urlparse

from PySide6.QtWidgets import QComboBox, QHBoxLayout, QPushButton, QVBoxLayout

if TYPE_CHECKING:
    from ....aiprovider.aiprovider import AIProvider
    from ....writing_tools_app import WritingToolsApp


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


# ============================================================================
# provider_model_fetcher.py
# ============================================================================
"""Async model fetching for OpenAI-compatible providers."""

import logging
from typing import TYPE_CHECKING, Callable

if TYPE_CHECKING:
    from ....aiprovider.openAI_compatible import OpenAICompatibleProvider


class ProviderModelFetcher:
    """Handles async model fetching for OpenAI-compatible providers."""

    def __init__(self):
        self._logger = logging.getLogger(__name__)
        self._is_fetching = False

    def fetch_models(
        self,
        provider: "OpenAICompatibleProvider",
        api_base: str,
        api_key: str,
        on_success: Callable[[list[str]], None],
        on_failure: Callable[[str], None],
    ) -> None:
        """Fetch models asynchronously.
        
        Args:
            provider: OpenAI-compatible provider instance
            api_base: API base URL
            api_key: API key
            on_success: Callback with list of models
            on_failure: Callback with error message
        """
        if self._is_fetching:
            self._logger.debug("Already fetching models, skipping")
            return

        if not api_base or not api_key:
            self._logger.debug("Missing credentials, skipping fetch")
            return

        self._is_fetching = True
        self._logger.debug(f"Fetching models with api_base: {api_base}")

        def success_wrapper(models):
            self._is_fetching = False
            if not models:
                self._logger.debug("No models returned from fetch")
                return
            on_success(models)

        def failure_wrapper(error_msg):
            self._is_fetching = False
            self._logger.warning(f"Failed to fetch models: {error_msg}")
            on_failure(error_msg)

        provider.fetch_models_async(
            success_wrapper,
            failure_wrapper,
            api_base=api_base,
            api_key=api_key,
        )

    @property
    def is_fetching(self) -> bool:
        """Check if currently fetching models."""
        return self._is_fetching


# ============================================================================
# provider_settings.py (SIMPLIFIED)
# ============================================================================
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
from .provider_model_fetcher import ProviderModelFetcher
from .provider_preset_manager import ProviderPresetManager
from .provider_ui_builder import ProviderUIBuilder


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
        self._build_provider_selector(layout)

        # Provider UI container
        self.provider_container = QVBoxLayout()
        layout.addLayout(self.provider_container)

        # Initial provider UI
        self._initialize_provider_ui()

        # Connect provider change
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)
        self._signal_connections.append(
            (self.provider_dropdown, "currentIndexChanged", self._on_provider_changed)
        )

        # Vision comment
        self._update_vision_comment_visibility(self.app.ai_processor.current_provider)

    def _build_provider_selector(self, layout: QVBoxLayout) -> None:
        """Build provider dropdown selector."""
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

    def _initialize_provider_ui(self) -> None:
        """Initialize UI for current provider."""
        if self.app.ai_processor.current_provider:
            self.init_provider_ui(
                self.app.ai_processor.current_provider,
                self.provider_container,
            )
        else:
            self._fallback_provider_initialization()

    def _fallback_provider_initialization(self) -> None:
        """Fallback if no provider is set."""
        current_internal_name = self.provider_dropdown.currentData()
        provider_instance = self.provider_manager.find_provider_by_name(
            current_internal_name
        )

        if not provider_instance:
            default_provider_name = list(PROVIDER_CLASSES.keys())[0]
            provider_class = PROVIDER_CLASSES.get(default_provider_name)
            if provider_class:
                try:
                    provider_instance = provider_class(self.app)
                except Exception as e:
                    self._logger.error(
                        f"Failed to create default provider {default_provider_name}: {e}"
                    )
                    return

        if provider_instance:
            self.app.ai_processor.current_provider = provider_instance
            self.init_provider_ui(provider_instance, self.provider_container)

    def init_provider_ui(self, provider: "AIProvider", layout: QVBoxLayout) -> None:
        """Initialize UI for a specific provider."""
        # Refresh config
        self._refresh_provider_config(provider)

        # Clean up old UI
        self._cleanup_provider_layout()

        # Store weakref
        self._current_provider_ref = weakref.ref(provider)
        self.current_provider_layout = QVBoxLayout()

        # Build UI components
        self.provider_name_label, self.description_label = (
            self.ui_builder.build_provider_header(provider, self.current_provider_layout)
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
            provider_config = self.app.settings_manager.providers.get(
                provider.internal_name, {}
            )
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

    def _auto_fetch_models_if_needed(self, provider: "AIProvider") -> None:
        """Auto-fetch models for OpenAI-compatible if credentials exist."""
        if provider.internal_name != "openai-compatible":
            return

        provider_config = self.app.settings_manager.providers.get(
            provider.internal_name, {}
        )
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

    def _fetch_models(
        self, provider: "AIProvider", api_base: str, api_key: str
    ) -> None:
        """Fetch models and update UI."""
        from ....aiprovider.openAI_compatible import OpenAICompatibleProvider

        if not isinstance(provider, OpenAICompatibleProvider):
            return

        def on_success(models):
            if self.current_provider_layout:
                self.ui_builder.replace_model_setting_with_dropdown(
                    provider,
                    self.current_provider_layout,
                    models,
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

    def _on_provider_changed(self) -> None:
        """Handle provider change."""
        if not self.provider_dropdown:
            return

        current_internal_name = self.provider_dropdown.currentData()
        if not current_internal_name:
            return

        self._logger.debug(f"Provider changed to: {current_internal_name}")

        new_provider = self.provider_manager.switch_provider(current_internal_name)
        if not new_provider:
            self._logger.warning(f"Provider {current_internal_name} not found")
            return

        if self.provider_container:
            self.init_provider_ui(new_provider, self.provider_container)

        self._update_vision_comment_visibility(new_provider)

    def _update_vision_comment_visibility(self, provider: "AIProvider") -> None:
        """Update vision comment visibility based on provider."""
        if self.vision_comment:
            self.vision_comment.hide()
            self.vision_comment.setParent(None)
            self.vision_comment = None

        if provider.internal_name != "openai-compatible":
            self.vision_comment = QLabel(_("* Models with vision support"))
            self.vision_comment.setStyleSheet(
                f"{self.app.styles['label']}; font-style: italic;"
            )
            parent_layout = self.layout()
            if parent_layout:
                parent_layout.addWidget(self.vision_comment)

    def _refresh_provider_config(self, provider: "AIProvider") -> None:
        """Refresh provider configuration if supported."""
        self.provider_manager.refresh_provider_config(provider)

    def _cleanup_provider_layout(self) -> None:
        """Clean up previous provider layout."""
        if not self.current_provider_layout:
            return

        # Clean callbacks from previous provider settings
        if self._current_provider_ref:
            old_provider = self._current_provider_ref()
            if old_provider:
                for setting in old_provider.settings:
                    setting.set_auto_save_callback(lambda: None)

        parent = self.current_provider_layout.parent()
        if parent and hasattr(parent, "removeItem"):
            parent.removeItem(self.current_provider_layout)

        self.current_provider_layout.setParent(None)
        from ...ui_utils import ui_utils
        ui_utils.clear_layout(self.current_provider_layout)
        self.current_provider_layout.deleteLater()

        self._current_provider_ref = None

    def _disconnect_all_signals(self) -> None:
        """Disconnect all tracked signals."""
        for widget, signal_name, slot in self._signal_connections:
            try:
                signal = getattr(widget, signal_name, None)
                if signal:
                    signal.disconnect(slot)
                    self._logger.debug(f"Disconnected signal: {signal_name}")
            except Exception as e:
                self._logger.debug(f"Error disconnecting signal {signal_name}: {e}")

        self._signal_connections.clear()

    # ========================================================================
    # Theme & Language Support
    # ========================================================================

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
            self.description_label.setStyleSheet(
                f"{self.app.styles['label']}; text-align: center;"
            )
        if self.vision_comment:
            self.vision_comment.setStyleSheet(
                f"{self.app.styles['label']}; font-style: italic;"
            )

        # Update provider labels
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
        if not self.current_provider_layout:
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

            # Update buttons if provider has them
            if self.app.ai_processor.current_provider:
                if hasattr(self.app.ai_processor.current_provider, "additional_buttons"):
                    self._refresh_additional_buttons()

        finally:
            if self.provider_dropdown:
                self.provider_dropdown.blockSignals(False)

    def _refresh_additional_buttons(self) -> None:
        """Refresh text for additional buttons."""
        if not self.current_provider_layout:
            return

        from PySide6.QtWidgets import QPushButton
        from typing import cast

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

    def update_provider_button_text(self) -> None:
        """Update main button text when provider state changes."""
        # This method can be called from outside to update button text
        if self.app.ai_processor.current_provider:
            # Trigger button manager update if needed
            pass

    # ========================================================================
    # Cleanup
    # ========================================================================

    def closeEvent(self, event) -> None:
        """Cleanup on close."""
        self._logger.debug("ProviderSettings closing, cleaning up...")

        # Disconnect all signals
        self._disconnect_all_signals()

        # Clean provider layout
        self._cleanup_provider_layout()

        # Call parent closeEvent
        super().closeEvent(event)