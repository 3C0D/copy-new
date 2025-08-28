"""
Writing Tools - CustomPopupWindow module
Used for displaying a custom popup window with various input fields and options.
"""

import logging
import threading
from functools import partial
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from config.data_operations import create_default_actions_config
from config.interfaces import ActionConfig
from ui.ResponseWindow import ResponseWindow
from ui.ui_utils import ThemeBackground, get_effective_color_mode, get_icon_path

if TYPE_CHECKING:
    from ui.ResponseWindow import ResponseWindow
    from WritingToolApp import WritingToolApp


def _(x):
    return x


class ActionConfigWithName(ActionConfig, total=False):
    name: str


class ToggleSwitch(QCheckBox):
    """Custom toggle switch widget with sliding circle animation"""

    toggled = QtCore.Signal(bool)

    def __init__(self, parent: QWidget | None = None):
        super().__init__(parent)
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

        # Colors based on theme
        dark_mode = get_effective_color_mode() == "dark"

        if self.isChecked():
            bg_color = QtGui.QColor("#2196F3")  # Blue when ON
        else:
            bg_color = QtGui.QColor("#444" if dark_mode else "#ddd")  # Gray when OFF

        circle_color = QtGui.QColor("white")

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
        parent: QWidget | None = None,
        button_data: dict | None = None,
        title: str = "Edit Button",
    ):
        super().__init__(parent)
        self.button_data = (
            button_data
            if button_data
            else {
                "prefix": "Make this change to the following text:\n\n",
                "instruction": "",
                "icon": "icons/magnifying-glass",
                "open_in_window": False,
            }
        )
        self.setWindowTitle(title)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout(self)

        # Name
        name_label = QLabel("Button Name:")
        name_label.setStyleSheet(
            f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'}; font-weight: bold;"
        )
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if get_effective_color_mode() == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if get_effective_color_mode() == "dark" else "white"};
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
            }}
        """,
        )
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        instruction_label = QLabel(
            "What should your AI do with your selected text? (System Instruction)"
        )
        instruction_label.setStyleSheet(
            f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'}; font-weight: bold;"
        )
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(
            f"""
            QPlainTextEdit {{
                padding: 8px;
                border: 1px solid {"#777" if get_effective_color_mode() == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if get_effective_color_mode() == "dark" else "white"};
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
            }}
        """,
        )
        self.instruction_input.setPlainText(self.button_data.get("instruction", ""))
        self.instruction_input.setMinimumHeight(100)
        self.instruction_input.setPlaceholderText(
            """Examples:
    - Fix / improve / explain this code.
    - Make it funny.
    - Add emojis!
    - Roast this!
    - Translate to English.
    - Make the text title case.
    - If it's all caps, make it all small, and vice-versa.
    - Write a reply to this.
    - Analyse potential biases in this news article.""",
        )
        layout.addWidget(instruction_label)
        layout.addWidget(self.instruction_input)

        # open_in_window
        display_label = QLabel("How should your AI response be shown?")
        display_label.setStyleSheet(
            f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'}; font-weight: bold;"
        )
        layout.addWidget(display_label)

        radio_layout = QHBoxLayout()
        self.replace_radio = QRadioButton("Replace the selected text")
        self.window_radio = QRadioButton("In a chat pop-up window")
        for r in (self.replace_radio, self.window_radio):
            r.setStyleSheet(f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'};")

        self.replace_radio.setChecked(not self.button_data.get("open_in_window", False))
        self.window_radio.setChecked(self.button_data.get("open_in_window", False))

        radio_layout.addWidget(self.replace_radio)
        radio_layout.addWidget(self.window_radio)
        layout.addLayout(radio_layout)

        # Indicator information
        indicator_label = QLabel(
            "<i>A small indicator will be shown on the button: Ⓡ for replace, Ⓒ for chat</i>"
        )
        indicator_label.setStyleSheet(
            f"color: {'#aaa' if get_effective_color_mode() == 'dark' else '#666'}; font-size: 11px; font-style: italic;"
        )
        layout.addWidget(indicator_label)

        # OK & Cancel
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        for btn in (ok_button, cancel_button):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {"#444" if get_effective_color_mode() == "dark" else "#f0f0f0"};
                    color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
                    border: 1px solid {"#666" if get_effective_color_mode() == "dark" else "#ccc"};
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {"#555" if get_effective_color_mode() == "dark" else "#e0e0e0"};
                }}
            """,
            )
        btn_layout.addWidget(ok_button)
        btn_layout.addWidget(cancel_button)
        layout.addLayout(btn_layout)

        ok_button.clicked.connect(self.accept)
        cancel_button.clicked.connect(self.reject)

        self.setStyleSheet(
            f"""
            QDialog {{
                background-color: {"#222" if get_effective_color_mode() == "dark" else "#f5f5f5"};
                border-radius: 10px;
            }}
        """,
        )

    def get_button_data(self) -> ActionConfigWithName:
        return {
            "name": self.name_input.text(),
            "prefix": "Make this change to the following text:\n\n",
            # Retrieve multiline text
            "instruction": self.instruction_input.toPlainText(),
            "icon": "icons/custom",
            "open_in_window": self.window_radio.isChecked(),
        }


class DraggableButton(QPushButton):
    def __init__(self, parent_popup: "CustomPopupWindow", key: str, text: str):
        super().__init__(text, parent_popup)
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
        self.base_style = f"""
            QPushButton {{
                background-color: {"#444" if get_effective_color_mode() == "dark" else "white"};
                border: 1px solid {"#666" if get_effective_color_mode() == "dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if get_effective_color_mode() == "dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)

    def refresh_button_style(self) -> None:
        """Refresh the button style when color mode changes."""
        self.base_style = f"""
            QPushButton {{
                background-color: {"#444" if get_effective_color_mode() == "dark" else "white"};
                border: 1px solid {"#666" if get_effective_color_mode() == "dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if get_effective_color_mode() == "dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)

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
                self.base_style
                + """
                QPushButton {
                    border: 2px dashed #666;
                }
            """,
            )
        else:
            event.ignore()

    def dragLeaveEvent(self, event: QtGui.QDragLeaveEvent) -> None:
        self.setStyleSheet(self.base_style)
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

        self.setStyleSheet(self.base_style)
        event.setDropAction(Qt.DropAction.MoveAction)
        event.acceptProposedAction()

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle resize events to reposition UI elements."""
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())
        if self.action_indicator:
            self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)

    def set_action_indicator(self, open_in_window: bool) -> None:
        """Set the action indicator (Ⓡ or Ⓒ) based on action type."""
        if self.action_indicator:
            self.action_indicator.deleteLater()

        self.action_indicator = QLabel(self)
        indicator_text = "Ⓒ" if open_in_window else "Ⓡ"
        self.action_indicator.setText(indicator_text)
        self.action_indicator.setStyleSheet(
            f"""
            QLabel {{
                background-color: {"#666" if get_effective_color_mode() == "dark" else "#ddd"};
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
                border-radius: 10px;
                font-size: 12px;
                font-weight: bold;
                padding: 2px;
                min-width: 16px;
                max-width: 16px;
                min-height: 16px;
                max-height: 16px;
                text-align: center;
            }}
        """
        )
        self.action_indicator.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.action_indicator.setGeometry(self.width() - 20, 4, 16, 16)
        self.action_indicator.show()


class CustomPopupWindow(QWidget):
    def __init__(
        self,
        app: "WritingToolApp",
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

    def init_ui(self):
        """Initialize the main UI structure."""
        self._setup_window_properties()
        main_layout = self._create_main_layout()
        content_layout = self._create_background_and_content_layout(main_layout)

        self._create_top_bar(content_layout)
        self._create_input_area(content_layout)
        if self.has_sel_text:
            self.create_force_chat_toggle(content_layout)
        self._setup_buttons_and_content(content_layout)
        self._show_update_notice_if_available(content_layout)

        self._finalize_ui_setup()

    def _setup_window_properties(self) -> None:
        """Configure window flags and properties."""
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")

    def _create_main_layout(self) -> QVBoxLayout:
        """Create and configure the main layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        return main_layout

    def _create_background_and_content_layout(self, main_layout: QVBoxLayout) -> QVBoxLayout:
        """Create background widget and content layout."""
        self.background = ThemeBackground(
            self,
            self.app.settings_manager.theme or "gradient",
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
        if self.has_sel_text:
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
        reset_icon_path = get_icon_path("restore", with_theme=True)
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
        self.drag_label.setStyleSheet(
            f"""
            color: {"#fff" if get_effective_color_mode() == "dark" else "#333"};
            font-size: 14px;
            font-weight: bold;
        """,
        )
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
        pencil_icon = get_icon_path("pencil", with_theme=True)
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
        return f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin-top: 3px;
                color: {"#fff" if get_effective_color_mode() == "dark" else "#333"};
            }}
            QPushButton:hover {{
                background-color: {"#333" if get_effective_color_mode() == "dark" else "#ebebeb"};
            }}
        """

    def _get_close_button_style(self) -> str:
        """Get stylesheet for close buttons."""
        return f"""
            QPushButton {{
                background-color: transparent;
                color: {"#fff" if get_effective_color_mode() == "dark" else "#333"};
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {"#333" if get_effective_color_mode() == "dark" else "#ebebeb"};
            }}
        """

    def _create_input_area(self, content_layout: QVBoxLayout) -> None:
        """Create the input area with text field and send button."""
        self.input_area = QWidget()
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self._create_custom_input(input_layout)
        self._create_send_button(input_layout)

        content_layout.addWidget(self.input_area)

    def _create_custom_input(self, layout: QHBoxLayout) -> None:
        """Create the custom input text field."""
        self.custom_input = QLineEdit()
        placeholder = (
            _("Describe your change...")
            if self.has_sel_text
            else _("Ask your AI...")
        )
        self.custom_input.setPlaceholderText(placeholder)
        self.custom_input.setStyleSheet(self._get_input_style())
        self.custom_input.returnPressed.connect(self.on_custom_change)
        layout.addWidget(self.custom_input)

    def _create_send_button(self, layout: QHBoxLayout) -> None:
        """Create the send button for the input area."""
        send_btn = QPushButton()
        send_icon = get_icon_path("send", with_theme=True)
        if send_icon.exists():
            send_btn.setIcon(QtGui.QIcon(send_icon.as_posix()))

        send_btn.setStyleSheet(self._get_send_button_style())
        # Use a fallback size if self.custom_input is None
        input_height = self.custom_input.sizeHint().height() if self.custom_input else 32
        send_btn.setFixedSize(input_height, input_height)
        send_btn.clicked.connect(self.on_custom_change)
        layout.addWidget(send_btn)

    def _get_input_style(self) -> str:
        """Get stylesheet for input field."""
        return f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {"#777" if get_effective_color_mode() == "dark" else "#ccc"};
                border-radius: 8px;
                background-color: {"#333" if get_effective_color_mode() == "dark" else "white"};
                color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
            }}
        """

    def _get_send_button_style(self) -> str:
        """Get stylesheet for send button."""
        return f"""
            QPushButton {{
                background-color: {"#2e7d32" if get_effective_color_mode() == "dark" else "#4CAF50"};
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {"#1b5e20" if get_effective_color_mode() == "dark" else "#45a049"};
            }}
        """

    def _setup_buttons_and_content(self, content_layout: QVBoxLayout) -> None:
        """Setup buttons and main content based on available input."""
        if self.has_sel_text:
            self.build_buttons_list()
            self.rebuild_grid_layout(content_layout)
        else:
            # Only custom instructions input if no selected text
            if self.custom_input is not None:
                self.custom_input.setMinimumWidth(300)

        self.initialize_button_visibility()

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

        # Hide on deactivate only if NOT in edit mode
        if event.type() == QtCore.QEvent.Type.WindowDeactivate:
            if not self.edit_mode:
                self.hide()
                return True
        return super().eventFilter(watched, event)

    def create_force_chat_toggle(self, parent_layout: QVBoxLayout) -> None:
        """Create the Force Chat toggle with lock button."""
        self.force_chat_area = QWidget()
        force_chat_layout = QHBoxLayout(self.force_chat_area)
        force_chat_layout.setContentsMargins(5, 2, 5, 2)
        force_chat_layout.setSpacing(6)

        # Label
        label = QLabel("Force Chat:")
        label.setStyleSheet(
            f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'}; font-size: 11px;"
        )

        # Check if we should restore the locked state
        force_chat_locked = getattr(self.app.settings_manager, "force_chat_locked", False)
        force_chat_enabled = getattr(self.app.settings_manager, "force_chat_enabled", False)

        # Force Chat toggle switch (custom widget with sliding animation)
        self.force_chat_toggle = ToggleSwitch()

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

        self.force_chat_lock.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: 1px solid {"#666" if get_effective_color_mode() == "dark" else "#555"};
                border-radius: 4px;
                padding: 1px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {"#555" if get_effective_color_mode() == "dark" else "#e0e0e0"};
            }}
            QPushButton:checked {{
                background-color: {"#4CAF50" if get_effective_color_mode() == "dark" else "#4CAF50"};
                color: white;
                border: 1px solid {"#4CAF50" if get_effective_color_mode() == "dark" else "#4CAF50"};
            }}
        """
        )

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
            self.app.settings_manager.save()

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

        self.app.settings_manager.save()

    def is_force_chat_enabled(self) -> bool:
        """Check if Force Chat is currently enabled."""
        return bool(self.force_chat_toggle and self.force_chat_toggle.isChecked())

    def get_actions(self) -> dict[str, ActionConfig]:
        """
        Get actions directly from the unified settings system.
        Returns ActionConfig objects, no conversion needed.
        """
        if not hasattr(self.app, "settings_manager") or not self.app.settings_manager.settings:
            self._logger.warning("Settings manager not available, using default actions")
            return create_default_actions_config()

        return self.app.settings_manager.settings.actions

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
        }

    def build_buttons_list(self) -> None:
        """
        Loads actions from unified settings system,
        creates DraggableButton for each (except "Custom"),
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
            b = DraggableButton(self, name, name)
            icon_path = get_icon_path(action_config.get("icon", "Not Found"), with_theme=True)
            if icon_path.exists():
                b.setIcon(QtGui.QIcon(icon_path.as_posix()))

            # Set action indicator based on open_in_window
            open_in_window = action_config.get("open_in_window", False)
            b.set_action_indicator(open_in_window)

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

        # Use force_edit_mode if provided, otherwise use current edit_mode
        edit_mode_to_use = force_edit_mode if force_edit_mode is not None else self.edit_mode

        # Remove existing grid and Add New button - PROPERLY DELETE WIDGETS
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if isinstance(item, QGridLayout):
                grid = item
                # First, properly delete all widgets in the grid
                for j in reversed(range(grid.count())):
                    grid_item = grid.itemAt(j)
                    if grid_item and grid_item.widget():
                        widget = grid_item.widget()
                        grid.removeWidget(widget)
                        # Don't delete button_widgets here - they'll be re-added
                        if widget not in self.button_widgets:
                            widget.deleteLater()
                parent_layout.removeItem(grid)
                # Delete the grid layout itself
                grid.deleteLater()
            elif item.widget():
                widget = item.widget()
                if isinstance(widget, QPushButton) and widget.text() == "+ Add New":
                    parent_layout.removeWidget(widget)
                    widget.deleteLater()

        # Create new grid with fixed column width
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

        if isinstance(parent_layout, (QVBoxLayout, QHBoxLayout)):
            parent_layout.addLayout(grid)

        # Add New button (only in edit mode & only if we have text)
        if edit_mode_to_use and self.has_sel_text:
            add_btn = QPushButton("+ Add New")
            add_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {"#333" if get_effective_color_mode() == "dark" else "#e0e0e0"};
                    border: 1px solid {"#666" if get_effective_color_mode() == "dark" else "#ccc"};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                    text-align: center;
                    color: {"#fff" if get_effective_color_mode() == "dark" else "#000"};
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {"#444" if get_effective_color_mode() == "dark" else "#d0d0d0"};
                }}
            """,
            )
            add_btn.clicked.connect(self.add_new_button_clicked)
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

        circle_style = f"""
            QPushButton {{
                background-color: {"#666" if get_effective_color_mode() == "dark" else "#999"};
                border-radius: 10px;
                min-width: 16px;
                min-height: 16px;
                max-width: 16px;
                max-height: 16px;
                padding: 1px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {"#888" if get_effective_color_mode() == "dark" else "#bbb"};
            }}
        """

        # Create edit icon (top-left)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(3, 3, 16, 16)

        pencil_icon = get_icon_path("pencil", with_theme=True)
        if pencil_icon.exists():
            edit_btn.setIcon(QtGui.QIcon(pencil_icon.as_posix()))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (top-right)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, 3, 16, 16)
        del_icon = get_icon_path("trash", with_theme=True)
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
            self.input_area.setVisible(False)
        if self.force_chat_area is not None:
            self.force_chat_area.setVisible(False)
        if self.update_label is not None:
            self.update_label.setVisible(False)

        # Add edit overlays to buttons
        self.add_edit_overlays_to_buttons()

    def exit_edit_mode(self) -> None:
        """Exit edit mode - called when user clicks the close button in edit mode."""
        self.edit_mode = False
        self._logger.debug("Exiting edit mode")

        # Reload the window to ensure clean state and proper layout
        self.reload_window()

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
            self.has_sel_text
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
                    self.app.settings_manager.settings.actions = create_default_actions_config()
                    self.app.settings_manager.save()
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
                self.app.show_message_signal.emit(
                    "Error", f"An error occurred while resetting: {e!s}"
                )

    def add_new_button_clicked(self) -> None:
        dialog = ButtonEditDialog(self, title="Add New Button")
        if dialog.exec_():
            bd = dialog.get_button_data()

            action_config = ActionConfig(
                prefix=bd.get("prefix", ""),
                instruction=bd.get("instruction", ""),
                icon=bd.get("icon", ""),
                open_in_window=bd.get("open_in_window", False),
            )
            self.app.settings_manager.update_action(bd.get("name", ""), action_config)

            # Show success message
            msg = QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Added")
            msg.setText("Your new button has been saved and is now available in the tools list.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec_()

            # Reload the window instead of closing it
            self.reload_window()

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

        dialog = ButtonEditDialog(self, bd)
        if dialog.exec_():
            new_data = dialog.get_button_data()
            # Remove old action if name changed
            if new_data.get("name", "") != key:
                self.app.settings_manager.remove_action(key)

            # Create and save new ActionConfig
            from config.interfaces import ActionConfig

            action_config = ActionConfig(
                prefix=new_data.get("prefix", ""),
                instruction=new_data.get("instruction", ""),
                icon=new_data.get("icon", ""),
                open_in_window=new_data.get("open_in_window", False),
            )
            self.app.settings_manager.update_action(new_data.get("name", ""), action_config)

            # Show success message
            msg = QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Updated")
            msg.setText("Your button changes have been saved and are now active.")
            msg.setStandardButtons(QMessageBox.StandardButton.Ok)
            msg.exec_()

            # Reload the window instead of closing it
            self.reload_window()

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
            try:
                # Remove action using SettingsManager
                self.app.settings_manager.remove_action(key)

                # Clean up UI elements
                for btn_ in self.button_widgets[:]:
                    if btn_.key == key:
                        if hasattr(btn_, "icon_container") and btn_.icon_container:
                            btn_.icon_container.deleteLater()
                        btn_.deleteLater()
                        self.button_widgets.remove(btn_)

                # Reload settings and reload window
                self.app.settings_manager.load_settings()
                self.reload_window()

            except Exception as e:
                self._logger.exception(f"Error deleting button: {e}")
                self.app.show_message_signal.emit(
                    "Error", f"An error occurred while deleting the button: {e!s}"
                )

    def update_json_from_grid(self) -> None:
        """
        Called after a drop reorder. Reflect the new order in unified settings,
        so that user's custom arrangement persists.
        """
        if not hasattr(self.app, "settings_manager") or not self.app.settings_manager.settings:
            self._logger.error("Settings manager not available, cannot update order")
            return

        # Get current actions
        current_actions = self.app.settings_manager.settings.actions

        # Create new ordered dict based on button order
        new_actions = {}

        # Add Custom first if it exists
        if "Custom" in current_actions:
            new_actions["Custom"] = current_actions["Custom"]

        # Add buttons in their current order
        for b in self.button_widgets:
            if b.key in current_actions:
                new_actions[b.key] = current_actions[b.key]

        # Update settings and save
        self.app.settings_manager.settings.actions = new_actions
        self.app.settings_manager.save()
        self._logger.debug("Button order updated in unified settings")

    def reload_window(self) -> None:
        """
        Reload the window with updated button configuration.
        This recreates the popup window with the same selected text.
        """
        # Store current position and selected text
        current_pos = self.pos()
        selected_text = self.selected_text

        # Close current window
        self.close()

        # Create and show new popup window
        new_popup = CustomPopupWindow(self.app, selected_text)
        new_popup.move(current_pos)
        new_popup.show()
        new_popup.raise_()
        new_popup.activateWindow()

    def on_custom_change(self) -> None:
        """
        Prompt entered by user in the input field.
        """
        widget = getattr(self, "custom_input", None)
        txt = widget.text().strip() if widget else ""
        if txt:
            self.process_option("Custom", self.selected_text, self.is_force_chat_enabled(), txt)
            self._logger.debug(f" C'est ici que se ferme custom Windows.$$$$$$$$$$$$$$$$$$$$")
            self.close()

    def on_generic_instruction(self, instruction: str) -> None:
        """
        User clicked a generic instruction button.
        """
        if not self.edit_mode and self.selected_text is not None:
            self.process_option(
                instruction, self.selected_text.strip(), self.is_force_chat_enabled()
            )
            self.close()

    def process_option(
        self,
        option: str,
        selected_text: str | None,
        force_chat: bool = False,
        custom_change: str | None = None,
    ) -> None:
        """
        Process the selected writing option in a separate thread.
        """
        self._logger.debug(f"Processing option: {option}")
        self._logger.debug(f"selected_text: {selected_text}ùùùùùùùùùùùùùùùùùùùùùùùùùùùùù")

        # should_setup_response_window = self._should_display_in_response_window(
        #     option, selected_text, self.app.settings_manager.actions
        # )

        is_custom_option = option == "Custom"
        has_selected_text = bool(selected_text and selected_text.strip() != "")
        action_config = self.app.settings_manager.actions

        should_setup_response_window = (
            (is_custom_option and not has_selected_text)
            or action_config.get("open_in_window", False)
            or (force_chat and has_selected_text)  # Force Chat with text
        )

        if should_setup_response_window:
            self._logger.debug("Setting up response window for output")
            self._setup_response_window(option, selected_text)
        elif hasattr(self.app, "current_response_window"):
            self._logger.debug("Original selection will be replaced directly")
            delattr(self.app, "current_response_window")

        # Store force_chat state for the thread
        self._current_force_chat = force_chat

        # Start processing thread
        threading.Thread(
            target=self.process_option_thread,
            args=(option, selected_text, custom_change),
            daemon=True,
        ).start()

    def _setup_response_window(self, option: str, selected_text: str | None) -> None:
        """
        Set up the response window for the selected writing option.
        """
        self.app.create_response_window_signal.emit(option, selected_text or "")
        # is_custom = option == "Custom"
        # window_title = "Chat" if not is_custom else option
        # self.app.current_response_window = self.show_response_window(window_title, selected_text)

        # # Initialize chat history inline
        # # Il va falloir ajouter image.
        # self.app.current_response_window.chat_history = (
        #     []
        #     if not is_custom
        #     else [
        #         {
        #             "role": "user",
        #             "content": f"Original text to {option.lower()}:\n\n{selected_text}",
        #         },
        #     ]
        # )

    def show_response_window(self, option: str, text: str | None) -> ResponseWindow:
        """
        Show the response in a new window instead of pasting it.
        @see: ui.ResponseWindow.ResponseWindow
        """
        response_window = ResponseWindow(self.app, f"{option} Result")
        if text:
            response_window.selected_text = text  # Store the text for regeneration
            self._logger.debug(f"Showing response window with text: {text}!!!!!!!!!!!!!!!")
        self._logger.debug(f"Showing response window with text: {text}!!!!!!!!!!!!!!!")
        response_window.show() # ??? Le problème viendrait de là
        return response_window

    def process_option_thread(
        self, option: str, selected_text: str, custom_change: str | None = None
    ) -> None:
        """
        Thread function to process the selected writing option using the AI model.
        """
        self._logger.debug(f"Starting processing thread for option: {option}")

        try:
            prompt_data = self._prepare_prompt_data(option, selected_text, custom_change)
            if not prompt_data:
                return

            self.app.output_queue = ""
            should_open_window = self._should_display_in_response_window(
                option, selected_text, prompt_data["action_config"]
            )

            if should_open_window:
                self._process_window_response(option, selected_text, custom_change, prompt_data)
            else:
                self._process_direct_replacement(prompt_data)

        except Exception as e:
            self._handle_processing_error(e)

    def _prepare_prompt_data(
        self, option: str, selected_text: str, custom_change: str | None = None
    ) -> dict | None:
        """
        Prepare prompt data for AI processing.
        """
        has_selected_text = selected_text.strip() != ""
        is_custom_option = option == "Custom"

        if not has_selected_text:
            return self._handle_no_text_selected(is_custom_option, custom_change)
        else:
            return self._handle_text_selected(
                option, selected_text, custom_change, is_custom_option
            )

    def _handle_no_text_selected(
        self, is_custom_option: bool, custom_change: str | None
    ) -> dict | None:
        """Handle case where no text is selected."""
        if is_custom_option:
            return {
                "prompt": custom_change,
                "system_instruction": "You are a friendly, helpful, compassionate, and endearing AI conversational assistant. Avoid making assumptions or generating harmful, biased, or inappropriate content. When in doubt, do not make up information. Ask the user for clarification if needed. Try not be unnecessarily repetitive in your response. You can, and should as appropriate, use Markdown formatting to make your response nicely readable.",
                "action_config": {},
            }
        else:
            self.app.show_message_signal.emit("Error", "Please select text to use this option.")
            return None

    def _handle_text_selected(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        is_custom_option: bool,
    ) -> dict | None:
        """Handle case where text is selected."""
        action_config = self.app.settings_manager.actions.get(option)
        if not action_config:
            self._logger.error(f"Action not found: {option}")
            return None

        prompt_prefix = action_config.get("prefix", "")
        system_instruction = action_config.get("instruction", "")

        if is_custom_option:
            prompt = f"{prompt_prefix}Described change: {custom_change}\n\nText: {selected_text}"
        else:
            prompt = f"{prompt_prefix}{selected_text}"

        return {
            "prompt": prompt,
            "system_instruction": system_instruction,
            "action_config": action_config,
        }

    def _should_display_in_response_window(
        self, option: str, selected_text: str | None, action_config: dict
    ) -> bool:
        """
        Determine if response should be displayed in a window.
        Conditions:
        - Custom option with no selected text
        - Selected text and "open_in_window" is True in action config
        - Force Chat is enabled and there is selected text
        # - There is an image to process
        """
        has_selected_text = bool(selected_text and selected_text.strip() != "")
        is_custom_option = option == "Custom"
        force_chat = getattr(self, "_current_force_chat", False)

        return (
            (is_custom_option and not has_selected_text)
            or (has_selected_text and action_config.get("open_in_window", False))
            or (force_chat and has_selected_text)
            # or self.has_image
        )

    def _process_window_response(
        self,
        option: str,
        selected_text: str,
        custom_change: str | None,
        prompt_data: dict,
    ) -> None:
        """Process AI response for window display."""
        if not self.app.current_provider:
            return

        self._logger.debug("Getting response for window display")
        response = self.app.current_provider.get_response(
            prompt_data["system_instruction"],
            str(prompt_data["prompt"]),
            return_response=True,
        )
        self._logger.debug(f"Got response of length: {len(response) if response else 0}")

        self._update_chat_history_if_needed(option, selected_text, custom_change)
        self._update_response_window(response)

    def _update_chat_history_if_needed(
        self, option: str, selected_text: str, custom_change: str | None
    ) -> None:
        """Update chat history for custom prompts without text."""
        is_custom_option = option == "Custom"
        has_selected_text = selected_text.strip() != ""

        if is_custom_option and not has_selected_text and self.app.current_response_window:
            self.app.current_response_window.chat_history.append(
                {"role": "user", "content": custom_change or ""},
            )

    def _update_response_window(self, response: str) -> None:
        """Update response window with AI response (thread-safe)."""
        if hasattr(self.app, "current_response_window") and self.app.current_response_window:
            QtCore.QMetaObject.invokeMethod(
                self.app.current_response_window,
                "set_text",
                QtCore.Qt.ConnectionType.QueuedConnection,
                QtCore.Q_ARG(str, response),
            )
            self._logger.debug("Invoked set_text on response window")
        else:
            self._logger.warning("current_response_window not available for update")

    def _process_direct_replacement(self, prompt_data: dict) -> None:
        """Process AI response for direct text replacement."""
        if not self.app.current_provider:
            return

        self._logger.debug("Getting response for direct replacement")
        prompt_str = str(prompt_data["prompt"])
        self.app.current_provider.get_response(prompt_data["system_instruction"], prompt_str)
        self._logger.debug("Response processed")

    def _handle_processing_error(self, error: Exception) -> None:
        """Handle errors during AI processing."""
        self._logger.error(f"An error occurred: {error}", exc_info=True)

        if "Resource has been exhausted" in str(error):
            self.app.show_message_signal.emit(
                "Error - Rate Limit Hit",
                "Whoops! You've hit the per-minute rate limit of the Gemini API. Please try again in a few moments.\n\nIf this happens often, simply switch to a Gemini model with a higher usage limit in Settings.",
            )
        else:
            self.app.show_message_signal.emit("Error", f"An error occurred: {error}")

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
