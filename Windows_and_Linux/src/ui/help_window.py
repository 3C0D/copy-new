import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QScrollArea,
    QVBoxLayout,
)

from .ui_utils import ThemedWidget

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp


def _(x):
    """Translation function placeholder."""
    return x


class HelpWindow(ThemedWidget):
    """
    The help window for the application.
    """

    content_layout: QVBoxLayout

    def __init__(self, app: "WritingToolsApp | None" = None) -> None:
        if app is None:
            raise ValueError("HelpWindow requires a WritingToolsApp instance")
        super().__init__(app)
        self._logger = logging.getLogger(__name__)
        self.min_width = 600
        self.min_height = 650  # Same as AboutWindow
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface for the help window."""
        self._setup_window()
        self._create_layout()
        self._load_content()

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.clean_TitleBar()
        self._calculate_window_size()
        self.center_on_screen()

    def _create_layout(self) -> None:
        """Create the main layout structure."""
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_content(self) -> None:
        """Load and display the help content."""
        # Title
        self._title_label: QLabel = self._create_title_label()
        self.content_layout.addWidget(
            self._title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # Scrollable main content
        help_content: str = self._get_help_content()
        content_widget: QScrollArea = self._create_scrollable_content(help_content)
        self.content_layout.addWidget(content_widget)

    def _create_title_label(self) -> QLabel:
        """Create the main title label."""
        title_label = QLabel(_("Writing Tools Help"))
        title_label.setStyleSheet(self.app.styles["label_title"])
        return title_label

    def _get_help_content(self) -> str:
        """Get the formatted help content HTML."""
        current_mode = self.app.settings_manager.color_mode
        text_color = "#f0f0f0" if current_mode == "dark" else "#333333"
        bg_color = "transparent"
        highlight_bg = (
            "rgba(76, 175, 80, 0.2)" if current_mode == "dark" else "rgba(76, 175, 80, 0.1)"
        )
        border_color = "#555555" if current_mode == "dark" else "#dddddd"

        return f"""
        <div style='text-align: left; line-height: 1.6; color: {text_color}; background-color: {bg_color};'>
            <h2 style='color: {text_color};'>🎯 {_("How to Use Writing Tools")}</h2>

            <h3 style='color: {text_color};'> 🖼️  {_("Image Processing Priority")}</h3>
            <p><strong>{_("Clipboard Images:")}</strong> {_("Images in clipboard take priority over text. Press your configured shortcut for image analysis (OCR, translation, description, etc.).")}</p>
            <p><strong>{_("Screenshot Workflow:")}</strong> {_("Take a screenshot (Ctrl+Shift+S or Print Screen) → Image copied to clipboard → Ctrl+Space → Enter prompt → Chat window opens with AI response → Continue discussion about the image.")}</p>
            <p><strong>{_("Clipboard Management:")}</strong> <b>{_("Validated prompts clear clipboard to prevent reuse. Cancelled prompts keep the image.")}</b></p>

            <h3 style='color: {text_color};'>📝 {_("Text Selection & Interaction Modes")}</h3>
            <p><strong>{_("When no image in clipboard:")}</strong> {_("With no image in clipboard, text selection works with two interaction paths:")}</p>

            <div style='margin-left: 20px; margin-bottom: 15px;'>
                <h4 style='color: {text_color};'>🎯 {_("Manual Prompt Input")}</h4>
                <p>{_("Type your custom prompt in the text area → Choose behavior:")}</p>
                <ul style='margin-left: 20px;'>
                    <li><strong>{_("Chat Mode:")}</strong> {_("Click Force Chat or use Ctrl+Enter to open chat window")}</li>
                    <li><strong>{_("Replace Text:")}</strong> {_("Press Enter to replace selected text (editable text only)")}</li>
                </ul>
            </div>

            <div style='margin-left: 20px; margin-bottom: 15px;'>
                <h4 style='color: {text_color};'>⚡ {_("Predefined Action Buttons")}</h4>
                <p>{_("Click action buttons with predefined prompts → Behavior indicated by icons:")}</p>
                <ul style='margin-left: 20px;'>
                    <li><strong>💬 C</strong> {_("(Chat icon) → Opens chat window regardless of text type")}</li>
                    <li><strong>🔄 R</strong> {_("(Replace icon) → Replaces editable text, opens modal for non-editable text")}</li>
                </ul>
                <p><em>{_("Icons show default behavior when Force Chat is not active")}</em></p>
            </div>

            <div style='margin-left: 20px;'>
                <h4 style='color: {text_color};'>📋 {_("Text Type Behavior")}</h4>
                <ul style='margin-left: 20px;'>
                    <li><strong>{_("Editable Text:")}</strong> {_("Can be replaced or opened in chat mode")}</li>
                    <li><strong>{_("Non-Editable Text:")}</strong> {_("Always opens in modal window without modifying original")}</li>
                    <li><strong>{_("No Selection:")}</strong> {_("Opens prompt that directly enters chat mode")}</li>
                </ul>
            </div>

            <h3 style='color: {text_color};'>💬 {_("Force Chat Mode")}</h3>
            <p><strong>{_("Force Chat Button:")}</strong> {_("Overrides default behavior to always open chat mode")}</p>
            <p><strong>{_("Lockable Mode:")}</strong> {_("Keep Force Chat permanently active for sensitive editable text")}</p>

            <h3 style='color: {text_color};'>⚙️ {_("Settings & Configuration")}</h3>
            <p><strong>{_("Interface Settings:")}</strong> {_("Customize appearance, themes, and window behavior")}</p>
            <p><strong>{_("Global Shortcut:")}</strong> {_("Set your preferred keyboard shortcut (default: ctrl space). Use spaces as separators, e.g., ctrl shift a, ctrl shift +")}</p>
            <p><strong>{_("LLM Selection:")}</strong> {_("Choose from available AI models. Models marked with ⭐ support image processing across all providers")}</p>

            <h4 style='color: {text_color};'>🔧 {_("Ollama Integration")}</h4>
            <p><strong>{_("Installation:")}</strong> {_("Auto-install Ollama and open chat interface immediately")}</p>
            <p><strong>{_("Model Testing:")}</strong> {_("Click models in chat interface to test and install directly")}</p>
            <p><strong>{_("Model Management:")}</strong> {_("Installed models appear immediately in settings dropdown")}</p>

            <h3 style='color: {text_color};'>🎛️  {_("Systray/Settings")}</h3>
            <p><strong>{_("System Tray Menu:")}</strong> {_("Right-click icon for quick access to settings, help, and mode toggles")}</p>

            <div style='margin-top: 30px; padding: 15px; background: {highlight_bg}; border: 1px solid {border_color}; border-radius: 8px;'>
                <strong style='color: {text_color};'>💡 {_("Quick Reference:")}</strong><br>
                <div style='display: flex; justify-content: space-between; margin-top: 10px; color: {text_color};'>
                    <div>
                        <strong>{_("Flow:")}</strong><br>
                         🖼️  Image → ctrl space → Prompt → Chat<br>
                        📝 Text → ctrl space → Manual/Action → Chat/Replace<br>
                        ❌ Cancel → Clipboard preserved<br>
                        ✅ Validate → Clipboard cleared
                    </div>
                    <div>
                        <strong>{_("Icons:")}</strong><br>
                        💬 C = Chat mode<br>
                        🔄 R = Replace mode<br>
                        ⭐ = Image support
                    </div>
                </div>
            </div>
        </div>
        """

    def _create_scrollable_content(self, content: str) -> QScrollArea:
        """Create a scrollable area for the content."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(self.app.styles["transparent_background"]("QScrollArea"))

        self.content_widget = QLabel(content)
        self.content_widget.setWordWrap(True)
        self.content_widget.setOpenExternalLinks(True)
        self.content_widget.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        self.content_widget.setStyleSheet(self.app.styles["help_content_label"])

        scroll_area.setWidget(self.content_widget)
        return scroll_area

    def refresh_language(self) -> None:
        """Refresh all text elements to reflect the current language."""
        self.content_widget.setText(self._get_help_content())
        if hasattr(self, "_title_label"):
            self._title_label.setText(_("Help"))

    def refresh_theme(self) -> None:
        """Refresh all theme-dependent styles in the help window."""
        super().refresh_theme()

        background_theme = self.get_current_background_theme()
        color_mode = self.app.settings_manager.color_mode

        theme_icon = "🌙" if color_mode == "dark" else "☀️ "
        bg_icon = "⚽" if background_theme == "plain" else "🌈"

        self._logger.debug(
            f"🎯 HelpWindow theme update: {theme_icon} Color={color_mode} {bg_icon} BG={background_theme}"
        )

        # Update HTML content with new colors
        help_content = self._get_help_content()
        self.content_widget.setText(help_content)

        # Update title style
        if hasattr(self, "_title_label"):
            self._title_label.setStyleSheet(self.app.styles["label_title"])

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handle window close event.
        """
        super().closeEvent(event)
        self.app.systray_manager.help_window = None
        self._logger.debug("HelpWindow closeEvent finished")
