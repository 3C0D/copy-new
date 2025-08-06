import logging

import markdown2
import pyperclip
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt, Slot

# from ui.ui_utils import colorMode

_ = lambda x: x


class NonEditableModal(QtWidgets.QDialog):
    """Modal window to display transformed text when pasting fails."""

    def __init__(self, app, transformed_text):
        super().__init__()
        self.app = app
        self.transformed_text = transformed_text

        # Frameless window, always on top
        self.setWindowFlags(
            Qt.WindowType.Dialog | Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint,
        )
        self.setModal(True)

        # Fixed size
        self.setFixedSize(600, 400)

        self.setup_ui()
        self.apply_styles()

        # Center on screen
        self.move(
            QtWidgets.QApplication.primaryScreen().geometry().center() - self.rect().center(),
        )

    def setup_ui(self):
        """Setup the user interface"""
        layout = QtWidgets.QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Text display area
        self.text_display = QtWidgets.QTextBrowser()
        self.text_display.setReadOnly(True)
        self.text_display.setOpenExternalLinks(True)

        # Convert markdown to HTML
        html_content = markdown2.markdown(
            self.transformed_text,
            extras=["fenced-code-blocks", "tables"],
        )
        self.text_display.setHtml(html_content)
        layout.addWidget(self.text_display)

        # Buttons
        button_layout = QtWidgets.QHBoxLayout()
        button_layout.addStretch()

        # Copy button
        self.copy_button = QtWidgets.QPushButton("📋")
        self.copy_button.setFixedSize(36, 36)
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setToolTip(_("Copy text"))

        # Close button
        self.close_button = QtWidgets.QPushButton("✕")
        self.close_button.setFixedSize(36, 36)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip(_("Close"))

        button_layout.addWidget(self.copy_button)
        button_layout.addWidget(self.close_button)
        layout.addLayout(button_layout)

        self.copy_button.setFocus()

    def apply_styles(self):
        """Apply theme styles"""
        # Direct method through Qt
        is_dark = self.app.palette().color(QtGui.QPalette.ColorRole.Window).lightness() < 128
        # is_dark = colorMode == "dark"
        # is_dark = False

        if is_dark:
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #2a2a2a;
                    border: 1px solid #404040;
                    border-radius: 8px;
                }
                QTextBrowser {
                    background-color: #1e1e1e;
                    color: #ffffff;
                    border: 1px solid #404040;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton {
                    background-color: #404040;
                    border: none;
                    border-radius: 4px;
                    color: #ffffff;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #4a9eff;
                }
            """,
            )
        else:
            self.setStyleSheet(
                """
                QDialog {
                    background-color: #ffffff;
                    border: 1px solid #d0d0d0;
                    border-radius: 8px;
                }
                QTextBrowser {
                    background-color: #f5f5f5;
                    color: #000000;
                    border: 1px solid #d0d0d0;
                    border-radius: 4px;
                    padding: 8px;
                }
                QPushButton {
                    background-color: #f0f0f0;
                    border: none;
                    border-radius: 4px;
                    color: #000000;
                    font-size: 16px;
                }
                QPushButton:hover {
                    background-color: #4a9eff;
                    color: #ffffff;
                }
            """,
            )

    @Slot()
    def copy_text(self):
        """Copy the transformed text to clipboard"""
        try:
            pyperclip.copy(self.transformed_text)
            self.copy_button.setText("✓")
            QtCore.QTimer.singleShot(1000, lambda: self.copy_button.setText("📋"))
        except Exception as e:
            logging.exception(f"Error copying text: {e}")

    def keyPressEvent(self, event):
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif event.key() == Qt.Key.Key_Return and event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            self.copy_text()
        else:
            super().keyPressEvent(event)


# Example usage for testing
if __name__ == "__main__":
    app = QtWidgets.QApplication([])

    # Test text with markdown
    test_text = """# Test Title

Here is a **bold text** and an *italic text*.

## Liste
- Item 1
- Item 2
- Item 3

```python
def hello():
    print("Hello World!")
```

[Link Google](https://google.com)
"""

    modal = NonEditableModal(app, test_text)
    modal.show()

    app.exec()
