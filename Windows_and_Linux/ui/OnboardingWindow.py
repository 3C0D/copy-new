import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QHBoxLayout, QRadioButton

from ui.ui_utils import ThemedWidget, ui_utils
from ui.ThemeManager import ThemeAwareMixin

if TYPE_CHECKING:
    from Windows_and_Linux.WritingToolApp import WritingToolApp

_ = lambda x: x


class OnboardingWindow(ThemeAwareMixin, ThemedWidget):
    """
    The onboarding window for first-time application setup.
    Guides users through initial configuration including shortcuts and theme selection.
    """

    # Signal emitted when window is closed (not when proceeding to next step)
    close_signal = QtCore.Signal()

    def __init__(self, app: 'WritingToolApp'):
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
        self.min_height = 550

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
        self.resize(950, 550)  # Reduced height by 50px to avoid taskbar overlap

        # Add minimize button flag
        self.add_minimize_button()

    def _create_layout(self):
        """Create the main layout structure with scroll area and margins."""
        # Main layout is already created in ThemedWidget with proper margins
        main_layout = QtWidgets.QVBoxLayout(self.background)

        # Create scroll area with same styling as SettingsWindow
        scroll_area = QtWidgets.QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        # Custom styling for transparent and aesthetic scroll bars
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
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
            """
        )

        # Create scrollable content widget with transparent background
        scroll_content = QtWidgets.QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        self.content_layout = QtWidgets.QVBoxLayout(scroll_content)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

        # Set up scroll area
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

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

        # Color mode selection section (auto-saves on change)
        color_mode_section = self._create_color_mode_section()
        self.content_layout.addLayout(color_mode_section)

        # Theme selection section (auto-saves and applies on change)
        theme_section = self._create_theme_section()
        self.content_layout.addLayout(theme_section)

        # Navigation button to proceed to next step (API configuration)
        next_button = self._create_next_button()
        self.content_layout.addWidget(next_button)

    def _create_title_label(self):
        """Create the main title label with theme-appropriate styling."""
        title_label = QtWidgets.QLabel(_("Welcome to Writing Tools") + "!")
        title_label.setObjectName("title_label")  # Set object name for style refresh
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_effective_mode(self):
        """Get the effective color mode based on user settings."""
        user_mode = self.app.settings_manager.color_mode or "auto"
        if user_mode == "auto":
            import darkdetect

            return "dark" if darkdetect.isDark() else "light"
        return user_mode

    def _get_title_style(self):
        """Get the title styling based on current theme (dark/light mode)."""
        current_mode = self._get_effective_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
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

    def _create_color_mode_section(self):
        """Create the color mode selection section with dropdown."""
        color_mode_layout = QtWidgets.QVBoxLayout()

        # Color mode selection title
        color_mode_title = QtWidgets.QLabel(_("Color Mode:"))
        color_mode_title.setStyleSheet(self._get_content_style())
        color_mode_layout.addWidget(color_mode_title)

        # Dropdown for color mode selection
        self.color_mode_dropdown = QtWidgets.QComboBox()
        self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

        # Set current selection based on saved setting (preserve existing values)
        current_mode = self.app.settings_manager.color_mode or "auto"
        mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
        self.color_mode_dropdown.setCurrentIndex(mode_index)

        # Apply styling to dropdown
        self.color_mode_dropdown.setStyleSheet(self._get_dropdown_style())

        # Auto-save color mode changes for immediate visual feedback
        self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

        # Prevent wheel scroll from interfering with main scroll area
        self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

        color_mode_layout.addWidget(self.color_mode_dropdown)

        return color_mode_layout

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
        current_mode = self._get_effective_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
        style = f"font-size: 16px; color: {color};"
        return style

    def _get_info_style(self):
        """Get the info text styling based on current theme (dark/light mode)."""
        current_mode = self._get_effective_mode()
        color = '#aaaaaa' if current_mode == 'dark' else '#666666'
        style = f"font-size: 16px; color: {color}; font-style: italic; margin: 10px 0;"
        return style

    def _get_input_style(self):
        """Get the input field styling based on current theme."""
        current_mode = self._get_effective_mode()
        return f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if current_mode == 'dark' else 'white'};
            color: {'#ffffff' if current_mode == 'dark' else '#000000'};
            border: 1px solid {'#666' if current_mode == 'dark' else '#ccc'};
        """

    def _get_radio_style(self):
        """Get the radio button styling based on current theme."""
        current_mode = self._get_effective_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
        style = f"color: {color};"
        return style

    def _get_dropdown_style(self):
        """Get the dropdown styling based on current theme."""
        current_mode = self._get_effective_mode()
        if current_mode == 'dark':
            return """
                QComboBox {
                    background-color: #444;
                    color: #ffffff;
                    border: 1px solid #666;
                    padding: 5px;
                    font-size: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: #444;
                    color: #ffffff;
                    selection-background-color: #666;
                }
            """
        else:
            return """
                QComboBox {
                    background-color: white;
                    color: #000000;
                    border: 1px solid #ccc;
                    padding: 5px;
                    font-size: 14px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #000000;
                    selection-background-color: #e0e0e0;
                }
            """

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

    def auto_save_color_mode(self):
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

            # IMPORTANT: Explicitly save to file to ensure persistence
            self.app.settings_manager.save()

            # Update global colorMode variable
            from ui.ui_utils import set_color_mode

            set_color_mode(color_mode)

            # Apply color mode change immediately via centralized theme manager
            from ui.ThemeManager import theme_manager

            theme_manager.change_theme(color_mode)

            # Refresh UI styles with updated colorMode
            self._refresh_ui_styles()

    def _refresh_ui_styles(self):
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if hasattr(self, 'color_mode_dropdown') and self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self._get_dropdown_style())

        # Update other UI elements
        if hasattr(self, 'shortcut_input') and self.shortcut_input:
            self.shortcut_input.setStyleSheet(self._get_input_style())

        # Update radio buttons
        if hasattr(self, 'gradient_radio') and self.gradient_radio:
            radio_style = self._get_radio_style()
            self.gradient_radio.setStyleSheet(radio_style)
            self.plain_radio.setStyleSheet(radio_style)

        # Update title label
        if hasattr(self, 'title_label'):
            for widget in self.findChildren(QtWidgets.QLabel):
                if widget.objectName() == "title_label":
                    widget.setStyleSheet(self._get_title_style())

        # Update all content labels
        for widget in self.findChildren(QtWidgets.QLabel):
            if widget != self.color_mode_dropdown and not widget.objectName() == "title_label":
                widget.setStyleSheet(self._get_content_style())

        # Update specific labels with their appropriate styles
        for widget in self.findChildren(QtWidgets.QLabel):
            if widget.objectName() == "title_label":
                widget.setStyleSheet(self._get_title_style())
            elif widget.objectName() != "":  # Skip background widgets but apply content style to others
                widget.setStyleSheet(self._get_content_style())

        # Force background update
        if hasattr(self, 'background') and self.background:
            self.background.update()

    def _save_shortcut_setting(self):
        """Save only the shortcut setting to persistent storage."""
        try:
            self.app.settings_manager.hotkey = self.shortcut
            logging.debug(f"Shortcut setting saved: {self.shortcut}")
        except Exception as e:
            logging.error(f"Failed to save shortcut setting: {e}")

    def _save_theme_setting(self):
        """Save only the theme setting to persistent storage."""
        try:
            self.app.settings_manager.theme = self.theme
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
            self.app.settings_manager.hotkey = self.shortcut
            self.app.settings_manager.theme = self.theme
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

    def refresh_theme(self):
        """Appelé automatiquement quand le thème change via ThemeManager."""
        # Utiliser l'ancienne méthode pour l'instant, sera refactorisée plus tard
        self._refresh_ui_styles()
