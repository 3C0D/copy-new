import logging
import os
from functools import partial

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
from ui.ui_utils import ThemeBackground, colorMode

_ = lambda x: x


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
        name_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.name_input = QLineEdit()
        self.name_input.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {'#777' if colorMode == 'dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if colorMode == 'dark' else 'white'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
            }}
        """,
        )
        if "name" in self.button_data:
            self.name_input.setText(self.button_data["name"])
        layout.addWidget(name_label)
        layout.addWidget(self.name_input)

        # Instruction (changed to a multiline QPlainTextEdit)
        instruction_label = QLabel("What should your AI do with your selected text? (System Instruction)")
        instruction_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        self.instruction_input = QPlainTextEdit()
        self.instruction_input.setStyleSheet(
            f"""
            QPlainTextEdit {{
                padding: 8px;
                border: 1px solid {'#777' if colorMode == 'dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if colorMode == 'dark' else 'white'};
                color: {'#fff' if colorMode == 'dark' else '#000'};
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
        display_label.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'}; font-weight: bold;")
        layout.addWidget(display_label)

        radio_layout = QHBoxLayout()
        self.replace_radio = QRadioButton("Replace the selected text")
        self.window_radio = QRadioButton("In a pop-up window (with follow-up support)")
        for r in (self.replace_radio, self.window_radio):
            r.setStyleSheet(f"color: {'#fff' if colorMode == 'dark' else '#333'};")

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
                    background-color: {'#444' if colorMode == 'dark' else '#f0f0f0'};
                    color: {'#fff' if colorMode == 'dark' else '#000'};
                    border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
                    border-radius: 5px;
                    padding: 8px;
                    min-width: 100px;
                }}
                QPushButton:hover {{
                    background-color: {'#555' if colorMode == 'dark' else '#e0e0e0'};
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
                background-color: {'#222' if colorMode == 'dark' else '#f5f5f5'};
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
        self.setAttribute(QtCore.Qt.WA_Hover, True)
        self.setAttribute(QtCore.Qt.WA_StyledBackground, True)

        # Use a dynamic property "hover" (default False)
        self.setProperty("hover", False)

        # Set fixed size (adjust as needed)
        self.setFixedSize(120, 40)

        # Define base style using the dynamic property instead of the :hover pseudo-class
        self.base_style = f"""
            QPushButton {{
                background-color: {"#444" if colorMode=="dark" else "white"};
                border: 1px solid {"#666" if colorMode=="dark" else "#ccc"};
                border-radius: 8px;
                padding: 10px;
                font-size: 14px;
                text-align: left;
                color: {"#fff" if colorMode=="dark" else "#000"};
            }}
            QPushButton[hover="true"] {{
                background-color: {"#555" if colorMode=="dark" else "#f0f0f0"};
            }}
        """
        self.setStyleSheet(self.base_style)
        logging.debug("DraggableButton initialized")

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
        if event.button() == QtCore.Qt.LeftButton:
            if self.popup.edit_mode:
                self.drag_start_position = event.pos()
                event.accept()
                return
        super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        if not (event.buttons() & QtCore.Qt.LeftButton) or not self.drag_start_position:
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
            drop_action = drag.exec_(QtCore.Qt.MoveAction)
            logging.debug(f"Drag completed with action: {drop_action}")

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

        source_idx = int(event.mimeData().data("application/x-button-index").data().decode())
        target_idx = self.popup.button_widgets.index(self)

        if source_idx != target_idx:
            bw = self.popup.button_widgets
            bw[source_idx], bw[target_idx] = bw[target_idx], bw[source_idx]
            self.popup.rebuild_grid_layout(force_edit_mode=True)
            self.popup.update_json_from_grid()

        self.setStyleSheet(self.base_style)
        event.setDropAction(QtCore.Qt.MoveAction)
        event.acceptProposedAction()

    def resizeEvent(self, event):
        super().resizeEvent(event)
        if self.icon_container:
            self.icon_container.setGeometry(0, 0, self.width(), self.height())


class CustomPopupWindow(QtWidgets.QWidget):
    def __init__(self, app, selected_text):
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

        self.button_widgets = []

        logging.debug("Initializing CustomPopupWindow")
        self.init_ui()

    def init_ui(self):
        logging.debug("Setting up CustomPopupWindow UI")
        self.setWindowFlags(QtCore.Qt.WindowStaysOnTopHint | QtCore.Qt.FramelessWindowHint)
        self.setAttribute(QtCore.Qt.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background = ThemeBackground(
            self,
            self.app.settings_manager.settings.system.get("theme", "dark"),
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
                background-color: {'#333' if colorMode=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.reset_button.setToolTip(_("Reset to Default Buttons"))
        top_bar.addWidget(self.reset_button, 0, Qt.AlignLeft)

        # The label "Drag to rearrange" (BOLD as requested)
        self.drag_label = QLabel("Drag to rearrange")
        self.drag_label.setStyleSheet(
            f"""
            color: {'#fff' if colorMode=='dark' else '#333'};
            font-size: 14px;
            font-weight: bold; /* <--- BOLD TEXT */
        """,
        )
        self.drag_label.setAlignment(Qt.AlignCenter)
        self.drag_label.hide()
        top_bar.addWidget(self.drag_label, 1, Qt.AlignVCenter | Qt.AlignHCenter)

        # Close button for edit mode (right side)
        self.edit_close_button = QPushButton("×")
        self.edit_close_button.setFixedSize(24, 24)
        self.edit_close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {'#fff' if colorMode=='dark' else '#333'};
                font-size: 20px;
                font-weight: bold;
                border: none;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#333' if colorMode=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.edit_close_button.clicked.connect(self.exit_edit_mode)
        self.edit_close_button.setToolTip(_("Exit Edit Mode"))
        self.edit_close_button.hide()
        top_bar.addWidget(self.edit_close_button, 0, Qt.AlignRight)

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
                color: {'#fff' if colorMode=='dark' else '#333'};
            }}
            QPushButton:hover {{
                background-color: {'#333' if colorMode=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.edit_button.clicked.connect(self.enter_edit_mode)
        self.edit_button.setToolTip(_("Edit Tools Layout"))
        top_bar.addWidget(self.edit_button, 0, Qt.AlignLeft)

        # Close button block:
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                color: {'#fff' if colorMode=='dark' else '#333'};
                font-size: 20px;   /* bigger text */
                font-weight: bold; /* bold text */
                border: none;
                border-radius: 6px;
                padding: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#333' if colorMode=='dark' else '#ebebeb'};
            }}
        """,
        )
        self.close_button.clicked.connect(self.close)
        top_bar.addWidget(self.close_button, 0, Qt.AlignRight)
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
                border: 1px solid {'#777' if colorMode=='dark' else '#ccc'};
                border-radius: 8px;
                background-color: {'#333' if colorMode=='dark' else 'white'};
                color: {'#fff' if colorMode=='dark' else '#000'};
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
                background-color: {'#2e7d32' if colorMode=='dark' else '#4CAF50'};
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if colorMode=='dark' else '#45a049'};
            }}
        """,
        )
        send_btn.setFixedSize(self.custom_input.sizeHint().height(), self.custom_input.sizeHint().height())
        send_btn.clicked.connect(self.on_custom_change)
        input_layout.addWidget(send_btn)

        content_layout.addWidget(self.input_area)

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
        update_available = self.app.settings_manager.settings.system.get("update_available",False)

        if update_available:
            update_label = QLabel()
            update_label.setOpenExternalLinks(True)
            update_label.setText(
                '<a href="https://github.com/theJayTea/WritingTools/releases" style="color:rgb(255, 0, 0); text-decoration: underline; font-weight: bold;">There\'s an update! :D Download now.</a>',
            )
            update_label.setStyleSheet("margin-top: 10px;")
            content_layout.addWidget(update_label, alignment=QtCore.Qt.AlignCenter)

        logging.debug("CustomPopupWindow UI setup complete")
        self.installEventFilter(self)
        QtCore.QTimer.singleShot(250, lambda: self.custom_input.setFocus())

    def get_actions(self):
        """
        Get actions directly from the unified settings system.
        Returns ActionConfig objects, no conversion needed.
        """
        if not hasattr(self.app, "settings_manager") or not self.app.settings_manager.settings:
            logging.warning("Settings manager not available, using default actions")
            return create_default_actions_config()

        logging.debug("Loading actions from unified settings")
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

        self.button_widgets.clear()
        actions = self.get_actions()

        for name, action_config in actions.items():
            if name == "Custom":
                continue
            b = DraggableButton(self, name, name)
            icon_path = get_icon_path(action_config.icon, with_theme=True)
            if os.path.exists(icon_path):
                b.setIcon(QtGui.QIcon(icon_path))

            # Add tooltip with tool name and description
            tooltip_text = name
            if action_config.instruction:
                # Truncate long instructions for tooltip
                instruction = (
                    action_config.instruction[:100] + "..."
                    if len(action_config.instruction) > 100
                    else action_config.instruction
                )
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

        # Remove existing grid and Add New button
        for i in reversed(range(parent_layout.count())):
            item = parent_layout.itemAt(i)
            if isinstance(item, QtWidgets.QGridLayout):
                grid = item
                for j in reversed(range(grid.count())):
                    w = grid.itemAt(j).widget()
                    if w:
                        grid.removeWidget(w)
                parent_layout.removeItem(grid)
            elif item.widget() and isinstance(item.widget(), QPushButton) and item.widget().text() == "+ Add New":
                item.widget().deleteLater()

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

        parent_layout.addLayout(grid)

        # Add New button (only in edit mode & only if we have text)
        if edit_mode_to_use and self.has_text:
            add_btn = QPushButton("+ Add New")
            add_btn.setStyleSheet(
                f"""
                QPushButton {{
                    background-color: {'#333' if colorMode=='dark' else '#e0e0e0'};
                    border: 1px solid {'#666' if colorMode=='dark' else '#ccc'};
                    border-radius: 8px;
                    padding: 10px;
                    font-size: 14px;
                    text-align: center;
                    color: {'#fff' if colorMode=='dark' else '#000'};
                    margin-top: 10px;
                }}
                QPushButton:hover {{
                    background-color: {'#444' if colorMode=='dark' else '#d0d0d0'};
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
        btn.icon_container.setAttribute(QtCore.Qt.WA_TransparentForMouseEvents, False)

        btn.icon_container.setGeometry(0, 0, btn.width(), btn.height())

        circle_style = f"""
            QPushButton {{
                background-color: {'#666' if colorMode=='dark' else '#999'};
                border-radius: 10px;
                min-width: 16px;
                min-height: 16px;
                max-width: 16px;
                max-height: 16px;
                padding: 1px;
                margin: 0px;
            }}
            QPushButton:hover {{
                background-color: {'#888' if colorMode=='dark' else '#bbb'};
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
        self.edit_button.hide()
        self.close_button.hide()
        self.reset_button.show()
        self.edit_close_button.show()
        self.drag_label.show()
        self.input_area.setVisible(False)

        # Add edit overlays to buttons
        self.add_edit_overlays_to_buttons()

    def exit_edit_mode(self):
        """Exit edit mode - called when user clicks the close button in edit mode."""
        self.edit_mode = False
        logging.debug("Exiting edit mode")

        # Hide edit mode UI elements
        self.reset_button.hide()
        self.edit_close_button.hide()
        self.drag_label.hide()
        self.edit_button.show()
        self.close_button.show()
        self.input_area.setVisible(True)

        # Remove edit overlays from buttons
        self.remove_edit_overlays_from_buttons()

    def remove_edit_overlays_from_buttons(self):
        """Remove edit overlays from all buttons."""
        for btn in self.button_widgets:
            try:
                btn.clicked.disconnect()
            except:
                pass
            btn.clicked.connect(partial(self.on_generic_instruction, btn.key))
            if hasattr(btn, "icon_container") and btn.icon_container:
                btn.icon_container.deleteLater()
                btn.icon_container = None
            btn.setStyleSheet(btn.base_style)

        # Rebuild grid layout (force non-edit mode)
        self.rebuild_grid_layout(force_edit_mode=False)

    def initialize_button_visibility(self):
        """Initialize button visibility for normal (non-edit) mode."""
        self.edit_mode = False
        self.reset_button.hide()
        self.edit_close_button.hide()
        self.drag_label.hide()
        if self.has_text:
            self.edit_button.show()
        self.close_button.show()
        self.input_area.setVisible(True)

    def on_reset_clicked(self):
        """
        Reset options to default actions and reload the interface.
        """
        confirm_box = QtWidgets.QMessageBox()
        confirm_box.setWindowFlags(confirm_box.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        confirm_box.setWindowTitle("Confirm Reset to Defaults?")
        confirm_box.setText(
            "This will reset all buttons to their original configuration.\nYour custom buttons will be removed.\n\nAre you sure you want to continue?",
        )
        confirm_box.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm_box.setDefaultButton(QtWidgets.QMessageBox.No)

        if confirm_box.exec_() == QtWidgets.QMessageBox.Yes:
            try:
                logging.debug("Resetting to default actions")
                # Reset actions to defaults in unified settings
                if hasattr(self.app, "settings_manager") and self.app.settings_manager.settings:
                    # Reset actions to defaults
                    self.app.settings_manager.settings.actions = create_default_actions_config()
                    self.app.save_settings()
                else:
                    logging.error("Settings manager not available for reset")

                # Reload the interface immediately
                self.build_buttons_list()
                self.rebuild_grid_layout(force_edit_mode=self.edit_mode)

                # Show success message
                success_msg = QtWidgets.QMessageBox()
                success_msg.setWindowFlags(success_msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
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
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Added")
            msg.setText("Your new button has been saved and is now available in the tools list.")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
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
            msg.setWindowFlags(msg.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
            msg.setWindowTitle("Button Updated")
            msg.setText("Your button changes have been saved and are now active.")
            msg.setStandardButtons(QtWidgets.QMessageBox.Ok)
            msg.exec_()

            # Reload the window instead of closing it
            self.reload_window()

    def delete_button_clicked(self, btn):
        """Handle deletion of a button."""
        key = btn.key
        confirm = QtWidgets.QMessageBox()
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowStaysOnTopHint)
        confirm.setWindowTitle("Confirm Delete?")
        confirm.setText("Are you sure you want to continue?")
        confirm.setStandardButtons(QtWidgets.QMessageBox.Yes | QtWidgets.QMessageBox.No)
        confirm.setDefaultButton(QtWidgets.QMessageBox.No)

        if confirm.exec_() == QtWidgets.QMessageBox.Yes:
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
        self.app.save_settings()
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
        txt = self.custom_input.text().strip()
        if txt:
            self.app.process_option("Custom", self.selected_text, txt)
            self.close()

    def on_generic_instruction(self, instruction):
        if not self.edit_mode:
            self.app.process_option(instruction, self.selected_text)
            self.close()

    def eventFilter(self, obj, event):
        # Hide on deactivate only if NOT in edit mode
        if event.type() == QtCore.QEvent.WindowDeactivate:
            if not self.edit_mode:
                self.hide()
                return True
        return super().eventFilter(obj, event)

    def keyPressEvent(self, event):
        if event.key() == QtCore.Qt.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)
