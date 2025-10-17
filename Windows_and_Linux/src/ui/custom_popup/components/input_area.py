"""
Input area component for CustomPopupWindow.
Handles the input field and send button.
"""

from typing import TYPE_CHECKING

from PySide6 import QtGui
from PySide6.QtWidgets import QHBoxLayout, QLineEdit, QPushButton, QWidget

from ...ui_utils import ui_utils

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp


class InputArea(QWidget):
    """Input area widget containing text input and send button."""

    def __init__(self, app: "WritingToolsApp", has_sel_text: bool, has_image: bool):
        super().__init__()
        self.app = app
        self.has_sel_text = has_sel_text
        self.has_image = has_image
        self.custom_input: QLineEdit | None = None
        self.send_button: QPushButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the input area layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(8)

        # Create input field
        self._create_custom_input(layout)
        # Create send button
        self._create_send_button(layout)

    def _create_custom_input(self, layout: QHBoxLayout) -> None:
        """Create the custom input text field."""
        self.custom_input = QLineEdit()
        placeholder = (
            _("Describe your change...")
            if self.has_sel_text
            else _("Ask anything about this image...")
            if self.has_image
            else _("Ask your AI...")
        )
        self.custom_input.setPlaceholderText(placeholder)
        self.custom_input.setStyleSheet(self._get_input_style())
        layout.addWidget(self.custom_input)

    def _create_send_button(self, layout: QHBoxLayout) -> None:
        """Create the send button for the input area."""
        self.send_button = QPushButton()
        send_icon = ui_utils.get_icon_path(self.app, "send", with_theme=True)

        self.send_button.setStyleSheet(self._get_send_button_style())
        # Use a fallback size if self.custom_input is None
        input_height = self.custom_input.sizeHint().height() if self.custom_input else 32
        self.send_button.setFixedSize(input_height, input_height)
        if send_icon.exists():
            self.send_button.setIcon(QtGui.QIcon(send_icon.as_posix()))
        layout.addWidget(self.send_button)

    def _get_input_style(self) -> str:
        """Get the styling for input elements."""
        return self.app.styles["input_full"]

    def _get_send_button_style(self) -> str:
        """Get stylesheet for send button."""
        return self.app.styles["send_button"]

    def get_input_text(self) -> str:
        """Get the current text from the input field."""
        return self.custom_input.text() if self.custom_input else ""

    def set_focus(self) -> None:
        """Set focus to the input field."""
        if self.custom_input:
            self.custom_input.setFocus()

    def connect_send_signal(self, callback) -> None:
        """Connect the send button clicked signal."""
        if self.send_button:
            self.send_button.clicked.connect(callback)
        if self.custom_input:
            self.custom_input.returnPressed.connect(callback)


def _(x):
    return x
