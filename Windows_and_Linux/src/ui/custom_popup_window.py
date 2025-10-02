"""
Writing Tools - CustomPopupWindow module
Used for displaying a custom popup window with various input fields and options.
"""

import logging
from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config.constants import (
    ANTHROPIC_MODELS,
    GEMINI_MODELS,
    MISTRAL_MODELS,
    OPENAI_MODELS,
)
from ..config.data_operations import create_default_actions_config
from ..config.interfaces import ActionConfig, ActionConfigWithName
from .ui_utils import ThemeBackground, ui_utils

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


def _(x):
    return x


class ToggleSwitch(QCheckBox):
    """Custom toggle switch widget with sliding circle animation"""

    toggled = QtCore.Signal(bool)

    def __init__(self, app: "WritingToolsApp", parent: QWidget | None = None):
        super().__init__(parent)
        self.app = app
        self.setFixedSize(50, 24)
        self.setCheckable(True)
        self._circle_position: int = 2
        self._animation = QtCore.QPropertyAnimation(self, b"circle_position")
        self._animation.setDuration(150)

        # Connect native QCheckBox signal to animation
        self.toggled.connect(self._animate_to_position)

    def setChecked(self, arg__1: bool) -> None:
        super().setChecked(arg__1)

    def setCheckable(self, arg__1: bool) -> None:
        super().setCheckable(arg__1)

    @QtCore.Property(int)
    def circle_position(self) -> int:  # type: ignore
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos: int) -> None:
        self._circle_position = pos
        self.update()

    def _animate_to_position(self) -> None:
        start_pos = 2 if not self.isChecked() else 28
        end_pos = 28 if self.isChecked() else 2

        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setChecked(not self.isChecked())

    def paintEvent(self, arg__1: QtGui.QPaintEvent) -> None:
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Colors from styles
        if self.isChecked():
            bg_color = QtGui.QColor(self.app.styles["color_primary"])
        else:
            bg_color = QtGui.QColor(self.app.styles["color_secondary"])

        circle_color = QtGui.QColor(self.app.styles["color_background"])

        # Draw background
        painter.setBrush(QtGui.QBrush(bg_color))
        painter.setPen(QtCore.Qt.PenStyle.NoPen)
        painter.drawRoundedRect(0, 0, 50, 24, 12, 12)

        # Draw circle
        painter.setBrush(QtGui.QBrush(circle_color))
        painter.drawEllipse(self._circle_position, 2, 20, 20)


class ButtonEditDialog(QDialog):
    """
    Dialog for editing or creating a button's properties
    (name/title, system instruction, open_in_window, etc.).
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        parent: QWidget | None = None,
        button_data: dict | None = None,
        title: str = "Edit Button",
        is_image_context: bool = False,
    ):
        super().__init__(parent)
        self.app = app
        self.is_image_context = is_image_context
        self.button_data = (
            button_data
            if button_data
            else {
                "prefix": "Analyze this image:\n\n"
                if is_image_context
                else "Make this change to the following text:\n\n",
                "instruction": "",
                "icon": "icons/magnifying-glass",
                "open_in_window": False,
                "image": is_image_context,
            }
        )
        if is_image_context:
            self.button_data["image"] = True
        self.setWindowTitle(title)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name
        name_label = QLabel("Button Name:")
        name_label.setStyleSheet(self.app.styles["label"])
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(self.app.styles["input"])
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # No checkbox - image context is determined by popup context

        # Instruction (changed to a multiline QPlainTextEdit)
        content_type = "image" if self.is_image_context else "selected text"
        instruction_label = QLabel(
            f"What should your AI do with your {content_type}? (System Instruction)"
        )
        instruction_label.setStyleSheet(self.app.styles["label"])
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(self.app.styles["input"])
        self.instruction_input.setPlainText(self.button_data.get("instruction", ""))
        self.instruction_input.setMinimumHeight(100)
        if self.is_image_context:
            placeholder = """Examples:
    - Extract and translate any text visible in this image.
    - Describe this image in detail.
    - What objects can you see in this image?
    - Analyse the mood or atmosphere of this image.
    - What colors are prominent in this image?
    - Describe this image for someone who cannot see it."""
        else:
            placeholder = """Examples:
    - Fix / improve / explain this code.
    - Make it funny.
    - Add emojis!
    - Roast this!
    - Translate to English.
    - Make the text title case.
    - If it's all caps, make it all small, and vice-versa.
    - Write a reply to this.
    - Analyse potential biases in this news article."""

        self.instruction_input.setPlaceholderText(placeholder)
        layout.addWidget(instruction_label)
        layout.addWidget(self.instruction_input)

        if self.is_image_context:
            # Force chat note for image actions
            self.force_chat_label = QLabel(
                "<i>Image actions always open in chat window (force chat)</i>"
            )
            self.force_chat_label.setStyleSheet(self.app.styles["label_small"])
            layout.addWidget(self.force_chat_label)
        else:
            # open_in_window options - only for text actions
            self.display_label = QLabel("How should your AI response be shown?")
            self.display_label.setStyleSheet(self.app.styles["label"])
            layout.addWidget(self.display_label)

            self.radio_layout = QHBoxLayout()
            self.replace_radio = QRadioButton("Replace the selected text")
            self.window_radio = QRadioButton("In a chat pop-up window")
            for r in (self.replace_radio, self.window_radio):
                r.setStyleSheet(self.app.styles["radio"])

            self.replace_radio.setChecked(not self.button_data.get("open_in_window", False))
            self.window_radio.setChecked(self.button_data.get("open_in_window", False))

            self.radio_layout.addWidget(self.replace_radio)
            self.radio_layout.addWidget(self.window_radio)
            layout.addLayout(self.radio_layout)

            # Indicator information - only for text actions
            self.indicator_label = QLabel(
                "<i>A small indicator will be shown on the button: Ⓡ for replace, Ⓒ for chat</i>"
            )
            self.indicator_label.setStyleSheet(self.app.styles["label_small"])
            layout.addWidget(self.indicator_label)

        # OK & Cancel
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        for btn in (ok_button, cancel_button):
            btn.setStyleSheet(self.app.styles["button"])

        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addLayout(btn_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.setStyleSheet(self.app.styles["dialog"])

    def get_button_data(self) -> ActionConfigWithName:
        return {
            "name": self.name_input.text(),
            "prefix": "Analyze this image:\n\n"
            if self.is_image_context
            else "Make this change to the following text:\n\n",
            # Retrieve multiline text
            "instruction": self.instruction_input.toPlainText(),
            "icon": "icons/custom",
            "open_in_window": self.window_radio.isChecked() if not self.is_image_context else True,
            "image": self.is_image_context,
        }


class DraggableButton(QPushButton):
    def __init__(
        self, app: "WritingToolsApp", parent_popup: "CustomPopupWindow", key: str, text: str
    ):
        super().__init__(text, parent_popup)
        self.app = app
        self.popup: CustomPopupWindow = parent_popup
        self.key: str = key
        self.drag_start_position: QtCore.QPoint | None = None
        self.setAcceptDrops(True)
        self.icon_container: QWidget | None = None
        self.action_indicator: QLabel | None = None

        # Enable mouse tracking and hover events, and styled background
        self.setMouseTracking(True)
        self.setAttribute(Qt.WidgetAttribute.WA_Hover, True)
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed)
        self.setFixedSize(120, 40)

        # Define base style using the dynamic property instead of the :hover pseudo-class
        self.setStyleSheet(self.app.styles["button"])

    def refresh_button_style(self) -> None:
        """Refresh the button style when color mode changes."""
        self.setStyleSheet(self.app.styles["button"])

    def enterEvent(self, event: QtGui.QEnterEvent) -> None:
        # Only update the hover property if NOT in edit mode.
        if not self.popup.edit_mode:
            self.setProperty("hover", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event: QtCore.QEvent) -> None:
        if not self.popup.edit_mode:
            self.setProperty("hover", False)
            self.style().unpolish(self)
            self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, e: QtGui.QMouseEvent) -> None:
        if e.button() == Qt.MouseButton.LeftButton:
            if self.popup.edit_mode:
                self.drag_start_position = e.pos()
                e.accept()
                return
        super().mousePressEvent(e)

    def mouseMoveEvent(self, arg__1: QtGui.QMouseEvent) -> None:
        if not (arg__1.buttons() & Qt.MouseButton.LeftButton) or not self.drag_start_position:
            return

        distance = (arg__1.pos() - self.drag_start_position).manhattanLength()
        if distance < QApplication.startDragDistance():
            return

        if self.popup.edit_mode:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            idx = self.popup.button_widgets.index(self)
            mime_data.setData("application/x-button-index", str(idx).encode())
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(arg__1.pos())

            self.drag_start_position = None
            _ = drag.exec_(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event: QtGui.QDragEnterEvent) -> None:
        if self.popup.edit_mode and event.mimeData().hasFormat("application/x-button-index"):
            event.acceptProposedAction()
            self.setStyleSheet(
                self.app.styles["button"]
                + """
                QPushButton {
                    border: 2px dashed #666;
                }
                """,
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        self.setStyleSheet(self.app.styles["button"])
        event.accept()

    def dropEvent(self, event: QtGui.QDropEvent) -> None:
        if not self.popup.edit_mode or not event.mimeData().hasFormat("application/x-button-index"):
            event.ignore()
            return

        mime_data = event.mimeData().data("application/x-button-index")
        source_idx = int(bytes(mime_data).decode())
        target_idx = self.popup.button_widgets.index(self)

        if source_idx != target_idx:
            bw = self.popup.button_widgets
            bw[source_idx], bw[target_idx] = bw[target_idx], bw[source_idx]
            self.popup.rebuild_grid_layout()
            self.popup.update_json_from_grid()

        self.setStyleSheet(self.app.styles["button"])
        event.setDropAction(Qt.DropAction.MoveAction)
        event.acceptProposedAction()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle resize events to reposition UI elements."""
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())
        if self.action_indicator:
            self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)

    def set_action_indicator(self, open_in_window: bool, is_image_action: bool | None) -> None:
        """Set the action indicator (Ⓡ or Ⓒ) based on action type."""
        if is_image_action:
            return

        if self.action_indicator:
            self.action_indicator.deleteLater()

        self.action_indicator = QLabel(self)

        indicator_text = "Ⓒ" if open_in_window else "Ⓡ"

        self.action_indicator.setText(indicator_text)
        self.action_indicator.setStyleSheet(self.app.styles["action_indicator"])
        self.action_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)
        self.action_indicator.show()


class CustomPopupWindow(QWidget):
    def __init__(
        self,
        app: "WritingToolsApp",
        selected_text: str | None = None,
        image: QtGui.QImage | None = None,
    ):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.app = app
        self.selected_text: str | None = selected_text
        self.image: QtGui.QImage | None = image
        self.edit_mode = False
        self.has_sel_text = bool(selected_text.strip() if selected_text else False)
        self.has_image = bool(image is not None)

        # UI Components - initialized to None
        self._init_ui_components()

        # Variables for dragging functionality
        self.is_dragging = False
        self.drag_start_position: QtCore.QPoint | None = None

        self.button_widgets: list[Any] = []
        self.init_ui()

    def _init_ui_components(self) -> None:
        """Initialize all UI component references to None."""
        self.drag_label: QLabel | None = None
        self.edit_button: QPushButton | None = None
        self.reset_button: QPushButton | None = None
        self.edit_close_button: QPushButton | None = None
        self.close_button: QPushButton | None = None
        self.custom_input: QLineEdit | None = None
        self.input_area: QWidget | None = None
        self.update_label: QLabel | None = None
        self.force_chat_toggle: QCheckBox | None = None
        self.force_chat_lock: QPushButton | None = None
        self.force_chat_area: QWidget | None = None
        self.top_bar_widget: QWidget | None = None
        self.remove_image_button: QPushButton | None = None
        self.image_preview_container: QWidget | None = None

    def init_ui(self):
        """Initialize the main UI structure."""
        self.edit_mode = False  # Ensure we start in normal mode
        self._setup_window_properties()
        main_layout = self._create_main_layout()
        content_layout = self._create_background_and_content_layout(main_layout)

        self._create_top_bar(content_layout)
        self._create_input_area(content_layout)
        if self.has_sel_text:
            self.create_force_chat_toggle(content_layout)
        if self.has_sel_text or self.has_image:
            buttons_layout = self._create_buttons_scroll_layout(content_layout)
            self._setup_buttons_and_content(buttons_layout)
        self._create_image_preview_area(content_layout)
        self._show_update_notice_if_available(content_layout)

        self._finalize_ui_setup()

    def _setup_window_properties(self) -> None:
        """Configure window flags and properties."""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")
        self.min_width = 300  # be sure to see action buttons and scrollbar
        self.min_height = 150  # when no selected text or image
        self.setMinimumSize(self.min_width, self.min_height)

    def _create_main_layout(self) -> QVBoxLayout:
        """Create and configure the main layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        return main_layout

    def _create_background_and_content_layout(self, main_layout: QVBoxLayout) -> QVBoxLayout:
        """Create background widget and content layout."""
        self.background = ThemeBackground(
            self.app,
            self,
            self.app.settings_manager.background_theme or "gradient",
            is_popup=True,
            border_radius=10,
        )
        main_layout.addWidget(self.background)

        content_layout = QVBoxLayout(self.background)
        content_layout.setContentsMargins(10, 4, 10, 10)
        content_layout.setSpacing(10)
        return content_layout

    def _create_top_bar(self, content_layout: QVBoxLayout) -> None:
        """Create the top bar with all its components."""
        self.top_bar_widget = QWidget()
        self.top_bar_widget.setFixedHeight(30)
        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        if self.has_sel_text or self.has_image:
            self._create_reset_button(top_bar_layout)
            self._create_drag_label(top_bar_layout)
            self._create_edit_buttons(top_bar_layout)
        self._create_close_button(top_bar_layout)
        # Configure mouse events for draggable top bar
        self.setup_draggable_top_bar()

        content_layout.addWidget(self.top_bar_widget)

    def _create_reset_button(self, layout: QHBoxLayout) -> None:
        """Create the reset button for edit mode."""
        self.reset_button = QPushButton()
        reset_icon_path = ui_utils.get_icon_path(self.app, "restore", with_theme=True)
        if reset_icon_path.exists():
            self.reset_button.setIcon(QtGui.QIcon(reset_icon_path.as_posix()))

        self.reset_button.setText("")
        self.reset_button.setFixedSize(24, 24)
        self.reset_button.setStyleSheet(self._get_icon_button_style())
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.reset_button.setToolTip(_("Reset to Default Buttons"))
        self.reset_button.installEventFilter(self)

        layout.addWidget(self.reset_button, 0, Qt.AlignmentFlag.AlignLeft)

    def _create_drag_label(self, layout: QHBoxLayout) -> None:
        """Create the drag instruction label for edit mode."""
        self.drag_label = QLabel("Drag to rearrange")
        self.drag_label.setStyleSheet(self.app.styles["label"])
        self.drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_label.hide()

        layout.addWidget(
            self.drag_label,
            1,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter,
        )

    def _create_edit_buttons(self, layout: QHBoxLayout) -> None:
        """Create edit and edit close buttons."""
        # Edit close button (shown in edit mode)
        self.edit_close_button = QPushButton("×")
        self.edit_close_button.setFixedSize(24, 24)
        self.edit_close_button.setStyleSheet(self._get_close_button_style())
        self.edit_close_button.clicked.connect(self.exit_edit_mode)
        self.edit_close_button.setToolTip(_("Exit Edit Mode"))
        self.edit_close_button.hide()
        self.edit_close_button.installEventFilter(self)
        layout.addWidget(self.edit_close_button, 0, Qt.AlignmentFlag.AlignRight)

        # Edit button (shown in normal mode)
        self.edit_button = QPushButton()
        pencil_icon = ui_utils.get_icon_path(self.app, "pencil", with_theme=True)
        if pencil_icon.exists():
            self.edit_button.setIcon(QtGui.QIcon(pencil_icon.as_posix()))

        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setStyleSheet(self._get_icon_button_style())
        self.edit_button.clicked.connect(self.enter_edit_mode)
        self.edit_button.setToolTip(_("Edit Tools Layout"))
        self.edit_button.installEventFilter(self)
        layout.addWidget(self.edit_button, 0, Qt.AlignmentFlag.AlignLeft)

    def _create_close_button(self, layout: QHBoxLayout) -> None:
        """Create the main close button."""
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet(self._get_close_button_style())
        self.close_button.clicked.connect(self.close)
        self.close_button.installEventFilter(self)
        layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)

    def _get_icon_button_style(self) -> str:
        """Get stylesheet for icon buttons."""
        return self.app.styles["icon_small_button"]

    def _get_close_button_style(self) -> str:
        """Get stylesheet for close buttons."""
        return self.app.styles["close_small_button"]

    def _create_input_area(self, content_layout: QVBoxLayout) -> None:
        """Create the input area with text field and send button."""
        self.input_area = QWidget()
        input_layout = QVBoxLayout(self.input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)
        input_layout.setSpacing(8)

        # Create horizontal layout for input field and send button
        input_row = QWidget()
        input_row_layout = QHBoxLayout(input_row)
        input_row_layout.setContentsMargins(0, 0, 0, 0)

        self._create_custom_input(input_row_layout)
        self._create_send_button(input_row_layout)

        input_layout.addWidget(input_row)
        content_layout.addWidget(self.input_area)

    def _create_image_preview_area(self, content_layout: QVBoxLayout) -> None:
        """Create the image preview area if there's an image."""
        if self.has_image:
            self._create_image_preview(content_layout)

    def _create_image_preview(self, content_layout: QVBoxLayout) -> None:
        """Create an image preview widget in the content layout."""
        # Image preview container
        self.image_preview_container = QWidget()
        preview_container = self.image_preview_container
        preview_container.setStyleSheet(self.app.styles["container"])
        preview_layout = QVBoxLayout(preview_container)
        preview_layout.setContentsMargins(4, 4, 4, 4)  # Reduced padding to fit button better
        preview_layout.setSpacing(5)

        # Header row with label and remove button
        header_row = QWidget()
        header_layout = QHBoxLayout(header_row)
        header_layout.setContentsMargins(0, 0, -2, 0)  # Slight left shift for button
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
        self.remove_image_button.clicked.connect(self._remove_image_from_clipboard)
        self.remove_image_button.setToolTip(
            "Remove image from clipboard\n"
            "This will close the application and clear the clipboard.\n"
            "Restart with hotkey to continue without the image."
        )

        header_layout.addWidget(self.remove_image_button)
        preview_layout.addWidget(header_row)

        # Actual image display
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
            self.image_display.setText("No image preview available")

        preview_layout.addWidget(self.image_display)
        content_layout.addWidget(preview_container)

    def _remove_image_from_clipboard(self) -> None:
        """Remove image from clipboard and close application."""
        try:
            # Clear the clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.clear()

            # Show a brief message to the user
            self.app.ui_manager.show_message_signal.emit(
                "Image Removed",
                f"Image has been removed from clipboard.\n"
                f"Application will close.\n"
                f"Restart with {self.app.settings_manager.hotkey} to continue.",
            )

            #  Clean the image and close
            self.app.popup_manager.clean_image()
            self.close()

            # Schedule application quit after a brief delay to allow message to be shown
            # QtCore.QTimer.singleShot(2000, self.app.quit)

        except Exception:
            # In case of error, just close the popup
            self.close()

    def _create_custom_input(self, layout: QHBoxLayout) -> None:
        """Create the custom input text field."""
        self.custom_input = QLineEdit()
        placeholder = (
            _("Describe your change...")
            if self.has_sel_text
            else _("Ask anything about this image...")
            if self.has_image
            else _("Ask your AI...")
        )
        self.custom_input.setPlaceholderText(placeholder)
        self.custom_input.setStyleSheet(self._get_input_style())
        self.custom_input.returnPressed.connect(self.on_custom_change)
        layout.addWidget(self.custom_input)

    def _create_send_button(self, layout: QHBoxLayout) -> None:
        """Create the send button for the input area."""
        send_btn = QPushButton()
        send_icon = ui_utils.get_icon_path(self.app, "send", with_theme=True)
        if send_icon.exists():
            send_btn.setIcon(QtGui.QIcon(send_icon.as_posix()))

        send_btn.setStyleSheet(self._get_send_button_style())
        # Use a fallback size if self.custom_input is None
        input_height = self.custom_input.sizeHint().height() if self.custom_input else 32
        send_btn.setFixedSize(input_height, input_height)
        send_btn.clicked.connect(self.on_custom_change)
        layout.addWidget(send_btn)

    def _get_input_style(self) -> str:
        """Get the styling for input elements."""
        return self.app.styles["input_full"]

    def _get_send_button_style(self) -> str:
        """Get stylesheet for send button."""
        return self.app.styles["send_button"]

    def _create_buttons_scroll_layout(self, parent_layout: QVBoxLayout) -> QVBoxLayout:
        """Create a scrollable layout specifically for buttons."""
        buttons_scroll = QScrollArea()
        buttons_scroll.setWidgetResizable(True)  # vertical scroll when more action buttons
        buttons_scroll.setFrameShape(QFrame.Shape.NoFrame)  # No border
        buttons_scroll.setMaximumHeight(250)

        buttons_widget = QWidget()
        buttons_widget.setStyleSheet("background: transparent;")
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        buttons_scroll.setWidget(buttons_widget)
        parent_layout.addWidget(buttons_scroll)

        return buttons_layout

    def _setup_buttons_and_content(self, content_layout: QVBoxLayout) -> None:
        """Setup buttons and main content based on available input."""
        if self.has_sel_text or self.has_image:
            self.build_buttons_list()
            self.rebuild_grid_layout(content_layout)
            self.initialize_button_visibility()
        else:
            # Only custom instructions input if no selected text
            if self.custom_input is not None:
                self.custom_input.setMinimumWidth(400)

    def _show_update_notice_if_available(self, content_layout: QVBoxLayout) -> None:
        """Show update notice if an update is available."""
        update_available = self.app.settings_manager.update_available or False

        if update_available:
            self.update_label = QLabel()
            self.update_label.setOpenExternalLinks(True)
            self.update_label.setText(
                '<a href="https://github.com/theJayTea/WritingTools/releases" '
                'style="color:rgb(255, 0, 0); text-decoration: underline; font-weight: bold;">'
                "There's an update! :D Download now."
                "</a>"
            )
            self.update_label.setStyleSheet("margin-top: 10px;")
            content_layout.addWidget(
                self.update_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
            )

    def _finalize_ui_setup(self) -> None:
        """Finalize UI setup with event filters and focus."""
        self.installEventFilter(self)
        QtCore.QTimer.singleShot(
            250, lambda: self.custom_input.setFocus() if self.custom_input else None
        )

    def setup_draggable_top_bar(self) -> None:
        """Configure top bar to be draggable"""
        if self.top_bar_widget:
            # Install event filter on top bar
            self.top_bar_widget.installEventFilter(self)

            # Change cursor to indicate draggable area
            self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Event filter that handles cursor changes and dragging behavior for the top bar.

        This filter manages:
        - Setting appropriate cursors for buttons and top bar
        - Handling drag & drop functionality for window movement
        - Window deactivation behavior
        """
        # Handle buttons cursors first
        if watched in [
            self.close_button,
            self.edit_close_button,
            self.reset_button,
            self.edit_button,
        ]:
            if event.type() in [QtCore.QEvent.Type.Enter, QtCore.QEvent.Type.Leave]:
                if watched == self.close_button and self.close_button:
                    self.close_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.edit_close_button and self.edit_close_button:
                    self.edit_close_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.reset_button and self.reset_button:
                    self.reset_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.edit_button and self.edit_button:
                    self.edit_button.setCursor(Qt.CursorShape.ArrowCursor)
            return False

        # Handle dragging via top bar
        if watched == self.top_bar_widget and isinstance(event, QtGui.QMouseEvent):
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.is_dragging = True
                    self.drag_start_position = event.globalPosition().toPoint() - self.pos()
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.ClosedHandCursor)
                    return True

            elif event.type() == QtCore.QEvent.Type.MouseMove:
                if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
                    if self.drag_start_position is not None:
                        new_position = event.globalPosition().toPoint() - self.drag_start_position
                        self.move(new_position)
                    return True

            elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.is_dragging = False
                    self.drag_start_position = None
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)
                    return True

            elif event.type() == QtCore.QEvent.Type.Enter:
                if not self.is_dragging:
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)

            elif event.type() == QtCore.QEvent.Type.Leave:
                if not self.is_dragging:
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.ArrowCursor)

        # The window will now stay open when clicking outside
        return super().eventFilter(watched, event)

    def create_force_chat_toggle(self, parent_layout: QVBoxLayout) -> None:
        """Create the Force Chat toggle with lock button."""
        self.force_chat_area = QWidget()
        force_chat_layout = QHBoxLayout(self.force_chat_area)
        force_chat_layout.setContentsMargins(5, 2, 5, 2)
        force_chat_layout.setSpacing(6)

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

        # Connect signals
        self.force_chat_toggle.toggled.connect(self.on_force_chat_toggled)
        self.force_chat_lock.toggled.connect(self.on_force_chat_lock_toggled)

        # Add to layout
        force_chat_layout.addWidget(label)
        force_chat_layout.addWidget(self.force_chat_toggle)
        force_chat_layout.addWidget(self.force_chat_lock)
        force_chat_layout.addStretch()

        parent_layout.addWidget(self.force_chat_area)

    def update_lock_icon(self) -> None:
        """Update the lock icon based on current state."""
        # Ensure the lock button exists
        if not self.force_chat_lock:
            return
        if self.force_chat_lock.isChecked():
            self.force_chat_lock.setText("🔒")
        else:
            self.force_chat_lock.setText("🔓")

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

    def get_actions(self) -> dict[str, ActionConfig]:
        """
        Get actions directly from the unified settings system.
        Returns ActionConfig objects, no conversion needed.
        """
        return self.app.settings_manager.actions

    @staticmethod
    def action_config_to_dict(action_config: ActionConfig) -> dict:
        """
        Convert ActionConfig to dict format for ButtonEditDialog compatibility.
        Only use when dict format is specifically needed.
        """
        return {
            "prefix": action_config.get("prefix", ""),
            "instruction": action_config.get("instruction", ""),
            "icon": action_config.get("icon", ""),
            "open_in_window": action_config.get("open_in_window", False),
            "image": action_config.get("image", False),
        }

    def build_buttons_list(self) -> None:
        """
        Loads actions from unified settings system,
        creates DraggableButton for each (except "Custom"),
        filtering based on whether image is present,
        storing them in self.button_widgets in the same order.
        """

        # Properly delete old button widgets before clearing the list
        for old_button in self.button_widgets:
            if hasattr(old_button, "icon_container") and old_button.icon_container:
                old_button.icon_container.deleteLater()
            if hasattr(old_button, "action_indicator") and old_button.action_indicator:
                old_button.action_indicator.deleteLater()
            old_button.deleteLater()

        self.button_widgets.clear()
        actions = self.get_actions()

        for name, action_config in actions.items():
            if name == "Custom":
                continue
            # Filter actions based on image presence
            is_image_action = action_config.get("image", False)
            if self.has_image != is_image_action:  # clever shortcut
                continue

            b = DraggableButton(self.app, self, name, name)
            icon_path = ui_utils.get_icon_path(
                self.app, action_config.get("icon", "Not Found"), with_theme=True
            )
            if icon_path.exists():
                b.setIcon(QtGui.QIcon(icon_path.as_posix()))

            # Set action indicator based on open_in_window
            open_in_window = action_config.get("open_in_window", False)
            b.set_action_indicator(open_in_window, is_image_action)

            # Add tooltip with tool name and description
            tooltip_text = name
            if action_config.get("instruction", None):
                # Truncate long instructions for tooltip
                instruction = action_config.get("instruction", "")
                if instruction:
                    instruction = (
                        instruction[:100] + "..." if len(instruction) > 100 else instruction
                    )
                tooltip_text = f"{name}\n{instruction}"
            b.setToolTip(tooltip_text)

            if not self.edit_mode:
                b.clicked.connect(partial(self.on_generic_instruction, name))
            self.button_widgets.append(b)

    def rebuild_grid_layout(self, parent_layout=None, force_edit_mode=None) -> None:
        """Rebuild grid layout with consistent sizing and proper Add New button placement."""
        if not parent_layout:
            parent_layout = self.background.layout()

        edit_mode_to_use = force_edit_mode if force_edit_mode is not None else self.edit_mode

        # Find or create the scroll area
        buttons_scroll = None
        scroll_index = -1

        # Look for existing scroll area
        for i in range(parent_layout.count()):
            item = parent_layout.itemAt(i)
            if item and item.widget() and isinstance(item.widget(), QScrollArea):
                buttons_scroll = item.widget()
                scroll_index = i
                break

        # If no scroll area exists, create one (for normal mode)
        if not buttons_scroll and (self.has_sel_text or self.has_image):
            buttons_scroll = QScrollArea()
            buttons_scroll.setWidgetResizable(True)
            buttons_scroll.setFrameShape(QFrame.Shape.NoFrame)
            buttons_scroll.setMaximumHeight(250)

            buttons_widget = QWidget()
            buttons_widget.setStyleSheet("background: transparent;")
            buttons_layout = QVBoxLayout(buttons_widget)
            buttons_layout.setContentsMargins(0, 0, 0, 0)
            buttons_layout.setSpacing(5)

            buttons_scroll.setWidget(buttons_widget)
            parent_layout.addWidget(buttons_scroll)
            scroll_index = parent_layout.count() - 1

        # Clean up existing content in scroll area
        if buttons_scroll and isinstance(buttons_scroll, QScrollArea):
            buttons_widget = buttons_scroll.widget()
            if buttons_widget:
                buttons_layout = buttons_widget.layout()
                if buttons_layout:
                    self.clear_layout(buttons_layout)

                    # Create and populate grid
                    grid = QGridLayout()
                    grid.setSpacing(10)
                    grid.setColumnMinimumWidth(0, 120)
                    grid.setColumnMinimumWidth(1, 120)

                    # Add buttons to grid
                    row = 0
                    col = 0
                    for b in self.button_widgets:
                        grid.addWidget(b, row, col)
                        col += 1
                        if col > 1:
                            col = 0
                            row += 1

                    if isinstance(buttons_layout, (QVBoxLayout, QHBoxLayout)):
                        buttons_layout.addLayout(grid)

        # Remove existing "Add New" button from main layout
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QPushButton) and widget.text() == "+ Add New":
                    parent_layout.removeWidget(widget)
                    widget.deleteLater()

        # Add "Add New" button outside scroll area (only in edit mode & only if we have text or image)
        if edit_mode_to_use and (self.has_sel_text or self.has_image):
            add_btn = QPushButton("+ Add New")
            add_btn.setStyleSheet(self._get_add_button_style())
            add_btn.clicked.connect(self.add_new_button_clicked)

            if isinstance(parent_layout, (QVBoxLayout, QHBoxLayout)):
                if scroll_index >= 0:
                    parent_layout.insertWidget(scroll_index + 1, add_btn)
                else:
                    parent_layout.addWidget(add_btn)

    def add_edit_delete_icons(self, btn) -> None:
        """Add edit/delete icons as overlays with proper spacing."""
        if hasattr(btn, "icon_container") and btn.icon_container:
            btn.icon_container.deleteLater()

        btn.icon_container = QWidget(btn)
        btn.icon_container.setAttribute(
            QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False
        )

        btn.icon_container.setGeometry(0, 0, btn.width(), btn.height())

        circle_style = self.app.styles["icon_button"]

        # Create edit icon (top-left)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(3, 3, 16, 16)

        pencil_icon = ui_utils.get_icon_path(self.app, "pencil", with_theme=True)
        if pencil_icon.exists():
            edit_btn.setIcon(QtGui.QIcon(pencil_icon.as_posix()))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (top-right)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, 3, 16, 16)
        del_icon = ui_utils.get_icon_path(self.app, "trash", with_theme=True)
        if del_icon.exists():
            delete_btn.setIcon(QtGui.QIcon(del_icon.as_posix()))
        delete_btn.setStyleSheet(circle_style)
        delete_btn.clicked.connect(partial(self.delete_button_clicked, btn))
        delete_btn.show()

        btn.icon_container.raise_()
        btn.icon_container.show()

    def enter_edit_mode(self) -> None:
        """Enter edit mode - called when user clicks the pencil icon."""
        self.edit_mode = True
        self._logger.debug("Entering edit mode")

        # Show edit mode UI elements
        if self.edit_button is not None:
            if self.edit_button is not None:
                self.edit_button.hide()
        if self.close_button is not None:
            self.close_button.hide()
        if self.reset_button is not None:
            self.reset_button.show()
        if self.edit_close_button is not None:
            self.edit_close_button.show()
        if self.drag_label is not None:
            self.drag_label.show()
        if self.input_area is not None:
            self.input_area.hide()
        if self.force_chat_area is not None:
            self.force_chat_area.hide()
        if self.update_label is not None:
            self.update_label.hide()
        if self.image_preview_container is not None:
            self.image_preview_container.hide()

        self.rebuild_grid_layout(force_edit_mode=True)

        # Add edit overlays to buttons
        self.add_edit_overlays_to_buttons()

        # Force height to 400 for image edit mode to eliminate empty spaces
        if self.has_image:
            self.resize(self.width(), 420)

    def exit_edit_mode(self) -> None:
        """Exit edit mode - called when user clicks the close button in edit mode."""
        self.edit_mode = False
        self._logger.debug("Exiting edit mode")

        # Reload the window to ensure clean state and proper layout
        # Note: reload_window creates a new window, so adjustSize is not needed here
        self.reload_window()

    def rebuild_edit_mode_with_scroll(self) -> None:
        """Rebuild layout for edit mode while preserving scroll functionality."""
        main_layout = self.background.layout()

        # Look for existing scroll area more precisely
        buttons_scroll = None
        scroll_index = -1
        for i in range(main_layout.count()):
            item = main_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QScrollArea):
                    buttons_scroll = widget
                    scroll_index = i
                    break

        if buttons_scroll:
            buttons_widget = buttons_scroll.widget()
            if buttons_widget:
                buttons_layout = buttons_widget.layout()
                if buttons_layout and isinstance(buttons_layout, (QVBoxLayout, QHBoxLayout)):
                    # Clear existing grid
                    self.clear_layout(buttons_layout)

                    # Rebuild grid in edit mode (WITHOUT the Add New button)
                    grid = QGridLayout()
                    grid.setSpacing(10)
                    grid.setColumnMinimumWidth(0, 120)
                    grid.setColumnMinimumWidth(1, 120)

                    # Add buttons to grid
                    row = 0
                    col = 0
                    for b in self.button_widgets:
                        grid.addWidget(b, row, col)
                        col += 1
                        if col > 1:
                            col = 0
                            row += 1

                    buttons_layout.addLayout(grid)

        # Remove existing "Add New" button if it exists
        for i in reversed(range(main_layout.count())):
            item = main_layout.itemAt(i)
            if item and item.widget():
                widget = item.widget()
                if isinstance(widget, QPushButton) and widget.text() == "+ Add New":
                    main_layout.removeWidget(widget)
                    widget.deleteLater()

        # Add "Add New" button AFTER the scroll area, in the main layout
        add_btn = QPushButton("+ Add New")
        add_btn.setStyleSheet(self._get_add_button_style())
        add_btn.clicked.connect(self.add_new_button_clicked)
        if isinstance(main_layout, (QVBoxLayout, QHBoxLayout)):
            main_layout.insertWidget(scroll_index + 1, add_btn)  # Just after the scroll area
        else:
            # Fallback: just add at the end
            main_layout.addWidget(add_btn)

    def clear_layout(self, layout) -> None:
        """Clear all items from a layout."""
        while layout.count():
            item = layout.takeAt(0)
            if item.widget():
                # Don't delete button widgets, just remove them
                if item.widget() not in self.button_widgets:
                    item.widget().deleteLater()
            elif item.layout():
                self.clear_layout(item.layout())
                item.layout().deleteLater()

    def _get_add_button_style(self) -> str:
        """Get stylesheet for Add New button."""
        return self.app.styles["add_button"]

    def add_edit_overlays_to_buttons(self) -> None:
        """Add edit overlays to all buttons when entering edit mode."""
        for btn in self.button_widgets:
            self.add_edit_delete_icons(btn)

        # Rebuild grid layout to show edit mode
        self.rebuild_grid_layout(force_edit_mode=True)

    def initialize_button_visibility(self) -> None:
        """Initialize button visibility for normal (non-edit) mode."""
        self.edit_mode = False
        self._logger.debug("Initializing button visibility")
        if hasattr(self, "reset_button") and self.reset_button is not None:
            self.reset_button.hide()
        if hasattr(self, "edit_close_button") and self.edit_close_button is not None:
            self.edit_close_button.hide()
        if hasattr(self, "drag_label") and self.drag_label is not None:
            self.drag_label.hide()
        if (
            (self.has_sel_text or self.has_image)
            and hasattr(self, "edit_button")
            and self.edit_button is not None
        ):
            self.edit_button.show()
        if hasattr(self, "close_button") and self.close_button is not None:
            self.close_button.show()
        if hasattr(self, "input_area") and self.input_area is not None:
            self.input_area.setVisible(True)
        if hasattr(self, "force_chat_area") and self.force_chat_area is not None:
            self.force_chat_area.setVisible(not self.edit_mode)
        if hasattr(self, "image_preview_container") and self.image_preview_container is not None:
            self.image_preview_container.setVisible(True)
        if hasattr(self, "update_label") and self.update_label is not None:
            self.update_label.setVisible(True)

    def on_reset_clicked(self) -> None:
        """
        Reset options to default actions and reload the interface.
        """
        confirm_box = QMessageBox()
        confirm_box.setWindowFlags(
            confirm_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        confirm_box.setWindowTitle("Confirm Reset to Defaults?")
        confirm_box.setText(
            "This will reset all buttons to their original configuration.\nYour custom buttons will be removed.\n\nAre you sure you want to continue?",
        )
        confirm_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        confirm_box.setDefaultButton(QMessageBox.StandardButton.No)

        if confirm_box.exec_() == QMessageBox.StandardButton.Yes:
            try:
                self._logger.debug("Resetting to default actions")
                # Reset actions to defaults in unified settings
                if hasattr(self.app, "settings_manager") and self.app.settings_manager.settings:
                    # Reset actions to defaults
                    self.app.settings_manager.actions = create_default_actions_config()
                else:
                    self._logger.error("Settings manager not available for reset")

                # Reload the interface immediately
                self.build_buttons_list()
                self.rebuild_grid_layout(force_edit_mode=self.edit_mode)

                # Show success message
                success_msg = QMessageBox()
                success_msg.setWindowFlags(
                    success_msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
                )
                success_msg.setWindowTitle("Reset Complete")
                success_msg.setText("Buttons have been reset to their default configuration.")
                success_msg.exec_()

            except Exception as e:
                self._logger.exception(f"Error resetting options: {e}")
                self.app.ui_manager.show_message_signal.emit(
                    "Error", f"An error occurred while resetting: {e!s}"
                )

    def add_new_button_clicked(self) -> None:
        dialog = ButtonEditDialog(
            self.app, self, title="Add New Button", is_image_context=self.has_image
        )
        if dialog.exec_():
            bd = dialog.get_button_data()

            # Check if the name already exists
            if bd.get("name", "") in self.get_actions():
                if not ui_utils.show_confirmation_dialog(
                    "Overwrite Existing Action",
                    f"An action named '{bd.get('name', '')}' already exists. Do you want to overwrite it?",
                ):
                    return  # The user canceled

            action_config = ActionConfig(
                prefix=bd.get("prefix", ""),
                instruction=bd.get("instruction", ""),
                icon=bd.get("icon", ""),
                open_in_window=bd.get("open_in_window", False),
                image=bd.get("image", False),
            )

            success = self.app.settings_manager.update_action(bd.get("name", ""), action_config)

            if success:
                # Stay in edit mode and refresh buttons
                self.build_buttons_list()
                self.rebuild_grid_layout(force_edit_mode=True)
                self.add_edit_overlays_to_buttons()
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to save button changes. Please try again."
                )

    def edit_button_clicked(self, btn: QPushButton) -> None:
        """User clicked the small pencil icon over a button."""
        key = getattr(btn, "key", None)
        if key is None:
            self._logger.error("Button does not have a 'key' attribute.")
            return
        actions = self.get_actions()
        if key not in actions:
            self._logger.error(f"Action not found: {key}")
            return

        action_config = actions[key]
        bd = self.action_config_to_dict(action_config)
        bd["name"] = key

        dialog = ButtonEditDialog(self.app, self, bd, is_image_context=self.has_image)
        if dialog.exec_():
            new_data = dialog.get_button_data()

            success = True

            # Remove old action if name changed
            if new_data.get("name", "") != key:
                if new_data.get("name", "") in self.get_actions():
                    if not ui_utils.show_confirmation_dialog(
                        "Overwrite Existing Action",
                        f"An action named '{new_data.get('name', '')}' already exists. Do you want to overwrite it?",
                    ):
                        return  # The user cancelled

                # Delete the old action
                success = self.app.settings_manager.remove_action(key)

            # Create and save new ActionConfig (only if previous operation succeeded)
            if success:
                action_config = ActionConfig(
                    prefix=new_data.get("prefix", ""),
                    instruction=new_data.get("instruction", ""),
                    icon=new_data.get("icon", ""),
                    open_in_window=new_data.get("open_in_window", False),
                    image=new_data.get("image", False),
                )
                success = self.app.settings_manager.update_action(
                    new_data.get("name", ""), action_config
                )

            if success:
                # Stay in edit mode and refresh buttons
                self.build_buttons_list()
                self.rebuild_grid_layout(force_edit_mode=True)
                self.add_edit_overlays_to_buttons()
                # Show success message after UI update
                QtCore.QTimer.singleShot(
                    100,
                    lambda: self.app.ui_manager.show_message_signal.emit(
                        "Button Updated", "Your button changes have been saved and are now active."
                    ),
                )
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to save button changes. Please try again."
                )

    def delete_button_clicked(self, btn: QPushButton) -> None:
        """Handle deletion of a button."""
        key = getattr(btn, "key", None)
        if key is None:
            self._logger.error("Button does not have a 'key' attribute.")
            return

        confirm = QMessageBox()
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        confirm.setWindowTitle("Confirm Delete?")
        confirm.setText("Are you sure you want to continue?")
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)

        if confirm.exec_() == QMessageBox.StandardButton.Yes:
            # Remove action using SettingsManager
            success = self.app.settings_manager.remove_action(key)

            if success:
                # Clean up UI elements and refresh
                for btn_ in self.button_widgets[:]:
                    if btn_.key == key:
                        if hasattr(btn_, "icon_container") and btn_.icon_container:
                            btn_.icon_container.deleteLater()
                        btn_.deleteLater()
                        self.button_widgets.remove(btn_)

                # Stay in edit mode and refresh buttons
                self.rebuild_grid_layout(force_edit_mode=True)
                self.add_edit_overlays_to_buttons()
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to delete the button. Please try again."
                )

    def update_json_from_grid(self) -> None:
        """
        Called after a drop reorder. Reflect the new order in unified settings,
        so that user's custom arrangement persists.
        """
        # Get current actions
        current_actions = self.app.settings_manager.actions

        # Create new ordered dict based on button order
        new_actions = {}

        # Add Custom first if it exists
        if "Custom" in current_actions:
            new_actions["Custom"] = current_actions["Custom"]

        # Add buttons in their current order
        for b in self.button_widgets:
            if b.key in current_actions:
                new_actions[b.key] = current_actions[b.key]

        # Update settings (auto-saves)
        self.app.settings_manager.actions = new_actions
        self._logger.debug("Button order updated in unified settings")

    def reload_window(self) -> None:
        """
        Reload the window with updated button configuration.
        This recreates the popup window with the same selected text and image.
        """
        # Store current position, selected text, and image
        current_pos = self.pos()
        selected_text = self.selected_text
        image = self.image

        # Close current window
        self.close()

        # Create and show new popup window
        new_popup = CustomPopupWindow(self.app, selected_text, image)
        new_popup.move(current_pos)
        new_popup.show()

    def on_custom_change(self) -> None:
        """
        Prompt entered by user in the input field.
        """
        # Check if image is provided but model doesn't support vision
        if self.has_image and not self._check_vision_support():
            self.app.ui_manager.show_message_signal.emit(
                "Vision Not Supported",
                f"The current AI model {self.app.get_current_model(self.app.settings_manager.provider) or 'Unknown'} does not support image analysis. Please select a model that supports vision capabilities.",
            )
            return

        widget = getattr(self, "custom_input", None)
        txt = widget.text() if widget else ""
        if txt.strip():
            self.app.ai_processor.process_option(
                "Custom", self.selected_text, self.is_force_chat_enabled(), txt, self.image
            )
            self.close()

    def on_generic_instruction(self, instruction: str) -> None:
        """
        User clicked a generic instruction button.
        """
        if not self.edit_mode and (self.selected_text is not None or self.has_image):
            self.app.ai_processor.process_option(
                instruction, self.selected_text, self.is_force_chat_enabled(), None, self.image
            )
            self.close()

    def _check_vision_support(self) -> bool:
        """
        Check if the current AI provider and model support vision/image analysis.

        Returns:
            bool: True if the current model supports vision, False otherwise
        """
        provider_name = self.app.settings_manager.provider
        api_model = self.app.get_current_model(provider_name)

        return self._has_vision_support(provider_name, api_model)

    def _has_vision_support(self, provider_name: str, api_model: str) -> bool:
        """
        Common function to check vision support for a given provider and model.

        Args:
            provider_name: The internal provider name
            api_model: The model identifier

        Returns:
            bool: True if the model supports vision, False otherwise
        """
        self._logger.debug(
            f"Checking vision support for provider: {provider_name}, model: {api_model}"
        )

        if not provider_name or not api_model:
            return False

        # Map providers to their model lists
        provider_models = {
            "gemini": GEMINI_MODELS,
            "openai": OPENAI_MODELS,
            "anthropic": ANTHROPIC_MODELS,
            "mistral": MISTRAL_MODELS,
        }

        # Check standard providers
        if provider_name in provider_models:
            return any(
                model_tuple[1] == api_model and model_tuple[2].get("vision", False)
                for model_tuple in provider_models[provider_name]
            )

        # Special case for Ollama
        if provider_name == "ollama":
            vision_indicators = ["llava", "bakllava", "moondream", "minicpm-v", "qwen2.5vl"]
            return any(indicator in api_model.lower() for indicator in vision_indicators)

        return False

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.edit_mode:
                # If in edit mode, exit edit mode (like clicking the close button)
                self.exit_edit_mode()
            else:
                # If not in edit mode, close the window
                self.close()
        else:
            super().keyPressEvent(event)
