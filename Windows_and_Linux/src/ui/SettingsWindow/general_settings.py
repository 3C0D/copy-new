"""
general_settings.py

General settings component: language, hotkey, theme, color mode, autostart.
All settings auto-save when changed.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .settings_window import SettingsWindow

from ...autostart_manager import AutostartManager
from ...config.data_operations import get_available_languages


def _(x):
    return x


class GeneralSettings(QWidget):
    """Widget containing all general application settings."""

    def __init__(self, app: "WritingToolsApp", parent: "SettingsWindow"):
        super().__init__(parent)
        self.app = app
        self.parent_window = parent
        self._logger = logging.getLogger(__name__)

        # Flag to prevent recursive language changes
        self._changing_language = False

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

        # Autostart checkbox
        self.autostart_checkbox = QCheckBox(_("Start on Boot"))
        self.autostart_checkbox.setStyleSheet(self.app.styles["checkbox"])

        # Sync with registry
        AutostartManager.sync_with_settings(self.app.settings_manager)

        # Set state from settings
        self.autostart_checkbox.setChecked(
            getattr(self.app.settings_manager, "start_on_boot", False)
        )
        self.autostart_checkbox.stateChanged.connect(self._on_autostart_changed)
        layout.addWidget(self.autostart_checkbox)

        # Language selection
        self.language_label = QLabel(_("Language:"))
        self.language_label.setStyleSheet(self.app.styles["label"])
        layout.addWidget(self.language_label)

        self.language_dropdown = QComboBox()
        self.language_dropdown.setStyleSheet(self.app.styles["dropdown"])
        self.language_dropdown.wheelEvent = lambda e: e.ignore()

        current_language = self.app.settings_manager.language or "en"

        # Populate with available languages
        available_languages = get_available_languages()
        for display_name, lang_code in available_languages:
            self.language_dropdown.addItem(display_name, lang_code)

        # Set current selection
        current_index = self.language_dropdown.findData(current_language)
        if current_index != -1:
            self.language_dropdown.setCurrentIndex(current_index)
        else:
            # Default to English
            english_index = self.language_dropdown.findData("en")
            if english_index != -1:
                self.language_dropdown.setCurrentIndex(english_index)

        self.language_dropdown.currentIndexChanged.connect(self._on_language_changed)
        layout.addWidget(self.language_dropdown)

        # Shortcut key
        self.shortcut_label = QLabel(_("Shortcut Key:"))
        self.shortcut_label.setStyleSheet(self.app.styles["label"])
        layout.addWidget(self.shortcut_label)

        self.shortcut_input = QLineEdit(self.app.settings_manager.hotkey or "ctrl+space")
        self.shortcut_input.setStyleSheet(self.app.styles["input"])
        self.shortcut_input.setPlaceholderText("e.g., ctrl+space, ctrl+shift+a")
        self.shortcut_input.editingFinished.connect(self._on_shortcut_changed)
        layout.addWidget(self.shortcut_input)

        # Background theme
        self.theme_label = QLabel(_("Background Theme:"))
        self.theme_label.setStyleSheet(self.app.styles["label"])
        layout.addWidget(self.theme_label)

        theme_layout = QHBoxLayout()
        self.gradient_radio = QRadioButton(_("Blurry Gradient"))
        self.plain_radio = QRadioButton(_("Plain"))
        self.gradient_radio.setStyleSheet(self.app.styles["radio"])
        self.plain_radio.setStyleSheet(self.app.styles["radio"])

        current_theme = self.parent_window.current_background_theme
        self.gradient_radio.setChecked(current_theme == "gradient")
        self.plain_radio.setChecked(current_theme == "plain")

        self.gradient_radio.toggled.connect(self._on_theme_changed)
        self.plain_radio.toggled.connect(self._on_theme_changed)

        theme_layout.addWidget(self.gradient_radio)
        theme_layout.addWidget(self.plain_radio)
        layout.addLayout(theme_layout)

        # Color mode
        self.color_mode_label = QLabel(_("Color Mode:"))
        self.color_mode_label.setStyleSheet(self.app.styles["label"])
        layout.addWidget(self.color_mode_label)

        self.color_mode_dropdown = QComboBox()
        self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

        current_mode = self.app.settings_manager.color_mode
        mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
        self.color_mode_dropdown.setCurrentIndex(mode_index)

        self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])
        self.color_mode_dropdown.currentTextChanged.connect(self._on_color_mode_changed)
        self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

        layout.addWidget(self.color_mode_dropdown)

    def _on_autostart_changed(self, state: int) -> None:
        """Handle autostart toggle and auto-save."""
        enable = state == 2  # Qt.Checked
        AutostartManager.set_autostart_with_sync(enable, self.app.settings_manager)

        # Update systray action state if systray exists
        if self.app.systray_manager.autostart_action:
            self.app.systray_manager.autostart_action.setChecked(enable)

    def _on_language_changed(self) -> None:
        """Handle language change and auto-save."""
        if self._changing_language:
            return

        if self.language_dropdown is None:
            return

        selected_lang_code = self.language_dropdown.currentData()
        if selected_lang_code:
            self._changing_language = True
            try:
                self.app.language_manager.set_language(selected_lang_code)
            finally:
                self._changing_language = False

    def _on_shortcut_changed(self) -> None:
        """Handle shortcut change and auto-save."""
        if self.shortcut_input is None:
            return

        self.app.settings_manager.hotkey = self.shortcut_input.text() or "ctrl+space"
        self.app.hotkey_manager.register_hotkey()

    def _on_theme_changed(self) -> None:
        """Handle theme change and auto-save."""
        if self.gradient_radio is None:
            return

        theme = "gradient" if self.gradient_radio.isChecked() else "plain"
        self.app.theme_manager.change_background_theme(theme)

    def _on_color_mode_changed(self) -> None:
        """Handle color mode change and auto-save."""
        if self.color_mode_dropdown is None:
            return

        selected_text = self.color_mode_dropdown.currentText()
        mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
        color_mode = mode_mapping.get(selected_text, "auto")

        self.app.theme_manager.change_color_mode(color_mode)
        self.parent_window.refresh_theme()


    def refresh_theme(self) -> None:
        """Refresh theme for all UI components."""
        if self.language_label:
            self.language_label.setStyleSheet(self.app.styles["label"])
        if self.language_dropdown:
            self.language_dropdown.setStyleSheet(self.app.styles["dropdown"])
        if self.shortcut_label:
            self.shortcut_label.setStyleSheet(self.app.styles["label"])
        if self.shortcut_input:
            self.shortcut_input.setStyleSheet(self.app.styles["input"])
        if self.theme_label:
            self.theme_label.setStyleSheet(self.app.styles["label"])
        if self.gradient_radio:
            self.gradient_radio.setStyleSheet(self.app.styles["radio"])
        if self.plain_radio:
            self.plain_radio.setStyleSheet(self.app.styles["radio"])
        if self.color_mode_label:
            self.color_mode_label.setStyleSheet(self.app.styles["label"])
        if self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])
        if self.autostart_checkbox:
            self.autostart_checkbox.setStyleSheet(self.app.styles["checkbox"])

    def refresh_language(self) -> None:
        """Refresh language for all text elements."""
        # Block signals during refresh to prevent loops
        if self.language_dropdown:
            self.language_dropdown.blockSignals(True)
        if self.color_mode_dropdown:
            self.color_mode_dropdown.blockSignals(True)

        try:
            # Update all text labels
            if self.language_label:
                self.language_label.setText(_("Language:"))
            if self.shortcut_label:
                self.shortcut_label.setText(_("Shortcut Key:"))
            if self.theme_label:
                self.theme_label.setText(_("Background Theme:"))
            if self.color_mode_label:
                self.color_mode_label.setText(_("Color Mode:"))

            # Update radio buttons
            if self.gradient_radio:
                self.gradient_radio.setText(_("Blurry Gradient"))
            if self.plain_radio:
                self.plain_radio.setText(_("Plain"))

            # Update color mode dropdown items
            if self.color_mode_dropdown:
                self.color_mode_dropdown.clear()
                self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])
                # Restore current selection
                current_mode = self.app.settings_manager.color_mode
                mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
                self.color_mode_dropdown.setCurrentIndex(mode_index)

            # Update checkbox
            if self.autostart_checkbox:
                self.autostart_checkbox.setText(_("Start on Boot"))

        finally:
            # Always restore signals
            if self.language_dropdown:
                self.language_dropdown.blockSignals(False)
            if self.color_mode_dropdown:
                self.color_mode_dropdown.blockSignals(False)
