"""
ui_components.py

Factory functions for creating styled UI components.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QRadioButton,
)

if TYPE_CHECKING:
    from ....core.settings_manager import SettingsManager
    from ....writing_tools_app import WritingToolsApp

from ....config.data_operations import get_available_languages


def create_styled_widget(widget_class, style_key, app, **kwargs):
    """
    Create a widget with app styling applied.

    Args:
        widget_class: Qt widget class (QLabel, QComboBox, etc.).
        style_key: Style key from app.styles ('label', 'dropdown', etc.).
        app: Application instance with styles dictionary.
        **kwargs: Arguments for widget constructor.

    Returns:
        Styled widget instance.
    """
    widget = widget_class(**kwargs)
    widget.setStyleSheet(app.styles[style_key])
    return widget


def create_language_section(app: "WritingToolsApp", settings_manager: "SettingsManager"):
    """
    Create language selection label and dropdown.

    Args:
        app: Application instance for styling.
        settings_manager: Settings with current language preference.

    Returns:
        tuple: (QLabel, QComboBox) - Label and dropdown widgets.
    """
    label = create_styled_widget(QLabel, "label", app, text="Language:")
    dropdown = create_styled_widget(QComboBox, "dropdown", app)
    dropdown.wheelEvent = lambda e: e.ignore()

    current_language = settings_manager.language or "en"

    # Populate with available languages
    available_languages = get_available_languages()
    for display_name, lang_code in available_languages:
        dropdown.addItem(display_name, lang_code)

    # Set current selection
    current_index = dropdown.findData(current_language)
    if current_index != -1:
        dropdown.setCurrentIndex(current_index)
    else:
        # Default to English
        english_index = dropdown.findData("en")
        if english_index != -1:
            dropdown.setCurrentIndex(english_index)

    return label, dropdown


def create_shortcut_section(app: "WritingToolsApp", settings_manager: "SettingsManager"):
    """
    Create shortcut key label and input field.

    Args:
        app: Application instance for styling.
        settings_manager: Settings with current hotkey.

    Returns:
        tuple: (QLabel, QLineEdit) - Label and input widgets.
    """
    label = create_styled_widget(QLabel, "label", app, text="Shortcut Key:")
    input_field = create_styled_widget(
        QLineEdit, "input", app, text=settings_manager.hotkey or "ctrl space"
    )
    input_field.setPlaceholderText("e.g., ctrl space, ctrl shift a, ctrl shift +")

    return label, input_field


def create_theme_section(app: "WritingToolsApp", parent_window):
    """
    Create background theme label and radio buttons (Gradient/Plain).

    Args:
        app: Application instance for styling.
        parent_window: Settings window with current theme state.

    Returns:
        tuple: (QLabel, QHBoxLayout, QRadioButton, QRadioButton)
               Label, layout, gradient radio, plain radio.
    """
    label = create_styled_widget(QLabel, "label", app, text="Background Theme:")

    layout = QHBoxLayout()
    gradient_radio = create_styled_widget(QRadioButton, "radio", app, text="Blurry Gradient")
    plain_radio = create_styled_widget(QRadioButton, "radio", app, text="Plain")

    current_theme = parent_window.current_background_theme
    gradient_radio.setChecked(current_theme == "gradient")
    plain_radio.setChecked(current_theme == "plain")

    layout.addWidget(gradient_radio)
    layout.addWidget(plain_radio)

    return label, layout, gradient_radio, plain_radio


def create_color_mode_section(app: "WritingToolsApp", settings_manager: "SettingsManager"):
    """
    Create color mode label and dropdown (Auto/Light/Dark).

    Args:
        app: Application instance for styling.
        settings_manager: Settings with current color mode.

    Returns:
        tuple: (QLabel, QComboBox) - Label and dropdown widgets.
    """
    label = create_styled_widget(QLabel, "label", app, text="Color Mode:")
    dropdown = create_styled_widget(QComboBox, "dropdown", app)
    dropdown.addItems(["Auto", "Light", "Dark"])
    dropdown.wheelEvent = lambda e: e.ignore()

    current_mode = settings_manager.color_mode
    mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
    dropdown.setCurrentIndex(mode_index)

    return label, dropdown


def create_autostart_section(app: "WritingToolsApp", settings_manager: "SettingsManager"):
    """
    Create autostart checkbox ("Start on Boot").

    Args:
        app: Application instance for styling.
        settings_manager: Settings with autostart preference.

    Returns:
        QCheckBox: Configured checkbox widget.
    """
    checkbox = create_styled_widget(QCheckBox, "checkbox", app, text="Start on Boot")

    # Sync with registry
    from ....autostart_manager import AutostartManager

    AutostartManager.sync_with_settings(settings_manager)

    # Set state from settings
    checkbox.setChecked(getattr(settings_manager, "start_on_boot", False))

    return checkbox
