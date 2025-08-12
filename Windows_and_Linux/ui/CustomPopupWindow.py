import logging
import os
from functools import partial
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QDialog,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPlainTextEdit,
    QPushButton,
    QRadioButton,
    QVBoxLayout,
    QWidget,
)

from config.data_operations import create_default_actions_config
from ui.ui_utils import ThemeBackground, colorMode, get_effective_color_mode

if TYPE_CHECKING:
    from Windows_and_Linux.WritingToolApp import WritingToolApp

_ = lambda x: x


class ToggleSwitch(QWidget):
    """Custom toggle switch widget with sliding circle animation"""

    toggled = QtCore.Signal(bool)

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(50, 24)
        self.setCheckable(True)
        self._checked = False
        self._circle_position = 2
        self._animation = QtCore.QPropertyAnimation(self, b"circle_position")
        self._animation.setDuration(150)

    def setChecked(self, checked):
        if self._checked != checked:
            self._checked = checked
            self._animate_to_position()
            self.toggled.emit(checked)

    def isChecked(self):
        return self._checked

    def setCheckable(self, checkable):
        # For compatibility with QCheckBox interface
        pass

    @QtCore.Property(int)
    def circle_position(self):
        return self._circle_position

    @circle_position.setter
    def circle_position(self, pos):
        self._circle_position = pos
        self.update()

    def _animate_to_position(self):
        start_pos = 2 if not self._checked else 28
        end_pos = 28 if self._checked else 2

        self._animation.setStartValue(start_pos)
        self._animation.setEndValue(end_pos)
        self._animation.start()

    def mousePressEvent(self, event):
        if event.button() == QtCore.Qt.MouseButton.LeftButton:
            self.setChecked(not self._checked)

    def paintEvent(self, event):
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)

        # Colors based on theme
        dark_mode = get_effective_color_mode() == 'dark'

        if self._checked:
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

    def __init__(self, parent=None, button_data=None, title="Edit Button"):
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
                border: 1px solid {'#777' if get_effective_color_mode() == 'dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if get_effective_color_mode() == 'dark' else 'white'};
                color: {'#fff' if get_effective_color_mode() == 'dark' else '#000'};
            }}
        """,
        )
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        instruction_label = QLabel("What should your AI do with your selected text? (System Instruction)")
        instruction_label.setStyleSheet(
            f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'}; font-weight: bold;"
        )
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(
            f"""
            QPlainTextEdit {{
                padding: 8px;
                border: 1px solid {'#777' if get_effective_color_mode() == 'dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if get_effective_color_mode() == 'dark' else 'white'};
                color: {'#fff' if get_effective_color_mode() == 'dark' else '#000'};
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
        self.window_radio = QRadioButton("In a pop-up window (with follow-up support)")
        for r in (self.replace_radio, self.window_radio):
            r.setStyleSheet(f"color: {'#fff' if get_effective_color_mode() == 'dark' else '#333'};")

        self.replace_radio.setChecked(not self.button_data.get("open_in_window", False))
        self.window_radio.setChecked(self.button_data.get("open_in_window", False))

        radio_layout.addWidget(self.replace_radio)
        radio_layout.addWidget(self.window_radio)
        layout.addLayout(radio_layout)

        # OK & Cancel
        btn_layout = QHBoxLayout()
        ok_button = QPushButton("OK")
        cancel_button = QPushButton("Cancel")
        for btn in (ok_button, cancel_button):
            btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {'#444' if get_effective_color_mode() == 'dark' else '#f0f0f0'};
                    color: {'#fff' if get_effective_color_mode() == 'dark' else '#000'};
                    border: 1px solid {'#666' if get_effective_color_mode() == 'dark' else '#ccc'};
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {'#555' if get_effective_color_mode() == 'dark' else '#e0e0e0'};
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
                background-color: {'#222' if get_effective_color_mode() == 'dark' else '#f5f5f5'};
                border-radius: 10px;
            }}
        """,
        )

    def get_button_data(self):
        return {
            "name": self.name_input.text(),
            "prefix": "Make this change to the following text:\n\n",
            # Retrieve multiline text
            "instruction": self.instruction_input.toPlainText(),
            "icon": "icons/custom",
            "open_in_window": self.window_radio.isChecked(),
        }


class DraggableButton(QtWidgets.QPushButton):
    def __init__(self, parent_popup, key, text):
        super().__init__(text, parent_popup)
        self.popup = parent_popup
        self.key = key
        self.drag_start_position = None
        self.setAcceptDrops(True)
        self.icon_container = None

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
                background-color: {"#444" if get_effective_color_mode()=="dark" else "white"};
                border: 1px solid {"#666" if get_effective_color_mode()=="dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if get_effective_color_mode()=="dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if get_effective_color_mode()=="dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)

    def refresh_button_style(self):
        """Refresh the button style when color mode changes."""
        self.base_style = f"""
            QPushButton {{
                background-color: {"#444" if get_effective_color_mode()=="dark" else "white"};
                border: 1px solid {"#666" if get_effective_color_mode()=="dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if get_effective_color_mode()=="dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if get_effective_color_mode()=="dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)

    def enterEvent(self, event):
        # Only update the hover property if NOT in edit mode.
        if not self.popup.edit_mode:
            self.setProperty("hover", True)
            self.style().unpolish(self)
            self.style().polish(self)
        super().enterEvent(event)

    def leaveEvent(self, event):
        if not self.popup.edit_mode:
            self.setProperty("hover", False)
            self.style().unpolish(self)
            self.style().polish(self)
        super().leaveEvent(event)

    def mousePressEvent(self, event):
        if event.button() == Qt.MouseButton.LeftButton:
            if self.popup.edit_mode:
                self.drag_start_position = event.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & Qt.MouseButton.LeftButton) or not self.drag_start_position:
            return

        distance = (event.pos() - self.drag_start_position).manhattanLength()
        if distance < QtWidgets.QApplication.startDragDistance():
            return

        if self.popup.edit_mode:
            drag = QtGui.QDrag(self)
            mime_data = QtCore.QMimeData()
            idx = self.popup.button_widgets.index(self)
            mime_data.setData("application/x-button-index", str(idx).encode())
            drag.setMimeData(mime_data)

            pixmap = self.grab()
            drag.setPixmap(pixmap)
            drag.setHotSpot(event.pos())

            self.drag_start_position = None
            drop_action = drag.exec_(Qt.DropAction.MoveAction)

    def dragEnterEvent(self, event):
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

    def dragLeaveEvent(self, event):
        self.setStyleSheet(self.base_style)
        event.accept()

    def dropEvent(self, event):
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

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())


class CustomPopupWindow(QtWidgets.QWidget):
    def __init__(self, app: 'WritingToolApp', selected_text):
        super().__init__()
        self.app = app
        self.selected_text = selected_text
        self.edit_mode = False
        self.has_text = bool(selected_text.strip())

        self.drag_label = None
        self.edit_button = None
        self.reset_button = None
        self.edit_close_button = None
        self.close_button = None
        self.custom_input = None
        self.input_area = None

        # Force Chat toggle and lock state
        self.force_chat_toggle = None
        self.force_chat_lock = None
        self.force_chat_area = None

        self.button_widgets = []

        self.init_ui()

    def init_ui(self):
        self.setWindowFlags(Qt.WindowType.WindowStaysOnTopHint | Qt.WindowType.FramelessWindowHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background = ThemeBackground(
            self,
            self.app.settings_manager.theme or "gradient",
            is_popup=True,
            border_radius=10,
        )
        main_layout.addWidget(self.background)

        content_layout = QtWidgets.QVBoxLayout(self.background)
        # Margin Control
        content_layout.setContentsMargins(10, 4, 10, 10)
        content_layout.setSpacing(10)

        # TOP BAR LAYOUT & STYLE
        top_bar = QHBoxLayout()
        top_bar.setContentsMargins(0, 0, 0, 0)
        top_bar.setSpacing(0)

        # The "Reset" button (left side in edit mode)
        from ui.ui_utils import get_icon_path

        self.reset_button = QPushButton()
        reset_icon_path = get_icon_path("restore", with_theme=True)
        if os.path.exists(reset_icon_path):
            self.reset_button.setIcon(QtGui.QIcon(reset_icon_path))
        self.reset_button.setText("")
        self.reset_button.setFixedSize(24, 24)
        self.reset_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                padding: 0px;
                margin-top: 3px;
            }}
            QPushButton:hover {{
                background-color: {'#333' if get_effective_color_mode()=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.reset_button.setToolTip(_("Reset to Default Buttons"))
        top_bar.addWidget(self.reset_button, 0, Qt.AlignmentFlag.AlignLeft)

        # The label "Drag to rearrange" (BOLD as requested)
        self.drag_label = QLabel("Drag to rearrange")
        self.drag_label.setStyleSheet(
            f"""
            color: {'#fff' if get_effective_color_mode()=='dark' else '#333'};
            font-size: 14px;
            font-weight: bold; /* <--- BOLD TEXT */
        """,
        )
        self.drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_label.hide()
        top_bar.addWidget(self.drag_label, 1, Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter)

        # Close button for edit mode (right side)
        self.edit_close_button = QPushButton("×")
        self.edit_close_button.setFixedSize(24, 24)
        self.edit_close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {'#fff' if get_effective_color_mode()=='dark' else '#333'};
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#333' if get_effective_color_mode()=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.edit_close_button.clicked.connect(self.exit_edit_mode)
        self.edit_close_button.setToolTip(_("Exit Edit Mode"))
        self.edit_close_button.hide()
        top_bar.addWidget(self.edit_close_button, 0, Qt.AlignmentFlag.AlignRight)

        # Edit button (pencil icon) - only shown when not in edit mode
        self.edit_button = QPushButton()
        pencil_icon = get_icon_path("pencil", with_theme=True)
        if os.path.exists(pencil_icon):
            self.edit_button.setIcon(QtGui.QIcon(pencil_icon))
        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 6px;
                color: {'#fff' if get_effective_color_mode()=='dark' else '#333'};
            }}
            QPushButton:hover {{
                background-color: {'#333' if get_effective_color_mode()=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.edit_button.clicked.connect(self.enter_edit_mode)
        self.edit_button.setToolTip(_("Edit Tools Layout"))
        top_bar.addWidget(self.edit_button, 0, Qt.AlignmentFlag.AlignLeft)

        # Close button block:
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {'#fff' if get_effective_color_mode()=='dark' else '#333'};
                font-size: 20px;   /* bigger text */
                font-weight: bold; /* bold text */
                border: none;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#333' if get_effective_color_mode()=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.close_button.clicked.connect(self.close)
        top_bar.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)
        content_layout.addLayout(top_bar)

        # Input area (hidden in edit mode)
        self.input_area = QWidget()
        input_layout = QHBoxLayout(self.input_area)
        input_layout.setContentsMargins(0, 0, 0, 0)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText(_("Describe your change...") if self.has_text else _("Ask your AI..."))
        self.custom_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {'#777' if get_effective_color_mode()=='dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if get_effective_color_mode()=='dark' else 'white'};
                color: {'#fff' if get_effective_color_mode()=='dark' else '#000'};
            }}
        """,
        )
        self.custom_input.returnPressed.connect(self.on_custom_change)
        input_layout.addWidget(self.custom_input)

        send_btn = QPushButton()
        send_icon = get_icon_path("send", with_theme=True)
        if os.path.exists(send_icon):
            send_btn.setIcon(QtGui.QIcon(send_icon))
        send_btn.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {'#2e7d32' if get_effective_color_mode()=='dark' else '#4CAF50'};
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if get_effective_color_mode()=='dark' else '#45a049'};
            }}
        """,
        )
        send_btn.setFixedSize(self.custom_input.sizeHint().height(), self.custom_input.sizeHint().height())
        send_btn.clicked.connect(self.on_custom_change)
        input_layout.addWidget(send_btn)

        content_layout.addWidget(self.input_area)

        # Force Chat toggle area (only shown when text is selected)
        if self.has_text:
            self.create_force_chat_toggle(content_layout)

        if self.has_text:
            self.build_buttons_list()
            self.rebuild_grid_layout(content_layout)
        else:
            # If no text, hide the edit button; user can only do custom instructions
            self.edit_button.hide()
            self.custom_input.setMinimumWidth(300)

        # Initialize button visibility for normal mode
        self.initialize_button_visibility()

        # show update notice if applicable
        update_available = self.app.settings_manager.update_available or False

        if update_available:
            update_label = QLabel()
            update_label.setOpenExternalLinks(True)
            update_label.setText(
                '<a href="https://github.com/theJayTea/WritingTools/releases" style="color:rgb(255, 0, 0); text-decoration: underline; font-weight: bold;">There\'s an update! :D Download now.</a>',
            )
            update_label.setStyleSheet("margin-top: 10px;")
            content_layout.addWidget(update_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        self.installEventFilter(self)
        QtCore.QTimer.singleShot(250, lambda: self.custom_input.setFocus() if self.custom_input else None)

    def create_force_chat_toggle(self, parent_layout):
        """Create the Force Chat toggle with lock button."""
        self.force_chat_area = QWidget()
        force_chat_layout = QHBoxLayout(self.force_chat_area)
        force_chat_layout.setContentsMargins(5, 2, 5, 2)
        force_chat_layout.setSpacing(6)

        # Label
        label = QLabel("Force Chat:")
        label.setStyleSheet(f"color: {'#fff' if get_effective_color_mode()=='dark' else '#333'}; font-size: 11px;")

        # Check if we should restore the locked state
        force_chat_locked = getattr(self.app.settings_manager, 'force_chat_locked', False)
        force_chat_enabled = getattr(self.app.settings_manager, 'force_chat_enabled', False)

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
                border: 1px solid {'#666' if get_effective_color_mode()=='dark' else '#555'};
                border-radius: 4px;
                padding: 1px;
                font-size: 10px;
            }}
            QPushButton:hover {{
                background-color: {'#555' if get_effective_color_mode()=='dark' else '#e0e0e0'};
            }}
            QPushButton:checked {{
                background-color: {'#4CAF50' if get_effective_color_mode()=='dark' else '#4CAF50'};
                color: white;
                border: 1px solid {'#4CAF50' if get_effective_color_mode()=='dark' else '#4CAF50'};
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

    def update_lock_icon(self):
        """Update the lock icon based on current state."""
        if self.force_chat_lock and self.force_chat_lock.isChecked():
            self.force_chat_lock.setText("🔒")
        else:
            self.force_chat_lock.setText("🔓")

    def on_force_chat_toggled(self, checked):
        """Handle Force Chat toggle state change."""
        # If locked, save the state
        if self.force_chat_lock and self.force_chat_lock.isChecked():
            self.app.settings_manager.force_chat_enabled = checked
            self.app.settings_manager.save()

    def on_force_chat_lock_toggled(self, checked):
        """Handle Force Chat lock state change."""
        self.update_lock_icon()

        # Save lock state
        self.app.settings_manager.force_chat_locked = checked

        if checked:
            # When locking, save current toggle state
            self.app.settings_manager.force_chat_enabled = self.force_chat_toggle.isChecked()
        else:
            # When unlocking, reset toggle to default (off)
            self.force_chat_toggle.setChecked(False)
            self.app.settings_manager.force_chat_enabled = False

        self.app.settings_manager.save()

    def is_force_chat_enabled(self):
        """Check if Force Chat is currently enabled."""
        return self.force_chat_toggle and self.force_chat_toggle.isChecked()

    def get_actions(self):
        """
        Get actions directly from the unified settings system.
        Returns ActionConfig objects, no conversion needed.
        """
        if not hasattr(self.app, "settings_manager") or not self.app.settings_manager.settings:
            logging.warning("Settings manager not available, using default actions")
            return create_default_actions_config()

        return self.app.settings_manager.settings.actions

    @staticmethod
    def action_config_to_dict(action_config):
        """
        Convert ActionConfig to dict format for ButtonEditDialog compatibility.
        Only use when dict format is specifically needed.
        """
        return {
            "prefix": action_config.prefix,
            "instruction": action_config.instruction,
            "icon": action_config.icon,
            "open_in_window": action_config.open_in_window,
        }

    def build_buttons_list(self):
        """
        Loads actions from unified settings system,
        creates DraggableButton for each (except "Custom"),
        storing them in self.button_widgets in the same order.
        """
        from ui.ui_utils import get_icon_path

        # Properly delete old button widgets before clearing the list
        for old_button in self.button_widgets:
            if hasattr(old_button, 'icon_container') and old_button.icon_container:
                old_button.icon_container.deleteLater()
            old_button.deleteLater()

        self.button_widgets.clear()
        actions = self.get_actions()

        for name, action_config in actions.items():
            if name == "Custom":
                continue
            b = DraggableButton(self, name, name)
            icon_path = get_icon_path(action_config.get("icon", None), with_theme=True)
            if os.path.exists(icon_path):
                b.setIcon(QtGui.QIcon(icon_path))

            # Add tooltip with tool name and description
            tooltip_text = name
            if action_config.get("instruction", None):
                # Truncate long instructions for tooltip
                instruction = action_config.get("instruction", "")
                if instruction:
                    instruction = instruction[:100] + "..." if len(instruction) > 100 else instruction
                tooltip_text = f"{name}\n{instruction}"
            b.setToolTip(tooltip_text)

            if not self.edit_mode:
                b.clicked.connect(partial(self.on_generic_instruction, name))
            self.button_widgets.append(b)

    def rebuild_grid_layout(self, parent_layout=None, force_edit_mode=None):
        """Rebuild grid layout with consistent sizing and proper Add New button placement."""
        if not parent_layout:
            parent_layout = self.background.layout()

        # Use force_edit_mode if provided, otherwise use current edit_mode
        edit_mode_to_use = force_edit_mode if force_edit_mode is not None else self.edit_mode

        # Remove existing grid and Add New button - PROPERLY DELETE WIDGETS
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if isinstance(item, QtWidgets.QGridLayout):
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
        grid = QtWidgets.QGridLayout()
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

        if isinstance(parent_layout, (QtWidgets.QVBoxLayout, QtWidgets.QHBoxLayout)):
            parent_layout.addLayout(grid)

        # Add New button (only in edit mode & only if we have text)
        if edit_mode_to_use and self.has_text:
            add_btn = QPushButton("+ Add New")
            add_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {'#333' if get_effective_color_mode()=='dark' else '#e0e0e0'};
                    border: 1px solid {'#666' if get_effective_color_mode()=='dark' else '#ccc'};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                    text-align: center;
                    color: {'#fff' if get_effective_color_mode()=='dark' else '#000'};
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {'#444' if get_effective_color_mode()=='dark' else '#d0d0d0'};
                }}
            """,
            )
            add_btn.clicked.connect(self.add_new_button_clicked)
            parent_layout.addWidget(add_btn)

    def add_edit_delete_icons(self, btn):
        """Add edit/delete icons as overlays with proper spacing."""
        if hasattr(btn, "icon_container") and btn.icon_container:
            btn.icon_container.deleteLater()

        btn.icon_container = QtWidgets.QWidget(btn)
        btn.icon_container.setAttribute(QtCore.Qt.WidgetAttribute.WA_TransparentForMouseEvents, False)

        btn.icon_container.setGeometry(0, 0, btn.width(), btn.height())

        circle_style = f"""
            QPushButton {{
                background-color: {'#666' if get_effective_color_mode()=='dark' else '#999'};
                border-radius: 10px;
                min-width: 16px;
                min-height: 16px;
                max-width: 16px;
                max-height: 16px;
                padding: 1px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#888' if get_effective_color_mode()=='dark' else '#bbb'};
            }}
        """

        # Create edit icon (top-left)
        edit_btn = QPushButton(btn.icon_container)
        edit_btn.setGeometry(3, 3, 16, 16)
        from ui.ui_utils import get_icon_path

        pencil_icon = get_icon_path("pencil", with_theme=True)
        if os.path.exists(pencil_icon):
            edit_btn.setIcon(QtGui.QIcon(pencil_icon))
        edit_btn.setStyleSheet(circle_style)
        edit_btn.clicked.connect(partial(self.edit_button_clicked, btn))
        edit_btn.show()

        # Create delete icon (top-right)
        delete_btn = QPushButton(btn.icon_container)
        delete_btn.setGeometry(btn.width() - 23, 3, 16, 16)
        del_icon = get_icon_path("trash", with_theme=True)
        if os.path.exists(del_icon):
            delete_btn.setIcon(QtGui.QIcon(del_icon))
        delete_btn.setStyleSheet(circle_style)
        delete_btn.clicked.connect(partial(self.delete_button_clicked, btn))
        delete_btn.show()

        btn.icon_container.raise_()
        btn.icon_container.show()

    def enter_edit_mode(self):
        """Enter edit mode - called when user clicks the pencil icon."""
        self.edit_mode = True
        logging.debug("Entering edit mode")

        # Show edit mode UI elements
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

        # Add edit overlays to buttons
        self.add_edit_overlays_to_buttons()

    def exit_edit_mode(self):
        """Exit edit mode - called when user clicks the close button in edit mode."""
        self.edit_mode = False
        logging.debug("Exiting edit mode")

        # Reload the window to ensure clean state and proper layout
        self.reload_window()

    def add_edit_overlays_to_buttons(self):
        """Add edit overlays to all buttons when entering edit mode."""
        for btn in self.button_widgets:
            self.add_edit_delete_icons(btn)

        # Rebuild grid layout to show edit mode
        self.rebuild_grid_layout(force_edit_mode=True)

    def initialize_button_visibility(self):
        """Initialize button visibility for normal (non-edit) mode."""
        self.edit_mode = False
        if hasattr(self, 'reset_button') and self.reset_button is not None:
            self.reset_button.hide()
        if hasattr(self, 'edit_close_button') and self.edit_close_button is not None:
            self.edit_close_button.hide()
        if hasattr(self, 'drag_label') and self.drag_label is not None:
            self.drag_label.hide()
        if self.has_text and hasattr(self, 'edit_button') and self.edit_button is not None:
            self.edit_button.show()
        if hasattr(self, 'close_button') and self.close_button is not None:
            self.close_button.show()
        if hasattr(self, 'input_area') and self.input_area is not None:
            self.input_area.setVisible(True)
        if hasattr(self, 'force_chat_area') and self.force_chat_area is not None:
            self.force_chat_area.setVisible(not self.edit_mode)

    def on_reset_clicked(self):
        """
        Reset options to default actions and reload the interface.
        """
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setWindowFlags(confirm_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        confirm_box.setWindowTitle("Confirm Reset to Defaults?")
        confirm_box.setText(
            "This will reset all buttons to their original configuration.\nYour custom buttons will be removed.\n\nAre you sure you want to continue?",
        )
        confirm_box.setStandardButtons(
            QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No
        )
        confirm_box.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)

        if confirm_box.exec_() == QtWidgets.QMessageBox.StandardButton.Yes:
            try:
                logging.debug("Resetting to default actions")
                # Reset actions to defaults in unified settings
                if hasattr(self.app, "settings_manager") and self.app.settings_manager.settings:
                    # Reset actions to defaults
                    self.app.settings_manager.settings.actions = create_default_actions_config()
                    self.app.settings_manager.save()
                else:
                    logging.error("Settings manager not available for reset")

                # Reload the interface immediately
                self.build_buttons_list()
                self.rebuild_grid_layout(force_edit_mode=self.edit_mode)

                # Show success message
                success_msg = QtWidgets.QMessageBox()
                success_msg.setWindowFlags(success_msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
                success_msg.setWindowTitle("Reset Complete")
                success_msg.setText("Buttons have been reset to their default configuration.")
                success_msg.exec_()

            except Exception as e:
                logging.exception(f"Error resetting options: {e}")
                self.app.show_message_signal.emit("Error", f"An error occurred while resetting: {e!s}")

    def add_new_button_clicked(self):
        dialog = ButtonEditDialog(self, title="Add New Button")
        if dialog.exec_():
            bd = dialog.get_button_data()
            # Create new ActionConfig and save directly
            from config.interfaces import ActionConfig

            action_config = ActionConfig(
                prefix=bd["prefix"],
                instruction=bd["instruction"],
                icon=bd["icon"],
                open_in_window=bd["open_in_window"],
            )
            self.app.settings_manager.update_action(bd["name"], action_config)

            # Show success message
            msg = QtWidgets.QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Added")
            msg.setText("Your new button has been saved and is now available in the tools list.")
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec_()

            # Reload the window instead of closing it
            self.reload_window()

    def edit_button_clicked(self, btn):
        """User clicked the small pencil icon over a button."""
        key = btn.key
        actions = self.get_actions()
        if key not in actions:
            logging.error(f"Action not found: {key}")
            return

        action_config = actions[key]
        bd = self.action_config_to_dict(action_config)
        bd["name"] = key

        dialog = ButtonEditDialog(self, bd)
        if dialog.exec_():
            new_data = dialog.get_button_data()
            # Remove old action if name changed
            if new_data["name"] != key:
                self.app.settings_manager.remove_action(key)

            # Create and save new ActionConfig
            from config.interfaces import ActionConfig

            action_config = ActionConfig(
                prefix=new_data["prefix"],
                instruction=new_data["instruction"],
                icon=new_data["icon"],
                open_in_window=new_data["open_in_window"],
            )
            self.app.settings_manager.update_action(new_data["name"], action_config)

            # Show success message
            msg = QtWidgets.QMessageBox()
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Updated")
            msg.setText("Your button changes have been saved and are now active.")
            msg.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Ok)
            msg.exec_()

            # Reload the window instead of closing it
            self.reload_window()

    def delete_button_clicked(self, btn):
        """Handle deletion of a button."""
        key = btn.key
        confirm = QtWidgets.QMessageBox()
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        confirm.setWindowTitle("Confirm Delete?")
        confirm.setText("Are you sure you want to continue?")
        confirm.setStandardButtons(QtWidgets.QMessageBox.StandardButton.Yes | QtWidgets.QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QtWidgets.QMessageBox.StandardButton.No)

        if confirm.exec_() == QtWidgets.QMessageBox.StandardButton.Yes:
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
                logging.exception(f"Error deleting button: {e}")
                self.app.show_message_signal.emit("Error", f"An error occurred while deleting the button: {e!s}")

    def update_json_from_grid(self):
        """
        Called after a drop reorder. Reflect the new order in unified settings,
        so that user's custom arrangement persists.
        """
        if not hasattr(self.app, "settings_manager") or not self.app.settings_manager.settings:
            logging.error("Settings manager not available, cannot update order")
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
        logging.debug("Button order updated in unified settings")

    def reload_window(self):
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

    def on_custom_change(self):
        txt = self.custom_input.text().strip() if self.custom_input else ""
        if txt:
            self.app.process_option("Custom", self.selected_text, txt, force_chat=self.is_force_chat_enabled())
            self.close()

    def on_generic_instruction(self, instruction):
        if not self.edit_mode:
            self.app.process_option(instruction, self.selected_text, force_chat=self.is_force_chat_enabled())
            self.close()

    def eventFilter(self, obj, event):
        # Hide on deactivate only if NOT in edit mode
        if event.type() == QtCore.QEvent.Type.WindowDeactivate:
            if not self.edit_mode:
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.edit_mode:
                # If in edit mode, exit edit mode (like clicking the close button)
                self.toggle_edit_mode()
            else:
                # If not in edit mode, close the window
                self.close()
        else:
            super().keyPressEvent(event)

    def _on_focus_in(self, event):
        """Called when custom_input gains focus."""
        self.edit_mode = True
        if hasattr(self, '_original_focus_in'):
            self._original_focus_in(event)

    def _on_focus_out(self, event):
        """Called when custom_input loses focus."""
        self.edit_mode = False
        if hasattr(self, '_original_focus_out'):
            self._original_focus_out(event)
