"""
general_settings_widget.py

Refactored GeneralSettings widget using modular components.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp
    from ..settings_window import SettingsWindow

from .refresh_manager import RefreshManager
from .settings_handlers import SettingsHandlers
from .ui_components import (
    create_autostart_section,
    create_color_mode_section,
    create_language_section,
    create_shortcut_section,
    create_theme_section,
)


def _(x):
    return x


class GeneralSettings(QWidget):
    """Widget containing all general application settings."""

    def __init__(self, app: "WritingToolsApp", parent: "SettingsWindow"):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent
        self._logger = logging.getLogger(__name__)

        # Delegate to handlers
        self.handlers = SettingsHandlers(app, parent)

        # Initialize UI components as None
        self.autostart_checkbox = None
        self.language_label = None
        self.language_dropdown = None
        self.shortcut_label = None
        self.shortcut_input = None
        self.theme_label = None
        self.gradient_radio = None
        self.plain_radio = None
        self.color_mode_label = None
        self.color_mode_dropdown = None

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize general settings UI."""
        layout = QVBoxLayout(self)
        layout.setSpacing(15)
        layout.setContentsMargins(0, 0, 0, 0)

        # Autostart
        self.autostart_checkbox = create_autostart_section(self.app, self.app.settings_manager)
        self.autostart_checkbox.stateChanged.connect(
            lambda state: self.handlers.handle_autostart_changed(state)
        )
        layout.addWidget(self.autostart_checkbox)

        # Language
        self.language_label, self.language_dropdown = create_language_section(
            self.app, self.app.settings_manager
        )
        self.language_dropdown.currentIndexChanged.connect(
            lambda: self.handlers.handle_language_changed(self.language_dropdown)
        )
        layout.addWidget(self.language_label)
        layout.addWidget(self.language_dropdown)

        # Shortcut
        self.shortcut_label, self.shortcut_input = create_shortcut_section(
            self.app, self.app.settings_manager
        )
        self.shortcut_input.editingFinished.connect(
            lambda: self.handlers.handle_shortcut_changed(self.shortcut_input)
        )
        layout.addWidget(self.shortcut_label)
        layout.addWidget(self.shortcut_input)

        # Theme
        self.theme_label, theme_layout, self.gradient_radio, self.plain_radio = (
            create_theme_section(self.app, self.parent_window)
        )
        self.gradient_radio.toggled.connect(
            lambda: self.handlers.handle_theme_changed(self.gradient_radio)
        )
        layout.addWidget(self.theme_label)
        layout.addLayout(theme_layout)

        # Color mode
        self.color_mode_label, self.color_mode_dropdown = create_color_mode_section(
            self.app, self.app.settings_manager
        )
        self.color_mode_dropdown.currentTextChanged.connect(
            lambda: self.handlers.handle_color_mode_changed(self.color_mode_dropdown)
        )
        layout.addWidget(self.color_mode_label)
        layout.addWidget(self.color_mode_dropdown)

    def refresh_theme(self) -> None:
        """Refresh theme for all UI components."""
        widgets_dict = {
            "label": [
                self.language_label,
                self.shortcut_label,
                self.theme_label,
                self.color_mode_label,
            ],
            "dropdown": [self.language_dropdown, self.color_mode_dropdown],
            "input": [self.shortcut_input],
            "radio": [self.gradient_radio, self.plain_radio],
            "checkbox": [self.autostart_checkbox],
        }
        RefreshManager.refresh_theme(widgets_dict, self.app.styles)

    def refresh_language(self) -> None:
        """Refresh language for all text elements."""
        components = [
            (self.language_label, lambda: _("Language:")),
            (self.shortcut_label, lambda: _("Shortcut Key:")),
            (self.theme_label, lambda: _("Background Theme:")),
            (self.gradient_radio, lambda: _("Blurry Gradient")),
            (self.plain_radio, lambda: _("Plain")),
            (self.color_mode_label, lambda: _("Color Mode:")),
            (self.autostart_checkbox, lambda: _("Start on Boot")),
        ]
        RefreshManager.refresh_language(
            components,
            self.color_mode_dropdown,
            self.app.settings_manager.color_mode,
            translator_func=_,
        )
