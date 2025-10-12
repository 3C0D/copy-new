import base64
import tempfile
import time
import urllib.parse
from pathlib import Path

from PySide6.QtGui import QImage
from PySide6.QtWidgets import QApplication


class ImageProcessor:
    """Handles image processing and clipboard operations."""

    SUPPORTED_IMAGE_EXTENSIONS = {
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".bmp",
        ".tiff",
        ".tif",
        ".webp",
        ".svg",
    }
    FILE_URL_PREFIX = "file:///"

    def __init__(self, app, logger):
        self.app = app
        self._logger = logger

    def _normalize_path_text(self, text: str) -> str | None:
        """
        Normalize text that might be a file path by removing quotes and handling URLs.

        Args:
            text: Raw text that might contain a file path

        Returns:
            Normalized path string or None if invalid
        """
        if not isinstance(text, str) or not text.strip():
            return None

        normalized_text = text.strip()

        # Remove surrounding quotes (Windows "Copy as path" adds quotes)
        if normalized_text.startswith('"') and normalized_text.endswith('"'):
            normalized_text = normalized_text[1:-1]

        # Handle file:// URLs
        if normalized_text.startswith(self.FILE_URL_PREFIX):
            normalized_text = normalized_text[len(self.FILE_URL_PREFIX) :]
            try:
                normalized_text = urllib.parse.unquote(normalized_text)
            except Exception as e:
                self._logger.debug(f"Error URL decoding path: {e}")
                return None

        return normalized_text if normalized_text else None

    def _is_image_path(self, text: str) -> bool:
        """
        Check if the text is a path to a valid image file.

        Args:
            text: The text to check

        Returns:
            True if it's a path to a valid image file, False otherwise
        """
        normalized_path = self._normalize_path_text(text)
        if not normalized_path:
            return False

        if not self.app.input_manager._is_file_path(normalized_path):
            return False

        try:
            path = Path(normalized_path)

            # Check file extension
            if path.suffix.lower() not in self.SUPPORTED_IMAGE_EXTENSIONS:
                return False

            # Verify the image can be loaded
            image = QImage(str(path))
            return not image.isNull()

        except Exception as e:
            self._logger.debug(f"Error validating image path: {e}")
            return False

    def _load_image_from_path(self, text: str) -> QImage | None:
        """
        Load an image from a file path.

        Args:
            text: The file path text

        Returns:
            The loaded QImage or None if failed
        """
        normalized_path = self._normalize_path_text(text)
        if not normalized_path or not self._is_image_path(text):
            return None

        try:
            path = Path(normalized_path)
            image = QImage(str(path))

            if image.isNull():
                self._logger.debug(f"Failed to load image from path: {path}")
                return None

            self._logger.debug(
                f"Successfully loaded image from path: {path} - size: {image.width()}x{image.height()}"
            )
            return image

        except Exception as e:
            self._logger.error(f"Error loading image from path {text}: {e}")
            return None

    def _process_clipboard_image_data(self, mime_data) -> QImage | None:
        """Process image data from clipboard MIME data."""
        try:
            available_formats = mime_data.formats()
            self._logger.debug(f"Available clipboard formats: {available_formats}")

            image_data = mime_data.imageData()

            if isinstance(image_data, QImage):
                self._logger.debug("QImage found in clipboard")
                if image_data.isNull():
                    self._logger.warning("QImage is null")
                    return None
                return image_data

            elif hasattr(image_data, "toImage"):  # QPixmap
                self._logger.debug("Converting QPixmap to QImage")
                qimage = image_data.toImage()
                if qimage.isNull():
                    self._logger.warning("Converted QImage is null")
                    return None
                self._logger.debug(f"QPixmap converted: {qimage.width()}x{qimage.height()}")
                return qimage

            else:
                self._logger.warning(f"Unknown image type: {type(image_data)}")
                return None

        except Exception as e:
            self._logger.error(f"Error processing clipboard image data: {e}")
            return None

    def get_image_from_clipboard(self) -> QImage | None:
        """
        Get image data from clipboard (screenshots, copied images, or image file paths).

        Returns:
            QImage if found and valid, None otherwise
        """
        try:
            clipboard = QApplication.clipboard()
            if not clipboard:
                self._logger.warning("Unable to access clipboard")
                return None

            mime_data = clipboard.mimeData()
            if not mime_data:
                self._logger.debug("No MIME data available in clipboard")
                return None

            # First check for actual image data
            if mime_data.hasImage():
                image = self._process_clipboard_image_data(mime_data)
                if image:
                    self.app.clipboard_manager._clear_clipboard_safely(True)
                    return image

            # If no image data, check for text that might be an image path
            elif mime_data.hasText():
                text = mime_data.text()
                if not text:
                    self._logger.debug("Clipboard contains empty text")
                    return None

                self._logger.debug(f"Checking if clipboard text is image path: {text[:50]}...")

                if self._is_image_path(text):
                    self._logger.debug("Clipboard contains image path, loading image")
                    image = self._load_image_from_path(text)
                    if image:
                        self.app.clipboard_manager._clear_clipboard_safely(True)
                        return image
                    else:
                        self._logger.debug("Failed to load image from clipboard path")
                else:
                    self._logger.debug("Clipboard text is not an image path")

            else:
                self._logger.debug("No image or text found in clipboard")

            return None

        except Exception as e:
            self._logger.error(f"Error processing clipboard: {e}")
            return None

    def qimage_to_base64(self, image: QImage, use_physical_file: bool = True) -> str:
        """
        Convert QImage to base64 string for API transmission.

        Supports two approaches:
        1. Physical file approach (use_physical_file=True): Creates temporary file, saves QImage, reads and converts to base64
        2. Memory approach (use_physical_file=False): Direct conversion using QBuffer without file I/O

        Args:
            image: QImage to convert
            use_physical_file: Whether to use temporary file approach. Defaults to False for memory-based conversion.

        Returns:
            str: Base64 encoded image data
        """
        try:
            if use_physical_file:
                # Original approach using temporary file
                return self._qimage_to_base64_with_file(image)
            else:
                # Alternative approach using memory buffer
                return self._qimage_to_base64_memory(image)

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64: {e}")
            return ""

    def _qimage_to_base64_with_file(self, image: QImage) -> str:
        """
        Convert QImage to base64 using temporary file approach (legacy method).

        Args:
            image: QImage to convert

        Returns:
            str: Base64 encoded image data
        """
        try:
            # Create temporary file path
            temp_path = self._get_temp_image_path()
            self._logger.debug(
                f" 🖼️\u00a0 Converting QImage to base64 with file - temp path: {temp_path}"
            )

            # Save QImage to temporary file (PNG format for compatibility)
            if not image.save(str(temp_path)):  # Use overload without format parameter
                self._logger.error(" 🖼️\u00a0 Failed to save QImage to temporary file")
                return ""

            self._logger.debug(f" 🖼️\u00a0 QImage saved successfully to: {temp_path}")

            # Read the temporary file and convert to base64
            try:
                with open(temp_path, "rb") as image_file:
                    image_bytes = image_file.read()
                    base64_string = base64.b64encode(image_bytes).decode("utf-8")

                self._logger.debug(
                    f" 🖼️\u00a0 Converted image to base64: {len(base64_string)} characters"
                )
                self._logger.debug(f" 🖼️\u00a0 Base64 preview: {base64_string[:100]}...")
                return base64_string

            finally:
                # Clean up temporary file
                try:
                    temp_path.unlink(missing_ok=True)
                    self._logger.debug(f" 🖼️\u00a0 Cleaned up temporary file: {temp_path}")
                except Exception as cleanup_error:
                    self._logger.warning(
                        f" 🖼️\u00a0 Failed to cleanup temporary file {temp_path}: {cleanup_error}"
                    )

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64 with file: {e}")
            return ""

    def _qimage_to_base64_memory(self, image: QImage) -> str:
        """
        Convert QImage to base64 using memory buffer approach (new method).

        Args:
            image: QImage to convert

        Returns:
            str: Base64 encoded image data
        """
        try:
            from PySide6.QtCore import QBuffer, QByteArray, QIODevice

            # Validate image
            if image.isNull():
                self._logger.error(" 🖼️\u00a0 Image is null, cannot convert")
                return ""

            self._logger.debug(
                f" 🖼️\u00a0 Image size: {image.width()}x{image.height()}, format: {image.format()}"
            )

            # Create byte array and buffer
            byte_array = QByteArray()
            buffer = QBuffer(byte_array)

            if not buffer.open(QIODevice.OpenModeFlag.WriteOnly):
                self._logger.error(" 🖼️\u00a0 Failed to open buffer for writing")
                return ""

            # Save QImage to buffer in PNG format
            # Try to save directly first, then fallback to conversion
            save_success = image.save(buffer, "PNG")  # type: ignore
            if not save_success:
                # Fallback: convert to RGB32 format
                rgb_image = image.convertToFormat(QImage.Format.Format_RGB32)
                buffer.close()
                buffer = QBuffer(byte_array)
                buffer.open(QIODevice.OpenModeFlag.WriteOnly)
                save_success = rgb_image.save(buffer, "PNG")  # type: ignore
            buffer.close()

            if not save_success:
                self._logger.error(" 🖼️\u00a0 Failed to save QImage to memory buffer")
                return ""

            # Get the size of saved data
            image_bytes = byte_array.data()
            if not image_bytes:
                self._logger.error(" 🖼️\u00a0 No data saved to buffer")
                return ""

            self._logger.debug(f" 🖼️\u00a0 Image saved to buffer: {len(image_bytes)} bytes")

            # Convert to base64
            base64_string = base64.b64encode(image_bytes).decode("utf-8")

            self._logger.debug(
                f" 🖼️\u00a0 Converted image to base64 from memory: {len(base64_string)} characters"
            )
            return base64_string

        except Exception as e:
            self._logger.error(f"Error converting QImage to base64 from memory: {e}", exc_info=True)
            return ""

    def _get_temp_image_path(self) -> Path:
        """
        Get appropriate temporary file path for clipboard image based on execution mode.

        Returns:
            Path: Temporary file path for clipboard image
        """

        try:
            # Determine execution mode - this would need to be passed or accessed differently
            # For now, use system temp directory

            temp_dir = Path(tempfile.gettempdir())

            # Create unique temporary file name
            temp_filename = f"writingtools_clipboard_{int(time.time() * 1000)}.png"
            temp_path = temp_dir / temp_filename

            self._logger.debug(f"Using temporary image path: {temp_path}")
            return temp_path

        except Exception as e:
            self._logger.error(f"Error creating temp image path: {e}")
            # Fallback to system temp directory

            return (
                Path(tempfile.gettempdir())
                / f"writingtools_clipboard_{int(time.time() * 1000)}.png"
            )
