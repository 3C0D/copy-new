"""
Thinking Animation - Manages the animated "Thinking..." indicator.
"""

from PySide6 import QtCore
from PySide6.QtWidgets import QLabel, QLineEdit


def _(x):
    return x


class ThinkingAnimation:
    """Manages the animated thinking indicator with cycling dots"""

    def __init__(self):
        self.timer = QtCore.QTimer()
        self.timer.timeout.connect(self.update_dots)
        self.timer.setInterval(300)

        self.dots_state = 0
        self.dots = ["", ".", "..", "..."]

        self.loading_label: QLabel | None = None
        self.input_field: QLineEdit | None = None
        self.is_image_mode = False

    def set_widgets(
        self,
        loading_label: QLabel | None = None,
        input_field: QLineEdit | None = None,
        is_image_mode: bool = False,
    ) -> None:
        """Set the widgets that will display the animation"""
        self.loading_label = loading_label
        self.input_field = input_field
        self.is_image_mode = is_image_mode

    def update_dots(self) -> None:
        """Update the thinking animation dots with proper cycling"""
        self.dots_state = (self.dots_state + 1) % len(self.dots)
        dots = self.dots[self.dots_state]

        if self.loading_label and self.loading_label.isVisible():
            base_text = _("Analyzing image") if self.is_image_mode else _("Thinking")
            self.loading_label.setText(f"{base_text}{dots}")
        elif self.input_field:
            self.input_field.setPlaceholderText(_("Thinking") + f"{dots}")

    def start(self, initial: bool = False) -> None:
        """Start the thinking animation"""
        self.dots_state = 0

        if initial and self.loading_label:
            base_text = _("Analyzing image") if self.is_image_mode else _("Thinking")
            self.loading_label.setText(base_text)
            self.loading_label.setVisible(True)
        elif self.input_field:
            self.input_field.setPlaceholderText(_("Thinking"))

        self.timer.start()

    def stop(self) -> None:
        """Stop the thinking animation"""
        self.timer.stop()

        if self.loading_label:
            self.loading_label.hide()

        if self.input_field:
            placeholder_text = (
                _("Ask a follow-up question about this image") + "..."
                if self.is_image_mode
                else _("Ask a follow-up question") + "..."
            )
            self.input_field.setPlaceholderText(placeholder_text)
            self.input_field.setEnabled(True)