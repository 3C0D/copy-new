"""
Force chat toggle component for CustomPopupWindow.
Handles the Force Chat toggle switch and lock functionality.
"""

from typing import TYPE_CHECKING

from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QWidget

from ..toggle_switch import ToggleSwitch

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp


class ForceChatWidget(QWidget):
    """Force Chat toggle widget with lock functionality."""

    def __init__(self, app: "WritingToolsApp"):
        super().__init__()
        self.app = app
        self.force_chat_toggle: ToggleSwitch | None = None
        self.force_chat_lock: QPushButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the force chat widget layout."""
        layout = QHBoxLayout(self)
        layout.setContentsMargins(5, 2, 5, 2)
        layout.setSpacing(6)

        # Label
        label = QLabel("Force Chat:")
        label.setStyleSheet(self.app.styles["label_small"])

        # Check if we should restore the locked state
        force_chat_locked = getattr(self.app.settings_manager, "force_chat_locked", False)
        force_chat_enabled = getattr(self.app.settings_manager, "force_chat_enabled", False)

        # Force Chat toggle switch (custom widget with sliding animation)
        self.force_chat_toggle = ToggleSwitch(self.app)

        if force_chat_locked:
            self.force_chat_toggle.setChecked(force_chat_enabled)

        # Lock button (cadenas) - restore saved state
        self.force_chat_lock = QPushButton("🔓")
        self.force_chat_lock.setCheckable(True)
        self.force_chat_lock.setChecked(force_chat_locked)  # Restore saved state
        self.force_chat_lock.setFixedSize(20, 20)
        self.force_chat_lock.setToolTip("Lock this setting to keep it between uses")

        # Update lock icon based on state
        self.update_lock_icon()

        self.force_chat_lock.setStyleSheet(self.app.styles["lock_button"])

        # Add to layout
        layout.addWidget(label)
        layout.addWidget(self.force_chat_toggle)
        layout.addWidget(self.force_chat_lock)
        layout.addStretch()

    def update_lock_icon(self) -> None:
        """Update the lock icon based on current state."""
        # Ensure the lock button exists
        if not self.force_chat_lock:
            return
        if self.force_chat_lock.isChecked():
            self.force_chat_lock.setText("🔒")
        else:
            self.force_chat_lock.setText("🔓")

    def connect_signals(self, toggle_callback, lock_callback) -> None:
        """Connect the toggle and lock button signals."""
        if self.force_chat_toggle:
            self.force_chat_toggle.toggled.connect(toggle_callback)
        if self.force_chat_lock:
            self.force_chat_lock.toggled.connect(lock_callback)

    def on_force_chat_toggled(self, checked: bool) -> None:
        """Handle Force Chat toggle state change. Save if locked."""
        # If locked, save the state
        if self.force_chat_lock and self.force_chat_lock.isChecked():
            self.app.settings_manager.force_chat_enabled = checked

    def on_force_chat_lock_toggled(self, checked: bool) -> None:
        """Handle Force Chat lock state change."""
        self.update_lock_icon()

        # Save lock state
        self.app.settings_manager.force_chat_locked = checked

        # Ensure toggle widget exists
        if not self.force_chat_toggle:
            return

        if checked:
            # When locking, save current toggle state
            self.app.settings_manager.force_chat_enabled = self.force_chat_toggle.isChecked()
        else:
            # When unlocking, reset toggle to default (off)
            self.force_chat_toggle.setChecked(False)
            self.app.settings_manager.force_chat_enabled = False

    def is_force_chat_enabled(self) -> bool:
        """Check if Force Chat is currently enabled."""
        return bool(self.force_chat_toggle and self.force_chat_toggle.isChecked())
