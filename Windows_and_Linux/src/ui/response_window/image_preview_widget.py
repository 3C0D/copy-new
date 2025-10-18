"""
Image Preview Widget - Manages the collapsible image preview section.
"""

from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QHBoxLayout, QLabel, QPushButton, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


def _(x):
    return x


class ImagePreviewWidget(QWidget):
    """Collapsible image preview widget for response window"""

    def __init__(
        self,
        app: "WritingToolsApp",
        image: QtGui.QImage,
        parent: QWidget | None = None,
    ):
        super().__init__(parent)
        self.app = app
        self.image = image
        self.image_display_collapsed = False

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the image preview widget"""
        self.setStyleSheet(self.app.styles["response_window_image_section"])

        section_layout = QVBoxLayout(self)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(8)

        # Header with collapse/expand button
        header_layout = QHBoxLayout()

        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.setStyleSheet(self.app.styles["response_window_toggle_button"])
        self.toggle_button.clicked.connect(self._toggle_image_preview)
        header_layout.addWidget(self.toggle_button)

        header_label = QLabel(_("Source Image"))
        header_label.setStyleSheet(self.app.styles["response_window_header_label"])
        header_layout.addWidget(header_label)

        header_layout.addStretch()

        # Image info
        info_text = f"{self.image.width()}×{self.image.height()} pixels"
        info_label = QLabel(info_text)
        info_label.setStyleSheet(self.app.styles["response_window_info_label"])
        header_layout.addWidget(info_label)

        section_layout.addLayout(header_layout)

        # Image display
        self.image_display_widget = QLabel()
        self.image_display_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)
        self.image_display_widget.setStyleSheet(self.app.styles["response_window_image_display"])

        # Scale image for display
        pixmap = QtGui.QPixmap.fromImage(self.image)
        scaled_pixmap = pixmap.scaled(
            400,
            300,  # Max display size in response window
            QtCore.Qt.AspectRatioMode.KeepAspectRatio,
            QtCore.Qt.TransformationMode.SmoothTransformation,
        )
        self.image_display_widget.setPixmap(scaled_pixmap)

        section_layout.addWidget(self.image_display_widget)

    def _toggle_image_preview(self) -> None:
        """Toggle the image preview visibility."""
        if self.image_display_collapsed:
            self.image_display_widget.setVisible(True)
            self.toggle_button.setText("▼")
            self.image_display_collapsed = False
        else:
            self.image_display_widget.setVisible(False)
            self.toggle_button.setText("▶")
            self.image_display_collapsed = True

    def refresh_language(self) -> None:
        """Refresh language-specific text elements"""
        # Update header label
        for child in self.findChildren(QLabel):
            if child.text() == "Source Image" or _("Source Image") in child.text():
                child.setText(_("Source Image"))
                break
