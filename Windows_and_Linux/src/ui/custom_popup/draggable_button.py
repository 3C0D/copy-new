"""
DraggableButton module
Draggable button widget for the custom popup window.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import QApplication, QPushButton, QWidget

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .custom_popup_window import CustomPopupWindow


class DraggableButton(QPushButton):
    def __init__(
        self, app: "WritingToolsApp", parent_popup: "CustomPopupWindow", key: str, text: str
    ):
        super().__init__(text, parent_popup)
        self.app = app
        self.popup: CustomPopupWindow = parent_popup
        self.key: str = key
        self.drag_start_position: QtCore.QPoint | None = None
        self.setAcceptDrops(True)
        self.icon_container: QWidget | None = None
        self.action_indicator: QtWidgets.QLabel | None = None

        # Enable mouse tracking and hover events, and styled background
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed)
        self.setFixedSize(120, 40)

        # Define base style using the dynamic property instead of the :hover pseudo-class
        self.setStyleSheet(self.app.styles["button"])

    def refresh_button_style(self) -> None:
        """Refresh the button style when color mode changes."""
        self.setStyleSheet(self.app.styles["button"])

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        # Only update the hover property if NOT in edit mode.
        if not self.popup.edit_mode:
            self.setProperty("hover", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if not self.popup.edit_mode:
            self.setProperty("hover", False)
            self.style().unpolish(self)
            self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            if self.popup.edit_mode:
                self.drag_start_position = e.pos()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, arg__1: QtGui.QMouseEvent) -> None:
        if not (arg__1.buttons() & Qt.MouseButton.LeftButton) or not self.drag_start_position:
            return

        distance = (arg__1.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        if self.popup.edit_mode:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            idx = self.popup.button_widgets.index(self)
            mime_data.setData("application/x-button-index", str(idx).encode())
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(arg__1.pos())

            self.drag_start_position = None
            _ = drag.exec_(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if self.popup.edit_mode and event.mimeData().hasFormat("application/x-button-index"):
            event.acceptProposedAction()
            self.setStyleSheet(
                self.app.styles["button"]
                + """
                QPushButton {
                    border: 2px dashed #666;
                }
                """,
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        self.setStyleSheet(self.app.styles["button"])
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if not self.popup.edit_mode or not event.mimeData().hasFormat("application/x-button-index"):
            event.ignore()
            return

        mime_data = event.mimeData().data("application/x-button-index")
        source_idx = int(bytes(mime_data).decode())
        target_idx = self.popup.button_widgets.index(self)

        if source_idx != target_idx:
            bw = self.popup.button_widgets
            bw[source_idx], bw[target_idx] = bw[target_idx], bw[source_idx]
            self.popup.rebuild_grid_layout()
            self.popup.update_json_from_grid()

        self.setStyleSheet(self.app.styles["button"])
        event.setDropAction(Qt.DropAction.MoveAction)
        event.acceptProposedAction()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle resize events to reposition UI elements."""
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())
        if self.action_indicator:
            self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)

    def set_action_indicator(self, open_in_window: bool, is_image_action: bool | None) -> None:
        """Set the action indicator (Ⓡ or Ⓒ) based on action type."""
        if is_image_action:
            return

        if self.action_indicator:
            self.action_indicator.deleteLater()

        self.action_indicator = QtWidgets.QLabel(self)

        indicator_text = "Ⓒ" if open_in_window else "Ⓡ"

        self.action_indicator.setText(indicator_text)
        self.action_indicator.setStyleSheet(self.app.styles["action_indicator"])
        self.action_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)
        self.action_indicator.show()
