"""
EditModeController module
Controls the edit mode.
"""

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .custom_popup_window import CustomPopupWindow
    from .widget_visibility_manager import WidgetVisibilityManager


class EditModeController:
    """Controls the edit mode."""

    def __init__(self, window: "CustomPopupWindow", visibility_manager: "WidgetVisibilityManager"):
        self.window = window
        self.visibility_manager = visibility_manager

    def enter_edit_mode(self) -> None:
        self.window.edit_mode = True
        self.visibility_manager.set_edit_mode(True)
        self.window.button_manager.rebuild_grid_layout(force_edit_mode=True)
        self.window.button_manager.add_edit_overlays_to_buttons()

        # Hide components that shouldn't be visible in edit mode
        if self.window.force_chat_widget:
            self.window.force_chat_widget.hide()
        if self.window.update_notice:
            self.window.update_notice.hide()
        if self.window.image_preview:
            self.window.image_preview.hide()

        if self.window.has_image:
            self.window.resize(self.window.width(), 420)

    def exit_edit_mode(self) -> None:
        self.window.edit_mode = False
        self.window.reload_window()
