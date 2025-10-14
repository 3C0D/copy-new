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
        connection = self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)
        self._signal_connections.append((self.provider_dropdown, "currentIndexChanged", self._on_provider_changed))

        # Vision comment
        self.vision_comment = QLabel(_("* Models with vision support"))
        self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")
        layout.addWidget(self.vision_comment)

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

        self._add_provider_settings(provider)

        layout.addLayout(self.current_provider_layout)

        # Disable dropdown scroll interference
        self._disable_dropdown_scroll(self.current_provider_layout)

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

        # Use weakref to avoid reference cycles
        provider_ref = weakref.ref(provider)
        provider_manager_ref = weakref.ref(self.provider_manager)

        for setting in provider.settings:
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)

            # Callback with weakref to avoid cycle
            def auto_save_callback(p_ref=provider_ref, pm_ref=provider_manager_ref):
                provider_obj = p_ref()
                provider_manager_obj = pm_ref()
                if provider_obj is not None and provider_manager_obj is not None:
                    provider_manager_obj.save_provider_settings(provider_obj)
                else:
                    self._logger.debug("Provider or manager was garbage collected")

            setting.set_auto_save_callback(auto_save_callback)
            setting.render_to_layout(self.current_provider_layout)

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
