"""
Page revue et commentée
Vérifier la section scroll.
"""

import webbrowser

from PySide6 import QtCore, QtGui, QtWidgets
from ui.ui_utils import ThemedWidget, colorMode

_ = lambda x: x


class AboutWindow(ThemedWidget):
    """
    The about window for the application.
    """

    def __init__(self):
        super().__init__()
        self.min_width = 600
        self.min_height = 650
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface for the about window."""
        self._setup_window()
        self._create_layout()
        self._load_content()

    def _setup_window(self):
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

    def _center_on_screen(self):
        """Center the window on the primary screen."""
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        window_rect = self.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        self.move(x, y)

    def _set_transparent_icon(self):
        """Set a transparent window icon."""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        self.setWindowIcon(QtGui.QIcon(pixmap))

    def _create_layout(self):
        """Create the main layout structure."""
        self.content_layout = QtWidgets.QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_content(self):
        """Load and display the about content."""
        # Title
        title_label = self._create_title_label()
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Scrollable main content
        about_content = self._get_about_content()
        content_widget = self._create_scrollable_content(about_content)
        self.content_layout.addWidget(content_widget)

        # Update button
        update_button = self._create_update_button()
        self.content_layout.addWidget(update_button)

    def _create_title_label(self):
        """Create the main title label."""
        title_label = QtWidgets.QLabel(_("About Writing Tools"))
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self):
        """Get the title styling based on current theme."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _get_about_content(self):
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

    def _get_contributors_html(self):
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
            ("Alok Saboo", "https://github.com/arsaboo", _("Helped improve the reliability of text selection.")),
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
            ("Vadim Karpenko", "https://github.com/Vadim-Karpenko", _("Helped add the start-on-boot setting.")),
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

    def _create_scrollable_content(self, content):
        """Create a scrollable widget for the main content."""
        about_label = QtWidgets.QLabel(content)
        about_label.setStyleSheet(self._get_content_style())
        about_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignTop)
        about_label.setWordWrap(True)
        about_label.setOpenExternalLinks(True)

        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidget(about_label)
        scroll_area.setWidgetResizable(True)
        # Needed ?
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)

        scroll_area.setStyleSheet("QScrollArea { background: transparent; border: none; }")

        return scroll_area

    def _create_update_button(self):
        """Create the update check button with modern styling."""
        update_button = QtWidgets.QPushButton(_("Check for updates"))
        update_button.setStyleSheet(self._get_button_style())
        update_button.clicked.connect(self.check_for_updates)
        update_button.setCursor(QtCore.Qt.CursorShape.PointingHandCursor)
        return update_button

    def _get_content_style(self):
        """Get the content styling based on current theme."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
        return f"font-size: 14px; color: {color}; padding: 10px;"

    def _get_button_style(self):
        """Get the button styling with theme awareness."""
        base_style = """
                QPushButton {
                background-color: #4CAF50; color: white; padding: 12px 24px;
                font-size: 16px; font-weight: bold; border: none; border-radius: 8px;
                }
            QPushButton:hover { background-color: #45a049; }
            QPushButton:pressed { background-color: #3d8b40; }
            """

        # Add theme-specific enhancements
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        if current_mode == 'light':
            base_style += """
                QPushButton { box-shadow: 0 2px 4px rgba(0,0,0,0.1); }
                QPushButton:hover { box-shadow: 0 4px 8px rgba(0,0,0,0.15); }
                QPushButton:pressed { box-shadow: 0 1px 2px rgba(0,0,0,0.1); }
            """

        return base_style

    def check_for_updates(self):
        """Open the GitHub releases page to check for updates."""
        webbrowser.open("https://github.com/theJayTea/WritingTools/releases")

    def resizeEvent(self, event):
        """Handle window resize events to maintain minimum size."""
        super().resizeEvent(event)
        # Enforce minimum dimensions
        if self.width() < self.min_width or self.height() < self.min_height:
            self.resize(max(self.width(), self.min_width), max(self.height(), self.min_height))

    def original_app(self):
        """Open the original app GitHub page."""
        webbrowser.open("https://github.com/TheJayTea/WritingTools")
