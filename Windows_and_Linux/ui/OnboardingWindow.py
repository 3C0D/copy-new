import logging

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QHBoxLayout, QRadioButton

from ui.ui_utils import ThemedWidget, colorMode, ui_utils

_ = lambda x: x


class OnboardingWindow(ThemedWidget):
    """
    The onboarding window for first-time application setup.
    Guides users through initial configuration including shortcuts and theme selection.
    """

    # Closing signal
    close_signal = QtCore.Signal()

    def __init__(self, app):
        super().__init__()
        self.app = app
        self.shortcut = "ctrl+space"
        self.theme = "gradient"
        self.content_layout: QtWidgets.QVBoxLayout
        self.shortcut_input: QtWidgets.QLineEdit
        self.gradient_radio: QRadioButton
        self.plain_radio: QRadioButton
        self.self_close = False
        self.min_width = 600
        self.min_height = 500
        self.init_ui()

    def init_ui(self):
        """Initialize the user interface for the onboarding window."""
        logging.debug("Initializing onboarding UI")
        self._setup_window()
        self._create_layout()
        self._load_welcome_screen()

    def _setup_window(self):
        """Configure window properties and positioning."""
        self.setWindowTitle(_("Welcome to Writing Tools"))
        self.resize(600, 500)

    def _create_layout(self):
        """Create the main layout structure."""
        self.content_layout = QtWidgets.QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_welcome_screen(self):
        """Load and display the welcome screen content."""
        self.show_welcome_screen()

    def show_welcome_screen(self):
        """Display the main welcome screen with features and settings."""
        ui_utils.clear_layout(self.content_layout)

        # Title
        title_label = self._create_title_label()
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Features section
        features_widget = self._create_features_section()
        self.content_layout.addWidget(features_widget)

        # Shortcut configuration section
        shortcut_section = self._create_shortcut_section()
        self.content_layout.addLayout(shortcut_section)

        # Theme selection section
        theme_section = self._create_theme_section()
        self.content_layout.addLayout(theme_section)

        # Next button
        next_button = self._create_next_button()
        self.content_layout.addWidget(next_button)

    def _create_title_label(self):
        """Create the main title label."""
        title_label = QtWidgets.QLabel(_("Welcome to Writing Tools") + "!")
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self):
        """Get the title styling based on current theme."""
        color = '#ffffff' if colorMode == 'dark' else '#333333'
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _create_features_section(self):
        """Create the features description section."""
        features_content = self._get_features_content()

        features_label = QtWidgets.QLabel(features_content)
        features_label.setStyleSheet(self._get_content_style())
        features_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        return features_label

    def _get_features_content(self):
        """Get the formatted features content."""
        return f"""• {_('Instantly optimize your writing with AI by selecting your text and invoking Writing Tools with "ctrl+space", anywhere.')} 

• {_('Get a summary you can chat with of articles, YouTube videos, or documents by select all text with "ctrl+a"')}
  {_('(or select the YouTube transcript from its description), invoking Writing Tools, and choosing Summary.')}

• {_('Chat with AI anytime by invoking Writing Tools without selecting any text.')}

• {_('Supports an extensive range of AI models:')}
    - {_('Gemini 2.0')}
    - {_('ANY OpenAI Compatible API — including local LLMs!')}
        """

    def _create_shortcut_section(self):
        """Create the shortcut configuration section."""
        shortcut_layout = QtWidgets.QVBoxLayout()

        shortcut_label = QtWidgets.QLabel(_('Customize your shortcut key (default: "ctrl+space"):'))
        shortcut_label.setStyleSheet(self._get_content_style())
        shortcut_layout.addWidget(shortcut_label)

        self.shortcut_input = QtWidgets.QLineEdit(self.shortcut)
        self.shortcut_input.setStyleSheet(self._get_input_style())
        shortcut_layout.addWidget(self.shortcut_input)

        return shortcut_layout

    def _create_theme_section(self):
        """Create the theme selection section."""
        theme_layout = QtWidgets.QVBoxLayout()

        theme_label = QtWidgets.QLabel(_("Choose your theme:"))
        theme_label.setStyleSheet(self._get_content_style())
        theme_layout.addWidget(theme_label)

        # Radio buttons container
        radio_layout = QHBoxLayout()

        self.gradient_radio = QRadioButton(_("Gradient"))
        self.plain_radio = QRadioButton(_("Plain"))

        # Style radio buttons
        radio_style = self._get_radio_style()
        self.gradient_radio.setStyleSheet(radio_style)
        self.plain_radio.setStyleSheet(radio_style)

        # Set default selection
        self.gradient_radio.setChecked(self.theme == "gradient")
        self.plain_radio.setChecked(self.theme == "plain")

        radio_layout.addWidget(self.gradient_radio)
        radio_layout.addWidget(self.plain_radio)

        theme_layout.addLayout(radio_layout)
        return theme_layout

    def _create_next_button(self):
        """Create the next button with original styling."""
        next_button = QtWidgets.QPushButton(_("Next"))
        next_button.setStyleSheet(self._get_button_style())
        next_button.clicked.connect(self._on_next_clicked)
        return next_button

    def _get_content_style(self):
        """Get the content styling based on current theme."""
        color = '#ffffff' if colorMode == 'dark' else '#333333'
        return f"font-size: 16px; color: {color};"

    def _get_input_style(self):
        """Get the input field styling based on current theme."""
        return f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if colorMode == 'dark' else 'white'};
            color: {'#ffffff' if colorMode == 'dark' else '#000000'};
            border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
        """

    def _get_radio_style(self):
        """Get the radio button styling based on current theme."""
        color = '#ffffff' if colorMode == 'dark' else '#333333'
        return f"color: {color};"

    def _get_button_style(self):
        """Get the button styling with theme awareness."""
        return """
            QPushButton {
                background-color: #4CAF50;
                color: white;
                padding: 10px;
                font-size: 16px;
                border: none;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
        """

    def _on_next_clicked(self):
        """Handle the next button click event."""
        # Validate and save shortcut
        self.shortcut = self.shortcut_input.text().strip()
        if not self.shortcut:
            self.shortcut = "ctrl+space"  # Fallback to default

        # Determine selected theme
        self.theme = "gradient" if self.gradient_radio.isChecked() else "plain"

        logging.debug(f"User selected shortcut: {self.shortcut}, theme: {self.theme}")

        # Save settings using the application's settings manager
        self._save_settings()

        # Proceed to next step
        self._show_api_key_input()

    def _save_settings(self):
        """Save the user's selected settings."""
        try:
            self.app.settings_manager.update_system_setting("hotkey", self.shortcut)
            self.app.settings_manager.update_system_setting("theme", self.theme)
            logging.debug("Settings saved successfully")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def _show_api_key_input(self):
        """Show the API key configuration screen."""
        self.app.show_settings(providers_only=True)
        self.self_close = True
        self.close()

    def closeEvent(self, event):
        """Handle window close events."""
        # Emit the close signal only if not self-closing
        if not self.self_close:
            self.close_signal.emit()
        super().closeEvent(event)
