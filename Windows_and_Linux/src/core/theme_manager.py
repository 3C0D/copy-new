"""
Centralized theme manager for the entire application.
"""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore

if TYPE_CHECKING:
    from PySide6.QtWidgets import QWidget

    from ..writing_tools_app import WritingToolsApp


class ThemeManager(QtCore.QObject):
    """Centralized theme manager with signals to notify changes."""

    color_mode_changed = QtCore.Signal(str)  # Emits the new mode (dark/light)

    background_theme_changed = QtCore.Signal(str)  # Emits the new background theme (gradient/plain)

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self._registered_widgets: list[QWidget] = []

    def register_widget(self, widget: "QWidget") -> None:
        """Register a widget to receive theme updates."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget: "QWidget") -> None:
        """Unregister a widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def change_color_mode(self, new_mode: str) -> None:
        """Change the color mode and notify all registered widgets."""
        # Log color mode change with distinctive icon
        theme_icon = "🌙" if new_mode == "dark" else ("☀️" if new_mode == "light" else "🔄")
        self._logger.debug(f"🎨 ThemeManager color mode: {theme_icon} Color={new_mode}")

        # Save to settings
        self.app.settings_manager.color_mode = new_mode

        # Update styles
        self.app.styles = self.get_styles()
        # Emit signal
        self.color_mode_changed.emit(new_mode)

        # Refresh all registered widgets
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_theme"):
                try:
                    widget.refresh_theme() # type: ignore
                except RuntimeError:
                    # Widget destroyed, remove it from the list
                    self._registered_widgets.remove(widget)

    def change_background_theme(self, new_theme: str) -> None:
        """Change the background theme (gradient/plain) and notify all registered widgets."""
        # Log background theme change with distinctive icon
        bg_icon = "🌈" if new_theme == "gradient" else "⚽"
        self._logger.debug(f"🎨 ThemeManager background theme: {bg_icon} BG={new_theme}")

        # Save to settings
        self.app.settings_manager.background_theme = new_theme

        # Emit signal and update all registered widgets with the new theme
        self.background_theme_changed.emit(new_theme)

    def get_styles(self) -> dict[str, str]:
        """
        Return a single dictionary that contains every standard stylesheet
        used across the application. The CSS is built once per theme change
        so every consumer can simply do: self.styles = app.theme_manager.get_styles()
        """
        mode = self.app.settings_manager.color_mode
        dark = mode == "dark"

        # Base colours (matching original functions exactly)
        bg_primary = "#2d2d2d" if dark else "#ffffff"
        fg_primary = "#ffffff" if dark else "#000000"
        bg_control = "#444444" if dark else "white"
        fg_control = "#ffffff" if dark else "#000000"
        fg_control_text = "#ffffff" if dark else "#333333"  # For labels/radios
        border = "#666666" if dark else "#cccccc"
        border_checkbox = "#666666"  # Specific color for checkboxes
        selection = "#666" if dark else "#e0e0e0"

        # Button colours
        primary_default = "#4CAF50" if dark else "#008CBA"
        primary_hover = "#45a049" if dark else "#007095"
        primary_pressed = "#3d8b40" if dark else "#005f7a"

        secondary_default = "#666666" if dark else "#cccccc"
        secondary_hover = "#555555" if dark else "#bbbbbb"
        secondary_pressed = "#444444" if dark else "#aaaaaa"

        close_default = "#3d8b40" if dark else "#0277bd"
        close_hover = "#2e7d32" if dark else "#01579b"
        close_pressed = "#1b5e20" if dark else "#004d40"

        return {
            # ----------  COLORS  ----------
            "color_primary": "#2196F3",
            "color_secondary": "#444" if dark else "#ddd",
            "color_background": "white",
            # ----------  CONTAINERS  ----------
            "dialog": f"""
                QDialog {{
                    background-color: {bg_primary};
                    color: {fg_primary};
                }}
            """,
            # ----------  LABELS  ----------
            "label": f"""
                QLabel {{
                    font-size: 16px;
                    color: {fg_control_text};
                }}
            """,
            "label_small": f"""
                QLabel {{
                    font-size: 14px;
                    color: {fg_control_text};
                }}
            """,
            "label_title": f"""
                QLabel {{
                    font-size: 24px;
                    font-weight: bold;
                    color: {fg_primary};
                }}
            """,
            "warning_label": """
                QLabel {
                    font-size: 14px;
                    color: #ff6b6b;
                    font-weight: bold;
                }
            """,
            # ----------  INPUTS  ----------
            "input": f"""
                QLineEdit {{
                    font-size: 16px;
                    padding: 5px;
                    background-color: {bg_control};
                    color: {fg_control};
                    border: 1px solid {border};
                }}
            """,
            # ----------  DROPDOWNS  ----------
            "dropdown": f"""
                QComboBox {{
                    background-color: {bg_control};
                    color: {fg_control};
                    border: 1px solid {border};
                    padding: 5px;
                    font-size: 16px;
                }}
                QComboBox QAbstractItemView {{
                    background-color: {bg_control};
                    color: {fg_control};
                    selection-background-color: {selection};
                }}
            """,
            # ----------  BUTTONS  ----------
            "button": f"""
                QPushButton {{
                    font-size: 14px;
                    padding: 8px 16px;
                    border: 1px solid {border};
                    background-color: {bg_control};
                    color: {fg_control};
                }}
                QPushButton:hover {{
                    background-color: {selection};
                }}
                QPushButton:pressed {{
                    background-color: {border};
                }}
            """,
            "primary_button": f"""
                QPushButton {{
                    background-color: {primary_default};
                    border: none;
                    color: white;
                    padding: 10px;
                    font-size: 16px;
                    border-radius: 5px;
                }}
                QPushButton:hover {{
                    background-color: {primary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {primary_pressed};
                }}
                QPushButton:disabled {{
                    background-color: {primary_pressed};
                    color: #bdbdbd;
                    border-color: {primary_pressed};
                }}
            """,
            "secondary_button": f"""
                QPushButton {{
                    background-color: {secondary_default};
                    color: {fg_primary if dark else "#333333"};
                    padding: 8px 12px;
                    font-size: 14px;
                    border: none;
                    border-radius: 4px;
                }}
                QPushButton:hover {{
                    background-color: {secondary_hover};
                }}
                QPushButton:pressed {{
                    background-color: {secondary_pressed};
                }}
            """,
            "close_button": f"""
                QPushButton {{
                    background-color: {close_default};
                    color: white;
                    border: none;
                    border-radius: 6px;
                    font-size: 14px;
                    font-weight: bold;
                    padding: 8px 16px;
                }}
                QPushButton:hover {{
                    background-color: {close_hover};
                }}
                QPushButton:pressed {{
                    background-color: {close_pressed};
                }}
            """,
            "delete_button": """
                QPushButton {
                    background-color: #dc3545;
                    color: white;
                    border: none;
                    border-radius: 50%;
                    font-size: 14px;
                    font-weight: bold;
                    min-width: 20px;
                    min-height: 20px;
                    padding: 0;
                }
                QPushButton:hover {
                    background-color: #c82333;
                }
                QPushButton:pressed {
                    background-color: #bd2130;
                }
            """,
            "container": f"""
                QWidget {{
                    background-color: transparent;
                    border: 1px solid {"#666666" if dark else "#777777D2"};
                    border-radius: 8px;
                    padding: 8px;
                }}
            """,
            "image_preview": f"""
                QLabel {{
                    border: 1px solid {"rgba(0, 140, 186, 0.8)" if not dark else "rgba(76, 175, 80, 0.8)"};
                    border-radius: 4px;
                    {"background-color: rgba(248, 248, 248, 0.4);" if not dark else "background-color: rgba(255, 255, 255, 0.1);"}
                }}
            """,
            "icon_button": f"""
                QPushButton {{
                    background-color: {"#666" if dark else "#999"};
                    border-radius: 10px;
                    min-width: 16px;
                    min-height: 16px;
                    max-width: 16px;
                    max-height: 16px;
                    padding: 1px;
                    margin: 0px;
                }}
                QPushButton:hover {{
                    background-color: {"#888" if dark else "#bbb"};
                }}
            """,
            "lock_button": f"""
                QPushButton {{
                    {"background-color: #f0f0f0; color: #333333;" if not dark else "background-color: #555555; color: white;"}
                    border: 1px solid {"#999999" if not dark else "#666666"};
                    border-radius: 4px;
                    padding: 2px;
                    font-size: 14px;
                    min-width: 20px;
                    min-height: 20px;
                }}
                QPushButton:hover {{
                    background-color: {selection};
                    border: 1px solid {"#777777" if not dark else "#888888"};
                }}
                QPushButton:checked {{
                    background-color: #4CAF50;
                    color: white;
                    border: 1px solid #4CAF50;
                }}
            """,
            "input_full": f"""
                QLineEdit {{
                    padding: 10px;
                    border: 2px solid {border};
                    border-radius: 8px;
                    background-color: {bg_control};
                    color: {fg_control};
                    font-size: 14px;
                }}
                QLineEdit:focus {{
                    border-color: {"#4CAF50" if dark else "#2196F3"};
                }}
            """,
            "send_button": f"""
                QPushButton {{
                    background-color: {"#2e7d32" if dark else "#4CAF50"};
                    border: none;
                    border-radius: 8px;
                    padding: 5px;
                }}
                QPushButton:hover {{
                    background-color: {"#1b5e20" if dark else "#45a049"};
                }}
            """,
            "icon_small_button": f"""
                QPushButton {{
                    background-color: transparent;
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                    margin-top: 3px;
                    color: {fg_control};
                }}
                QPushButton:hover {{
                    background-color: {selection};
                }}
            """,
            "close_small_button": f"""
                QPushButton {{
                    background-color: transparent;
                    color: {fg_control};
                    font-size: 20px;
                    font-weight: bold;
                    border: none;
                    border-radius: 6px;
                    padding: 0px;
                }}
                QPushButton:hover {{
                    background-color: {selection};
                }}
            """,
            "add_button": f"""
                QPushButton {{
                    background-color: {bg_control if dark else "#e0e0e0"};
                    border: 1px solid {border};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                    text-align: center;
                    color: {fg_control};
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {selection if dark else "#d0d0d0"};
                }}
            """,
            "action_indicator": f"""
                QLabel {{
                    background-color: {secondary_default};
                    color: {fg_primary};
                    border-radius: 10px;
                    font-size: 12px;
                    font-weight: bold;
                    padding: 2px;
                    min-width: 16px;
                    max-width: 16px;
                    min-height: 16px;
                    max-height: 16px;
                    text-align: center;
                }}
            """,
            # ----------  OTHER CONTROLS  ----------
            "radio": f"""
                QRadioButton {{
                    color: {fg_control_text};
                    font-size: 16px;
                }}
            """,
            "checkbox": f"""
                QCheckBox {{
                    color: {fg_control_text};
                    font-size: 16px;
                    spacing: 8px;
                }}
                QCheckBox::indicator {{
                    width: 13px;
                    height: 13px;
                    border-radius: 2px;
                }}
                QCheckBox::indicator:unchecked {{
                    border: 2px solid {border_checkbox};
                    background-color: {bg_control};
                }}
                QCheckBox::indicator:checked {{
                    border: 2px solid {border_checkbox};
                    background-color: {border_checkbox};
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOSIgaGVpZ2h0PSI5IiB2aWV3Qm94PSIwIDAgOSA5IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJNNy41IDIuNUwzLjc1IDYuMjVMMi41IDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
                }}
            """
            if not dark
            else f"""
                QCheckBox {{
                    color: {fg_control_text};
                    font-size: 16px;
                }}
            """,
            "tray_menu": f"""
                QMenu {{
                    background-color: {bg_primary};
                    color: {fg_primary};
                    border: 1px solid {border};
                    border-radius: 8px;
                    padding: 2px;
                    selection-background-color: {selection};
                }}
                QMenu::item {{
                    padding: 4px 20px;
                    border-radius: 4px;
                }}
                QMenu::item:selected {{
                    background-color: {selection};
                }}
            """,
            "non_editable_modal": f"""
                QWidget {{
                    background-color: {"#2a2a2a" if dark else "#ffffff"};
                    border: 1px solid {"#404040" if dark else "#d0d0d0"};
                    border-radius: 8px;
                }}
                QTextBrowser {{
                    background-color: {"#1e1e1e" if dark else "#f5f5f5"};
                    color: {"#ffffff" if dark else "#000000"};
                    border: 1px solid {"#404040" if dark else "#d0d0d0"};
                    border-radius: 4px;
                    padding: 8px;
                }}
                QPushButton {{
                    background-color: {"#404040" if dark else "#e8e8e8"};
                    border: none;
                    border-radius: 4px;
                    color: {"#ffffff" if dark else "#000000"};
                    font-size: 16px;
                }}
                QPushButton:hover {{
                    background-color: #4a9eff;
                    {"" if dark else "color: #ffffff;"}
                }}
            """,
        }
