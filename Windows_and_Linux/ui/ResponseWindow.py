import logging
from typing import TYPE_CHECKING, Optional

import markdown2
from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Slot
from PySide6.QtWidgets import (
    QScrollArea,
    QVBoxLayout,
    QWidget,
    QTextBrowser,
    QToolButton,
    QApplication,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QSizePolicy,
    QLineEdit,
)

from ui.ui_utils import ThemedWidget, get_effective_color_mode

if TYPE_CHECKING:
    from Windows_and_Linux.WritingToolApp import WritingToolApp

_ = lambda x: x


class MarkdownTextBrowser(QTextBrowser):
    """Enhanced text browser for displaying Markdown content with improved sizing"""

    def __init__(self, parent=None, is_user_message=False):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setOpenExternalLinks(True)
        self.zoom_factor = 1.2
        self.base_font_size = 14
        self.is_user_message = is_user_message

        # Critical: Remove scrollbars to prevent extra space
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)

        # Set size policies to prevent unwanted expansion
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        self._apply_zoom()

    def _apply_zoom(self):
        new_size = int(self.base_font_size * self.zoom_factor)

        # Updated stylesheet with table styling
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()

        self.setStyleSheet(
            f"""
            QTextBrowser {{
                background-color: {('transparent' if self.is_user_message else '#333' if current_mode == 'dark' else '#f8f9fa')};
                color: {'#ffffff' if current_mode == 'dark' else '#212529'};
                border: {('none' if self.is_user_message else '1px solid ' + ('#555' if current_mode == 'dark' else '#dee2e6'))};
                border-radius: 8px;
                padding: 8px;
                margin: 0px;
                font-size: {new_size}px;
                line-height: 1.3;
                width: 100%;
            }}

            /* Table styles */
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 10px 0;
            }}

            th, td {{
                border: 1px solid {'#555' if current_mode == 'dark' else '#dee2e6'};
                padding: 8px;
                text-align: left;
            }}

            th {{
                background-color: {'#444' if current_mode == 'dark' else '#e9ecef'};
                font-weight: bold;
            }}

            tr:nth-child(even) {{
                background-color: {'#3a3a3a' if current_mode == 'dark' else '#f8f9fa'};
            }}

            tr:hover {{
                background-color: {'#484848' if current_mode == 'dark' else '#e9ecef'};
            }}
        """,
        )

    def _update_size(self):
        # Calculate correct document width
        available_width = self.viewport().width() - 16  # Account for padding
        self.document().setTextWidth(available_width)

        # Get precise content height
        doc_size = self.document().size()
        content_height = doc_size.height()

        # Add minimal padding for content
        new_height = int(content_height + 16)  # Reduced total padding

        if self.minimumHeight() != new_height:
            self.setMinimumHeight(new_height)
            self.setMaximumHeight(new_height)  # Force fixed height

            # Update scroll area if needed
            scroll_area = self.get_scroll_area()
            if scroll_area:
                scroll_area.update_content_height()

    def wheelEvent(self, event):
        if event.modifiers() == Qt.KeyboardModifier.ControlModifier:
            delta = event.angleDelta().y()
            # Get the main response window
            parent = self.parent()
            while parent and not isinstance(parent, ResponseWindow):
                parent = parent.parent()

            if parent:
                if delta > 0:
                    parent.zoom_all_messages("in")
                else:
                    parent.zoom_all_messages("out")
                event.accept()
        # Pass wheel events to parent for scrolling
        else:
            parent = self.parent()
            if parent and isinstance(parent, QWidget) and hasattr(parent, 'wheelEvent'):
                parent.wheelEvent(event)

    def zoom_in(self):
        old_factor = self.zoom_factor
        self.zoom_factor = min(3.0, self.zoom_factor * 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def zoom_out(self):
        old_factor = self.zoom_factor
        self.zoom_factor = max(0.5, self.zoom_factor / 1.1)
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def reset_zoom(self):
        old_factor = self.zoom_factor
        self.zoom_factor = 1.2  # Reset to default zoom
        if old_factor != self.zoom_factor:
            self._apply_zoom()
            self._update_size()

    def get_scroll_area(self):
        """Find the parent ChatContentScrollArea"""
        parent = self.parent()
        while parent:
            if isinstance(parent, ChatContentScrollArea):
                return parent
            parent = parent.parent()
        return None

    def resizeEvent(self, event):
        super().resizeEvent(event)
        self._update_size()


class MessageContainer(QWidget):
    """Container for individual messages with copy functionality"""

    def __init__(self, parent=None, is_user=False, text="", text_display=None):
        super().__init__(parent)
        self.markdown_text = text
        self.is_user = is_user
        self.text_display = text_display
        self.setSizePolicy(
            QSizePolicy.Policy.Expanding,
            QSizePolicy.Policy.Minimum,
        )

        # Main layout for the message container
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        if self.text_display:
            layout.addWidget(self.text_display)

        # Add copy button for assistant messages only (positioned absolutely)
        if not is_user:
            self.copy_btn = QToolButton(self)
            # Use the copy_md icon (SVG format with theme support)
            from ui.ui_utils import get_icon_path

            icon_path = get_icon_path("copy_md", with_theme=True)
            self.copy_btn.setIcon(QtGui.QIcon(icon_path))
            from ui.ui_utils import get_effective_color_mode

            current_mode = get_effective_color_mode()

            self.copy_btn.setStyleSheet(
                f"""
                QToolButton {{
                    background-color: {'rgba(68, 68, 68, 0.9)' if current_mode == 'dark' else 'rgba(248, 249, 250, 0.95)'};
                    border: 1px solid {'#666' if current_mode == 'dark' else '#dee2e6'};
                    border-radius: 6px;
                    padding: 2px;
                    margin: 0px;
                    spacing: 0px;
                }}
                QToolButton:hover {{
                    background-color: {'rgba(85, 85, 85, 0.9)' if current_mode == 'dark' else 'rgba(233, 236, 239, 0.95)'};
                    border: 1px solid {'#777' if current_mode == 'dark' else '#adb5bd'};
                }}
            """,
            )
            self.copy_btn.setToolTip(_("Copy as Markdown"))
            self.copy_btn.clicked.connect(self.copy_content)
            self.copy_btn.setFixedSize(32, 32)
            self.copy_btn.setIconSize(QtCore.QSize(24, 24))
            self.copy_btn.hide()  # Initially hidden

            # Install event filter to handle hover
            self.installEventFilter(self)

    def eventFilter(self, obj, event):
        """Handle mouse enter/leave events to show/hide copy button"""
        if obj == self and not self.is_user:
            if event.type() == QtCore.QEvent.Type.Enter:
                if hasattr(self, "copy_btn"):
                    self.copy_btn.show()
            elif event.type() == QtCore.QEvent.Type.Leave:
                if hasattr(self, "copy_btn"):
                    self.copy_btn.hide()
        return super().eventFilter(obj, event)

    def resizeEvent(self, event):
        """Position the copy button in the top-right corner"""
        super().resizeEvent(event)
        if hasattr(self, "copy_btn") and not self.is_user:
            # Position button in top-right corner with some margin
            btn_size = self.copy_btn.size()
            self.copy_btn.move(
                self.width() - btn_size.width() - 8,  # 8px from right edge
                8,  # 8px from top edge
            )

    def copy_content(self):
        """Copy the message content to clipboard with visual feedback"""
        QApplication.clipboard().setText(self.markdown_text)

        # Visual feedback: temporarily change button color
        if hasattr(self, "copy_btn"):
            original_style = self.copy_btn.styleSheet()

            # Success feedback style
            success_style = f"""
                QToolButton {{
                    background-color: rgba(76, 175, 80, 0.9);
                    border: 1px solid #4CAF50;
                    border-radius: 6px;
                    padding: 2px;
                }}
            """

            # Apply success style
            self.copy_btn.setStyleSheet(success_style)

            # Reset to original style after 500ms
            QtCore.QTimer.singleShot(
                500,
                lambda: self.copy_btn.setStyleSheet(original_style),
            )


class ChatContentScrollArea(QScrollArea):
    """Improved scrollable container for chat messages with dynamic sizing and proper spacing"""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.content_widget: Optional[QWidget] = None
        self.layout: Optional[QVBoxLayout] = None
        self.setup_ui()

    def setup_ui(self):
        self.setWidgetResizable(True)
        self.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.setVerticalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAsNeeded)

        # Main container widget with explicit size policy
        self.content_widget = QWidget()
        self.content_widget.setSizePolicy(
            QSizePolicy.Policy.Preferred,
            QSizePolicy.Policy.MinimumExpanding,
        )
        self.setWidget(self.content_widget)

        # Main layout with improved spacing
        self.layout = QVBoxLayout(self.content_widget)
        self.layout.setSpacing(8)  # Reduced spacing between messages
        self.layout.setContentsMargins(15, 15, 15, 15)  # Adjusted margins
        self.layout.addStretch()

        # Enhanced scroll area styling - consistent with SettingsWindow
        self.setStyleSheet(
            """
            QScrollArea {
                background-color: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background-color: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(0, 0, 0, 0.1);
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(128, 128, 128, 0.6);
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(128, 128, 128, 1.0);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """,
        )

    def add_message(self, text, is_user=False):
        if not self.layout:
            return None

        # Remove bottom stretch
        self.layout.takeAt(self.layout.count() - 1)

        # Create text display first
        text_display = MarkdownTextBrowser(self.content_widget, is_user_message=is_user)
        html = markdown2.markdown(text, extras=["tables"])
        text_display.setHtml(html)

        # Wrap in MessageContainer for copy functionality
        msg_container = MessageContainer(
            self.content_widget,
            is_user=is_user,
            text=text,
            text_display=text_display,
        )

        self.layout.addWidget(msg_container)
        self.layout.addStretch()

        parent = self.parent()
        if hasattr(parent, "current_text_display") and isinstance(parent, ResponseWindow):
            parent.current_text_display = text_display

        QtCore.QTimer.singleShot(50, self.post_message_updates)

        return text_display

    def post_message_updates(self):
        """Handle updates after adding a message with proper timing"""
        self.scroll_to_bottom()
        parent = self.parent()
        if isinstance(parent, ResponseWindow):
            parent._adjust_window_height()

    def update_content_height(self):
        """Recalculate total content height with improved spacing calculation"""
        if not self.layout:
            return

        total_height = 0

        # Calculate height of all messages
        for i in range(self.layout.count() - 1):  # Skip stretch item
            item = self.layout.itemAt(i)
            if item and item.widget():
                widget_height = item.widget().sizeHint().height()
                total_height += widget_height

        # Add spacing between messages and margins
        total_height += self.layout.spacing() * (self.layout.count() - 2)  # Message spacing
        total_height += self.layout.contentsMargins().top() + self.layout.contentsMargins().bottom()

        # Set minimum height with some padding
        if self.content_widget:
            self.content_widget.setMinimumHeight(total_height + 10)

        # Update window height if needed
        parent = self.parent()
        if isinstance(parent, ResponseWindow):
            parent._adjust_window_height()

    def scroll_to_bottom(self):
        """Smooth scroll to bottom of content"""
        vsb = self.verticalScrollBar()
        vsb.setValue(vsb.maximum())

    def resizeEvent(self, event):
        """Handle resize events with improved width calculations"""
        super().resizeEvent(event)

        if not self.layout:
            return

        # Update width for all message displays
        available_width = self.width() - 40  # Account for margins
        for i in range(self.layout.count() - 1):  # Skip stretch item
            item = self.layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                if isinstance(container, MessageContainer):
                    # Recalculate text width and height for MessageContainer
                    text_display = container.text_display
                    if text_display and text_display.document():
                        text_display.document().setTextWidth(available_width)
                        doc_size = text_display.document().size()
                        exact_height = int(doc_size.height() + 20)  # Reduced padding
                        text_display.setMinimumHeight(exact_height)
                        text_display.setMaximumHeight(exact_height)  # Fixed height for all messages


class ResponseWindow(ThemedWidget):
    """Enhanced response window with improved sizing and zoom handling"""

    def __init__(self, app: 'WritingToolApp', title=_("Response"), parent=None):
        super().__init__()
        self.app = app
        self.original_title = title
        self.setWindowTitle(title)
        self.option = title.replace(" Result", "")
        self.selected_text = None
        self.input_field = None
        self.loading_label = None
        self.loading_container = None
        self.chat_area = None
        self.chat_history = []
        self.current_text_display: Optional[MarkdownTextBrowser] = None

        # Setup thinking animation with full range of dots
        self.thinking_timer = QtCore.QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_dots)
        self.thinking_dots_state = 0
        self.thinking_dots = ["", ".", "..", "..."]  # Now properly includes all states
        self.thinking_timer.setInterval(300)

        self.init_ui()
        logging.debug("Connecting response signals")
        self.app.followup_response_signal.connect(self.handle_followup_response)
        logging.debug("Response signals connected")

        # Set initial size for "Thinking..." state
        initial_width = 500
        initial_height = 250
        self.resize(initial_width, initial_height)

    def init_ui(self):
        # Window setup with enhanced flags
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowMaximizeButtonHint,
        )
        self.setMinimumSize(600, 400)

        # Main layout setup
        content_layout = QVBoxLayout(self.background)
        content_layout.setContentsMargins(20, 20, 20, 20)
        content_layout.setSpacing(10)

        # Top bar with zoom controls
        top_bar = QHBoxLayout()

        title_label = QLabel(self.option)
        current_mode = get_effective_color_mode()
        title_label.setStyleSheet(
            f"font-size: 20px; font-weight: bold; color: {'#ffffff' if current_mode == 'dark' else '#333333'};",
        )
        top_bar.addWidget(title_label)

        top_bar.addStretch()

        # Zoom label with matched size
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(
            f"""
            color: {'#aaaaaa' if current_mode == 'dark' else '#666666'};
            font-size: 14px;
            margin-right: 5px;
        """,
        )
        top_bar.addWidget(zoom_label)

        # Enhanced zoom controls with swapped order
        zoom_controls = [
            ("plus", "Zoom In", lambda: self.zoom_all_messages("in")),
            ("minus", "Zoom Out", lambda: self.zoom_all_messages("out")),
            ("reset", "Reset Zoom", lambda: self.zoom_all_messages("reset")),
        ]

        for icon, tooltip, action in zoom_controls:
            btn = QPushButton()
            from ui.ui_utils import get_icon_path

            btn.setIcon(QtGui.QIcon(get_icon_path(icon, with_theme=True)))
            btn.setStyleSheet(self.get_button_style())
            btn.setToolTip(tooltip)
            btn.clicked.connect(action)
            btn.setFixedSize(30, 30)
            top_bar.addWidget(btn)

        content_layout.addLayout(top_bar)

        # Copy controls with matching text size
        copy_bar = QHBoxLayout()
        copy_hint = QLabel(
            _("Hover over assistant responses for individual copy buttons"),
        )
        copy_hint.setStyleSheet(
            f"color: {'#aaaaaa' if current_mode == 'dark' else '#666666'}; font-size: 14px;",
        )
        copy_bar.addWidget(copy_hint)
        copy_bar.addStretch()
        content_layout.addLayout(copy_bar)

        # Loading indicator
        loading_container = QWidget()
        loading_layout = QHBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)

        self.loading_label = QLabel(_("Thinking"))
        self.loading_label.setStyleSheet(
            f"""
            QLabel {{
                color: {'#ffffff' if current_mode == 'dark' else '#333333'};
                font-size: 18px;
                padding: 20px;
            }}
        """,
        )
        self.loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        loading_inner_container = QWidget()
        loading_inner_container.setFixedWidth(180)
        loading_inner_layout = QHBoxLayout(loading_inner_container)
        loading_inner_layout.setContentsMargins(0, 0, 0, 0)
        loading_inner_layout.addWidget(self.loading_label)

        loading_layout.addStretch()
        loading_layout.addWidget(loading_inner_container)
        loading_layout.addStretch()

        content_layout.addWidget(loading_container)
        self.loading_container = loading_container

        # Start thinking animation
        self.start_thinking_animation(initial=True)

        # Enhanced chat area with full width
        self.chat_area = ChatContentScrollArea()
        content_layout.addWidget(self.chat_area)

        # Input area with enhanced styling
        bottom_bar = QHBoxLayout()

        self.input_field = QLineEdit()
        self.input_field.setPlaceholderText(_("Ask a follow-up question") + "...")
        self.input_field.setStyleSheet(
            f"""
            QLineEdit {{
                padding: 8px;
                border: 1px solid {'#777' if current_mode == 'dark' else '#dee2e6'};
                border-radius: 8px;
                background-color: {'#333' if current_mode == 'dark' else '#f8f9fa'};
                color: {'#ffffff' if current_mode == 'dark' else '#212529'};
                font-size: 14px;
            }}
        """,
        )
        self.input_field.returnPressed.connect(self.send_message)
        bottom_bar.addWidget(self.input_field)

        send_button = QPushButton()
        from ui.ui_utils import get_icon_path

        send_button.setIcon(QtGui.QIcon(get_icon_path("send", with_theme=True)))
        send_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {'#2e7d32' if current_mode == 'dark' else '#4CAF50'};
                border: none;
                border-radius: 8px;
                padding: 5px;
            }}
            QPushButton:hover {{
                background-color: {'#1b5e20' if current_mode == 'dark' else '#45a049'};
            }}
        """,
        )
        send_button.setFixedSize(
            self.input_field.sizeHint().height(),
            self.input_field.sizeHint().height(),
        )
        send_button.clicked.connect(self.send_message)
        bottom_bar.addWidget(send_button)

        content_layout.addLayout(bottom_bar)

    # Method to get first response text
    def get_first_response_text(self):
        """Get the first model response text from chat history"""
        try:
            # Check chat history exists
            if not self.chat_history:
                return None

            # Find first assistant message
            for msg in self.chat_history:
                if msg["role"] == "assistant":
                    return msg["content"]

            return None
        except Exception as e:
            logging.exception(f"Error getting first response: {e}")
            return None

    def copy_first_response(self):
        """Copy only the first model response as Markdown"""
        response_text = self.get_first_response_text()
        if response_text:
            QApplication.clipboard().setText(response_text)

    def get_button_style(self):
        current_mode = get_effective_color_mode()
        return f"""
            QPushButton {{
                background-color: {'#444' if current_mode == 'dark' else '#f8f9fa'};
                color: {'#ffffff' if current_mode == 'dark' else '#212529'};
                border: 1px solid {'#666' if current_mode == 'dark' else '#dee2e6'};
                border-radius: 5px;
                padding: 8px;
                font-size: 14px;
            }}
            QPushButton:hover {{
                background-color: {'#555' if current_mode == 'dark' else '#e9ecef'};
            }}
        """

    def update_thinking_dots(self):
        """Update the thinking animation dots with proper cycling"""
        self.thinking_dots_state = (self.thinking_dots_state + 1) % len(self.thinking_dots)
        dots = self.thinking_dots[self.thinking_dots_state]

        if self.loading_label and self.loading_label.isVisible():
            self.loading_label.setText(_("Thinking") + f"{dots}")
        elif self.input_field:
            self.input_field.setPlaceholderText(_("Thinking") + f"{dots}")

    def start_thinking_animation(self, initial=False):
        """Start the thinking animation for either initial load or follow-up questions"""
        self.thinking_dots_state = 0

        if initial and self.loading_label and self.loading_container:
            self.loading_label.setText(_("Thinking"))
            self.loading_label.setVisible(True)
            self.loading_container.setVisible(True)
        elif self.input_field:
            self.input_field.setPlaceholderText(_("Thinking"))
            if self.loading_container:
                self.loading_container.setVisible(False)

        self.thinking_timer.start()

    def stop_thinking_animation(self):
        """Stop the thinking animation"""
        self.thinking_timer.stop()
        if self.loading_container:
            self.loading_container.hide()
        if self.loading_label:
            self.loading_label.hide()
        if self.input_field:
            self.input_field.setPlaceholderText(_("Ask a follow-up question"))
            self.input_field.setEnabled(True)

        # Force layout update
        if self.layout():
            self.layout().invalidate()
            self.layout().activate()

    def zoom_all_messages(self, action="in"):
        """Apply zoom action to all messages in the chat"""
        if not self.chat_area or not self.chat_area.layout:
            return

        for i in range(self.chat_area.layout.count() - 1):  # Skip stretch item
            item = self.chat_area.layout.itemAt(i)
            if item and item.widget():
                container = item.widget()
                if isinstance(container, MessageContainer):
                    text_display = container.text_display
                    if text_display:
                        if action == "in":
                            text_display.zoom_in()
                        elif action == "out":
                            text_display.zoom_out()
                        else:  # reset
                            text_display.reset_zoom()

        # Update layout after zooming
        if self.chat_area:
            self.chat_area.update_content_height()

    def _adjust_window_height(self):
        """Calculate and set the ideal window height"""
        # Skip adjustment if window already has a size
        if hasattr(self, "_size_initialized"):
            return

        try:
            # Get content widget height
            if not self.chat_area or not self.chat_area.content_widget:
                return

            content_height = self.chat_area.content_widget.sizeHint().height()

            # Calculate other UI elements height
            input_height = self.input_field.height() if self.input_field else 0
            ui_elements_height = (
                self.layout().contentsMargins().top()
                + self.layout().contentsMargins().bottom()
                + input_height
                + self.layout().spacing() * 5
                + 200  # Increased from 185 for taller default height
            )

            # Get screen constraints
            screen = QApplication.screenAt(self.pos())
            if not screen:
                screen = QApplication.primaryScreen()

            # Calculate maximum available height (85% of screen)
            max_height = int(screen.geometry().height() * 0.85)

            # Calculate desired height to show more content initially
            desired_content_height = int(content_height * 0.85)  # Show 85% of content
            desired_total_height = min(
                desired_content_height + ui_elements_height,
                max_height,
            )

            # Set reasonable minimum height - increased by 10%
            final_height = max(600, desired_total_height)  # Increased from 540

            # Set width to 600px
            final_width = 600

            # Update both width and height
            self.resize(final_width, final_height)

            # Center on screen
            frame_geometry = self.frameGeometry()
            screen_center = screen.geometry().center()
            frame_geometry.moveCenter(screen_center)
            self.move(frame_geometry.topLeft())

            # Mark size as initialized
            self._size_initialized = True

        except Exception as e:
            logging.exception(f"Error adjusting window height: {e}")
            self.resize(600, 600)  # Updated fallback size
            self._size_initialized = True

    @Slot(str)
    def set_text(self, text):
        """Set initial response text with enhanced handling"""
        if not text.strip() or not self.chat_area:
            return

        # Always ensure chat history is initialized properly
        self.chat_history = [
            {"role": "user", "content": f"{self.option}: {self.selected_text}"},
            {"role": "assistant", "content": text},  # Add initial response immediately
        ]

        self.stop_thinking_animation()
        text_display = self.chat_area.add_message(text)

        # Update zoom state
        if (
            self.app.settings_manager.settings.custom_data
            and "response_window_zoom" in self.app.settings_manager.settings.custom_data
            and text_display
        ):
            text_display.zoom_factor = self.app.settings_manager.settings.custom_data["response_window_zoom"]
            text_display._apply_zoom()

        QtCore.QTimer.singleShot(100, self._adjust_window_height)

    @Slot(str)
    def handle_followup_response(self, response_text):
        """Handle the follow-up response from the AI with improved layout handling"""
        if response_text and self.chat_area:
            if self.loading_label:
                self.loading_label.setVisible(False)
            text_display = self.chat_area.add_message(response_text)

            # Maintain consistent zoom level
            if hasattr(self, "current_text_display") and self.current_text_display and text_display:
                text_display.zoom_factor = self.current_text_display.zoom_factor
                text_display._apply_zoom()

            if len(self.chat_history) > 0 and self.chat_history[-1]["role"] != "assistant":
                self.chat_history.append(
                    {"role": "assistant", "content": response_text},
                )

        self.stop_thinking_animation()
        if self.input_field:
            self.input_field.setEnabled(True)

        # Update window height
        QtCore.QTimer.singleShot(100, self._adjust_window_height)

    def send_message(self):
        """Send a new message/question"""
        if not self.input_field or not self.chat_area:
            return

        message = self.input_field.text().strip()
        if not message:
            return

        self.input_field.setEnabled(False)
        self.input_field.clear()

        # Add user message and maintain zoom level
        text_display = self.chat_area.add_message(message, is_user=True)
        if hasattr(self, "current_text_display") and self.current_text_display and text_display:
            text_display.zoom_factor = self.current_text_display.zoom_factor
            text_display._apply_zoom()

        self.chat_history.append({"role": "user", "content": message})
        self.start_thinking_animation()
        self.app.process_followup_question(self, message)

    def copy_as_markdown(self):
        """Copy conversation as Markdown"""
        markdown = ""
        for msg in self.chat_history:
            if msg["role"] == "user":
                markdown += f"**User**: {msg['content']}\n\n"
            else:
                markdown += f"**Assistant**: {msg['content']}\n\n"

        QApplication.clipboard().setText(markdown)

    def closeEvent(self, event):
        """Handle window close event"""
        # Save zoom factor to settings
        if hasattr(self, "current_text_display") and self.current_text_display:
            if not self.app.settings_manager.settings.custom_data:
                self.app.settings_manager.settings.custom_data = {}
            self.app.settings_manager.response_window_zoom = self.current_text_display.zoom_factor
            self.app.save_settings()

        self.chat_history = []

        if hasattr(self.app, "current_response_window"):
            delattr(self.app, "current_response_window")

        super().closeEvent(event)
