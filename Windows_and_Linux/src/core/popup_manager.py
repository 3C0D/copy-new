import time
from typing import Optional

from pynput import keyboard
from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QCursor, QIcon, QImage
from PySide6.QtWidgets import QApplication

from ..ui.ui_utils import ui_utils
from .image_processor import ImageProcessor


class PopupManager(QObject):
    """Manages popup window creation and display."""

    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self._logger = logger
        self.image_processor = ImageProcessor(logger)

        # State variables
        self.image: Optional[QImage] = None
        self.has_image: bool = False
        self.original_selection: Optional[str] = None
        self.popup_window = None

    def _determine_image_source(self) -> tuple[Optional[QImage], Optional[str]]:
        """
        Determine the source of image and selected text.

        Returns:
            Tuple of (image, selected_text)
        """
        # Check clipboard first
        if self.image is None:
            self.image = self.image_processor.get_clipboard_image()

        # If we have an image from clipboard, no need to check text
        if self.image:
            self._logger.debug(
                f"🖼️ Image found in clipboard - size: {self.image.width()}x{self.image.height()}"
            )
            return self.image, None

        # No image in clipboard, check selected text
        selected_text = self.original_selection = self.get_selected_text(sleep_duration=0.1)
        self._logger.debug(f'Selected text: "{selected_text}"')

        if not selected_text:
            self._logger.debug("🖼️ No image found, no text selection")
            return None, None

        # Check if selected text is an image path
        if self.image_processor._is_image_path(selected_text):
            self._logger.debug("Selected text is image path, loading image")
            image = self.image_processor._load_image_from_path(selected_text)
            if image:
                self._logger.debug(
                    f"🖼️ Image loaded from selection path - size: {image.width()}x{image.height()}"
                )
                return image, None  # Return None for selected_text as per requirements
            else:
                self._logger.debug("Failed to load image from selection path")
        else:
            self._logger.debug("🖼️ No image found, processing text selection")

        return None, selected_text

    def _create_popup_window(self, selected_text: Optional[str], image: Optional[QImage]) -> None:
        """Create and configure the popup window."""
        self._logger.debug("🆕🪟 Creating new popup window")

        # Import here to avoid circular imports
        from ..ui import CustomPopupWindow
        from ..ui.ui_utils import ui_utils

        self.popup_window = CustomPopupWindow.CustomPopupWindow(self.app, selected_text, image)

        # Set window icon
        icon_path = ui_utils.get_icon_path(
            self.app,
            "app_icon",
            with_theme=False,
        )
        if icon_path.exists():
            self.popup_window.setWindowIcon(QIcon(icon_path.as_posix()))

    def _display_popup_window(self, selected_text: Optional[str]) -> None:
        """Display and position the popup window."""
        if not self.popup_window:
            return

        self.popup_window.show()
        self.position_popup_window(self.popup_window, selected_text)

        ui_utils.existing_window_on_top(self.popup_window)

    @Slot()
    def show_popup(self) -> None:
        """
        Show the popup window when the hotkey is pressed.
        """
        try:
            # Determine image source and selected text
            self.image, selected_text = self._determine_image_source()
            self.has_image = bool(self.image is not None)

            # Create and display popup window
            self._create_popup_window(selected_text, self.image)
            self._display_popup_window(selected_text)

        except Exception as e:
            self._logger.error(f"Error showing popup window: {e}", exc_info=True)

    # Placeholder methods that should be implemented in the actual class
    def get_selected_text(
        self, sleep_duration: float = 0.2, max_retries: int = 3, retry_delay: float = 0.1
    ) -> str:
        """
        Get the currently selected text from any application by simulating Ctrl+C.
        """
        self._logger.debug("Getting selected text")
        clipboard = QApplication.clipboard()
        clipboard_backup = clipboard.text()
        self._logger.debug(
            f"Clipboard backed up: {clipboard_backup[:30] if clipboard_backup else 'Empty'} ..."
        )

        # Clear the clipboard
        clipboard.clear()
        selected_text = ""

        # Simulate Ctrl+C to copy selected text
        self._logger.debug("Simulating Ctrl+C")
        kbrd = keyboard.Controller()

        def press_ctrl_c():
            with kbrd.pressed(keyboard.Key.ctrl):
                kbrd.press("c")
                kbrd.release("c")

        # Retry mechanism for Ctrl+C
        for attempt in range(max_retries):
            self._logger.debug(f"Attempting Ctrl+C - attempt {attempt + 1}/{max_retries}")

            # Clear clipboard before each attempt to detect success
            clipboard.clear()

            # Simulate Ctrl+C
            press_ctrl_c()

            # Wait for clipboard to update
            time.sleep(sleep_duration)

            # Check if clipboard has new content
            current_clipboard = clipboard.text()

            if current_clipboard:  # Success - clipboard has content
                # Check if it's a file path (from QuickLook/file selection)
                if self.image_processor._is_file_path(current_clipboard):
                    self._logger.debug(
                        f"Detected file path, treating as no selection: {current_clipboard}"
                    )
                    selected_text = ""
                    break
                else:
                    selected_text = current_clipboard
                    self._logger.debug(
                        f"Ctrl+C successful on attempt {attempt + 1}: {selected_text[:30] if selected_text else 'Empty'} ..."
                    )
                    break
            else:
                # Failed attempt
                if attempt < max_retries - 1:  # Don't wait after the last attempt
                    self._logger.debug(
                        f"Ctrl+C failed on attempt {attempt + 1}/{max_retries}, retrying in {retry_delay}s..."
                    )
                    time.sleep(retry_delay)
                else:
                    self._logger.warning(
                        f"Ctrl+C failed after {max_retries} attempts - no text selected or clipboard access failed"
                    )

        # Clean the selected text
        if selected_text:
            selected_text = selected_text
            self._logger.debug(f"Text retrieved and cleaned: {len(selected_text)} characters")
        else:
            selected_text = ""
            self._logger.debug("No text was retrieved")

        # Restore the clipboard
        clipboard.setText(clipboard_backup if clipboard_backup else "")
        self._logger.debug("Clipboard restored")

        return selected_text

    def position_popup_window(
        self,
        popup_window,
        selected_text: str | None,
        width=300,
        height=450,
        offset_x=0,
        offset_y=20,
    ):
        """
        Position popup window to stay within screen bounds

        Args:
            popup_window: The popup window to position
            width: Window width in pixels
            height: Window height in pixels
            offset_x: Horizontal offset from cursor
            offset_y: Vertical offset from cursor
        """
        if not self.has_image and (selected_text is None or selected_text.strip() == ""):
            height = 150  # smaller window
        # Get cursor position

        cursor_pos = QCursor.pos()
        x = cursor_pos.x() + offset_x
        y = cursor_pos.y() + offset_y

        # Get screen dimensions
        screen = QApplication.primaryScreen().availableGeometry()

        # Adjust if too far right
        if x + width > screen.right():
            x = cursor_pos.x() - width

        # Adjust if too far down - place above cursor
        if y + height > screen.bottom():
            y = cursor_pos.y() - height - 20

        # Keep within screen bounds
        x = max(screen.left(), min(x, screen.right() - width))
        y = max(screen.top(), min(y, screen.bottom() - height))

        # Position the window
        popup_window.move(x, y)

    def _is_file_path(self, text: str) -> bool:
        """
        Check if the text is a file path (from file/icon selection).

        Args:
            text: The text to check

        Returns:
            bool: True if it's a file path, False if it's regular text
        """
        if not text or not text.strip():
            return False

        text = text.strip()

        # Check for file:// URLs (what we saw in the logs)
        if text.startswith("file:///"):
            return True

        # Check for Windows file paths (C:\, D:\, etc.)
        if len(text) > 2 and text[1:3] == ":\\":
            return True

        # Check for UNC paths (\\server\share)
        if text.startswith("\\\\"):
            return True

        # Check for Unix-style absolute paths
        if text.startswith("/") and "/" in text[1:]:
            return True

        return False

    def clean_image(self) -> None:
        """Clean up image resources."""
        if hasattr(self, "image") and self.image:
            self.image = None
        self.has_image = False
