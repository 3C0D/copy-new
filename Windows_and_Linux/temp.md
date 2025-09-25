On va refactoriser writing tool APP Déjà, on va extraire ces parties là. on va commencer avec image_processor

dans src/
WritingToolApp/
├── core/
│   ├── __init__.py
│   ├── image_processor.py  # Logique images
│   └── popup_manager.py    # Logique popup
├── ui/
│   └── ... (vos modules UI existants)


import urllib.parse
from pathlib import Path
from typing import Optional, Tuple
from QtCore import QApplication
from QtGui import QImage, QIcon
from QtWidgets import QWidget


class ImageProcessor:
    """Handles image processing and clipboard operations."""
    
    SUPPORTED_IMAGE_EXTENSIONS = {'.png', '.jpg', '.jpeg', '.gif', '.bmp', '.tiff', '.tif', '.webp', '.svg'}
    FILE_URL_PREFIX = "file:///"
    
    def __init__(self, logger):
        self._logger = logger
    
    def _normalize_path_text(self, text: str) -> Optional[str]:
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
            normalized_text = normalized_text[len(self.FILE_URL_PREFIX):]
            try:
                normalized_text = urllib.parse.unquote(normalized_text)
            except Exception as e:
                self._logger.debug(f"Error URL decoding path: {e}")
                return None
                
        return normalized_text if normalized_text else None
    
    def _is_file_path(self, text: str) -> bool:
        """Check if text looks like a file path."""
        try:
            path = Path(text)
            return path.exists() and path.is_file()
        except Exception:
            return False
    
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
            
        if not self._is_file_path(normalized_path):
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
    
    def _load_image_from_path(self, text: str) -> Optional[QImage]:
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
            
            self._logger.debug(f"Successfully loaded image from path: {path} - size: {image.width()}x{image.height()}")
            return image
            
        except Exception as e:
            self._logger.error(f"Error loading image from path {text}: {e}")
            return None
    
    def _clear_clipboard_safely(self, success: bool = True) -> None:
        """
        Clear clipboard only if operation was successful.
        
        Args:
            success: Whether the previous operation was successful
        """
        if not success:
            return
            
        try:
            clipboard = QApplication.clipboard()
            if clipboard:
                clipboard.clear()
                self._logger.debug("Clipboard cleared after successful operation")
        except Exception as e:
            self._logger.warning(f"Failed to clear clipboard: {e}")
    
    def _process_clipboard_image_data(self, mime_data) -> Optional[QImage]:
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
    
    def get_clipboard_image(self) -> Optional[QImage]:
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
                    self._clear_clipboard_safely(True)
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
                        self._clear_clipboard_safely(True)
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


class PopupManager:
    """Manages popup window creation and display."""
    
    def __init__(self, parent, logger):
        self.parent = parent
        self._logger = logger
        self.image_processor = ImageProcessor(logger)
        
        # State variables
        self.image: Optional[QImage] = None
        self.has_image: bool = False
        self.original_selection: Optional[str] = None
        self.popup_window = None
    
    def _determine_image_source(self) -> Tuple[Optional[QImage], Optional[str]]:
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
            self._logger.debug(f"🖼️ Image found in clipboard - size: {self.image.width()}x{self.image.height()}")
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
                self._logger.debug(f"🖼️ Image loaded from selection path - size: {image.width()}x{image.height()}")
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
        import ui.CustomPopupWindow
        import ui_utils
        
        self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(
            self.parent, selected_text, image
        )
        
        # Set window icon
        icon_path = ui_utils.get_icon_path(
            self.parent,
            "app_icon",
            with_theme=False,
        )
        if icon_path.exists():
            self.popup_window.setWindowIcon(QIcon(icon_path.as_posix()))
    
    def _display_popup_window(self, selected_text: Optional[str]) -> None:
        """Display and position the popup window."""
        if not self.popup_window:
            return
        
        import ui_utils
        
        self.popup_window.show()
        self.position_popup_window(self.popup_window, selected_text)
        ui_utils.existing_window_on_top(self.popup_window)
    
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
    def get_selected_text(self, sleep_duration: float = 0.1) -> Optional[str]:
        """Get currently selected text. Should be implemented in actual class."""
        raise NotImplementedError("This method should be implemented in the actual class")
    
    def position_popup_window(self, window, selected_text: Optional[str]) -> None:
        """Position the popup window. Should be implemented in actual class."""
        raise NotImplementedError("This method should be implemented in the actual class")