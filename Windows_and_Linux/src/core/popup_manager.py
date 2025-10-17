from PySide6.QtCore import QObject, Slot
from PySide6.QtGui import QCursor, QImage
from PySide6.QtWidgets import QApplication

from ..ui.ui_utils import ui_utils


class PopupManager(QObject):
    """Manages popup window creation and display."""

    def __init__(self, app, logger):
        super().__init__()
        self.app = app
        self._logger = logger
        self.image_processor = app.image_processor

        # State variables
        self.image: QImage | None = None
        self.has_image: bool = False
        self.original_selection: str | None = None
        self.popup_window = None

    def _determine_content_source(self) -> tuple[QImage | None, str | None]:
        """
        Determine if the source is an image from clipboard or selected text or image path.
        Automatically replaces old clipboard image with new one if different.

        Returns:
            Tuple of (image, selected_text)
        """
        # Check clipboard for image
        clipboard_image = self.image_processor.get_image_from_clipboard()

        # If we have a current image and a new clipboard image
        if self.image and clipboard_image:
            # Compare images to see if they're different
            if self._images_are_different(self.image, clipboard_image):
                self._logger.debug("🆕 New image detected in clipboard - replacing previous image")
                # Clear old image and replace with new one
                self.image = clipboard_image
                # Type assertion for PyLance since we know clipboard_image is not None here
                assert self.image is not None
                self._logger.debug(
                    f"🖼️ New clipboard image - size: {self.image.width()}x{self.image.height()}"
                )
                return self.image, None

        # If no current image but new clipboard image, use it
        elif clipboard_image and not self.image:
            self.image = clipboard_image
            # Type assertion for PyLance since we know clipboard_image is not None here
            assert self.image is not None
            self._logger.debug(
                f"🖼️ Image found in clipboard - size: {self.image.width()}x{self.image.height()}"
            )
            return self.image, None

        # If we already have an image from previous call, use it
        elif self.image:
            # Type assertion for PyLance since we know self.image is not None here
            assert self.image is not None
            self._logger.debug(
                f"🖼️ Using existing image - size: {self.image.width()}x{self.image.height()}"
            )
            return self.image, None

        # No image in clipboard, check selected text
        selected_text = self.original_selection = self.app.input_manager.get_selected_text(
            sleep_duration=0.1
        )
        self._logger.debug(f'Selected text: "{selected_text}"')

        if not selected_text:
            self._logger.debug("🖼️ No image found, no text selection")
            return None, None

        # Check if selected text is an image path
        if self.image_processor._is_image_path(selected_text):
            self._logger.debug("Selected text is image path, loading image")
            image = self.image_processor._load_image_from_path(selected_text)
            if image:
                # Type assertion for PyLance since we know image is not None here
                assert image is not None
                self._logger.debug(
                    f"🖼️ Image loaded from selection path - size: {image.width()}x{image.height()}"
                )
                return image, None  # Return None for selected_text as per requirements
            else:
                self._logger.debug("Failed to load image from selection path")
        else:
            self._logger.debug("🖼️ No image found, processing text selection")

        return None, selected_text

    def _images_are_different(self, img1: QImage | None, img2: QImage | None) -> bool:
        """
        Compare two images to determine if they're different.

        Args:
            img1: First image to compare
            img2: Second image to compare

        Returns:
            bool: True if images are different, False if they're the same
        """
        if not img1 or not img2:
            return True  # If either is None, they're different

        # First check basic properties
        if img1.width() != img2.width() or img1.height() != img2.height():
            return True

        # For more thorough comparison, we could convert to bytes and compare
        # but for performance, size comparison is often sufficient
        # If needed, we can enhance this with pixel-by-pixel comparison

        return False  # Same size = assume same image for now

    def _create_popup_window(self, selected_text: str | None, image: QImage | None) -> None:
        """Create and configure the popup window."""
        self._logger.debug("🆕🪟 Creating new popup window")

        # Import here to avoid circular imports
        from ..ui.custom_popup import custom_popup_window

        self.popup_window = custom_popup_window.CustomPopupWindow(self.app, selected_text, image)

    def _display_popup_window(self, selected_text: str | None) -> None:
        """Display and position the popup window."""
        if not self.popup_window:
            return

        self.popup_window.show()
        self.position_popup_window(self.popup_window, selected_text)
        ui_utils.existing_window_on_top(self.popup_window)

        # Force focus after window is fully displayed and positioned
        if self.popup_window.input_area and self.popup_window.input_area.custom_input:
            self.popup_window.input_area.custom_input.setFocus()

    @Slot()
    def show_popup(self) -> None:
        """
        Show the popup window when the hotkey is pressed.
        """
        try:
            # Determine content source
            self.image, selected_text = self._determine_content_source()
            self.has_image = bool(self.image is not None)

            # Create and display popup window
            self._create_popup_window(selected_text, self.image)
            self._display_popup_window(selected_text)

        except Exception as e:
            self._logger.error(f"Error showing popup window: {e}", exc_info=True)

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
        if not self.has_image and (
            selected_text is None or (selected_text and selected_text.strip() == "")
        ):
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

    def clean_image(self) -> None:
        """Clean up image resources."""
        if hasattr(self, "image") and self.image:
            self.image = None
        self.has_image = False
