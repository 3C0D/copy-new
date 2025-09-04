"""
Progress Window for long-running operations like Ollama installation.
"""

from PySide6 import QtCore, QtGui
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import (
    QDialog,
    QLabel,
    QProgressBar,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ui.ui_utils import get_color_mode


class ProgressWindow(QDialog):
    """
    A progress window with animated loading dots for long-running operations.
    """

    # Signal emitted when user cancels the operation
    cancelled = QtCore.Signal()

    def __init__(
        self,
        title: str = "Operation in progress",
        message: str = "Please wait",
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.setWindowTitle(title)
        self.setModal(True)
        self.setFixedSize(400, 150)

        # Animation state
        self.dots_count = 0
        self.base_message = message
        self.timer = QTimer()
        self.timer.timeout.connect(self._update_dots)

        self._setup_ui()
        self._apply_theme()

    def _setup_ui(self) -> None:
        """Setup the UI components."""
        layout = QVBoxLayout(self)
        layout.setSpacing(20)
        layout.setContentsMargins(30, 30, 30, 30)

        # Message label with animated dots
        self.message_label = QLabel(self.base_message)
        self.message_label.setWordWrap(True)
        self.message_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(self.message_label)

        # Progress bar (indeterminate)
        self.progress_bar = QProgressBar()
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        layout.addWidget(self.progress_bar)

        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)

    def _apply_theme(self) -> None:
        """Apply the current theme to the window."""
        current_mode = get_color_mode()

        if current_mode == "dark":
            bg_color = "#2b2b2b"
            text_color = "#ffffff"
            button_bg = "#4CAF50"
            button_hover = "#45a049"
            progress_bg = "#444444"
        else:
            bg_color = "#ffffff"
            text_color = "#333333"
            button_bg = "#008CBA"
            button_hover = "#007095"
            progress_bg = "#f0f0f0"

        self.setStyleSheet(f"""
            QDialog {{
                background-color: {bg_color};
                color: {text_color};
            }}
            QLabel {{
                font-size: 14px;
                color: {text_color};
            }}
            QPushButton {{
                background-color: {button_bg};
                color: white;
                padding: 8px 16px;
                font-size: 12px;
                border: none;
                border-radius: 4px;
            }}
            QPushButton:hover {{
                background-color: {button_hover};
            }}
            QProgressBar {{
                background-color: {progress_bg};
                border: 1px solid #cccccc;
                border-radius: 4px;
                text-align: center;
            }}
            QProgressBar::chunk {{
                background-color: {button_bg};
                border-radius: 3px;
            }}
        """)

    def start_animation(self) -> None:
        """Start the dots animation."""
        self.timer.start(500)  # Update every 500ms

    def stop_animation(self) -> None:
        """Stop the dots animation."""
        self.timer.stop()

    def _update_dots(self) -> None:
        """Update the animated dots."""
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.message_label.setText(f"{self.base_message}{dots}")

    def update_message(self, message: str) -> None:
        """Update the message text."""
        self.base_message = message
        self.dots_count = 0
        self._update_dots()

    def _on_cancel(self) -> None:
        """Handle cancel button click."""
        self.cancelled.emit()
        self.close()

    def closeEvent(self, arg__1: QtGui.QCloseEvent) -> None:
        """Handle window close event."""
        self.stop_animation()
        super().closeEvent(arg__1)


class OllamaInstallProgressWindow(ProgressWindow):
    """
    Specialized progress window for Ollama installation.
    """

    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(
            title="Ollama Installation",
            message="Ollama download in progress",
            parent=parent,
        )

    def set_downloading(self) -> None:
        """Set the window to downloading state."""
        self.update_message("Ollama download in progress")

    def set_installing(self) -> None:
        """Set the window to installing state."""
        self.update_message("Ollama installation in progress")

    def set_finishing(self) -> None:
        """Set the window to finishing state."""
        self.update_message("Finishing Ollama installation")
