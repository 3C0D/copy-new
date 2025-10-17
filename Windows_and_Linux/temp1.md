Je vois un problème dans le `response_window.py` actuel ! La méthode `_create_loading_indicator()` est devenue trop longue et contient du code qui devrait être dans `init_ui()`. 

Regarde la ligne 153 : `_create_loading_indicator()` contient tout le code de création du chat_area et de l'input_field, ce qui n'a rien à faire là-dedans.

Voici ce qui doit être corrigé :

## Problèmes identifiés :

1. **`_create_loading_indicator()`** (ligne 139-192) :
   - ❌ Contient la création du `chat_area` 
   - ❌ Contient la création de l'`input_field` et du send button
   - ❌ Elle fait ~50 lignes au lieu de ~25

2. **`init_ui()`** est incomplet :
   - ❌ N'appelle jamais `_create_loading_indicator()`
   - ❌ Ne crée jamais le chat_area ni l'input_field

## Solution :

Le code de l'artifact était correct. Il faut **remplacer tout le `response_window.py`** par la version de l'artifact `response_window_refactored`.

La version actuelle est un mélange entre l'ancien et le nouveau code, ce qui explique pourquoi `_create_loading_indicator()` contient trop de choses.

**Veux-tu que je te montre exactement ce qui doit être dans `init_ui()` et `_create_loading_indicator()` pour que ça corresponde à la structure propre ?**

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
from .image_preview_widget import ImagePreviewWidget
from .markdown_text_browser import MarkdownTextBrowser
from .message_container import MessageContainer
from .thinking_animation import ThinkingAnimation
from .window_sizing_manager import WindowSizingManager

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
        self.input_field: QLineEdit | None = None
        self.loading_label: QLabel | None = None
        self.loading_container: QWidget | None = None
        self.chat_area: ChatContentScrollArea | None = None
        self.chat_history: list = []
        self.current_text_display: MarkdownTextBrowser | None = None
        self.image_preview: ImagePreviewWidget | None = None

        # Initialize managers
        self.thinking_animation = ThinkingAnimation()
        self.sizing_manager = WindowSizingManager()

        self.init_ui()
        self._logger.debug("Connecting response signals")
        self.followup_response_signal.connect(self.handle_followup_response)
        self._logger.debug("Response signals connected")

        # Set initial size for "Thinking..." state
        self.resize(500, 250)

    def init_ui(self) -> None:
        self.setMinimumSize(600, 400)

        # Main layout setup
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(20, 20, 20, 20)
        self.content_layout.setSpacing(10)

        # Top bar with zoom controls
        self._create_top_bar()

        # Add image preview if we have an image
        if self.image:
            self.image_preview = ImagePreviewWidget(self.app, self.image, self.background)
            self.content_layout.addWidget(self.image_preview)

        # Copy controls
        self._create_copy_bar()

        # Loading indicator
        self._create_loading_indicator()

        # Enhanced chat area
        self.chat_area = ChatContentScrollArea(self.app)
        if self.content_layout:
            self.content_layout.addWidget(self.chat_area)

        # Input area
        self._create_input_bar()

        # Start thinking animation after all widgets are created
        self.thinking_animation.start(initial=True)

    def _create_top_bar(self) -> None:
        """Create the top bar with title and zoom controls"""
        top_bar = QHBoxLayout()

        title_label = QLabel(self.option)
        title_label.setStyleSheet(self.app.styles["response_window_title"])
        top_bar.addWidget(title_label)

        # Add image indicator in title bar if we have an image
        if self.image:
            image_indicator = QLabel("📷")
            image_indicator.setStyleSheet(self.app.styles["response_window_image_indicator"])
            image_indicator.setToolTip(_("Image analysis mode"))
            top_bar.addWidget(image_indicator)

        top_bar.addStretch()

        # Zoom label
        zoom_label = QLabel(_("Zoom:"))
        zoom_label.setStyleSheet(self.app.styles["response_window_zoom_label"])
        top_bar.addWidget(zoom_label)

        # Zoom controls
        zoom_controls = [
            ("plus", _("Zoom In"), lambda: self.zoom_all_messages("in")),
            ("minus", _("Zoom Out"), lambda: self.zoom_all_messages("out")),
            ("reset", _("Reset Zoom"), lambda: self.zoom_all_messages("reset")),
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

        if self.content_layout:
            self.content_layout.addLayout(top_bar)

    def _create_copy_bar(self) -> None:
        """Create the copy controls bar"""
        copy_bar = QHBoxLayout()
        copy_hint = QLabel(_("Hover over assistant responses for individual copy buttons"))
        copy_hint.setStyleSheet(self.app.styles["response_window_copy_hint"])
        copy_bar.addWidget(copy_hint)
        copy_bar.addStretch()
        if self.content_layout:
            self.content_layout.addLayout(copy_bar)

    def _create_loading_indicator(self) -> None:
        """Create the loading indicator"""
        self.loading_container = QWidget()
        loading_layout = QHBoxLayout(self.loading_container)
        loading_layout.setContentsMargins(0, 0, 0, 0)

        base_text = _("Analyzing image") if self.image else _("Thinking")
        self.loading_label = QLabel(base_text)
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

        if self.content_layout:
            self.content_layout.addWidget(self.loading_container)

    def _create_input_bar(self) -> None:
        """Create the input bar with text field and send button"""
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

        if self.content_layout:
            self.content_layout.addLayout(bottom_bar)

        # Connect animation to all widgets after creation
        self.thinking_animation.set_widgets(
            loading_label=self.loading_label,
            input_field=self.input_field,
            is_image_mode=bool(self.image),
        )

    def set_input_focus(self) -> None:
        """Force focus on input field when window opens"""
        if self.input_field:
            self.input_field.setFocus(Qt.FocusReason.OtherFocusReason)

    def start_thinking_animation(self, initial: bool = False) -> None:
        """Start the thinking animation"""
        self.thinking_animation.start(initial=initial)
        if initial and self.loading_container:
            self.loading_container.setVisible(True)
        elif self.loading_container:
            self.loading_container.setVisible(False)

    def stop_thinking_animation(self) -> None:
        """Stop the thinking animation"""
        self.thinking_animation.stop()
        if self.loading_container:
            self.loading_container.hide()

        # Force layout update
        if self.layout():
            self.layout().invalidate()
            self.layout().activate()

        # Force focus on input field
        QtCore.QTimer.singleShot(50, self.set_input_focus)

    def zoom_all_messages(self, action: str = "in") -> None:
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
        if not self.chat_area or not self.input_field:
            return

        input_height = self.input_field.height()
        self.sizing_manager.calculate_and_apply_size(self, self.chat_area, input_height)

    @Slot(str)
    def set_text(self, text: str) -> None:
        """Set initial response text"""
        if not text.strip() or not self.chat_area:
            return

        # Initialize chat history
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
        QtCore.QTimer.singleShot(150, self.set_input_focus)

    @Slot(str)
    def handle_followup_response(self, response_text: str) -> None:
        """Handle the follow-up response from the AI"""
        if response_text and self.chat_area:
            if self.loading_label:
                self.loading_label.setVisible(False)
            text_display = self.chat_area.add_message(response_text)

            # Maintain consistent zoom level
            if self.current_text_display and text_display:
                text_display.zoom_factor = self.current_text_display.zoom_factor
                text_display._apply_zoom()

            if len(self.chat_history) > 0 and self.chat_history[-1]["role"] != "assistant":
                self.chat_history.append({"role": "assistant", "content": response_text})

        self.stop_thinking_animation()
        if self.input_field:
            self.input_field.setEnabled(True)

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

        # Add user message
        text_display = self.chat_area.add_message(message, is_user=True)
        if self.current_text_display and text_display:
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
        """Refresh all text elements to reflect the current language"""
        try:
            # Update window title
            self.setWindowTitle(_("Response"))

            # Update title label in top bar
            if self.content_layout:
                top_bar_item = self.content_layout.itemAt(0)
                if top_bar_item and top_bar_item.layout():
                    top_bar_layout = top_bar_item.layout()
                    title_widget = top_bar_layout.itemAt(0).widget()
                    if isinstance(title_widget, QLabel):
                        title_widget.setText(self.option)

                    # Update zoom label and tooltips
                    for i in range(top_bar_layout.count()):
                        item = top_bar_layout.itemAt(i)
                        if item and item.widget():
                            widget = item.widget()
                            if isinstance(widget, QLabel) and "Zoom" in widget.text():
                                widget.setText(_("Zoom:"))
                            elif isinstance(widget, QPushButton):
                                tooltip = widget.toolTip()
                                if "Zoom In" in tooltip:
                                    widget.setToolTip(_("Zoom In"))
                                elif "Zoom Out" in tooltip:
                                    widget.setToolTip(_("Zoom Out"))
                                elif "Reset" in tooltip:
                                    widget.setToolTip(_("Reset Zoom"))

            # Update copy hint
            for child in self.findChildren(QLabel):
                if "Hover over" in child.text():
                    child.setText(_("Hover over assistant responses for individual copy buttons"))
                    break

            # Update loading label if visible
            if self.loading_label and self.loading_label.isVisible():
                current_text = self.loading_label.text()
                if "Analyzing" in current_text:
                    dots = current_text.replace("Analyzing image", "")
                    self.loading_label.setText(_("Analyzing image") + dots)
                elif "Thinking" in current_text:
                    dots = current_text.replace("Thinking", "")
                    self.loading_label.setText(_("Thinking") + dots)

            # Update input field placeholder
            if self.input_field:
                current_placeholder = self.input_field.placeholderText()
                if "Thinking" not in current_placeholder:
                    placeholder_text = (
                        _("Ask a follow-up question about this image") + "..."
                        if self.image
                        else _("Ask a follow-up question") + "..."
                    )
                    self.input_field.setPlaceholderText(placeholder_text)

            # Update image preview if present
            if self.image_preview:
                self.image_preview.refresh_language()

            # Update all child widgets with refresh_language
            for child in self.findChildren(QWidget):
                if hasattr(child, "refresh_language") and child != self:
                    try:
                        child.refresh_language()  # type: ignore
                    except RuntimeError:
                        pass

        except RuntimeError:
            pass

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event"""
        # Cancel any ongoing AI request
        if self.app.ai_processor.current_provider:
            self.app.ai_processor.current_provider.cancel()

        # Save zoom factor
        if self.current_text_display:
            self.app.settings_manager.response_window_zoom = self.current_text_display.zoom_factor

        self.chat_history = []

        if self.app.current_response_window is not None:
            self.app.current_response_window = None

        super().closeEvent(event)