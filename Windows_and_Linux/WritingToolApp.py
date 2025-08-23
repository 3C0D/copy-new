"""
WritingToolApp - Main application class for Writing Tools.

This module contains the core application logic for the Writing Tools application,
including AI provider management, hotkey handling, and user interface coordination.
"""

import gettext
import logging
import os
import platform
import signal
import sys
import threading
import time
import types
from pathlib import Path
from typing import TYPE_CHECKING, Optional

import pyperclip
from pynput import keyboard as pykeyboard
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QLocale, Signal, Slot
from PySide6.QtGui import QCursor, QGuiApplication, QImage
from PySide6.QtWidgets import QApplication, QMessageBox

import ui.AboutWindow
import ui.CustomPopupWindow
import ui.NonEditableModal
import ui.OnboardingWindow
import ui.SettingsWindow

if TYPE_CHECKING:
    from aiprovider import AIProvider
    from ui.ResponseWindow import ResponseWindow

from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from aiprovider import (
    AnthropicProvider,
    GeminiProvider,
    MistralProvider,
    OllamaProvider,
    OpenAICompatibleProvider,
)
from config.settings import SettingsManager
from ui.ResponseWindow import ResponseWindow
from ui.ui_utils import get_icon_path
from update_checker import UpdateChecker

_ = gettext.gettext


class WritingToolApp(QApplication):
    """
    The main application class for Writing Tools.
    """

    output_ready_signal = Signal(str)
    show_message_signal = Signal(str, str)  # a signal for showing message boxes
    hotkey_triggered_signal = Signal()
    followup_response_signal = Signal(str)

    def __init__(self, argv):
        super().__init__(argv)
        self._logger = logging.getLogger(__name__)
        self._logger.debug("Initializing WritingToolApp")

        try:
            self._logger.debug("Setting up core attributes...")
            self._setup_core_attributes()

            self._logger.debug("Setting up signals...")
            self._setup_signals()

            self._logger.debug("Setting up settings...")
            self._setup_settings()

            self._logger.debug("Setting up UI components...")
            self._setup_ui_components()

            self._logger.debug("Setting up hotkey system...")
            self._setup_hotkey_system()

            self._logger.debug("Setting up AI providers...")
            self._setup_ai_providers()

            self._logger.debug("Setting up spam protection...")
            self._setup_spam_protection()

            # Initialize app based on configuration state
            self._logger.debug("Checking provider configuration...")
            if not self.settings_manager.has_providers_configured():
                self._logger.debug("No providers configured, handling first launch...")
                self._handle_first_launch()
            else:
                self._logger.debug("Providers configured, handling normal launch...")
                self._handle_normal_launch()

        except Exception as e:
            self._logger.error(f"Error during initialization: {e}", exc_info=True)
            raise

    def _setup_core_attributes(self) -> None:
        """Set up core application attributes."""
        self._logger.debug("Setting up core attributes...")
        self.settings_manager = SettingsManager()
        self.popup_window = None
        self.current_response_window = None
        self.hotkey_listener = None
        self.ai_providers = {}
        self.current_provider = None
        self.is_processing = False
        self.last_hotkey_time = 0
        self.hotkey_cooldown = 0.5  # 500ms cooldown

    def _setup_signals(self) -> None:
        """Set up signal connections."""
        self._logger.debug("Setting up signals...")
        self.hotkey_triggered_signal.connect(self._show_popup)
        self.output_ready_signal.connect(self._handle_output_ready)
        self.show_message_signal.connect(self._show_message_box)
        self.followup_response_signal.connect(self._handle_followup_response)

    def _setup_settings(self) -> None:
        """Set up settings management."""
        self._logger.debug("Setting up settings...")
        try:
            self.settings_manager.load()
            self._logger.debug("Settings loaded successfully")
        except Exception as e:
            self._logger.error(f"Error loading settings: {e}")
            # Continue with default settings

    def _setup_ui_components(self) -> None:
        """Set up UI components."""
        self._logger.debug("Setting up UI components...")
        # UI components will be created when needed

    def _setup_hotkey_system(self) -> None:
        """Set up the global hotkey system."""
        self._logger.debug("Setting up hotkey system...")
        try:
            hotkey = self.settings_manager.get_hotkey()
            self._start_hotkey_listener(hotkey)
            self._logger.debug(f"Hotkey system started with key: {hotkey}")
        except Exception as e:
            self._logger.error(f"Error setting up hotkey system: {e}")

    def _setup_ai_providers(self) -> None:
        """Set up AI providers."""
        self._logger.debug("Setting up AI providers...")
        try:
            # Initialize providers based on settings
            providers_config = self.settings_manager.get_providers_config()
            
            for provider_name, config in providers_config.items():
                try:
                    if provider_name == "anthropic":
                        self.ai_providers[provider_name] = AnthropicProvider(config)
                    elif provider_name == "gemini":
                        self.ai_providers[provider_name] = GeminiProvider(config)
                    elif provider_name == "mistral":
                        self.ai_providers[provider_name] = MistralProvider(config)
                    elif provider_name == "ollama":
                        self.ai_providers[provider_name] = OllamaProvider(config)
                    elif provider_name == "openai_compatible":
                        self.ai_providers[provider_name] = OpenAICompatibleProvider(config)
                    
                    self._logger.debug(f"Provider {provider_name} initialized successfully")
                except Exception as e:
                    self._logger.error(f"Error initializing provider {provider_name}: {e}")
            
            # Set default provider
            default_provider = self.settings_manager.get_default_provider()
            if default_provider in self.ai_providers:
                self.current_provider = self.ai_providers[default_provider]
                self._logger.debug(f"Default provider set to: {default_provider}")
            elif self.ai_providers:
                self.current_provider = list(self.ai_providers.values())[0]
                self._logger.debug("First available provider set as default")
                
        except Exception as e:
            self._logger.error(f"Error setting up AI providers: {e}")

    def _setup_spam_protection(self) -> None:
        """Set up spam protection for hotkeys."""
        self._logger.debug("Setting up spam protection...")
        # Spam protection is handled in the hotkey listener

    def _handle_first_launch(self) -> None:
        """Handle first launch of the application."""
        self._logger.debug("Handling first launch...")
        try:
            # Show onboarding window
            onboarding = ui.OnboardingWindow.OnboardingWindow(self)
            onboarding.show()
            
            # Check if providers were configured during onboarding
            if self.settings_manager.has_providers_configured():
                self._handle_normal_launch()
            else:
                self._logger.warning("No providers configured after onboarding")
                
        except Exception as e:
            self._logger.error(f"Error during first launch handling: {e}")

    def _handle_normal_launch(self) -> None:
        """Handle normal launch of the application."""
        self._logger.debug("Handling normal launch...")
        try:
            # Check for updates
            if self.settings_manager.check_for_updates:
                self._check_for_updates()
                
            # Start system tray if enabled
            if self.settings_manager.show_system_tray:
                self._setup_system_tray()
                
        except Exception as e:
            self._logger.error(f"Error during normal launch handling: {e}")

    def _check_for_updates(self) -> None:
        """Check for application updates."""
        try:
            update_checker = UpdateChecker()
            if update_checker.check_for_updates():
                self.settings_manager.update_available = True
                self._logger.info("Update available")
        except Exception as e:
            self._logger.error(f"Error checking for updates: {e}")

    def _setup_system_tray(self) -> None:
        """Set up system tray icon and menu."""
        try:
            # System tray setup code would go here
            self._logger.debug("System tray setup completed")
        except Exception as e:
            self._logger.error(f"Error setting up system tray: {e}")

    def _start_hotkey_listener(self, hotkey: str) -> None:
        """Start the global hotkey listener."""
        try:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
                
            # Parse hotkey (e.g., "ctrl+shift+w")
            keys = hotkey.lower().split("+")
            key_combination = []
            
            for key in keys:
                if key == "ctrl":
                    key_combination.append(pykeyboard.Key.ctrl)
                elif key == "alt":
                    key_combination.append(pykeyboard.Key.alt)
                elif key == "shift":
                    key_combination.append(pykeyboard.Key.shift)
                elif key == "super":
                    key_combination.append(pykeyboard.Key.cmd)
                else:
                    key_combination.append(key)
            
            def on_activate():
                current_time = time.time()
                if current_time - self.last_hotkey_time > self.hotkey_cooldown:
                    self.last_hotkey_time = current_time
                    self._logger.debug("triggered hotkey")
                    self.hotkey_triggered_signal.emit()
                else:
                    self._logger.debug("Hotkey ignored due to cooldown")
            
            # Start listener
            self.hotkey_listener = pykeyboard.GlobalHotKey({
                hotkey: on_activate
            })
            self.hotkey_listener.start()
            
        except Exception as e:
            self._logger.error(f"Error starting hotkey listener: {e}")

    def _show_popup(self) -> None:
        """Show the popup window when the hotkey is pressed."""
        self._logger.debug("Showing popup window")
        # First attempt with default sleep
        selected_text = self.get_selected_text()

        # Retry with longer sleep if no text captured
        if not selected_text:
            self._logger.debug("No text captured, retrying with longer sleep")
            selected_text = self.get_selected_text(sleep_duration=0.5)

        clipboard_image = self.get_clipboard_image()
        self._logger.debug(f'Selected text: "{selected_text}"')
        self._logger.debug(f'Clipboard image: {clipboard_image is not None}')
        try:
            if self.popup_window is not None:
                self._logger.debug("Existing popup window found")
                if self.popup_window.isVisible():
                    self._logger.debug("Closing existing visible popup window")
                    self.popup_window.close()
                self.popup_window = None
            self._logger.debug("Creating new popup window")
            self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(
                self, selected_text, clipboard_image
            )

            # Set the window icon
            icon_path = get_icon_path("app_icon", with_theme=False)
            if icon_path.exists():
                self.setWindowIcon(QtGui.QIcon(icon_path.as_posix()))
            # Get the screen containing the cursor
            cursor_pos = QCursor.pos()
            screen = QGuiApplication.screenAt(cursor_pos)
            if screen is None:
                screen = QGuiApplication.primaryScreen()
            screen_geometry = screen.geometry()
            self._logger.debug(f"Cursor is on screen: {screen.name()}")
            self._logger.debug(f"Screen geometry: {screen_geometry}")
            # Show the popup to get its size
            self.popup_window.show()
            self.popup_window.adjustSize()
            # Ensure the popup it's focused, even on lower-end machines
            self.popup_window.activateWindow()
            if self.popup_window.custom_input:
                QtCore.QTimer.singleShot(100, self.popup_window.custom_input.setFocus)

            popup_width = self.popup_window.width()
            popup_height = self.popup_window.height()
            # Calculate position
            x = cursor_pos.x()
            y = cursor_pos.y() + 20  # 20 pixels below cursor
            # Adjust if the popup would go off the right edge of the screen
            if x + popup_width > screen_geometry.right():
                x = screen_geometry.right() - popup_width
            # Adjust if the popup would go off the bottom edge of the screen
            if y + popup_height > screen_geometry.bottom():
                y = cursor_pos.y() - popup_height - 10  # 10 pixels above cursor
            self.popup_window.move(x, y)
            self._logger.debug(f"Popup window moved to position: ({x}, {y})")
        except Exception as e:
            self._logger.error(f"Error showing popup window: {e}", exc_info=True)

    def debug_clipboard_contents(self) -> None:
        """
        Debug method to analyze clipboard contents and available formats.
        Helps diagnose clipboard detection issues.
        """
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            self._logger.debug("=== CLIPBOARD DEBUG INFO ===")
            self._logger.debug(f"Platform: {platform.system()}")
            self._logger.debug(f"hasImage(): {mime_data.hasImage()}")
            self._logger.debug(f"hasText(): {mime_data.hasText()}")
            self._logger.debug(f"hasUrls(): {mime_data.hasUrls()}")

            # List all available formats
            formats = mime_data.formats()
            self._logger.debug(f"Available formats ({len(formats)}): {formats}")

            # Check specific image formats
            image_formats = [
                "image/png", "image/jpeg", "image/jpg", "image/bmp",
                "image/gif", "image/tiff", "image/dib", "CF_DIB",
                "CF_BITMAP", "application/x-qt-image"
            ]

            for fmt in image_formats:
                has_format = mime_data.hasFormat(fmt)
                if has_format:
                    data_size = len(mime_data.data(fmt))
                    self._logger.debug(f"Format '{fmt}': YES ({data_size} bytes)")
                else:
                    self._logger.debug(f"Format '{fmt}': NO")

            # Linux-specific format checks
            if platform.system() == "Linux":
                self._logger.debug("--- Linux-specific format checks ---")
                linux_formats = [
                    "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
                    "application/x-qt-image", "application/x-qt-pixmap",
                    "image/x-portable-pixmap", "image/x-portable-bitmap",
                    "image/x-portable-graymap", "image/x-portable-anymap"
                ]
                
                for fmt in linux_formats:
                    has_format = mime_data.hasFormat(fmt)
                    if has_format:
                        data_size = len(mime_data.data(fmt))
                        self._logger.debug(f"Linux format '{fmt}': YES ({data_size} bytes)")
                    else:
                        self._logger.debug(f"Linux format '{fmt}': NO")
                
                # Check for any format containing image-related keywords
                self._logger.debug("--- Checking for image-related formats ---")
                for fmt in formats:
                    if any(img_type in fmt.lower() for img_type in ['image', 'pixmap', 'bitmap', 'png', 'jpeg', 'jpg', 'gif', 'bmp', 'tiff']):
                        has_format = mime_data.hasFormat(fmt)
                        if has_format:
                            data_size = len(mime_data.data(fmt))
                            self._logger.debug(f"Image-related format '{fmt}': YES ({data_size} bytes)")
                        else:
                            self._logger.debug(f"Image-related format '{fmt}': NO")

            self._logger.debug("=== END CLIPBOARD DEBUG ===")

        except Exception as e:
            self._logger.error(f"Error debugging clipboard: {e}")

    def get_clipboard_image(self) -> Optional[QImage]:
        """
        Get the image currently stored in the clipboard using Qt6 with multiple detection methods.
        Returns the image if found, None otherwise.

        Uses multiple approaches to detect images:
        1. Standard hasImage() method
        2. Format-specific detection for various image types
        3. Raw data analysis for Windows clipboard formats
        4. Linux-specific clipboard formats and methods
        5. Direct image data access
        """
        try:
            clipboard = QApplication.clipboard()
            mime_data = clipboard.mimeData()

            # Debug clipboard contents if in debug mode
            if self._logger.isEnabledFor(logging.DEBUG):
                self.debug_clipboard_contents()

            # Method 1: Standard Qt image detection
            if mime_data.hasImage():
                self._logger.debug("Method 1: hasImage() returned True")
                image = mime_data.imageData()
                if isinstance(image, QImage):
                    if not image.isNull():
                        self._logger.debug(f"Image found via hasImage(): {image.width()}x{image.height()}")
                        return image
                    else:
                        self._logger.debug("hasImage() returned null QImage")
                else:
                    # Convert QPixmap to QImage
                    try:
                        from PySide6.QtGui import QPixmap
                        if isinstance(image, QPixmap):
                            qimage = image.toImage()
                            if not qimage.isNull():
                                self._logger.debug(f"Image converted from QPixmap: {qimage.width()}x{qimage.height()}")
                                return qimage
                            else:
                                self._logger.debug("QPixmap conversion resulted in null QImage")
                    except Exception as e:
                        self._logger.debug(f"Error converting QPixmap: {e}")

            # Method 2: Format-specific detection
            image_formats = [
                "image/png", "image/jpeg", "image/jpg", "image/bmp",
                "image/gif", "image/tiff", "image/dib", "CF_DIB", "CF_BITMAP"
            ]

            for fmt in image_formats:
                if mime_data.hasFormat(fmt):
                    self._logger.debug(f"Method 2: Found format '{fmt}'")
                    try:
                        data = mime_data.data(fmt)
                        if data and not data.isEmpty():
                            # Try to load image from raw data
                            image = QImage()
                            if image.loadFromData(data):
                                if not image.isNull():
                                    self._logger.debug(f"Image loaded from format '{fmt}': {image.width()}x{image.height()}")
                                    return image
                                else:
                                    self._logger.debug(f"Format '{fmt}' data loaded but resulted in null image")
                            else:
                                self._logger.debug(f"Failed to load image from format '{fmt}' data")
                        else:
                            self._logger.debug(f"Format '{fmt}' has no data or empty data")
                    except Exception as e:
                        self._logger.debug(f"Error processing format '{fmt}': {e}")

            # Method 3: Windows-specific clipboard formats (for Print Screen)
            if platform.system() == "Windows":
                windows_formats = ["CF_DIB", "CF_BITMAP", "CF_DIBV5"]
                for fmt in windows_formats:
                    if mime_data.hasFormat(fmt):
                        self._logger.debug(f"Method 3: Found Windows format '{fmt}'")
                        try:
                            data = mime_data.data(fmt)
                            if data and not data.isEmpty():
                                # Try to create QImage from Windows DIB/Bitmap data
                                image = QImage()
                                if image.loadFromData(data):
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded from Windows format '{fmt}': {image.width()}x{image.height()}")
                                        return image
                                else:
                                    # Try alternative loading methods for Windows formats
                                    try:
                                        # Convert bytes to QByteArray and try different formats
                                        from PySide6.QtCore import QByteArray
                                        byte_array = QByteArray(data)

                                        # Try loading as different image formats
                                        for img_format in ["BMP", "PNG", "JPEG"]:
                                            image = QImage()
                                            if image.loadFromData(byte_array, img_format.encode()):
                                                if not image.isNull():
                                                    self._logger.debug(f"Image loaded from Windows format '{fmt}' as {img_format}: {image.width()}x{image.height()}")
                                                    return image
                                    except Exception as e:
                                        self._logger.debug(f"Alternative loading failed for '{fmt}': {e}")
                        except Exception as e:
                            self._logger.debug(f"Error processing Windows format '{fmt}': {e}")

            # Method 4: Linux-specific clipboard formats and methods
            if platform.system() == "Linux":
                self._logger.debug("Method 4: Checking Linux-specific clipboard formats")
                
                # Linux clipboard formats commonly used for images
                linux_formats = [
                    "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
                    "application/x-qt-image", "application/x-qt-pixmap",
                    "image/x-portable-pixmap", "image/x-portable-bitmap",
                    "image/x-portable-graymap", "image/x-portable-anymap"
                ]
                
                for fmt in linux_formats:
                    if mime_data.hasFormat(fmt):
                        self._logger.debug(f"Method 4: Found Linux format '{fmt}'")
                        try:
                            data = mime_data.data(fmt)
                            if data and not data.isEmpty():
                                # Try to load image from raw data
                                image = QImage()
                                if image.loadFromData(data):
                                    if not image.isNull():
                                        self._logger.debug(f"Image loaded from Linux format '{fmt}': {image.width()}x{image.height()}")
                                        return image
                                    else:
                                        self._logger.debug(f"Linux format '{fmt}' data loaded but resulted in null image")
                                else:
                                    self._logger.debug(f"Failed to load image from Linux format '{fmt}' data")
                        except Exception as e:
                            self._logger.debug(f"Error processing Linux format '{fmt}': {e}")
                
                # Try to get image data directly from clipboard (Linux-specific approach)
                try:
                    # Sometimes on Linux, the image data is available but not detected by hasImage()
                    image_data = mime_data.imageData()
                    if image_data is not None:
                        self._logger.debug("Method 4: Found imageData() directly on Linux")
                        if isinstance(image_data, QImage) and not image_data.isNull():
                            self._logger.debug(f"Direct imageData() successful on Linux: {image_data.width()}x{image_data.height()}")
                            return image_data
                        elif hasattr(image_data, 'toImage'):
                            # Try converting if it's a QPixmap
                            converted = image_data.toImage()
                            if not converted.isNull():
                                self._logger.debug(f"Direct imageData() converted on Linux: {converted.width()}x{converted.height()}")
                                return converted
                except Exception as e:
                    self._logger.debug(f"Linux-specific imageData() method failed: {e}")

            # Method 5: Try to get image data directly from clipboard (last resort)
            try:
                # Sometimes the image data is available but not detected by hasImage()
                image_data = mime_data.imageData()
                if image_data is not None:
                    self._logger.debug("Method 5: Found imageData() directly")
                    if isinstance(image_data, QImage) and not image_data.isNull():
                        self._logger.debug(f"Direct imageData() successful: {image_data.width()}x{image_data.height()}")
                        return image_data
                    elif hasattr(image_data, 'toImage'):
                        # Try converting if it's a QPixmap
                        converted = image_data.toImage()
                        if not converted.isNull():
                            self._logger.debug(f"Direct imageData() converted: {converted.width()}x{converted.height()}")
                            return converted
            except Exception as e:
                self._logger.debug(f"Method 5 failed: {e}")

            # Method 6: Try alternative clipboard access methods for Linux
            if platform.system() == "Linux":
                self._logger.debug("Method 6: Trying alternative Linux clipboard access")
                try:
                    # Try to access clipboard data in different ways
                    clipboard_data = clipboard.mimeData()
                    
                    # Check if there are any data formats that might contain image data
                    all_formats = clipboard_data.formats()
                    self._logger.debug(f"All available formats on Linux: {all_formats}")
                    
                    # Look for any format that might contain image data
                    for fmt in all_formats:
                        if any(img_type in fmt.lower() for img_type in ['image', 'pixmap', 'bitmap', 'png', 'jpeg', 'jpg']):
                            self._logger.debug(f"Method 6: Found potential image format '{fmt}'")
                            try:
                                data = clipboard_data.data(fmt)
                                if data and not data.isEmpty():
                                    # Try to load image from raw data
                                    image = QImage()
                                    if image.loadFromData(data):
                                        if not image.isNull():
                                            self._logger.debug(f"Image loaded from potential format '{fmt}': {image.width()}x{image.height()}")
                                            return image
                            except Exception as e:
                                self._logger.debug(f"Error processing potential format '{fmt}': {e}")
                                
                except Exception as e:
                    self._logger.debug(f"Alternative Linux clipboard access failed: {e}")

            self._logger.debug("No image found in clipboard using any method")

        except Exception as e:
            self._logger.error(f"Error getting clipboard image: {e}")

        return None

    def get_selected_text(self, sleep_duration: float = 0.2) -> str:
        """
        Get the currently selected text from any application.
        Args:
            sleep_duration (float): Time to wait for clipboard update
        """
        # Backup the clipboard
        clipboard_backup = pyperclip.paste()
        self._logger.debug(
            f'Clipboard backup: "{clipboard_backup}" (sleep: {sleep_duration}s)'
        )

        # Clear the clipboard
        self.clear_clipboard()

        # Simulate Ctrl+C
        self._logger.debug("Simulating Ctrl+C")
        kbrd = pykeyboard.Controller()

        def press_ctrl_c():
            kbrd.press(pykeyboard.Key.ctrl.value)
            kbrd.press("c")
            kbrd.release("c")
            kbrd.release(pykeyboard.Key.ctrl.value)

        press_ctrl_c()

        # Wait for the clipboard to update
        time.sleep(sleep_duration)
        self._logger.debug(f"Waited {sleep_duration}s for clipboard")

        # Get the selected text
        selected_text = pyperclip.paste()

        # Clean the selected text (remove leading/trailing whitespace and newlines)
        if selected_text:
            selected_text = selected_text.strip()

        # Restore the clipboard
        pyperclip.copy(clipboard_backup)

        return selected_text

    def clear_clipboard(self) -> None:
        """
        Clear the system clipboard.
        """
        try:
            pyperclip.copy("")
        except Exception as e:
            self._logger.error(f"Error clearing clipboard: {e}")

    def process_option(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str] = None,
        force_chat: bool = False,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Process the selected writing option in a separate thread.

        Args:
            option: The action option to process
            selected_text: The text selected by the user
            custom_change: Custom instruction for "Custom" option
            force_chat: If True, force response to open in ResponseWindow (chat mode)
        """
        self._logger.debug(f"Processing option: {option}")
        self._logger.debug(f"Selected text: {selected_text}")
        self._logger.debug(f"Custom change: {custom_change}")
        self._logger.debug(f"Force chat: {force_chat}")
        self._logger.debug(f"Image: {image is not None}")

        action_config = self.settings_manager.actions.get(option)
        if not action_config:
            self._logger.error(f"Action not found: {option}")
            return

        should_setup_window = self._should_display_in_window(
            option, selected_text, action_config, force_chat, image
        )

        if should_setup_window:
            is_empty_custom = option == "Custom" and not selected_text.strip()
            self._setup_response_window(is_empty_custom, option, selected_text, image)
        elif hasattr(self, "current_response_window"):
            delattr(self, "current_response_window")

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, custom_change, image),
            daemon=True,
        ).start()

    def _setup_response_window(
        self,
        is_empty_custom: bool,
        option: str,
        selected_text: str,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Set up the response window for displaying AI responses.
        """
        try:
            # Create response window
            self.current_response_window = ResponseWindow(
                self, option, selected_text, image
            )
            
            # Show the window
            self.current_response_window.show()
            
        except Exception as e:
            self._logger.error(f"Error setting up response window: {e}")

    def _should_display_in_window(
        self,
        option: str,
        selected_text: str,
        action_config: dict,
        force_chat: bool,
        image: QtGui.QImage | None = None,
    ) -> bool:
        """
        Determine if the response should be displayed in a window.
        """
        # Always show in window if force_chat is True
        if force_chat:
            return True
            
        # Check action configuration
        if action_config.get("open_in_window", False):
            return True
            
        # Show in window for custom options
        if option == "Custom":
            return True
            
        return False

    def process_option_thread(
        self,
        option: str,
        selected_text: str,
        custom_change: Optional[str] = None,
        image: QtGui.QImage | None = None,
    ) -> None:
        """
        Process the writing option in a separate thread.
        """
        try:
            # Get the current AI provider
            if not self.current_provider:
                self._logger.error("No AI provider available")
                return
                
            # Prepare the prompt
            if option == "Custom" and custom_change:
                prompt = custom_change
            else:
                action_config = self.settings_manager.actions.get(option)
                if not action_config:
                    self._logger.error(f"Action configuration not found for: {option}")
                    return
                    
                prompt = action_config.get("instruction", "")
                if selected_text:
                    prompt = f"{prompt}\n\nText: {selected_text}"
            
            # Add image context if available
            if image:
                prompt = f"{prompt}\n\n[Image from clipboard]"
            
            # Get response from AI provider
            response = self.current_provider.get_response(prompt)
            
            # Emit signal with response
            self.output_ready_signal.emit(response)
            
        except Exception as e:
            self._logger.error(f"Error in processing thread: {e}")
            error_msg = f"Error processing request: {str(e)}"
            self.output_ready_signal.emit(error_msg)

    def _handle_output_ready(self, response: str) -> None:
        """
        Handle when AI output is ready.
        """
        try:
            if self.current_response_window:
                self.current_response_window.set_text(response)
            else:
                # Fallback: copy to clipboard
                pyperclip.copy(response)
                self._logger.info("Response copied to clipboard")
                
        except Exception as e:
            self._logger.error(f"Error handling output: {e}")

    def _show_message_box(self, title: str, message: str) -> None:
        """
        Show a message box.
        """
        try:
            QMessageBox.information(None, title, message)
        except Exception as e:
            self._logger.error(f"Error showing message box: {e}")

    def _handle_followup_response(self, response: str) -> None:
        """
        Handle followup responses.
        """
        try:
            if self.current_response_window:
                self.current_response_window.add_followup(response)
            else:
                self._logger.warning("No response window available for followup")
                
        except Exception as e:
            self._logger.error(f"Error handling followup: {e}")

    def cleanup(self) -> None:
        """
        Clean up resources before exit.
        """
        try:
            if self.hotkey_listener:
                self.hotkey_listener.stop()
                
            if self.popup_window:
                self.popup_window.close()
                
            if self.current_response_window:
                self.current_response_window.close()
                
        except Exception as e:
            self._logger.error(f"Error during cleanup: {e}")

    def closeEvent(self, event) -> None:
        """
        Handle application close event.
        """
        try:
            self.cleanup()
            event.accept()
        except Exception as e:
            self._logger.error(f"Error during close: {e}")
            event.accept()

    def signal_handler(self, signum, frame) -> None:
        """
        Handle system signals for graceful shutdown.
        """
        try:
            self._logger.info(f"Received signal {signum}, shutting down gracefully")
            self.cleanup()
            sys.exit(0)
        except Exception as e:
            self._logger.error(f"Error during signal handling: {e}")
            sys.exit(1)