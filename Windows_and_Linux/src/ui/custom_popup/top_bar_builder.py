"""
TopBarBuilder module
Construit la barre supérieure avec ses composants.
"""

from typing import TYPE_CHECKING

from PySide6.QtCore import Qt
from PySide6.QtGui import QIcon
from PySide6.QtWidgets import QHBoxLayout, QPushButton

from ...ui import ui_utils

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp
    from .custom_popup_window import CustomPopupWindow


class TopBarBuilder:
    """Construit la barre supérieure avec ses composants."""

    def __init__(self, app: "WritingToolsApp", parent: "CustomPopupWindow"):
        self.app = app
        self.parent = parent

    def build(self, layout: QHBoxLayout) -> dict[str, QPushButton]:
        """Construit tous les boutons et retourne un dictionnaire."""
        buttons = {}

        if self.parent.has_sel_text or self.parent.has_image:
            buttons["reset"] = self._create_reset_button()
            buttons["edit"] = self._create_edit_button()
            buttons["edit_close"] = self._create_edit_close_button()

            layout.addWidget(buttons["reset"], 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(buttons["edit"], 0, Qt.AlignmentFlag.AlignLeft)
            layout.addWidget(buttons["edit_close"], 0, Qt.AlignmentFlag.AlignRight)

        buttons["close"] = self._create_close_button()
        layout.addWidget(buttons["close"], 0, Qt.AlignmentFlag.AlignRight)

        return buttons

    def _create_reset_button(self) -> QPushButton:
        btn = QPushButton()
        reset_icon_path = ui_utils.get_icon_path(self.app, "restore", with_theme=True)  # type: ignore
        if reset_icon_path.exists():
            btn.setIcon(QIcon(reset_icon_path.as_posix()))

        btn.setText("")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(self.app.styles["icon_small_button"])
        btn.clicked.connect(self.parent.on_reset_clicked)
        btn.setToolTip("Reset to Default Buttons")
        btn.installEventFilter(self.parent)

        return btn

    def _create_edit_button(self) -> QPushButton:
        btn = QPushButton()
        pencil_icon = ui_utils.get_icon_path(self.app, "pencil", with_theme=True)  # type: ignore
        if pencil_icon.exists():
            btn.setIcon(QIcon(pencil_icon.as_posix()))

        btn.setFixedSize(24, 24)
        btn.setStyleSheet(self.app.styles["icon_small_button"])
        btn.clicked.connect(self.parent.enter_edit_mode)
        btn.setToolTip("Edit Tools Layout")
        btn.installEventFilter(self.parent)

        return btn

    def _create_edit_close_button(self) -> QPushButton:
        btn = QPushButton("×")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(self.app.styles["close_small_button"])
        btn.clicked.connect(self.parent.exit_edit_mode)
        btn.setToolTip("Exit Edit Mode")
        btn.hide()
        btn.installEventFilter(self.parent)

        return btn

    def _create_close_button(self) -> QPushButton:
        btn = QPushButton("×")
        btn.setFixedSize(24, 24)
        btn.setStyleSheet(self.app.styles["close_small_button"])
        btn.clicked.connect(self.parent.close)
        btn.installEventFilter(self.parent)

        return btn
