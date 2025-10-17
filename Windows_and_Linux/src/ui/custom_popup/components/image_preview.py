"""
Image preview component for CustomPopupWindow.
Handles image display and removal functionality.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ....writing_tools_app import WritingToolsApp


class ImagePreview(QWidget):
    """Image preview widget for displaying clipboard images."""

    def __init__(self, app: "WritingToolsApp", image: QtGui.QImage | None):
        super().__init__()
        self.app = app
        self.image = image
        self.image_display: QLabel | None = None
        self.remove_image_button: QPushButton | None = None
        self._setup_ui()

    def _setup_ui(self) -> None:
        """Setup the image preview container."""
        self.setStyleSheet(self.app.styles["container"])

        layout = QVBoxLayout(self)
        layout.setContentsMargins(4, 4, 4, 4)
        layout.setSpacing(5)

        # Header row with label and remove button
        self._create_header(layout)

        # Image display
        self._create_image_display(layout)

    def _create_header(self, layout: QVBoxLayout) -> None:
        """Create the header with label and remove button."""
        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, -2, 0)
        header_layout.setSpacing(5)

        # Image preview label
        image_label = QLabel("📷 Image from Clipboard:")
        image_label.setStyleSheet(self.app.styles["label_small"])
        header_layout.addWidget(image_label)

        # Spacer to push button to the right
        header_layout.addStretch()

        # Remove image button (X)
        self.remove_image_button = QPushButton("×")
        self.remove_image_button.setFixedSize(20, 20)
        self.remove_image_button.setStyleSheet(self.app.styles["delete_button"])
        self.remove_image_button.setToolTip(
            "Remove image from clipboard\n"
            "This will close the application and clear the clipboard.\n"
            "Restart with hotkey to continue without the image."
        )

        header_layout.addWidget(self.remove_image_button)
        layout.addWidget(header_row)

    def _create_image_display(self, layout: QVBoxLayout) -> None:
        """Create the image display label."""
        self.image_display = QLabel()
        self.image_display.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_display.setMinimumHeight(120)
        self.image_display.setMaximumHeight(200)
        self.image_display.setStyleSheet(self.app.styles["image_preview"])

        # Scale and display the image
        if self.image:
            # Create a scaled pixmap for preview
            pixmap = QtGui.QPixmap.fromImage(self.image)
            scaled_pixmap = pixmap.scaled(
                300,
                180,  # Max preview size
                QtCore.Qt.AspectRatioMode.KeepAspectRatio,
                QtCore.Qt.TransformationMode.SmoothTransformation,
            )
            self.image_display.setPixmap(scaled_pixmap)
        else:
            self.image_display.setText(_("No image preview available"))

        layout.addWidget(self.image_display)

    def connect_remove_signal(self, callback) -> None:
        """Connect the remove image button clicked signal."""
        if self.remove_image_button:
            self.remove_image_button.clicked.connect(callback)

    def remove_image(self) -> None:
        """Remove image from clipboard and close application."""
        try:
            # Clear the clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.clear()

            # Show a brief message to the user
            self.app.ui_manager.show_message_signal.emit(
                "Image Removed",
                "Image has been removed from clipboard.\n"
                "Application will close.\n"
                "Restart with hotkey to continue without the image.",
            )

            # Clean the image and close - this will be handled by the parent window

        except Exception:
            # In case of error, just close the popup - handled by parent
            pass


def _(x):
    return x
