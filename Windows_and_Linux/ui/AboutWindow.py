import webbrowser

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QFrame,
    QLabel,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
)

from ui.ui_utils import ThemedWidget, get_effective_color_mode


def _(x):
    """Translation function placeholder."""
    return x


class AboutWindow(ThemedWidget):
    """
    The about window for the application.
    """

    min_width: int
    min_height: int
    content_layout: QVBoxLayout

    def __init__(self, app=None) -> None:
        super().__init__(app)
        self.min_width = 600
        self.min_height = 650
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface for the about window."""
        self._setup_window()
        self._create_layout()
        self._load_content()

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.clean_TitleBar()
        self.setMinimumSize(self.min_width, self.min_height)
        # Center window on screen
        self.center_on_screen()
        self.set_transparent_icon()

    def _create_layout(self) -> None:
        """Create the main layout structure."""
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_content(self) -> None:
        """Load and display the about content."""
        # Title
        self._title_label: QLabel = self._create_title_label()
        self.content_layout.addWidget(
            self._title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter
        )

        # Scrollable main content
        about_content: str = self._get_about_content()
        content_widget: QScrollArea = self._create_scrollable_content(about_content)
        self.content_layout.addWidget(content_widget)

        # Update button
        self._update_button: QPushButton = self._create_update_button()
        self.content_layout.addWidget(self._update_button)

    def _create_title_label(self) -> QLabel:
        """Create the main title label."""
        title_label = QLabel(_("About Writing Tools"))
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self) -> str:
        """Get the title styling based on current theme."""
        current_mode = get_effective_color_mode()
        color = "#ffffff" if current_mode == "dark" else "#333333"
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _get_about_content(self) -> str:
        """Get the formatted about content HTML."""
        return f"""
        <div style='text-align: center; line-height: 1.6;'>
            <p style='margin-bottom: 20px;'>
                {_("Writing Tools is a free & lightweight tool that helps you improve your writing with AI, similar to Apple's new Apple Intelligence feature. It works with an extensive range of AI LLMs, both online and locally run.")}
            </p>

            <p style='margin-bottom: 20px;'>
                <strong>{_("Created with care by Jesai, a high school student.")}</strong><br><br>
                {_("Feel free to check out my other AI app")},
                <a href="https://play.google.com/store/apps/details?id=com.jesai.blissai"><strong>Bliss AI</strong></a>.
                {_("It's a novel AI tutor that's free on the Google Play Store :)")}<br><br>
                <strong>{_("Contact me")}:</strong> jesaitarun@gmail.com
            </p>

            <div style='margin: 30px 0;'>
                <h3 style='margin-bottom: 15px;'>⭐ {_("Amazing Contributors")}</h3>
                {self._get_contributors_html()}
            </div>

            <div style='margin-top: 30px; padding: 15px; background: rgba(76, 175, 80, 0.1); border-radius: 8px;'>
                <strong>Version:</strong> 7.0 (Codename: Impeccably Improved)
            </div>

            <p style='margin-top: 20px;'>
                If you have a Mac, check out the
                <a href="https://github.com/theJayTea/WritingTools#-macos">Writing Tools macOS port</a>
                by <a href="https://github.com/Aryamirsepasi">Arya Mirsepasi</a>!
            </p>
        </div>
        """

    def _get_contributors_html(self) -> str:
        """Get the formatted contributors section."""
        contributors = [
            (
                "momokrono",
                "https://github.com/momokrono",
                _(
                    "Added Linux support, switched to the pynput API to improve Windows stability. Added Ollama API support, core logic for customizable buttons, and localization. Fixed misc. bugs and added graceful termination support by handling SIGINT signal."
                ),
            ),
            (
                "Cameron Redmore",
                "https://github.com/CameronRedmore",
                _(
                    "Extensively refactored Writing Tools and added OpenAI Compatible API support, streamed responses, and the text generation mode when no text is selected."
                ),
            ),
            (
                "Soszust40",
                "https://github.com/Soszust40",
                _("Helped add dark mode, the plain theme, tray menu fixes, and UI improvements."),
            ),
            (
                "Alok Saboo",
                "https://github.com/arsaboo",
                _("Helped improve the reliability of text selection."),
            ),
            (
                "raghavdhingra24",
                "https://github.com/raghavdhingra24",
                _("Made the rounded corners anti-aliased & prettier."),
            ),
            (
                "ErrorCatDev",
                "https://github.com/ErrorCatDev",
                _(
                    "Significantly improved the About window, making it scrollable and cleaning things up. Also improved our .gitignore & requirements.txt."
                ),
            ),
            (
                "Vadim Karpenko",
                "https://github.com/Vadim-Karpenko",
                _("Helped add the start-on-boot setting."),
            ),
        ]

        html_parts = []
        for i, (name, url, contribution) in enumerate(contributors, 1):
            html_parts.append(
                f"""
            <div style='text-align: left; margin: 15px 0; padding: 10px; background: rgba(255,255,255,0.05); border-radius: 6px;'>
                <strong>{i}. <a href="{url}">{name}</a>:</strong><br>
                <span style='margin-left: 15px;'>{contribution}</span>
            </div>
            """
            )

        return "".join(html_parts)

    def _create_scrollable_content(self, content: str) -> QScrollArea:
        """Create a scrollable widget for the main content."""
        about_label = QLabel(content)
        about_label.setStyleSheet(self._get_content_style())
        about_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        about_label.setWordWrap(True)
        about_label.setOpenExternalLinks(True)

        scroll_area = QScrollArea()
        scroll_area.setWidget(about_label)
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        return scroll_area

    def _create_update_button(self) -> QPushButton:
        """Create the update check button with modern styling."""
        update_button = QPushButton(_("Check for updates"))
        update_button.setStyleSheet(self._get_button_style())
        update_button.clicked.connect(self.check_for_updates)
        update_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        return update_button

    def _get_content_style(self) -> str:
        """Get the content styling with fixed dark colors for better readability."""
        color = "#e8dcc0"
        background = "rgba(45, 45, 45, 0.95)"
        return f"font-size: 14px; color: {color}; background-color: {background}; padding: 10px; border-radius: 8px;"

    def _get_button_style(self) -> str:
        """Get the button styling with theme awareness (Qt stylesheets only)."""

        mode = get_effective_color_mode()
        if mode == "dark":
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: #ffffff;
                    padding: 10px 20px;
                    font-size: 16px;
                    font-weight: bold;
                    border: 1px solid #2e7d32; /* darker green border for contrast */
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #43a047; }
                QPushButton:pressed { background-color: #388e3c; }
                QPushButton:disabled {
                    background-color: #2e7d32;
                    color: #bdbdbd;
                    border-color: #255d27;
                }
            """
        else:
            return """
                QPushButton {
                    background-color: #4CAF50;
                    color: #ffffff;
                    padding: 10px 20px;
                    font-size: 16px;
                    font-weight: bold;
                    border: 1px solid #3d8b40;
                    border-radius: 8px;
                }
                QPushButton:hover { background-color: #45a049; }
                QPushButton:pressed { background-color: #3d8b40; }
                QPushButton:disabled {
                    background-color: #a5d6a7;
                    color: #ffffff;
                    border-color: #8bc34a;
                }
            """

    def check_for_updates(self) -> None:
        """Open the GitHub releases page to check for updates."""
        webbrowser.open("https://github.com/theJayTea/WritingTools/releases")

    def refresh_theme(self) -> None:
        """Refresh all theme-dependent styles in the about window."""
        super().refresh_theme()

        current_bg_theme = self._get_current_background_theme()
        current_color_mode = get_effective_color_mode()

        theme_icon = "🌙" if current_color_mode == "dark" else "☀️\u00a0"
        bg_icon = "⚽" if current_bg_theme == "plain" else "🌈"

        print(
            f"🎯 AboutWindow theme update: {theme_icon} Color={current_color_mode} {bg_icon} BG={current_bg_theme}"
        )

        # Update title and button styles
        if hasattr(self, "_title_label"):
            self._title_label.setStyleSheet(self._get_title_style())
        if hasattr(self, "_update_button"):
            self._update_button.setStyleSheet(self._get_button_style())

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle window resize events to maintain minimum size."""
        super().resizeEvent(event)
        # Enforce minimum dimensions
        if self.width() < self.min_width or self.height() < self.min_height:
            self.resize(max(self.width(), self.min_width), max(self.height(), self.min_height))

    def original_app(self) -> None:
        """Open the original app GitHub page."""
        webbrowser.open("https://github.com/TheJayTea/WritingTools")
