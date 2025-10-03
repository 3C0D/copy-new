"""
WidgetVisibilityManager module
Gère la visibilité des widgets selon le mode d'édition.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom_popup_window import CustomPopupWindow


class WidgetVisibilityManager:
    """Gère la visibilité des widgets selon le mode."""

    def __init__(self, window: "CustomPopupWindow"):
        self.window = window

    def set_edit_mode(self, enabled: bool) -> None:
        """Configure tous les widgets pour le mode édition."""
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
