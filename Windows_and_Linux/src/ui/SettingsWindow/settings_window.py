"""
settings_window.py

Main SettingsWindow class - Simplified after onboarding removal.
All settings auto-save when changed.
"""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QApplication,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp

from ..ui_utils import ThemedWidget
from .general_settings import GeneralSettings
from .provider_settings import ProviderSettings


def _(x):
    return x


class SettingsWindow(ThemedWidget):
    """
    Simplified settings window with all options visible.
    Auto-saves all changes immediately.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolsApp"):
        super().__init__(app)
        self.app = app
        self._logger = logging.getLogger(__name__)

        # Store current background theme
        self.current_background_theme = self.app.settings_manager.background_theme or "gradient"

        # Set background theme
        if self.background is not None:
            self.background.background_theme = self.current_background_theme

        # Initialize UI components
        self.general_settings = None
        self.provider_settings = None
        self.close_button = None

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface with scroll support."""
        self.setWindowTitle(_("Settings"))
        self.min_width = 700
        self.min_height = 550
        self._calculate_window_size()

        main_layout = QVBoxLayout(self.background)

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create scrollable content widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Title
        title_label = QLabel(_("Settings"))
        title_label.setObjectName("title_label")
        title_label.setStyleSheet(self.app.styles["label_title"])
        content_layout.addWidget(
            title_label,
            alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
        )

        # General settings section
        self.general_settings = GeneralSettings(self.app, self)
        content_layout.addWidget(self.general_settings)

        # Visual separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Provider settings section
        self.provider_settings = ProviderSettings(self.app, self)
        content_layout.addWidget(self.provider_settings)

        # Final separator
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Finalize scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Add close button
        self.add_close_button(main_layout)

        # Set focus
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def add_close_button(self, main_layout: QVBoxLayout) -> None:
        """Add close button at the bottom."""
        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)
        button_layout.addStretch()

        self.close_button = QPushButton(_("Close Settings"))
        self.close_button.setFixedSize(150, 40)
        self.close_button.setStyleSheet(self.app.styles["close_button"])
        self.close_button.clicked.connect(self.save_and_close)

        button_layout.addWidget(self.close_button)
        main_layout.addWidget(button_container)

    def save_and_close(self) -> None:
        """Save settings and close window."""
        self.save_all_settings()
        self.close()

    def save_all_settings(self) -> None:
        """Save all current settings."""
        # Save general settings
        if self.general_settings:
            self.general_settings.save_settings()

        # Save provider settings
        if self.provider_settings:
            self.provider_settings.save_settings()

        # Re-register hotkey
        self.app.hotkey_manager.register_hotkey()

        self._logger.debug("All settings saved")

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        """Handle focus out event - manage focus carefully for dropdowns."""
        super().focusOutEvent(event)
        focused_widget = QApplication.focusWidget()
        if focused_widget and not self.isAncestorOf(focused_widget):
            QtCore.QTimer.singleShot(500, self.regain_focus_if_needed)

    def regain_focus_if_needed(self) -> None:
        """Regain focus only when appropriate."""
        if not self.isVisible():
            return

        # Don't steal focus from dropdowns
        focused_widget = QApplication.focusWidget()
        if focused_widget and isinstance(focused_widget, QComboBox):
            return

        # Check for open dropdown popups
        for widget in QApplication.allWidgets():
            if isinstance(widget, QComboBox) and widget.view().isVisible():
                return

        # Only regain focus if genuinely lost
        if not self.hasFocus() and not self.isAncestorOf(QApplication.focusWidget()):
            self.raise_()
            self.activateWindow()

    def refresh_theme(self) -> None:
        """Refresh theme for all components."""
        # Update title
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setStyleSheet(self.app.styles["label_title"])

        # Update close button
        if self.close_button:
            self.close_button.setStyleSheet(self.app.styles["close_button"])

        # Refresh component themes
        if self.general_settings:
            self.general_settings.refresh_theme()

        if self.provider_settings:
            self.provider_settings.refresh_theme()

        # Update system tray
        if self.app.systray_manager.tray_menu:
            self.app.systray_manager.apply_tray_menu_styles(self.app.systray_manager.tray_menu)

        # Refresh background
        super().refresh_theme()

    def refresh_language(self) -> None:
        """Refresh language for all components."""
        self.setWindowTitle(_("Settings"))

        # Update title
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setText(_("Settings"))

        # Update close button
        if self.close_button:
            self.close_button.setText(_("Close Settings"))

        # Refresh component languages
        if self.general_settings:
            self.general_settings.refresh_language()

        if self.provider_settings:
            self.provider_settings.refresh_language()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.save_and_close()
        else:
            super().keyPressEvent(event)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event."""
        super().closeEvent(event)
        # Update references in both managers
        self.app.systray_manager.settings_window = None
        self._logger.debug("SettingsWindow closing")
