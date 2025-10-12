"""
WidgetVisibilityManager module
Manages widget visibility according to the edit mode.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom_popup_window import CustomPopupWindow


class WidgetVisibilityManager:
    """Manages widget visibility according to the mode."""

    def __init__(self, window: "CustomPopupWindow"):
        self.window = window

    def set_edit_mode(self, enabled: bool) -> None:
        """Configures all widgets for edit mode."""
        visibility_map = {
            "edit_button": not enabled,
            "close_button": not enabled,
            "reset_button": enabled,
            "edit_close_button": enabled,
            "drag_label": enabled,
            "input_area": not enabled,
            "force_chat_area": not enabled and self.window.has_sel_text,
            "update_label": not enabled,
            "image_preview_container": not enabled and self.window.has_image,
        }

        for widget_name, should_show in visibility_map.items():
            widget = getattr(self.window, widget_name, None)
            if widget:
                widget.setVisible(should_show)
