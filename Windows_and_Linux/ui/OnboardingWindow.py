import logging

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QHBoxLayout, QRadioButton

from ui.ui_utils import ThemedWidget, colorMode, ui_utils

from Windows_and_Linux.WritingToolApp import WritingToolApp

_ = lambda x: x


class OnboardingWindow(ThemedWidget):
    """
    The onboarding window for first-time application setup.
    Guides users through initial configuration including shortcuts and theme selection.
    """

    # Signal emitted when window is closed (not when proceeding to next step)
    close_signal = QtCore.Signal()

    def __init__(self, app: WritingToolApp):
        super().__init__()
        self.app = app

        # Default configuration values
        self.shortcut = "ctrl+space"
        self.theme = "gradient"

        # UI components that will be referenced later
        self.content_layout: QtWidgets.QVBoxLayout
        self.shortcut_input: QtWidgets.QLineEdit  # Text field for shortcut input
        self.gradient_radio: QRadioButton  # Radio button for gradient theme
        self.plain_radio: QRadioButton  # Radio button for plain theme

        # Control flags
        self.self_close = False  # Flag to distinguish self-closing from user closing

        # Window dimensions
        self.min_width = 600
        self.min_height = 500

        self.init_ui()

    def init_ui(self):
        """Initialize the user interface for the onboarding window."""
        logging.debug("Initializing onboarding UI")
        self._setup_window()
        self._create_layout()
        self._show_welcome_screen()

    def _setup_window(self):
        """Configure window properties and positioning."""
        self.setWindowTitle(_("Welcome to Writing Tools"))
        self.resize(600, 500)

    def _create_layout(self):
        """Create the main layout structure with margins and spacing."""
        self.content_layout = QtWidgets.QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _show_welcome_screen(self):
        """Display the main welcome screen with features and settings configuration."""
        ui_utils.clear_layout(self.content_layout)

        # Main title at the top
        title_label = self._create_title_label()
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Features description section
        features_widget = self._create_features_section()
        self.content_layout.addWidget(features_widget)

        # Keyboard shortcut configuration section (auto-saves on change)
        shortcut_section = self._create_shortcut_section()
        self.content_layout.addLayout(shortcut_section)

        # Theme selection section (auto-saves and applies on change)
        theme_section = self._create_theme_section()
        self.content_layout.addLayout(theme_section)

        # Navigation button to proceed to next step (API configuration)
        next_button = self._create_next_button()
        self.content_layout.addWidget(next_button)

    def _create_title_label(self):
        """Create the main title label with theme-appropriate styling."""
        title_label = QtWidgets.QLabel(_("Welcome to Writing Tools") + "!")
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self):
        """Get the title styling based on current theme (dark/light mode)."""
        color = '#ffffff' if colorMode == 'dark' else '#333333'
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _create_features_section(self):
        """Create the features description section showing app capabilities."""
        features_content = self._get_features_content()

        features_label = QtWidgets.QLabel(features_content)
        features_label.setStyleSheet(self._get_content_style())
        features_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        return features_label

    def _get_features_content(self):
        """Get the formatted features content listing app capabilities."""
        return f"""• {_('Instantly optimize your writing with AI by selecting your text and invoking Writing Tools with "ctrl+space", anywhere.')} 

• {_('Get a summary you can chat with of articles, YouTube videos, or documents by select all text with "ctrl+a"')}
  {_('(or select the YouTube transcript from its description), invoking Writing Tools, and choosing Summary.')}

• {_('Chat with AI anytime by invoking Writing Tools without selecting any text.')}

• {_('Supports an extensive range of AI models:')}
    - {_('Gemini 2.0')}
    - {_('ANY OpenAI Compatible API — including local LLMs!')}
        """

    def _create_shortcut_section(self):
        """Create the keyboard shortcut configuration section with auto-save."""
        shortcut_layout = QtWidgets.QVBoxLayout()

        # Label explaining the shortcut configuration
        shortcut_label = QtWidgets.QLabel(_('Customize your shortcut key (default: "ctrl+space"):'))
        shortcut_label.setStyleSheet(self._get_content_style())
        shortcut_layout.addWidget(shortcut_label)

        # Text input field for shortcut (auto-saves on change)
        self.shortcut_input = QtWidgets.QLineEdit(self.shortcut)
        self.shortcut_input.setStyleSheet(self._get_input_style())
        # Connect signal to auto-save when user types
        self.shortcut_input.textChanged.connect(self._on_shortcut_changed)
        shortcut_layout.addWidget(self.shortcut_input)

        return shortcut_layout

    def _create_theme_section(self):
        """Create the theme selection section with immediate preview."""
        theme_layout = QtWidgets.QVBoxLayout()

        # Label for theme selection
        theme_label = QtWidgets.QLabel(_("Choose your theme:"))
        theme_label.setStyleSheet(self._get_content_style())
        theme_layout.addWidget(theme_label)

        # Container for radio buttons (horizontal layout)
        radio_layout = QHBoxLayout()

        # Theme option radio buttons
        self.gradient_radio = QRadioButton(_("Gradient"))  # Gradient background theme
        self.plain_radio = QRadioButton(_("Plain"))  # Plain background theme

        # Apply styling to radio buttons
        radio_style = self._get_radio_style()
        self.gradient_radio.setStyleSheet(radio_style)
        self.plain_radio.setStyleSheet(radio_style)

        # Set default selection based on current theme
        self.gradient_radio.setChecked(self.theme == "gradient")
        self.plain_radio.setChecked(self.theme == "plain")

        # Connect signals for immediate theme change and auto-save
        self.gradient_radio.toggled.connect(self._on_theme_changed)
        self.plain_radio.toggled.connect(self._on_theme_changed)

        radio_layout.addWidget(self.gradient_radio)
        radio_layout.addWidget(self.plain_radio)

        theme_layout.addLayout(radio_layout)
        return theme_layout

    def _create_next_button(self):
        """Create the 'Next' button that proceeds to API configuration step."""
        next_button = QtWidgets.QPushButton(_("Next"))
        next_button.setStyleSheet(self._get_button_style())
        # Connect to navigation handler (proceeds to API setup)
        next_button.clicked.connect(self._on_next_clicked)
        return next_button

    def _get_content_style(self):
        """Get the content styling based on current theme (dark/light mode)."""
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
        """Get the button styling with hover effects."""
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

    def _on_shortcut_changed(self):
        """Handle shortcut input changes and save automatically to settings."""
        new_shortcut = self.shortcut_input.text().strip()
        if new_shortcut:
            self.shortcut = new_shortcut
        else:
            self.shortcut = "ctrl+space"  # Fallback to default if empty

        # Auto-save shortcut setting immediately
        self._save_shortcut_setting()

    def _on_theme_changed(self):
        """Handle theme selection changes, apply immediately and save to settings."""
        # Determine the newly selected theme
        new_theme = "gradient" if self.gradient_radio.isChecked() else "plain"

        if new_theme != self.theme:
            self.theme = new_theme
            logging.debug(f"Theme changed to: {self.theme}")

            # Auto-save theme setting immediately
            self._save_theme_setting()

            # Apply theme change to UI immediately (live preview)
            self._apply_theme_change()

    def _apply_theme_change(self):
        """Apply the theme change immediately to the background for live preview."""
        # Update the background theme
        self.background.theme = self.theme
        # Force background redraw to show new theme
        self.background.update()

    def _save_shortcut_setting(self):
        """Save only the shortcut setting to persistent storage."""
        try:
            self.app.settings_manager.update_system_setting("hotkey", self.shortcut)
            logging.debug(f"Shortcut setting saved: {self.shortcut}")
        except Exception as e:
            logging.error(f"Failed to save shortcut setting: {e}")

    def _save_theme_setting(self):
        """Save only the theme setting to persistent storage."""
        try:
            self.app.settings_manager.update_system_setting("theme", self.theme)
            logging.debug(f"Theme setting saved: {self.theme}")
        except Exception as e:
            logging.error(f"Failed to save theme setting: {e}")

    def _on_next_clicked(self):
        """Handle 'Next' button click - navigate to API configuration step."""
        logging.debug("Proceeding to next step of onboarding")

        # Settings are already auto-saved, no need to save again
        # Navigate to API key configuration screen
        self._show_api_key_input()

    def _save_settings(self):
        """Save the user's selected settings (legacy method - kept for compatibility)."""
        try:
            self.app.settings_manager.update_system_setting("hotkey", self.shortcut)
            self.app.settings_manager.update_system_setting("theme", self.theme)
            logging.debug("Settings saved successfully")
        except Exception as e:
            logging.error(f"Failed to save settings: {e}")

    def _show_api_key_input(self):
        """Navigate to API key configuration screen and close this window."""
        # Open settings window focused on provider configuration
        self.app.show_settings(providers_only=True)
        # Mark as self-closing to avoid emitting close signal
        self.self_close = True
        # Close this onboarding window
        self.close()

    def closeEvent(self, event):
        """Handle window close events - distinguish between user close and navigation."""
        # Only emit close signal if user manually closed (not navigating to next step)
        if not self.self_close:
            self.close_signal.emit()
        super().closeEvent(event)
