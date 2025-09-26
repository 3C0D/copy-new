import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import (
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ..config.constants import AVAILABLE_LANGUAGES
from .ui_utils import ThemedWidget, ui_utils

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


def _(x):
    return x


class OnboardingWindow(ThemedWidget):
    """
    The onboarding window for first-time application setup.
    Guides users through initial configuration including shortcuts and theme selection.
    """

    # Signal emitted when window is closed (not when proceeding to next step)
    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolApp"):
        super().__init__(app)
        self._logger = logging.getLogger(__name__)
        self.app = app

        # Default configuration values
        self.shortcut = "ctrl+space"
        self.background_theme = self.app.settings_manager.background_theme or "gradient"

        # UI components that will be referenced later
        self.content_layout: QVBoxLayout
        self.shortcut_input: QLineEdit  # Text field for shortcut input
        self.gradient_radio: QRadioButton  # Radio button for gradient theme
        self.plain_radio: QRadioButton  # Radio button for plain theme

        # Control flags
        self.self_close = False  # Flag to distinguish self-closing from user closing

        # Window dimensions
        self.min_width = 950
        self.min_height = 550

        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface for the onboarding window."""
        self._logger.debug("Initializing onboarding UI")
        self._setup_window()
        self._create_layout()
        self._show_welcome_screen()
        # self.refresh_theme()

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.setWindowTitle(_("Welcome to Writing Tools"))
        self._calculate_window_size()

    def _create_layout(self) -> None:
        """Create the main layout structure with scroll area and margins."""
        # Main layout is already created in ThemedWidget with proper margins
        main_layout = QVBoxLayout(self.background)

        # Create scroll area with same styling as SettingsWindow
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)

        # Create scrollable content widget with transparent background
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

    def _show_welcome_screen(self) -> None:
        """Display the main welcome screen with features and settings configuration."""
        ui_utils.clear_layout(self.content_layout)

        # Main title at the top
        title_label = self._create_title_label()
        self.content_layout.addWidget(title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Features description section
        features_widget = self._create_features_section()
        self.content_layout.addWidget(features_widget)

        # Language selection section (auto-saves on change)
        language_section = self._create_language_section()
        self.content_layout.addLayout(language_section)

        # Keyboard shortcut configuration section (auto-saves on change)
        shortcut_section = self._create_shortcut_section()
        self.content_layout.addLayout(shortcut_section)

        # Color mode selection section (auto-saves on change)
        color_mode_section = self._create_color_mode_section()
        self.content_layout.addLayout(color_mode_section)

        # Theme selection section (auto-saves and applies on change)
        theme_section = self._create_theme_section()
        self.content_layout.addLayout(theme_section)

        # Navigation button to proceed to next step (API configuration)
        self._create_next_button()
        self.content_layout.addWidget(self.next_button)

    def _create_title_label(self) -> QLabel:
        """Create the main title label with theme-appropriate styling."""
        title_label = QLabel(_("Welcome to Writing Tools") + "!")
        title_label.setObjectName("title_label")  # Set object name for style refresh
        title_label.setStyleSheet(self.app.styles["label_title"])
        return title_label

    def _create_features_section(self) -> QWidget:
        """Create the features description section showing app capabilities."""
        features_content = self._get_features_content()

        features_label = QLabel(features_content)
        features_label.setStyleSheet(self.app.styles["label"])
        features_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignLeft)
        return features_label

    def _get_features_content(self) -> str:
        """Get the formatted features content listing app capabilities."""
        return f"""• {_('Instantly optimize your writing with AI by selecting your text and invoking Writing Tools with "ctrl+space", anywhere.')}

• {_('Get a summary you can chat with of articles, YouTube videos, or documents by select all text with "ctrl+a"')}
  {_("(or select the YouTube transcript from its description), invoking Writing Tools, and choosing Summary.")}

• {_("Chat with AI anytime by invoking Writing Tools without selecting any text.")}

• {_("Supports an extensive range of AI models:")}
    - {_("Gemini 2.0")}
    - {_("ANY OpenAI Compatible API — including local LLMs!")}
        """

    def _create_shortcut_section(self) -> QVBoxLayout:
        """Create the keyboard shortcut configuration section with auto-save."""
        shortcut_layout = QVBoxLayout()

        # Label explaining the shortcut configuration
        shortcut_label = QLabel(_('Customize your shortcut key (default: "ctrl+space"):'))
        shortcut_label.setStyleSheet(self.app.styles["label"])
        shortcut_layout.addWidget(shortcut_label)

        # Text input field for shortcut (auto-saves on change)
        self.shortcut_input = QLineEdit(self.shortcut)
        self.shortcut_input.setStyleSheet(self.app.styles["input"])
        # Connect signal to auto-save when user types
        self.shortcut_input.textChanged.connect(self._on_shortcut_changed)
        shortcut_layout.addWidget(self.shortcut_input)

        return shortcut_layout

    def _create_color_mode_section(self) -> QVBoxLayout:
        """Create the color mode selection section with dropdown."""
        color_mode_layout = QVBoxLayout()

        # Color mode selection title
        color_mode_title = QLabel(_("Color Mode:"))
        color_mode_title.setStyleSheet(self.app.styles["label"])
        color_mode_layout.addWidget(color_mode_title)

        # Dropdown for color mode selection
        self.color_mode_dropdown = QComboBox()
        self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

        # Set current selection based on saved setting (preserve existing values)
        current_mode = self.app.settings_manager.color_mode
        mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
        self.color_mode_dropdown.setCurrentIndex(mode_index)

        # Apply styling to dropdown
        self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Auto-save color mode changes for immediate visual feedback
        self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

        # Prevent wheel scroll from interfering with main scroll area
        self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

        color_mode_layout.addWidget(self.color_mode_dropdown)

        return color_mode_layout

    def _create_language_section(self) -> QVBoxLayout:
        """Create the language selection section with dropdown."""
        language_layout = QVBoxLayout()

        # Language selection title
        language_title = QLabel(_("Language:"))
        language_title.setStyleSheet(self.app.styles["label"])
        language_layout.addWidget(language_title)

        # Dropdown for language selection
        self.language_dropdown = QComboBox()
        # Populate dropdown with available languages
        for display_name, lang_code in AVAILABLE_LANGUAGES:
            self.language_dropdown.addItem(display_name, lang_code)

        # Set current selection based on saved language
        current_language = self.app.settings_manager.language or "en"
        current_index = self.language_dropdown.findData(current_language)
        if current_index != -1:
            self.language_dropdown.setCurrentIndex(current_index)
        else:
            # Default to English if current language not found
            english_index = self.language_dropdown.findData("en")
            if english_index != -1:
                self.language_dropdown.setCurrentIndex(english_index)

        # Apply styling to dropdown
        self.language_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Auto-save language changes
        self.language_dropdown.currentTextChanged.connect(self.auto_save_language)

        # Prevent wheel scroll from interfering with main scroll area
        self.language_dropdown.wheelEvent = lambda e: e.ignore()

        language_layout.addWidget(self.language_dropdown)

        return language_layout

    def _create_theme_section(self) -> QVBoxLayout:
        """Create the theme selection section with immediate preview."""
        theme_layout = QVBoxLayout()

        # Label for theme selection
        theme_label = QLabel(_("Choose your background theme:"))
        theme_label.setStyleSheet(self.app.styles["label"])
        theme_layout.addWidget(theme_label)

        # Container for radio buttons (horizontal layout)
        radio_layout = QHBoxLayout()

        # Theme option radio buttons
        self.gradient_radio = QRadioButton(_("Gradient"))  # Gradient background theme
        self.plain_radio = QRadioButton(_("Plain"))  # Plain background theme

        # Apply styling to radio buttons
        radio_style = self.app.styles["radio"]
        self.gradient_radio.setStyleSheet(radio_style)
        self.plain_radio.setStyleSheet(radio_style)

        # Set default selection based on current background_theme
        self.gradient_radio.setChecked(self.background_theme == "gradient")
        self.plain_radio.setChecked(self.background_theme == "plain")

        # Connect signals for immediate background_theme change and auto-save
        self.gradient_radio.toggled.connect(self._on_theme_changed)
        self.plain_radio.toggled.connect(self._on_theme_changed)

        radio_layout.addWidget(self.gradient_radio)
        radio_layout.addWidget(self.plain_radio)

        theme_layout.addLayout(radio_layout)
        return theme_layout

    def _create_next_button(self) -> QPushButton:
        """Create the 'Next' button that proceeds to API configuration step."""
        self.next_button = QPushButton(_("Next"))
        self.next_button.setStyleSheet(self.app.styles["close_button"])
        # Connect to navigation handler (proceeds to API setup)
        self.next_button.clicked.connect(self._on_next_clicked)
        return self.next_button

    def _on_shortcut_changed(self) -> None:
        """Handle shortcut input changes and save automatically to settings."""
        new_shortcut = self.shortcut_input.text().strip()
        if new_shortcut:
            self.shortcut = new_shortcut
        else:
            self.shortcut = "ctrl+space"  # Fallback to default if empty

        # Auto-save shortcut setting immediately
        self._save_shortcut_setting()

    def _on_theme_changed(self) -> None:
        """Handle theme selection changes, apply immediately and save to settings."""
        # Determine the newly selected theme
        new_theme = "gradient" if self.gradient_radio.isChecked() else "plain"

        if new_theme != self.background_theme:
            self.background_theme = new_theme

            # Auto-save theme setting immediately
            self._save_theme_setting()

            # Apply theme change to UI immediately (live preview)
            self.app.theme_manager.change_background_theme(new_theme)

    def auto_save_color_mode(self) -> None:
        """
        Auto-save color mode when it changes for immediate visual feedback.
        Preserves existing data and ensures proper persistence.
        """
        if hasattr(self, "color_mode_dropdown") and self.color_mode_dropdown is not None:
            # Get the selected text and convert to internal format
            selected_text = self.color_mode_dropdown.currentText()
            mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
            color_mode = mode_mapping.get(selected_text, "auto")

            # Save to settings manager (this preserves existing data in data.json)
            self.app.settings_manager.color_mode = color_mode

            # Apply theme change
            self.app.theme_manager.change_color_mode(color_mode)

            # Refresh UI styles with updated colorMode
            self.refresh_theme()

    def auto_save_language(self) -> None:
        """
        Auto-save language when it changes.
        """
        if hasattr(self, "language_dropdown") and self.language_dropdown is not None:
            # Get the selected language code
            selected_lang_code = self.language_dropdown.currentData()
            if selected_lang_code:
                self.app.settings_manager.language = selected_lang_code
                self._logger.debug(f"Language changed to: {selected_lang_code}")

    def refresh_theme(self) -> None:
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if hasattr(self, "color_mode_dropdown") and self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update language dropdown style
        if hasattr(self, "language_dropdown") and self.language_dropdown:
            self.language_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update other UI elements
        if hasattr(self, "shortcut_input") and self.shortcut_input:
            self.shortcut_input.setStyleSheet(self.app.styles["input"])

        # Update radio buttons
        if hasattr(self, "gradient_radio") and self.gradient_radio:
            radio_style = self.app.styles["radio"]
            self.gradient_radio.setStyleSheet(radio_style)
            self.plain_radio.setStyleSheet(radio_style)

        # Update title label
        if hasattr(self, "title_label"):
            for widget in self.findChildren(QLabel):
                if widget.objectName() == "title_label":
                    widget.setStyleSheet(self.app.styles["label_title"])

        # Update all content labels
        for widget in self.findChildren(QLabel):
            if widget != self.color_mode_dropdown and not widget.objectName() == "title_label":
                widget.setStyleSheet(self.app.styles["label"])

        # Update specific labels with their appropriate styles
        for widget in self.findChildren(QLabel):
            if widget.objectName() == "title_label":
                widget.setStyleSheet(self.app.styles["label_title"])
            elif (
                widget.objectName() != ""
            ):  # Skip background widgets but apply content style to others
                widget.setStyleSheet(self.app.styles["label"])

        # Update next button
        if hasattr(self, "next_button") and self.next_button:
            self.next_button.setStyleSheet(self.app.styles["close_button"])

        # Refresh background theme
        super().refresh_theme()

    def _save_shortcut_setting(self) -> None:
        """Save only the shortcut setting to persistent storage."""
        try:
            self.app.settings_manager.hotkey = self.shortcut
            self._logger.debug(f"Shortcut setting saved: {self.shortcut}")
        except Exception as e:
            self._logger.error(f"Failed to save shortcut setting: {e}")

    def _save_theme_setting(self) -> None:
        """Save only the theme setting to persistent storage."""
        try:
            self.app.settings_manager.background_theme = self.background_theme
        except Exception as e:
            self._logger.error(f"Failed to save background_theme setting: {e}")

    def _on_next_clicked(self) -> None:
        """Handle 'Next' button click - navigate to API configuration step."""
        self._logger.debug("Proceeding to next step of onboarding")

        # Settings are already auto-saved, no need to save again
        # Navigate to API key configuration screen
        self._show_api_key_input()

    def _save_settings(self) -> None:
        """Save the user's selected settings (legacy method - kept for compatibility)."""
        try:
            self.app.settings_manager.hotkey = self.shortcut
            self.app.settings_manager.background_theme = self.background_theme
            self._logger.debug("Settings saved successfully")
        except Exception as e:
            self._logger.error(f"Failed to save settings: {e}")

    def _show_api_key_input(self) -> None:
        """Navigate to API key configuration screen and close this window."""
        # Open settings window focused on provider configuration
        self.app.show_settings(providers_only=True)
        # Mark as self-closing to avoid emitting close signal
        self.self_close = True
        # Close this onboarding window
        self.close()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close events - distinguish between user close and navigation."""
        # Only emit close signal if user manually closed (not navigating to next step)
        if not self.self_close:
            self.close_signal.emit()
        super().closeEvent(event)
