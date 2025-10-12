"""
Centralized theme manager for the entire application.
Refactored to use modular style system.
"""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore

from .styles import (
    DARK_PALETTE,
    LIGHT_PALETTE,
    action_indicator,
    add_button,
    chat_scroll_area,
    checkbox,
    close_button,
    close_small_button,
    container,
    copy_button,
    copy_button_success,
    delete_button,
    dialog,
    dropdown,
    icon_button,
    icon_small_button,
    image_preview,
    input_field,
    input_full,
    label,
    label_small,
    label_title,
    lock_button,
    markdown_text_browser_ai,
    markdown_text_browser_user,
    neutral_button,
    non_editable_modal,
    primary_button,
    progress_window,
    radio_button,
    secondary_button,
    send_button,
    tray_menu,
    warning_label,
)

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
        self._current_palette = None
        self._update_palette()

    def _update_palette(self) -> None:
        """Update the current color palette based on settings."""
        mode = self.app.settings_manager.color_mode
        self._current_palette = DARK_PALETTE if mode == "dark" else LIGHT_PALETTE

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

        # Update palette and styles
        self._update_palette()
        self.app.styles = self.get_styles()

        # Emit signal
        self.color_mode_changed.emit(new_mode)

        # Refresh all registered widgets
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_theme"):
                try:
                    widget.refresh_theme()  # type: ignore
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
        used across the application. Uses the modular style system.
        """
        assert self._current_palette is not None, "Palette should be initialized"
        palette = self._current_palette

        return {
            # ----------  COLORS  ----------
            "color_primary": "#2196F3",
            "color_secondary": "#444" if palette.bg_primary == "#2d2d2d" else "#ddd",
            "color_background": "white",
            # ----------  CONTAINERS  ----------
            "dialog": dialog(palette),
            "container": container(palette),
            "image_preview": image_preview(palette),
            "non_editable_modal": non_editable_modal(palette),
            # ----------  TYPOGRAPHY  ----------
            "label": label(palette),
            "label_small": label_small(palette),
            "label_title": label_title(palette),
            "warning_label": warning_label(palette),
            "action_indicator": action_indicator(palette),
            # ----------  CONTROLS  ----------
            "input": input_field(palette),
            "input_full": input_full(palette),
            "dropdown": dropdown(palette),
            "checkbox": checkbox(palette),
            "radio": radio_button(palette),
            # ----------  BUTTONS  ----------
            "button": neutral_button(
                palette
            ),  # Legacy compatibility - neutral colors for action buttons
            "primary_button": primary_button(palette),
            "secondary_button": secondary_button(palette),
            "close_button": close_button(palette),
            "delete_button": delete_button(palette),
            "send_button": send_button(palette),
            "icon_button": icon_button(palette),
            "icon_small_button": icon_small_button(palette),
            "close_small_button": close_small_button(palette),
            "add_button": add_button(palette),
            "lock_button": lock_button(palette),
            # ----------  NAVIGATION  ----------
            "chat_scroll_area": chat_scroll_area(palette),
            "tray_menu": tray_menu(palette),
            # ----------  FEEDBACK  ----------
            "progress_window": progress_window(palette),
            # ----------  SPECIALIZED  ----------
            "markdown_text_browser_ai": markdown_text_browser_ai(palette),
            "markdown_text_browser_user": markdown_text_browser_user(palette),
            # ----------  LEGACY COMPATIBILITY  ----------
            # These will be removed in future versions as components are migrated
            "copy_button": copy_button(palette),
            "copy_button_success": copy_button_success(palette),
            "response_window_title": label_title(palette),  # Temporary mapping
            "response_window_image_indicator": label_small(palette),  # Temporary mapping
            "response_window_zoom_label": label_small(palette),  # Temporary mapping
            "response_window_copy_hint": label_small(palette),  # Temporary mapping
            "response_window_loading_label": label_title(palette),  # Temporary mapping
            "response_window_input": input_full(palette),  # Temporary mapping
            "response_window_send_button": send_button(palette),  # Temporary mapping
            "response_window_image_section": container(palette),  # Temporary mapping
            "response_window_toggle_button": secondary_button(palette),  # Temporary mapping
            "response_window_header_label": label(palette),  # Temporary mapping
            "response_window_info_label": label_small(palette),  # Temporary mapping
            "response_window_image_display": image_preview(palette),  # Temporary mapping
            "response_window_zoom_button": secondary_button(palette),  # Temporary mapping
            "help_content_label": """
                QLabel {
                    background: transparent;
                    padding: 10px;
                    font-size: 14px;
                }
            """,
            "about_content_label": """
                QLabel {
                    font-size: 14px;
                    color: #e8dcc0;
                    background-color: rgba(45, 45, 45, 0.95);
                    padding: 10px;
                    border-radius: 8px;
                }
            """,
            "about_update_button": primary_button(palette),  # Temporary mapping
            "transparent_background": "QWidget { background: transparent; }",
            "margin_top_10": "QLabel { margin-top: 10px; }",
        }
