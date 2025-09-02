"""
Writing Tools - NonEditableModal module
Used on non editable text selections, like a web page or PDF document.
"""

import logging
from typing import TYPE_CHECKING

import markdown2
import pyperclip
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QApplication,
    QDialog,
    QHBoxLayout,
    QPushButton,
    QTextBrowser,
    QVBoxLayout,
)

from ui.ThemeManager import ThemeAwareMixin, theme_manager
from ui.ui_utils import get_effective_color_mode

if TYPE_CHECKING:
    from WritingToolApp import WritingToolApp


def _(x):
    return x


class NonEditableModal(QDialog, ThemeAwareMixin):
    """Modal window to display transformed text when pasting fails."""

    def __init__(self, app: "WritingToolApp", transformed_text: str | None):
        QDialog.__init__(self)
        self.app = app
        self.transformed_text = transformed_text

        # Window with standard controls (minimize/close) and stay on top
        # self.setWindowFlags(
        #     Qt.WindowType.Dialog
        #     | Qt.WindowType.WindowStaysOnTopHint,
        # )
        self.setModal(True)

        # Fixed size
        self.setFixedSize(600, 400)

        self.setup_ui()
        self.apply_styles(get_effective_color_mode())

        # Register for theme changes
        self.register_for_theme_changes()

        # Center on screen
        self.move(
            QApplication.primaryScreen().geometry().center() - self.rect().center(),
        )

    def setup_ui(self) -> None:
        """Setup the user interface"""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(16, 16, 16, 16)
        layout.setSpacing(12)

        # Window controls at the top
        controls_layout = QHBoxLayout()
        controls_layout.addStretch()

        # Minimize button
        self.minimize_button = QPushButton("─")
        self.minimize_button.setFixedSize(36, 36)
        self.minimize_button.clicked.connect(self.showMinimized)
        self.minimize_button.setToolTip(_("Minimize"))

        # Close button
        self.close_button = QPushButton("✕")
        self.close_button.setFixedSize(36, 36)
        self.close_button.clicked.connect(self.close)
        self.close_button.setToolTip(_("Close"))

        controls_layout.addWidget(self.minimize_button)
        controls_layout.addWidget(self.close_button)
        layout.addLayout(controls_layout)

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

        # Copy button
        self.copy_button = QPushButton("📋")
        self.copy_button.setFixedSize(36, 36)
        self.copy_button.clicked.connect(self.copy_text)
        self.copy_button.setToolTip(_("Copy text"))

        copy_layout.addWidget(self.copy_button)
        layout.addLayout(copy_layout)

        self.copy_button.setFocus()

    def apply_styles(self, current_mode: str) -> None:
        """Apply theme styles"""
        is_dark = current_mode == "dark"

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

    def register_for_theme_changes(self) -> None:
        """Register this modal for theme change notifications."""
        try:
            theme_manager.register_widget(self)
            theme_manager.theme_changed.connect(self.refresh_theme)
        except ImportError:
            # ThemeManager not available, skip registration
            pass

    def refresh_theme(self, new_mode: str) -> None:
        """Refresh the modal's theme when color mode changes."""
        if new_mode is None:
            new_mode = get_effective_color_mode()
        self.apply_styles(new_mode)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle window close event and unregister from theme manager."""
        try:
            theme_manager.unregister_widget(self)
        except ImportError:
            pass
        super().closeEvent(event)

    @Slot()
    def copy_text(self) -> None:
        """Copy the transformed text to clipboard"""
        try:
            pyperclip.copy(self.transformed_text or "")
            self.copy_button.setText("✓")
            QtCore.QTimer.singleShot(1000, lambda: self.copy_button.setText("📋"))
        except Exception as e:
            logging.exception(f"Error copying text: {e}")

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None: # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle key press events"""
        if event.key() == Qt.Key.Key_Escape:
            self.close()
        elif (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ControlModifier
        ):
            self.copy_text()
        else:
            super().keyPressEvent(event)


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
