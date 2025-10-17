import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtCore import Qt, Signal, Slot
from PySide6.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from ..ui_utils import ThemedWidget, ui_utils
from .chat_scroll_area import ChatContentScrollArea
from .markdown_text_browser import MarkdownTextBrowser
from .message_container import MessageContainer

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


def _(x):
    return x


class ResponseWindow(ThemedWidget):
    """Enhanced response window"""

    followup_response_signal = Signal(str)

    def __init__(
        self,
        app: "WritingToolsApp",
        title: str = _("Response"),
        parent: QWidget | None = None,
    ):
        super().__init__(app)
        self._logger = logging.getLogger(__name__)
        self.app = app
        self.content_layout: QVBoxLayout | None = None
        self.original_title = title
        self.setWindowTitle(_("Response"))
        self.option = title.replace(" Result", "")
        self.selected_text: str | None = None
        self.image: QtGui.QImage | None = None
        self.input_field = None
        self.loading_label = None
        self.loading_container = None
        self.chat_area = None
        self.chat_history = []
        self.current_text_display: MarkdownTextBrowser | None = None

        # Setup thinking animation with full range of dots
        self.thinking_timer = QtCore.QTimer(self)
        self.thinking_timer.timeout.connect(self.update_thinking_dots)
        self.thinking_dots_state = 0
        self.thinking_dots = ["", ".", "..", "..."]  # Now properly includes all states
        self.thinking_timer.setInterval(300)

        self.init_ui()
        self._logger.debug("Connecting response signals")
        self.followup_response_signal.connect(self.handle_followup_response)
        self._logger.debug("Response signals connected")

        # Set initial size for "Thinking..." state
        initial_width = 500
        initial_height = 250
        self.resize(initial_width, initial_height)

    def init_ui(self) -> None:
        self.setMinimumSize(600, 400)

        # Main layout setup
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)

        # Top bar with zoom controls
        top_bar = QHBoxLayout()

        title_label = QLabel(self.option)
        title_label.setStyleSheet(self.app.styles["response_window_title"])
        top_bar.addWidget(title_label)

        # Add image indicator in title bar if we have an image
        if self.image:
            image_indicator = QLabel("📷")
            image_indicator.setStyleSheet(self.app.styles["response_window_image_indicator"])
            image_indicator.setToolTip("Image analysis mode")
            top_bar.addWidget(image_indicator)

        top_bar.addStretch()

        # Zoom label with matched size
        zoom_label = QLabel("Zoom:")
        zoom_label.setStyleSheet(self.app.styles["response_window_zoom_label"])
        top_bar.addWidget(zoom_label)

        # Enhanced zoom controls with swapped order
        zoom_controls = [
            ("plus", "Zoom In", lambda: self.zoom_all_messages("in")),
            ("minus", "Zoom Out", lambda: self.zoom_all_messages("out")),
            ("reset", "Reset Zoom", lambda: self.zoom_all_messages("reset")),
        ]

        for icon, tooltip, action in zoom_controls:
            btn = QPushButton()

            btn.setIcon(
                QtGui.QIcon(ui_utils.get_icon_path(self.app, icon, with_theme=True).as_posix())
            )
            btn.setStyleSheet(self.app.styles["response_window_zoom_button"])
            btn.setToolTip(tooltip)
            btn.clicked.connect(action)
            btn.setFixedSize(30, 30)
            top_bar.addWidget(btn)

        self.content_layout.addLayout(top_bar)

        # Add image preview if we have an image
        if self.image:
            self._create_image_preview_section()

        # Copy controls with matching text size
        copy_bar = QHBoxLayout()
        copy_hint = QLabel(
            _("Hover over assistant responses for individual copy buttons"),
        )
        copy_hint.setStyleSheet(self.app.styles["response_window_copy_hint"])
        copy_bar.addWidget(copy_hint)
        copy_bar.addStretch()
        self.content_layout.addLayout(copy_bar)

        # Loading indicator
        loading_container = QWidget()
        loading_layout = QHBoxLayout(loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)

        self.loading_label = QLabel(_("Analyzing image" if self.image else "Thinking"))
        self.loading_label.setStyleSheet(self.app.styles["response_window_loading_label"])
        self.loading_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)

        loading_inner_container = QWidget()
        loading_inner_container.setFixedWidth(180)
        loading_inner_layout = QHBoxLayout(loading_inner_container)
        loading_inner_layout.setContentsMargins(0, 0, 0, 0)
        loading_inner_layout.addWidget(self.loading_label)

        loading_layout.addStretch()
        loading_layout.addWidget(loading_inner_container)
        loading_layout.addStretch()

        self.content_layout.addWidget(loading_container)
        self.loading_container = loading_container

        # Start thinking animation
        self.start_thinking_animation(initial=True)

        # Enhanced chat area with full width
        self.chat_area = ChatContentScrollArea(self.app)
        self.content_layout.addWidget(self.chat_area)

        # Input area with enhanced styling
        bottom_bar = QHBoxLayout()

        self.input_field = QLineEdit()
        placeholder_text = (
            _("Ask a follow-up question about this image") + "..."
            if self.image
            else _("Ask a follow-up question") + "..."
        )
        self.input_field.setPlaceholderText(placeholder_text)
        self.input_field.setStyleSheet(self.app.styles["response_window_input"])
        self.input_field.returnPressed.connect(self.send_message)
        self.input_field.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
        bottom_bar.addWidget(self.input_field)

        send_button = QPushButton()

        send_button.setIcon(
            QtGui.QIcon(ui_utils.get_icon_path(self.app, "send", with_theme=True).as_posix())
        )
        send_button.setStyleSheet(self.app.styles["response_window_send_button"])
        send_button.setFixedSize(
            self.input_field.sizeHint().height(),
            self.input_field.sizeHint().height(),
        )
        send_button.clicked.connect(self.send_message)
        bottom_bar.addWidget(send_button)

        self.content_layout.addLayout(bottom_bar)

        # Ensure input field gets focus when window opens (moved to AIProcessor for better timing)

    def set_input_focus(self) -> None:
        """Force focus on input field when window opens"""
        if self.input_field:
            self.input_field.setFocus(Qt.FocusReason.OtherFocusReason)

    def _create_image_preview_section(self) -> None:
        """Create a collapsible image preview section in the response window."""
        if not self.image:
            return

        # Create collapsible section
        image_section = QWidget()
        image_section.setStyleSheet(self.app.styles["response_window_image_section"])

        section_layout = QVBoxLayout(image_section)
        section_layout.setContentsMargins(10, 10, 10, 10)
        section_layout.setSpacing(8)

        # Header with collapse/expand button
        header_layout = QHBoxLayout()

        self.toggle_button = QPushButton("▼")
        self.toggle_button.setFixedSize(20, 20)
        self.toggle_button.setStyleSheet(self.app.styles["response_window_toggle_button"])
        self.toggle_button.clicked.connect(self._toggle_image_preview)
        header_layout.addWidget(self.toggle_button)

        header_label = QLabel("Source Image")
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
        if self.content_layout:
            self.content_layout.addWidget(image_section)

        # Store references for toggling
        self.image_section = image_section
        self.image_display_collapsed = False

    def _toggle_image_preview(self) -> None:
        """Toggle the image preview visibility."""
        if hasattr(self, "image_display_widget") and hasattr(self, "toggle_button"):
            if self.image_display_collapsed:
                self.image_display_widget.setVisible(True)
                self.toggle_button.setText("▼")
                self.image_display_collapsed = False
            else:
                self.image_display_widget.setVisible(False)
                self.toggle_button.setText("▶")
                self.image_display_collapsed = True

    def update_thinking_dots(self) -> None:
        """Update the thinking animation dots with proper cycling"""
        self.thinking_dots_state = (self.thinking_dots_state + 1) % len(self.thinking_dots)
        dots = self.thinking_dots[self.thinking_dots_state]

        if self.loading_label and self.loading_label.isVisible():
            self.loading_label.setText(_("Thinking") + f"{dots}")
        elif self.input_field:
            self.input_field.setPlaceholderText(_("Thinking") + f"{dots}")

    def start_thinking_animation(self, initial=False) -> None:
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

    def stop_thinking_animation(self) -> None:
        """Stop the thinking animation"""
        self.thinking_timer.stop()
        if self.loading_container:
            self.loading_container.hide()
        if self.loading_label:
            self.loading_label.hide()
        if self.input_field:
            placeholder_text = (
                _("Ask a follow-up question about this image") + "..."
                if self.image
                else _("Ask a follow-up question") + "..."
            )
            self.input_field.setPlaceholderText(placeholder_text)
            self.input_field.setEnabled(True)
            # Force focus on input field, especially important for image mode
            QtCore.QTimer.singleShot(50, self.set_input_focus)

        # Force layout update
        if self.layout():
            self.layout().invalidate()
            self.layout().activate()

    def zoom_all_messages(self, action="in") -> None:
        """Apply zoom action to all messages in the chat"""
        if not self.chat_area or not self.chat_area.content_layout:
            return

        for i in range(self.chat_area.content_layout.count() - 1):  # Skip stretch item
            item = self.chat_area.content_layout.itemAt(i)
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

    def _adjust_window_height(self) -> None:
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
            self._logger.exception(f"Error adjusting window height: {e}")
            self.resize(600, 600)  # Updated fallback size
            self._size_initialized = True

    @Slot(str)
    def set_text(self, text: str) -> None:
        """Set initial response text with enhanced handling for image analysis"""
        if not text.strip() or not self.chat_area:
            return

        # Enhanced chat history initialization for image analysis
        if self.image:
            self.chat_history = [
                {"role": "user", "content": f"Image analysis request: {self.option}"},
                {"role": "assistant", "content": text},
            ]
        else:
            self.chat_history = [
                {"role": "user", "content": f"{self.option}: {self.selected_text}"},
                {"role": "assistant", "content": text},
            ]

        self.stop_thinking_animation()
        text_display = self.chat_area.add_message(text)

        # Update zoom state
        if text_display:
            text_display.zoom_factor = getattr(
                self.app.settings_manager, "response_window_zoom", 1.2
            )
            text_display._apply_zoom()

        QtCore.QTimer.singleShot(100, self._adjust_window_height)

        # Ensure input field keeps focus after content is displayed
        QtCore.QTimer.singleShot(150, self.set_input_focus)

    @Slot(str)
    def handle_followup_response(self, response_text: str) -> None:
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

    def send_message(self) -> None:
        """Send a new message/question"""
        if not self.input_field or not self.chat_area:
            return

        message = self.input_field.text()
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
        self.app.ai_processor.process_followup_question(self, message)

    def copy_as_markdown(self) -> None:
        """Copy conversation as Markdown"""
        markdown = ""
        for msg in self.chat_history:
            if msg["role"] == "user":
                markdown += f"**User**: {msg['content']}\n\n"
            else:
                markdown += f"**Assistant**: {msg['content']}\n\n"

        QApplication.clipboard().setText(markdown)

    def refresh_language(self) -> None:
        """Refresh all text elements to reflect the current language."""
        print("DEBUG: ResponseWindow.refresh_language() appelée!")  # DEBUG
        try:
            # Update window title
            self.setWindowTitle(_("Response"))

            # Update title label (first widget in top bar)
            if self.content_layout:
                top_bar_item = self.content_layout.itemAt(0)
                if top_bar_item:
                    top_bar_layout = top_bar_item.layout()
                    if top_bar_layout:
                        # Title is the first widget
                        title_widget = top_bar_layout.itemAt(0).widget()
                        if isinstance(title_widget, QLabel):
                            title_widget.setText(self.option)

                        # Find and update zoom label
                        for i in range(top_bar_layout.count()):
                            item = top_bar_layout.itemAt(i)
                            if item and item.widget():
                                widget = item.widget()
                                if isinstance(widget, QLabel) and "Zoom" in widget.text():
                                    widget.setText(_("Zoom:"))

            # Update copy hint
            if self.content_layout:
                for i in range(self.content_layout.count()):
                    item = self.content_layout.itemAt(i)
                    if item and item.layout():
                        layout = item.layout()
                        for j in range(layout.count()):
                            widget_item = layout.itemAt(j)
                            if widget_item and widget_item.widget():
                                widget = widget_item.widget()
                                if isinstance(widget, QLabel) and "Hover over" in widget.text():
                                    widget.setText(
                                        _(
                                            "Hover over assistant responses for individual copy buttons"
                                        )
                                    )

            # Update loading label
            if self.loading_label and self.loading_label.isVisible():
                current_text = self.loading_label.text()
                if "Analyzing" in current_text:
                    self.loading_label.setText(_("Analyzing image"))
                elif "Thinking" in current_text:
                    # Preserve the dots
                    dots = current_text.replace("Thinking", "").replace("Analyzing image", "")
                    self.loading_label.setText(_("Thinking") + dots)

            # Update input field placeholder
            if self.input_field:
                current_placeholder = self.input_field.placeholderText()
                if "Thinking" in current_placeholder:
                    # Preserve the dots
                    dots = current_placeholder.replace("Thinking", "")
                    self.input_field.setPlaceholderText(_("Thinking") + dots)
                else:
                    placeholder_text = (
                        _("Ask a follow-up question about this image") + "..."
                        if self.image
                        else _("Ask a follow-up question") + "..."
                    )
                    self.input_field.setPlaceholderText(placeholder_text)

            # Update image section header if present
            if hasattr(self, "image_section"):
                for child in self.image_section.findChildren(QLabel):
                    if child.text() == "Source Image":
                        child.setText(_("Source Image"))
                        break

            # Update all child widgets that have refresh_language method
            for child in self.findChildren(QWidget):
                if hasattr(child, "refresh_language") and child != self:
                    try:
                        child.refresh_language()  # type: ignore
                    except RuntimeError:
                        pass  # Widget destroyed

        except RuntimeError:
            # Widget might be destroyed, skip refresh
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event"""
        # Cancel any ongoing AI request when window is closed
        if self.app.ai_processor.current_provider:
            self.app.ai_processor.current_provider.cancel()

        # Save zoom factor to settings
        if hasattr(self, "current_text_display") and self.current_text_display:
            self.app.settings_manager.response_window_zoom = self.current_text_display.zoom_factor

        self.chat_history = []

        if self.app.current_response_window is not None:
            self.app.current_response_window = None

        super().closeEvent(event)
