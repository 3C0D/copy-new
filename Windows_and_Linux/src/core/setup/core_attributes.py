"""
Core attributes setup module for Writing Tools application.

This module contains setup functions for core application attributes.
"""

from ...core.ai_processor import AIProcessor
from ...core.clipboard_manager import ClipboardManager
from ...core.hotkey_manager import HotkeyManager
from ...core.image_processor import ImageProcessor
from ...core.input_manager import InputManager
from ...core.lifecycle_manager import LifecycleManager
from ...core.popup_manager import PopupManager
from ...core.text_processor import TextProcessor
from ...core.ui_manager import UIManager
from ...core.update_manager import UpdateManager
from ...systray import SystrayManager


def setup_core_attributes(app) -> None:
    """Initialize core application attributes."""
    app.current_response_window = None
    app.ai_processor = AIProcessor(app)
    app.text_processor = TextProcessor(app)
    app.hotkey_manager = HotkeyManager(app)
    app.systray_manager = SystrayManager(app)
    app.image_processor = ImageProcessor(app, app._logger)
    app.clipboard_manager = ClipboardManager(app, app._logger)
    app.input_manager = InputManager(app, app._logger)
    app.popup_manager = PopupManager(app, app._logger)
    app.ui_manager = UIManager(app)
    app.lifecycle_manager = LifecycleManager(app)
    app.update_manager = UpdateManager(app)
