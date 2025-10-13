"""
ButtonEditDialog module
Dialog for editing or creating a button's properties.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from ...config.interfaces import ActionConfigWithName

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp

def _(x):
    return x


class ButtonEditDialog(QDialog):
    """
    Dialog for editing or creating a button's properties
    (name/title, system instruction, open_in_window, etc.).
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        parent: QWidget | None = None,
        button_data: dict | None = None,
        title: str = "Edit Button",
        is_image_context: bool = False,
    ):
        super().__init__(parent)
        self.app = app
        self.is_image_context = is_image_context
        self.button_data = (
            button_data
            if button_data
            else {
                "prefix": "Analyze this image:\n\n"
                if is_image_context
                else "Make this change to the following text:\n\n",
                "instruction": "",
                "icon": "icons/magnifying-glass",
                "open_in_window": False,
            }
        )
        self.setWindowTitle(_("Edit Button"))
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name
        self.name_label = QLabel(_("Button Name:"))
        self.name_label.setStyleSheet(self.app.styles["label"])
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self.app.styles["input"])
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(self.name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        content_type = "image" if self.is_image_context else "selected text"
        self.instruction_label = QLabel(
            _("What should your AI do with your {content_type}? (System Instruction)").format(content_type=content_type)
        )
        self.instruction_label.setStyleSheet(self.app.styles["label"])
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(self.app.styles["input"])
        self.instruction_input.setPlainText(self.button_data.get("instruction", ""))
        self.instruction_input.setMinimumHeight(100)
        if self.is_image_context:
            placeholder = _("""Examples:
    - Extract and translate any text visible in this image.
    - Describe this image in detail.
    - What objects can you see in this image?
    - Analyse the mood or atmosphere of this image.
    - What colors are prominent in this image?
    - Describe this image for someone who cannot see it.""")
        else:
            placeholder = _("""Examples:
    - Fix / improve / explain this code.
    - Make it funny.
    - Add emojis!
    - Roast this!
    - Translate to English.
    - Make the text title case.
    - If it's all caps, make it all small, and vice-versa.
    - Write a reply to this.
    - Analyse potential biases in this news article.""")

        self.instruction_input.setPlaceholderText(placeholder)
        layout.addWidget(self.instruction_label)
        layout.addWidget(self.instruction_input)

        if self.is_image_context:
            # Force chat note for image actions
            self.force_chat_label = QLabel(
                _("<i>Image actions always open in chat window (force chat)</i>")
            )
            self.force_chat_label.setStyleSheet(self.app.styles["label_small"])
            layout.addWidget(self.force_chat_label)
        else:
            # open_in_window options - only for text actions
            self.display_label = QLabel(_("How should your AI response be shown?"))
            self.display_label.setStyleSheet(self.app.styles["label"])
            layout.addWidget(self.display_label)

            self.radio_layout = QHBoxLayout()
            self.replace_radio = QRadioButton(_("Replace the selected text"))
            self.window_radio = QRadioButton(_("In a chat pop-up window"))
            for r in (self.replace_radio, self.window_radio):
                r.setStyleSheet(self.app.styles["radio"])

            self.replace_radio.setChecked(not self.button_data.get("open_in_window", False))
            self.window_radio.setChecked(self.button_data.get("open_in_window", False))

            self.radio_layout.addWidget(self.replace_radio)
            self.radio_layout.addWidget(self.window_radio)
            layout.addLayout(self.radio_layout)

            # Indicator information - only for text actions
            self.indicator_label = QLabel(
                _("<i>A small indicator will be shown on the button: Ⓡ for replace, Ⓒ for chat</i>")
            )
            self.indicator_label.setStyleSheet(self.app.styles["label_small"])
            layout.addWidget(self.indicator_label)

        # OK & Cancel
        btn_layout = QHBoxLayout()
        self.ok_button = QPushButton(_("OK"))
        self.cancel_button = QPushButton(_("Cancel"))
        for btn in (self.ok_button, self.cancel_button):
            btn.setStyleSheet(self.app.styles["button"])

        btn_layout.addWidget(self.ok_button)
        btn_layout.addWidget(self.cancel_button)
        layout.addLayout(btn_layout)

        self.ok_button.clicked.connect(self.accept)
        self.cancel_button.clicked.connect(self.reject)

        self.setStyleSheet(self.app.styles["dialog"])

    def refresh_language(self) -> None:
        """Refresh all text elements to reflect the current language."""
        # Update window title
        self.setWindowTitle(_("Edit Button"))

        # Update labels - they are created in init_ui, so they should exist
        try:
            if hasattr(self, "name_label") and self.name_label:
                self.name_label.setText(_("Button Name:"))

            if hasattr(self, "instruction_label") and self.instruction_label:
                content_type = "image" if self.is_image_context else "selected text"
                self.instruction_label.setText(
                    _("What should your AI do with your {content_type}? (System Instruction)").format(content_type=content_type)
                )

            # Update placeholders
            if hasattr(self, "instruction_input") and self.instruction_input:
                if self.is_image_context:
                    placeholder = _("""Examples:
    - Extract and translate any text visible in this image.
    - Describe this image in detail.
    - What objects can you see in this image?
    - Analyse the mood or atmosphere of this image.
    - What colors are prominent in this image?
    - Describe this image for someone who cannot see it.""")
                else:
                    placeholder = _("""Examples:
    - Fix / improve / explain this code.
    - Make it funny.
    - Add emojis!
    - Roast this!
    - Translate to English.
    - Make the text title case.
    - If it's all caps, make it all small, and vice-versa.
    - Write a reply to this.
    - Analyse potential biases in this news article.""")

                self.instruction_input.setPlaceholderText(placeholder)

            # Update radio buttons and related labels
            if not self.is_image_context:
                if hasattr(self, "display_label") and self.display_label:
                    self.display_label.setText(_("How should your AI response be shown?"))

                if hasattr(self, "replace_radio") and self.replace_radio:
                    self.replace_radio.setText(_("Replace the selected text"))

                if hasattr(self, "window_radio") and self.window_radio:
                    self.window_radio.setText(_("In a chat pop-up window"))

                if hasattr(self, "indicator_label") and self.indicator_label:
                    self.indicator_label.setText(
                        _("<i>A small indicator will be shown on the button: Ⓡ for replace, Ⓒ for chat</i>")
                    )
            else:
                # Update force chat note for image context
                if hasattr(self, "force_chat_label") and self.force_chat_label:
                    self.force_chat_label.setText(
                        _("<i>Image actions always open in chat window (force chat)</i>")
                    )

            # Update buttons
            if hasattr(self, "ok_button") and self.ok_button:
                self.ok_button.setText(_("OK"))

            if hasattr(self, "cancel_button") and self.cancel_button:
                self.cancel_button.setText(_("Cancel"))

        except RuntimeError:
            # Widget might be destroyed, skip refresh
            pass

    def get_button_data(self) -> ActionConfigWithName:
        return {
            "name": self.name_input.text(),
            "prefix": "Analyze this image:\n\n"
            if self.is_image_context
            else "Make this change to the following text:\n\n",
            # Retrieve multiline text
            "instruction": self.instruction_input.toPlainText(),
            "icon": "icons/custom",
            "open_in_window": self.window_radio.isChecked() if not self.is_image_context else True,
        }
