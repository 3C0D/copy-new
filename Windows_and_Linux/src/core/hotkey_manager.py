"""
Hotkey Manager - Handles global hotkey registration and management.

This module contains the logic for managing global hotkeys, keyboard listeners,
spam protection, and signal handling for the Writing Tools application.
"""

import logging
import signal
import time
import types
from typing import TYPE_CHECKING, Optional

from pynput import keyboard as keyboard
from PySide6.QtCore import QMetaObject, QObject, Qt, QTimer, Signal, Slot

if TYPE_CHECKING:
    pass


class HotkeyManager(QObject):
    """
    Manages global hotkey registration, keyboard listeners, and spam protection.
    """

    hotkey_triggered_signal = Signal()

    def __init__(self, app):
        self.app = app
        self._logger = logging.getLogger(__name__)

        # Hotkey system attributes
        self.hotkey_listener: Optional[keyboard.Listener] = None
        self.ctrl_c_timer: Optional[QTimer] = None

        # Spam protection attributes
        self.recent_triggers: list[float] = []
        self.TRIGGER_WINDOW = 1.5  # Time window in seconds
        self.MAX_TRIGGERS = 3  # Max allowed triggers in window

        self.hotkey_triggered_signal.connect(self.on_hotkey_pressed)

        # Setup Ctrl+C listener
        self.setup_ctrl_c_listener()

    def setup_ctrl_c_listener(self) -> None:
        """
        Listener for Ctrl+C to exit the app.
        """
        signal.signal(signal.SIGINT, lambda signum, frame: self.handle_sigint(signum, frame))
        # This empty timer is needed to make sure that the sigint handler gets checked inside the main loop:
        # without it, the sigint handle would trigger only when an event is triggered, either by a hotkey combination
        # or by another GUI event like spawning a new window. With this we trigger it every 100ms with an empy lambda
        # so that the signal handler gets checked regularly.
        self.ctrl_c_timer = QTimer()
        self.ctrl_c_timer.start(100)
        self.ctrl_c_timer.timeout.connect(lambda: None)

    def handle_sigint(self, signum: int, frame: Optional[types.FrameType]) -> None:
        """
        Handle the SIGINT signal (Ctrl+C) to exit the app gracefully.

        Args:
            signum: Signal number (unused but required by signal handler interface)
            frame: Current stack frame (unused but required by signal handler interface)
        """
        del signum, frame  # Explicitly mark as unused
        self._logger.debug("Received SIGINT. Exiting...")
        self.app.lifecycle_manager.exit_app()

    def check_trigger_spam(self) -> bool:
        """
        Check if hotkey is being triggered too frequently.
        Returns True if spam is detected (3+ times in 1.5 seconds).
        """
        current_time = time.time()
        self.recent_triggers.append(current_time)

        # Remove old triggers outside the window
        self.recent_triggers = [
            t for t in self.recent_triggers if current_time - t <= self.TRIGGER_WINDOW
        ]

        return len(self.recent_triggers) >= self.MAX_TRIGGERS

    def start_hotkey_listener(self) -> None:
        """
        Create listener for hotkeys on Linux/Mac.
        """
        orig_shortcut = self.app.settings_manager.hotkey or "ctrl+space"

        # Parse the shortcut string, for example ctrl+alt+h -> <ctrl>+<alt>+<h>. Space are removed.
        shortcut = "+".join([f"<{t.strip()}>" for t in orig_shortcut.split("+")])

        self._logger.debug(f"Registering global hotkey for shortcut: {shortcut}")

        try:
            if self.hotkey_listener is not None:
                self.hotkey_listener.stop()
                self.hotkey_listener = None

            def on_activate():
                if self.app.systray_manager.paused:
                    return
                self._logger.debug("triggered hotkey")
                self.app.hotkey_triggered_signal.emit()  # Emit the signal when hotkey is pressed

            # Define the hotkey combination
            hotkey = keyboard.HotKey(keyboard.HotKey.parse(shortcut), on_activate)

            # Helper function to standardize key event
            def for_canonical(f):
                return lambda k: f(
                    self.hotkey_listener.canonical(k)
                    if k is not None and self.hotkey_listener is not None
                    else k
                )

            # Create a listener and store it as an attribute to stop it later
            self.hotkey_listener = keyboard.Listener(
                on_press=for_canonical(hotkey.press),
                on_release=for_canonical(hotkey.release),
            )

            # Start the listener
            self.hotkey_listener.start()
        except Exception as e:
            self._logger.error(f"Failed to register hotkey: {e}")

    def register_hotkey(self) -> None:
        """
        Register the global hotkey for activating Writing Tools.
        """
        self._logger.debug("Registering hotkey")
        self.start_hotkey_listener()
        self._logger.debug("Hotkey registered")

    @Slot()
    def on_hotkey_pressed(self) -> None:
        """
        Handle the hotkey press event.
        """
        self._logger.debug("Hotkey pressed ==============================")

        # Check for spam triggers
        if self.check_trigger_spam():
            self._logger.warning("Hotkey spam detected - quitting application")
            self.app.lifecycle_manager.exit_app()
            return

        # Close existing non-editable modal if open
        if hasattr(self.app, "non_editable_modal") and self.app.non_editable_modal is not None:
            self._logger.debug("Closing existing non-editable modal")
            self.app.non_editable_modal.close()
            self.app.non_editable_modal = None

        # Close existing popup window if open
        if hasattr(self.app, "popup_manager") and self.app.popup_manager.popup_window is not None:
            self._logger.debug("Closing existing popup window")
            self.app.popup_manager.popup_window.close()
            self.app.popup_manager.popup_window = None

        # Close existing response window if open
        if (
            hasattr(self.app, "current_response_window")
            and self.app.current_response_window is not None
        ):
            self._logger.debug("Closing existing response window")
            self.app.current_response_window.close()
            self.app.current_response_window = None

        # Original hotkey handling continues...
        if self.app.ai_processor.current_provider:
            self._logger.debug("Cancelling current provider's request")
            self.app.ai_processor.current_provider.cancel()
            self.app.ai_processor.output_queue = ""

        # noinspection PyTypeChecker
        QMetaObject.invokeMethod(
            self.app.popup_manager, "show_popup", Qt.ConnectionType.QueuedConnection
        )

    def cleanup(self) -> None:
        """
        Clean up hotkey resources when the application exits.
        """
        self._logger.debug("Stopping the listener")
        if self.hotkey_listener is not None:
            self.hotkey_listener.stop()
        self._logger.debug("Restoring default SIGINT handler")
        signal.signal(signal.SIGINT, signal.SIG_DFL)
