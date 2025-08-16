"""
Progress Window for long-running operations like Ollama installation.
"""

import logging
from PySide6 import QtCore, QtWidgets
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QDialog, QVBoxLayout, QLabel, QProgressBar, QPushButton

from ui.ui_utils import get_effective_color_mode


class ProgressWindow(QDialog):
    """
    A progress window with animated loading dots for long-running operations.
    """
    
    # Signal emitted when user cancels the operation
    cancelled = QtCore.Signal()
    
    def __init__(self, title="Opération en cours", message="Veuillez patienter", parent=None):
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
        
    def _setup_ui(self):
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
        self.cancel_button = QPushButton("Annuler")
        self.cancel_button.clicked.connect(self._on_cancel)
        layout.addWidget(self.cancel_button)
        
    def _apply_theme(self):
        """Apply the current theme to the window."""
        current_mode = get_effective_color_mode()
        
        if current_mode == 'dark':
            bg_color = '#2b2b2b'
            text_color = '#ffffff'
            button_bg = '#4CAF50'
            button_hover = '#45a049'
            progress_bg = '#444444'
        else:
            bg_color = '#ffffff'
            text_color = '#333333'
            button_bg = '#008CBA'
            button_hover = '#007095'
            progress_bg = '#f0f0f0'
        
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
        
    def start_animation(self):
        """Start the dots animation."""
        self.timer.start(500)  # Update every 500ms
        
    def stop_animation(self):
        """Stop the dots animation."""
        self.timer.stop()
        
    def _update_dots(self):
        """Update the animated dots."""
        self.dots_count = (self.dots_count + 1) % 4
        dots = "." * self.dots_count
        self.message_label.setText(f"{self.base_message}{dots}")
        
    def update_message(self, message):
        """Update the message text."""
        self.base_message = message
        self.dots_count = 0
        self._update_dots()
        
    def _on_cancel(self):
        """Handle cancel button click."""
        self.cancelled.emit()
        self.close()
        
    def closeEvent(self, event):
        """Handle window close event."""
        self.stop_animation()
        super().closeEvent(event)


class OllamaInstallProgressWindow(ProgressWindow):
    """
    Specialized progress window for Ollama installation.
    """
    
    def __init__(self, parent=None):
        super().__init__(
            title="Installation d'Ollama",
            message="Téléchargement d'Ollama en cours",
            parent=parent
        )
        
    def set_downloading(self):
        """Set the window to downloading state."""
        self.update_message("Téléchargement d'Ollama en cours")
        
    def set_installing(self):
        """Set the window to installing state."""
        self.update_message("Installation d'Ollama en cours")
        
    def set_finishing(self):
        """Set the window to finishing state."""
        self.update_message("Finalisation de l'installation")
