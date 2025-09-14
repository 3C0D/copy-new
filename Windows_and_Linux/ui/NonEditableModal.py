"""
Writing Tools - NonEditableModal module
Used on non editable text selections, like a web page or PDF document.
"""

import logging
from typing import TYPE_CHECKING

import markdown2
import pyperclip
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from ui.ui_utils import ThemedWidget

if TYPE_CHECKING:
    from WritingToolApp import WritingToolApp


def _(x):
    return x


class NonEditableModal(ThemedWidget):
    """Modal window to display transformed text when pasting fails."""

    # Signal    emitted when window is closed (not when proceeding to next step)
    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolApp", transformed_text: str | None):
        super().__init__(app)
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.transformed_text = transformed_text

        self._setup_window()
        self.setup_ui()
        self.apply_styles(self.app.settings_manager.color_mode)

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.clean_TitleBar()
        # Fixed size
        self.setMinimumSize(600, 300)
        self.center_on_screen()

    def setup_ui(self) -> None:
        """Setup the user interface"""
        # Use the background widget from ThemedWidget
        layout = QVBoxLayout(self.background)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Text display area
        self.text_display = QTextBrowser()
        self.text_display.setReadOnly(True)
        self.text_display.setOpenExternalLinks(True)

        # Convert markdown to HTML
        html_content = markdown2.markdown(
            self.transformed_text or "",
            extras=["fenced-code-blocks", "tables"],
        )
        self.text_display.setHtml(html_content)
        layout.addWidget(self.text_display)

        # Copy button at the bottom
        copy_layout = QHBoxLayout()
        copy_layout.addStretch()

        # Copy button with shortcut indication
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(36, 36)
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setToolTip(_("Copy text to clipboard\nShortcut: Ctrl+R"))

        copy_layout.addWidget(self.copy_button)
        layout.addLayout(copy_layout)

        self.copy_button.setFocus()

    def apply_styles(self, current_mode: str) -> None:
        """Apply theme styles"""
        is_dark = current_mode == "dark"

        if is_dark:
            self.setStyleSheet(
                """
                QWidget {
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
                QWidget {
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

    def refresh_theme(self) -> None:
        """Refresh the modal's theme when color mode changes."""
        new_mode = self.app.settings_manager.color_mode
        self.apply_styles(new_mode)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle window close event."""
        self.close_signal.emit()
        super().closeEvent(event)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle key press events for this modal."""
        if (
            event.key() == QtCore.Qt.Key.Key_R
            and event.modifiers() == QtCore.Qt.KeyboardModifier.ControlModifier
        ):
            # Ctrl+R to copy text
            self.copy_text()
        else:
            # Let parent handle other keys (including Escape)
            super().keyPressEvent(event)

    @Slot()
    def copy_text(self) -> None:
        """Copy the transformed text to clipboard"""
        try:
            pyperclip.copy(self.transformed_text or "")
            self.copy_button.setText("✓")
            QtCore.QTimer.singleShot(1000, lambda: self.copy_button.setText("📋"))
        except Exception as e:
            self._logger.exception(f"Error copying text: {e}")


# Example usage for testing
if __name__ == "__main__":
    from WritingToolApp import WritingToolApp

    app = QApplication([])
    writing_app = WritingToolApp(None)

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

    modal = NonEditableModal(writing_app, test_text)
    modal.show()

    app.exec()
