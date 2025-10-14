"""
Styles module for Writing Tools.
Provides centralized, modular theming system.
"""

from .colors import DARK_PALETTE, LIGHT_PALETTE, ColorPalette
from .containers import container, dialog, image_preview, non_editable_modal, transparent_background
from .controls import (
    add_button,
    checkbox,
    close_button,
    close_small_button,
    copy_button,
    copy_button_success,
    delete_button,
    dropdown,
    icon_small_button,
    input_field,
    input_full,
    lock_button,
    neutral_button,
    primary_button,
    radio_button,
    secondary_button,
    send_button,
)
from .feedback import progress_window
from .navigation import chat_scroll_area, tray_menu
from .specialized import icon_button, markdown_text_browser_ai, markdown_text_browser_user
from .typography import action_indicator, label, label_small, label_title, warning_label

__all__ = [
    # Colors
    "ColorPalette",
    "DARK_PALETTE",
    "LIGHT_PALETTE",
    # Containers
    "container",
    "dialog",
    "image_preview",
    "non_editable_modal",
    "transparent_background",
    # Controls
    "add_button",
    "checkbox",
    "close_button",
    "close_small_button",
    "copy_button",
    "copy_button_success",
    "delete_button",
    "dropdown",
    "icon_small_button",
    "input_field",
    "input_full",
    "lock_button",
    "neutral_button",
    "primary_button",
    "radio_button",
    "secondary_button",
    "send_button",
    # Feedback
    "progress_window",
    # Navigation
    "chat_scroll_area",
    "tray_menu",
    # Specialized
    "icon_button",
    "markdown_text_browser_ai",
    "markdown_text_browser_user",
    # Typography
    "action_indicator",
    "label",
    "label_small",
    "label_title",
    "warning_label",
]
