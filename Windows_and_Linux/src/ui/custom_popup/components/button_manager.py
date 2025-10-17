"""
Button manager component for CustomPopupWindow.
Handles button creation, layout, and management.
"""

from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...ui_utils import ui_utils
from ..draggable_button import DraggableButton

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp


class ButtonManager:
    """Manages the creation and layout of action buttons."""

    def __init__(self, app: "WritingToolsApp", parent_window):
        self.app = app
        self.parent_window = parent_window
        self.button_widgets: list[Any] = []

    def get_actions(self) -> dict[str, Any]:
        """
        Get actions directly from the unified settings system.
        Returns ActionConfig objects, combining text and image actions based on context.
        """
        if self.parent_window.has_image:
            return self.app.settings_manager.image_actions
        else:
            return self.app.settings_manager.actions

    def build_buttons_list(self) -> None:
        """
        Loads actions from unified settings system,
        creates DraggableButton for each (except "Custom"),
        filtering based on whether image is present,
        storing them in self.button_widgets in the same order.
        """

        # Properly delete old button widgets before clearing the list
        for old_button in self.button_widgets:
            if hasattr(old_button, "icon_container") and old_button.icon_container:
                old_button.icon_container.deleteLater()
            if hasattr(old_button, "action_indicator") and old_button.action_indicator:
                old_button.action_indicator.deleteLater()
            old_button.deleteLater()

        self.button_widgets.clear()
        actions = self.get_actions()

        for name, action_config in actions.items():
            if name == "Custom":
                continue

            # Skip empty action names (orphaned buttons from reset)
            if not name or not name.strip():
                continue

            # For image context, only include actions that are relevant to images
            # This prevents text-only actions from appearing when there's an image
            if self.parent_window.has_image:
                # You could add specific filtering logic here if needed
                # For now, include all non-Custom actions for images
                pass

            b = DraggableButton(self.app, self.parent_window, name, name)
            icon_path = ui_utils.get_icon_path(
                self.app, action_config.get("icon", "Not Found"), with_theme=True
            )
            if icon_path.exists():
                b.setIcon(QtGui.QIcon(icon_path.as_posix()))

            # Set action indicator based on open_in_window. Only for text actions.
            if not self.parent_window.has_image:
                open_in_window = action_config.get("open_in_window", True) or False
                b.set_action_indicator(open_in_window)

            # Add tooltip with tool name and description
            tooltip_text = name
            if action_config.get("instruction", None):
                # Truncate long instructions for tooltip
                instruction = action_config.get("instruction", "")
                if instruction:
                    instruction = (
                        instruction[:100] + "..." if len(instruction) > 100 else instruction
                    )
                tooltip_text = f"{name}\n{instruction}"
            b.setToolTip(tooltip_text)

            if not self.parent_window.edit_mode:
                b.clicked.connect(partial(self.parent_window.on_generic_instruction, name))
            self.button_widgets.append(b)

    def rebuild_grid_layout(self, parent_layout=None, force_edit_mode=None) -> None:
        """Rebuild grid layout with consistent sizing and proper Add New button placement."""
        if not parent_layout:
            parent_layout = self.parent_window.background.layout()

        edit_mode_to_use = (
            force_edit_mode if force_edit_mode is not None else self.parent_window.edit_mode
        )

        # Find or create the scroll area
        buttons_scroll = None
        scroll_index = -1

        # Look for existing scroll area
        for i in range(parent_layout.count()):
            item = parent_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QScrollArea):
                buttons_scroll = item.widget()
                scroll_index = i
                break

        # If no scroll area exists, create one (for normal mode)
        if not buttons_scroll and (self.parent_window.has_sel_text or self.parent_window.has_image):
            buttons_scroll = QScrollArea()
            buttons_scroll.setWidgetResizable(True)
            buttons_scroll.setFrameShape(QFrame.Shape.NoFrame)  # No border
            buttons_scroll.setMaximumHeight(250)
            buttons_scroll.setStyleSheet(self.app.styles["transparent_background"]("QScrollArea"))

            buttons_widget = QWidget()
            buttons_widget.setStyleSheet(self.app.styles["transparent_background"])
            buttons_layout = QVBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(5)

            buttons_scroll.setWidget(buttons_widget)
            parent_layout.addWidget(buttons_scroll)
            scroll_index = parent_layout.count() - 1

        # Clean up existing content in scroll area
        if buttons_scroll and isinstance(buttons_scroll, QScrollArea):
            buttons_widget = buttons_scroll.widget()
            if buttons_widget:
                buttons_layout = buttons_widget.layout()
                if buttons_layout:
                    self.clear_layout(buttons_layout)

                    # Create and populate grid
                    grid = QGridLayout()
                    grid.setSpacing(10)
                    grid.setColumnMinimumWidth(0, 120)
                    grid.setColumnMinimumWidth(1, 120)

                    # Add buttons to grid
                    row = 0
                    col = 0
                    for b in self.button_widgets:
                        grid.addWidget(b, row, col)
                        col += 1
                        if col > 1:
                            col = 0
                            row += 1

                    if isinstance(buttons_layout, (QVBoxLayout, QHBoxLayout)):
                        buttons_layout.addLayout(grid)

        # Remove existing "Add New" button from main layout
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if widget == self.parent_window.add_new_button:
                    parent_layout.removeWidget(widget)
                    widget.deleteLater()
                    self.parent_window.add_new_button = None

        # Add "Add New" button outside scroll area (only in edit mode & only if we have text or image)
        if edit_mode_to_use and (self.parent_window.has_sel_text or self.parent_window.has_image):
            self.parent_window.add_new_button = QPushButton()
            self.parent_window.add_new_button.setText("+ Add New")
            self.parent_window.add_new_button.setStyleSheet(self._get_add_button_style())
            self.parent_window.add_new_button.clicked.connect(
                self.parent_window.add_new_button_clicked
            )

            if isinstance(parent_layout, (QVBoxLayout, QHBoxLayout)):
                if scroll_index >= 0:
                    parent_layout.insertWidget(scroll_index + 1, self.parent_window.add_new_button)
                else:
                    parent_layout.addWidget(self.parent_window.add_new_button)

    def clear_layout(self, layout) -> None:
        """Clear all items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                # Don't delete button widgets, just remove them
                if item.widget() not in self.button_widgets:
                    item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()

    def _get_add_button_style(self) -> str:
        """Get stylesheet for Add New button."""
        return self.app.styles["add_button"]

    def remove_button_from_ui(self, key: str) -> None:
        """Remove a button from the UI by its key."""
        for btn in self.button_widgets[:]:
            if btn.key == key:
                if hasattr(btn, "icon_container") and btn.icon_container:
                    btn.icon_container.deleteLater()
                btn.deleteLater()
                self.button_widgets.remove(btn)
                break

    def add_edit_overlays_to_buttons(self) -> None:
        """Add edit overlays to all buttons when entering edit mode."""
        for btn in self.button_widgets:
            self.add_edit_delete_icons(btn)

        # Rebuild grid layout to show edit mode
        self.rebuild_grid_layout(force_edit_mode=True)

    def add_edit_delete_icons(self, btn) -> None:
        """Add edit/delete icons as overlays with proper spacing."""
        if hasattr(btn, "icon_container") and btn.icon_container:
            btn.icon_container.deleteLater()

        btn.icon_container = QWidget(btn)
        btn.icon_container.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
        )

        btn.icon_container.setGeometry(0, 0, btn.width(), btn.height())

        circle_style = self.app.styles["icon_button"]

        # Create edit icon (top-left)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(3, 3, 16, 16)

        pencil_icon = ui_utils.get_icon_path(self.app, "pencil", with_theme=True)
        if pencil_icon.exists():
            edit_btn.setIcon(QtGui.QIcon(pencil_icon.as_posix()))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.parent_window.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (top-right)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, 3, 16, 16)
        del_icon = ui_utils.get_icon_path(self.app, "trash", with_theme=True)
        if del_icon.exists():
            delete_btn.setIcon(QtGui.QIcon(del_icon.as_posix()))
        delete_btn.setStyleSheet(circle_style)
        delete_btn.clicked.connect(partial(self.parent_window.delete_button_clicked, btn))
        delete_btn.show()

        btn.icon_container.raise_()
        btn.icon_container.show()

    def update_json_from_grid(self) -> None:
        """
        Called after a drop reorder. Reflect the new order in unified settings,
        so that user's custom arrangement persists.
        """
        # Get current actions (text or image based on context)
        current_actions = self.get_actions()

        # Create new ordered dict based on button order
        new_actions = {}

        # Add Custom first if it exists
        if "Custom" in current_actions:
            new_actions["Custom"] = current_actions["Custom"]

        # Add buttons in their current order
        for b in self.button_widgets:
            if b.key in current_actions:
                new_actions[b.key] = current_actions[b.key]

        # Update settings (auto-saves) - use appropriate storage based on context
        if self.parent_window.has_image:
            self.app.settings_manager.image_actions = new_actions
        else:
            self.app.settings_manager.actions = new_actions
        self.app._logger.debug("Button order updated in unified settings")

        self.app._logger.debug("Button order updated in unified settings")
