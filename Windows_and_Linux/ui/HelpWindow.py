import webbrowser

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from ui.ui_utils import ThemedWidget


def _(x):
    """Translation function placeholder."""
    return x


class HelpWindow(ThemedWidget):
    """
    The help window for the application.
    """

    min_width: int
    min_height: int
    content_layout: QVBoxLayout

    def __init__(self) -> None:
        super().__init__()
        self.min_width = 600
        self.min_height = 750
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface for the help window."""
        self._setup_window()
        self._create_layout()
        self._load_content()

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.setWindowTitle(" ")  # Hidden title for clean look
        self.setMinimumSize(self.min_width, self.min_height)

        # Center window on screen
        self._center_on_screen()

        # Configure window flags for minimal chrome
        self.setWindowFlags(
            self.windowFlags()
            & ~QtCore.Qt.WindowType.WindowMinimizeButtonHint
            & ~QtCore.Qt.WindowType.WindowSystemMenuHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowTitleHint
        )

        self._set_transparent_icon()

    def _center_on_screen(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        self.move(x, y)

    def _set_transparent_icon(self) -> None:
        """Set a transparent window icon."""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        self.setWindowIcon(QtGui.QIcon(pixmap))

    def _create_layout(self) -> None:
        """Create the main layout structure."""
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_content(self) -> None:
        """Load and display the help content."""
        # Title
        title_label: QLabel = self._create_title_label()
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Scrollable main content
        help_content: str = self._get_help_content()
        content_widget: QScrollArea = self._create_scrollable_content(help_content)
        self.content_layout.addWidget(content_widget)

    def _create_title_label(self) -> QLabel:
        """Create the main title label."""
        title_label = QLabel(_("Writing Tools Help"))
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self) -> str:
        """Get the title styling based on current theme."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        color = "#ffffff" if current_mode == "dark" else "#333333"
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _get_help_content(self) -> str:
        """Get the formatted help content HTML."""
        from ui.ui_utils import get_effective_color_mode
        
        current_mode = get_effective_color_mode()
        text_color = "#ffffff" if current_mode == "dark" else "#333333"
        bg_color = "#2b2b2b" if current_mode == "dark" else "#ffffff"
        highlight_bg = "rgba(76, 175, 80, 0.2)" if current_mode == "dark" else "rgba(76, 175, 80, 0.1)"
        border_color = "#555555" if current_mode == "dark" else "#dddddd"
        
        return f"""
        <div style='text-align: left; line-height: 1.6; color: {text_color}; background-color: {bg_color};'>
            <h2 style='color: {text_color};'>🎯 {_("How to Use Writing Tools")}</h2>
            
            <h3 style='color: {text_color};'>🖼️ {_("Image Processing Priority")}</h3>
            <p><strong>{_("Clipboard Images:")}</strong> {_("When an image is in your clipboard, it takes priority over selected text. Press Ctrl+Space to open a prompt window for image analysis (OCR, translation, description, etc.).")}</p>
            <p><strong>{_("Screenshot Workflow:")}</strong> {_("Take a screenshot (Ctrl+Shift+S or Print Screen) → Image copied to clipboard → Ctrl+Space → Enter prompt → Chat window opens with AI response → Continue discussion about the image.")}</p>
            <p><strong>{_("Clipboard Management:")}</strong> <b>{_("Once you validate the prompt and enter chat mode, the image is cleared from clipboard to prevent accidental reuse. If you cancel the prompt, the image remains in clipboard.")}</b></p>

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
            <p><strong>{_("Global Shortcut:")}</strong> {_("Set your preferred keyboard shortcut (default: Ctrl+Space)")}</p>
            <p><strong>{_("LLM Selection:")}</strong> {_("Choose from available AI models. Models marked with ⭐ support image processing across all providers")}</p>
            
            <h4 style='color: {text_color};'>🔧 {_("Ollama Integration")}</h4>
            <p><strong>{_("Installation:")}</strong> {_("Writing Tools can install Ollama automatically, opening chat interface immediately")}</p>
            <p><strong>{_("Model Testing:")}</strong> {_("Click models in chat interface to test and install directly")}</p>
            <p><strong>{_("Model Management:")}</strong> {_("Installed models appear immediately in settings dropdown")}</p>

            <h3 style='color: {text_color};'>🎛️ {_("Systray/Settings")}</h3>
            <p><strong>{_("System Tray Menu:")}</strong> {_("Right-click icon for quick access to settings, help, and mode toggles")}</p>

            <div style='margin-top: 30px; padding: 15px; background: {highlight_bg}; border: 1px solid {border_color}; border-radius: 8px;'>
                <strong style='color: {text_color};'>💡 {_("Quick Reference:")}</strong><br>
                <div style='display: flex; justify-content: space-between; margin-top: 10px; color: {text_color};'>
                    <div>
                        <strong>{_("Flow:")}</strong><br>
                        🖼️ Image → Ctrl+Space → Prompt → Chat<br>
                        📝 Text → Ctrl+Space → Manual/Action → Chat/Replace<br>
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
        scroll_area.setStyleSheet("""
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollBar:vertical {
                background: transparent;
                width: 10px;
            }
            QScrollBar::handle:vertical {
                background: rgba(0, 0, 0, 0.2);
                border-radius: 5px;
            }
        """)

        content_widget = QLabel(content)
        content_widget.setWordWrap(True)
        content_widget.setOpenExternalLinks(True)
        content_widget.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 10px;
                font-size: 14px;
            }
        """)

        scroll_area.setWidget(content_widget)
        return scroll_area
