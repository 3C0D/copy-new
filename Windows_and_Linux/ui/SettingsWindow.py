"""
Page totalement revue et commentée.
vérifier/comparer logic scrolling avec About window
étendre l'autostart à linux
L285   No sure about that:      # Add save button (especially important for providers_only mode)
        self.add_save_button(main_layout)

"""

import logging
import os
import sys
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtWidgets, QtGui
from PySide6.QtGui import QImage
from PySide6.QtWidgets import QHBoxLayout, QRadioButton, QScrollArea, QWidget

if TYPE_CHECKING:
    from aiprovider import AIProvider
    from Windows_and_Linux.WritingToolApp import WritingToolApp
from config.constants import PROVIDER_DISPLAY_NAMES
from config.data_operations import get_provider_display_name, get_provider_internal_name
from ui.AutostartManager import AutostartManager
from ui.ui_utils import ThemedWidget, ui_utils, get_icon_path
from ui.ThemeManager import ThemeAwareMixin, theme_manager

_ = lambda x: x


class SettingsWindow(ThemeAwareMixin, ThemedWidget):
    """
    The settings window for the application.
    Now with scrolling support for better usability on smaller screens.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app: 'WritingToolApp', providers_only=False):
        super().__init__()
        self.app = app
        self.current_provider_layout = None
        # Special mode to show only provider settings (during first setup)
        self.providers_only = providers_only
        self.gradient_radio = None
        self.plain_radio = None
        self.color_mode_dropdown = None
        self.provider_dropdown = None
        self.provider_container = None
        self.autostart_checkbox = None
        self.shortcut_input = None
        # Reference to previous window to return to after closing
        self.previous_window = None

        # Store current theme as instance variable for use throughout the class
        self.current_theme = self.app.settings_manager.theme or "gradient"

        # Set the correct theme from saved settings
        if hasattr(self, "background") and self.background is not None:
            self.background.theme = self.current_theme

        self.init_ui()
        self.retranslate_ui()

    def _get_effective_mode(self):
        """Get the effective color mode based on user settings."""
        user_mode = self.app.settings_manager.color_mode or "auto"
        if user_mode == "auto":
            import darkdetect

            return "dark" if darkdetect.isDark() else "light"
        return user_mode

    def init_ui(self):
        """
        Initialize the user interface for the settings window.
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        # Fixed width to maintain consistent layout and provide space for dropdowns
        self.setMinimumWidth(700)
        self.setFixedWidth(700)

        # Window configuration - initially on top but can be moved to background
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint  # useful when user needs to retrieve API keys...
            | QtCore.Qt.WindowType.WindowTitleHint,
        )
        # Show on top initially but allow user to move to background
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)
        self.raise_()
        self.activateWindow()

        main_layout = QtWidgets.QVBoxLayout(self.background)  # Set icon, margin, and spacing in ThemedWidget

        # Earlier scroll_area and scroll_content creation moved up
        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QtWidgets.QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        scroll_area.setVerticalScrollBarPolicy(
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
            QScrollBar:horizontal {
                background-color: rgba(0, 0, 0, 0.1);
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(128, 128, 128, 0.6);
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: rgba(128, 128, 128, 1.0);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """,
        )

        # Create scrollable content widget with transparent background
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QtWidgets.QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Full settings window (not provider-only mode)
        if not self.providers_only:
            title_label = QtWidgets.QLabel(_("Settings"))
            title_label.setObjectName("title_label")  # For specific styling in refresh
            title_label.setStyleSheet(f"font-size: 24px; font-weight: bold; {self.get_label_style()}")
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Autostart functionality only for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QtWidgets.QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(self.get_checkbox_style())

                # Synchronize settings with registry state on startup
                AutostartManager.sync_with_settings(self.app.settings_manager)

                # Set checkbox state from settings (now synchronized)
                self.autostart_checkbox.setChecked(getattr(self.app.settings_manager, 'start_on_boot', False))
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Global hotkey configuration
            shortcut_label = QtWidgets.QLabel(_("Shortcut Key:"))
            shortcut_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(shortcut_label)

            self.shortcut_input = QtWidgets.QLineEdit(self.app.settings_manager.hotkey or 'ctrl+space')
            self.shortcut_input.setStyleSheet(self.get_input_style())
            # Auto-save when shortcut changes
            self.shortcut_input.textChanged.connect(self.auto_save_shortcut)
            content_layout.addWidget(self.shortcut_input)

            # Background theme selection
            theme_label = QtWidgets.QLabel(_("Background Theme:"))
            theme_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(theme_label)

            theme_layout = QHBoxLayout()
            self.gradient_radio = QRadioButton(_("Blurry Gradient"))
            self.plain_radio = QRadioButton(_("Plain"))
            self.gradient_radio.setStyleSheet(self.get_radio_style())
            self.plain_radio.setStyleSheet(self.get_radio_style())
            # Use the instance variable instead of re-reading from settings
            self.gradient_radio.setChecked(self.current_theme == "gradient")
            self.plain_radio.setChecked(self.current_theme == "plain")
            # Auto-save theme changes for immediate visual feedback
            self.gradient_radio.toggled.connect(self.auto_save_theme)
            self.plain_radio.toggled.connect(self.auto_save_theme)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

            # Color mode selection
            color_mode_label = QtWidgets.QLabel(_("Color Mode:"))
            color_mode_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(color_mode_label)

            self.color_mode_dropdown = QtWidgets.QComboBox()
            self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

            # Set current selection based on saved setting
            current_mode = self.app.settings_manager.color_mode or "auto"
            mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
            self.color_mode_dropdown.setCurrentIndex(mode_index)

            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

            # Auto-save color mode changes for immediate visual feedback
            self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

            # Prevent wheel scroll from interfering with main scroll area
            self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

            content_layout.addWidget(self.color_mode_dropdown)

        # AI Provider selection section
        provider_label = QtWidgets.QLabel(_("Choose AI Provider:"))
        provider_label.setStyleSheet(self.get_label_style())
        content_layout.addWidget(provider_label)

        self.provider_dropdown = QtWidgets.QComboBox()
        self.provider_dropdown.setStyleSheet(self.get_dropdown_style())
        self.provider_dropdown.setInsertPolicy(
            QtWidgets.QComboBox.InsertPolicy.NoInsert,
        )
        # Prevent wheel scroll from interfering with main scroll area
        self.provider_dropdown.wheelEvent = lambda e: e.ignore()

        current_provider = self.app.settings_manager.provider

        # Populate dropdown with display names while storing internal names as data
        # This separation allows for localized display names while maintaining stable internal identifiers
        for internal_name, display_name in PROVIDER_DISPLAY_NAMES.items():
            self.provider_dropdown.addItem(display_name, internal_name)

        # Set current selection based on internal name
        current_display_name = get_provider_display_name(current_provider)
        current_index = self.provider_dropdown.findText(current_display_name)
        if current_index != -1:
            self.provider_dropdown.setCurrentIndex(current_index)
        else:
            self.provider_dropdown.setCurrentIndex(0)  # Default to first item
        content_layout.addWidget(self.provider_dropdown)

        # Visual separator between provider selection and configuration
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Create container for provider UI
        self.provider_container = QtWidgets.QVBoxLayout()
        content_layout.addLayout(self.provider_container)

        # Initialize provider UI
        current_internal_name = self.provider_dropdown.currentData()
        provider_instance = next(
            (provider for provider in self.app.providers if provider.internal_name == current_internal_name),
            self.app.providers[0],
        )
        self.init_provider_ui(provider_instance, self.provider_container)

        # React to provider changes by rebuilding the UI and auto-saving
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)
        self.provider_dropdown.currentIndexChanged.connect(self.auto_save_provider)

        # Another visual separator before buttons
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Finalize scroll area setup
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Add save button (especially important for providers_only mode)
        self.add_save_button(main_layout)

        # Set appropriate window height based on screen size
        screen = QtWidgets.QApplication.primaryScreen().geometry()
        max_height = int(screen.height() * 0.85)  # 85% of screen height
        desired_height = min(
            550,
            max_height,
        )  # Cap at 600px or 85% of screen height (reduced by 100px from 700px to force scroll bars)
        self.resize(
            700,
            desired_height,
        )  # Use an exact width of 700px to provide space for dropdowns

        # No custom close button needed - use standard window controls

        # Ensure window can receive keyboard events and maintain focus
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def retranslate_ui(self):
        self.setWindowTitle(_("Settings"))

    def init_provider_ui(self, provider: 'AIProvider', layout):
        """
        Initialize the user interface for the provider, including logo, name, description and all settings.
        Dynamically builds UI based on provider configuration.
        """
        # Clean up previous provider UI to prevent memory leaks and layout conflicts
        if self.current_provider_layout:
            # Remove the old layout from its parent container first
            parent = self.current_provider_layout.parent()
            if parent and hasattr(parent, 'removeItem'):
                # Cast to layout type to access removeItem method
                from PySide6.QtWidgets import QLayout

                if isinstance(parent, QLayout):
                    parent.removeItem(self.current_provider_layout)
            self.current_provider_layout.setParent(None)
            ui_utils.clear_layout(self.current_provider_layout)
            self.current_provider_layout.deleteLater()

        # Also clear the container layout to ensure no old widgets remain
        ui_utils.clear_layout(layout)

        self.current_provider_layout = QtWidgets.QVBoxLayout()

        # Provider header with logo and name
        provider_header_layout = QtWidgets.QHBoxLayout()
        provider_header_layout.setSpacing(10)
        provider_header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Load and display provider logo if available
        if provider.logo:
            # Use get_icon_path for proper path resolution in all modes (dev, build, etc.)
            logo_path = get_icon_path(f"provider_{provider.logo}", with_theme=False)
            if logo_path and os.path.exists(logo_path):
                targetPixmap = ui_utils.resize_and_round_image(
                    QImage(logo_path),
                    30,
                    15,
                )
                logo_label = QtWidgets.QLabel()
                logo_label.setPixmap(targetPixmap)
                logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                provider_header_layout.addWidget(logo_label)
            else:
                logging.debug(f"Provider logo not found: {logo_path} for provider {provider.logo}")

        # Provider name display
        provider_name_label = QtWidgets.QLabel(provider.provider_name)
        # Provider title needs high contrast - force pure white/black
        # Use effective mode based on user settings
        current_mode = self._get_effective_mode()
        provider_color = '#ffffff' if current_mode == 'dark' else '#000000'
        provider_name_label.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {provider_color};")
        provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

        # Provider description if available
        if provider.description:
            description_label = QtWidgets.QLabel(provider.description)
            description_label.setStyleSheet(f"{self.get_label_style()} text-align: center;")
            description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(description_label)

        # Original single button logic
        if provider.button_text:
            button = QtWidgets.QPushButton(provider.button_text)
            # Use effective mode based on user settings
            current_mode = self._get_effective_mode()
            button.setStyleSheet(
                f"""
                    QPushButton {{
                        background-color: {'#4CAF50' if current_mode == 'dark' else '#008CBA'};
                        color: white;
                        padding: 10px;
                        font-size: 16px;
                        border: none;
                        border-radius: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: {'#45a049' if current_mode == 'dark' else '#007095'};
                    }}
                """,
            )
            button.clicked.connect(provider.button_action)
            self.current_provider_layout.addWidget(
                button,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

        # Initialize provider config if needed
        if not self.app.settings_manager.providers:
            self.app.settings_manager.providers = {}

        if provider.internal_name not in self.app.settings_manager.providers:
            self.app.settings_manager.providers[provider.internal_name] = {}

        # Build provider-specific settings UI dynamically
        provider_config = self.app.settings_manager.providers[provider.internal_name]
        for setting in provider.settings:
            # Load saved value or use default
            saved_value = provider_config.get(setting.name, setting.default_value)
            setting.set_value(saved_value)
            # Set auto-save callback for immediate saving
            setting.set_auto_save_callback(lambda: self.save_provider_settings())
            # Each setting knows how to render itself to the layout
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

        # Prevent dropdown controls from interfering with main scroll area
        self.disable_dropdown_scroll(self.current_provider_layout)

    def disable_dropdown_scroll(self, layout):
        """
        Recursively disable wheel events on all QComboBox widgets in the layout
        to prevent them from interfering with the main scroll area.
        This ensures smooth scrolling experience when hovering over dropdowns.
        """
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                widget = item.widget()
                if isinstance(widget, QtWidgets.QComboBox):
                    widget.wheelEvent = lambda e: e.ignore()
            elif item.layout():
                # Recursively check nested layouts
                self.disable_dropdown_scroll(item.layout())

    def showEvent(self, event):
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        # Force focus to this window when shown (important for hotkey workflow)
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def focusOutEvent(self, event):
        """
        Handle focus out event - carefully manage focus to allow dropdowns to work properly
        while maintaining window focus for hotkey workflow.
        """
        super().focusOutEvent(event)
        # Don't immediately regain focus as it interferes with dropdown interactions
        # Only regain focus if we lose it to something completely outside our window
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget and not self.isAncestorOf(focused_widget):
            # Delayed focus regain with additional safety checks
            QtCore.QTimer.singleShot(500, self.regain_focus_if_needed)

    def regain_focus_if_needed(self):
        """
        Intelligently regain focus only when appropriate.
        Avoids interfering with dropdown interactions or other legitimate focus changes.
        """
        if not self.isVisible():
            return

        # Don't steal focus from active dropdowns
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget and isinstance(focused_widget, QtWidgets.QComboBox):
            return

        # Check for any open dropdown popups in the entire application
        for widget in QtWidgets.QApplication.allWidgets():
            if isinstance(widget, QtWidgets.QComboBox) and widget.view().isVisible():
                return

        # Only regain focus if we genuinely lost it to something external
        if not self.hasFocus() and not self.isAncestorOf(
            QtWidgets.QApplication.focusWidget(),
        ):
            self.raise_()
            self.activateWindow()

    def add_save_button(self, main_layout):
        """
        Add a save/complete setup button at the bottom of the window.
        Button text varies based on context (setup vs normal settings).
        """

        button_container = QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)

        # Right-align the button
        button_layout.addStretch()

        # Different text for setup vs settings mode
        if self.providers_only:
            button_text = _("Complete Setup")
        else:
            button_text = _("Close Settings")

        self.save_button = QtWidgets.QPushButton(button_text)
        self.save_button.setFixedSize(150, 40)
        # Use effective mode based on user settings
        current_mode = self._get_effective_mode()
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {'#0078d4' if current_mode == 'light' else '#106ebe'};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {'#106ebe' if current_mode == 'light' else '#1e88e5'};
            }}
            QPushButton:pressed {{
                background-color: {'#005a9e' if current_mode == 'light' else '#0d47a1'};
            }}
        """,
        )

        # Connect button to save function
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        main_layout.addWidget(button_container)

    def resizeEvent(self, event):
        """Handle window resize events."""
        super().resizeEvent(event)

    def auto_save_shortcut(self):
        """
        Auto-save shortcut when it changes to provide immediate feedback.
        Automatically registers the new hotkey with the system.
        """
        if hasattr(self, "shortcut_input") and self.shortcut_input is not None and not self.providers_only:
            self.app.settings_manager.hotkey = self.shortcut_input.text() or "ctrl+space"
            self.app.register_hotkey()

    def auto_save_theme(self):
        """
        Auto-save theme when it changes for immediate visual feedback.
        """
        if hasattr(self, "gradient_radio") and self.gradient_radio is not None and not self.providers_only:
            theme = "gradient" if self.gradient_radio.isChecked() else "plain"
            self.app.settings_manager.theme = theme

            # Apply theme change immediately to the background for live preview
            if hasattr(self, "background") and self.background is not None:
                self.background.theme = theme
                self.background.update()

    def auto_save_color_mode(self):
        """
        Auto-save color mode when it changes for immediate visual feedback.
        """
        if hasattr(self, "color_mode_dropdown") and self.color_mode_dropdown is not None and not self.providers_only:
            # Get the selected text and convert to internal format
            selected_text = self.color_mode_dropdown.currentText()
            mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
            color_mode = mode_mapping.get(selected_text, "auto")

            self.app.settings_manager.color_mode = color_mode

            # Update global colorMode variable
            from ui.ui_utils import set_color_mode

            set_color_mode(color_mode)

            # Apply color mode change immediately via centralized theme manager
            theme_manager.change_theme(color_mode)

            # Refresh UI styles with updated colorMode
            self._refresh_ui_styles()

    def _refresh_ui_styles(self):
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if hasattr(self, 'color_mode_dropdown') and self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update provider dropdown style
        if hasattr(self, 'provider_dropdown') and self.provider_dropdown:
            self.provider_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update specific labels with their individual styles
        # Title label
        title_labels = self.findChildren(QtWidgets.QLabel)
        for widget in title_labels:
            if widget.text() == _("Settings"):
                widget.setStyleSheet(f"font-size: 24px; font-weight: bold; {self.get_label_style()}")
            elif widget.text() in [
                _("Shortcut Key:"),
                _("Background Theme:"),
                _("Color Mode:"),
                _("Choose AI Provider:"),
            ]:
                widget.setStyleSheet(self.get_label_style())

        # Update provider-specific labels by checking all labels
        for widget in title_labels:
            # Check if this is a provider name (contains provider name text)
            if (
                hasattr(widget, 'text')
                and widget.text()
                and any(provider in widget.text() for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"])
            ):
                # Provider title needs high contrast - force pure white/black
                # Use effective mode based on user settings
                current_mode = self._get_effective_mode()
                provider_color = '#ffffff' if current_mode == 'dark' else '#000000'
                widget.setStyleSheet(f"font-size: 18px; font-weight: bold; color: {provider_color};")
            # Check if this is a description (longer text, not a simple label)
            elif hasattr(widget, 'text') and widget.text() and len(widget.text()) > 50:
                widget.setStyleSheet(f"{self.get_label_style()} text-align: center;")
            # Update all other labels (field labels like "API Base URL", "API Model", etc.)
            elif (
                hasattr(widget, 'text')
                and widget.text()
                and widget.text()
                not in [
                    _("Settings"),
                    _("Shortcut Key:"),
                    _("Background Theme:"),
                    _("Color Mode:"),
                    _("Choose AI Provider:"),
                ]
                and len(widget.text()) <= 50
                and not any(provider in widget.text() for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"])
            ):
                # Apply standard label style for field labels
                current_mode = self._get_effective_mode()
                label_color = '#ffffff' if current_mode == 'dark' else '#333333'
                widget.setStyleSheet(f"font-size: 16px; color: {label_color};")

        # Update shortcut input if exists
        if hasattr(self, 'shortcut_input') and self.shortcut_input:
            self.shortcut_input.setStyleSheet(self.get_input_style())

        # Update radio buttons if they exist
        if hasattr(self, 'gradient_radio') and self.gradient_radio:
            radio_style = self.get_radio_style()
            self.gradient_radio.setStyleSheet(radio_style)
            if hasattr(self, 'plain_radio') and self.plain_radio:
                self.plain_radio.setStyleSheet(radio_style)

        # Update checkbox if it exists
        if hasattr(self, 'autostart_checkbox') and self.autostart_checkbox:
            self.autostart_checkbox.setStyleSheet(self.get_checkbox_style())

        # Force background update
        if hasattr(self, 'background') and self.background:
            self.background.update()

    def auto_save_provider(self):
        """
        Auto-save provider selection when it changes.
        """
        if hasattr(self, "provider_dropdown") and self.provider_dropdown is not None:
            provider_internal_name = self.provider_dropdown.currentData()
            if provider_internal_name:
                self.app.settings_manager.provider = provider_internal_name
                # Save provider-specific settings as well
                self.save_provider_settings()

    def save_provider_settings(self):
        """
        Save current provider-specific settings.
        """
        if hasattr(self, "provider_dropdown") and self.provider_dropdown is not None:
            provider_internal_name = self.provider_dropdown.currentData()
            if provider_internal_name:
                # Find the corresponding provider instance
                selected_provider = next(
                    (provider for provider in self.app.providers if provider.internal_name == provider_internal_name),
                    None,
                )
                if selected_provider:
                    selected_provider.save_config()

    def toggle_autostart(self, state):
        """Toggle the autostart setting based on checkbox state."""
        enable = state == 2  # Qt.Checked
        AutostartManager.set_autostart_with_sync(enable, self.app.settings_manager)

    def save_settings(self):
        """Save the current settings and close window."""
        self.save_settings_without_closing()
        self.close()

    def keyPressEvent(self, event):
        """Handle key press events for keyboard shortcuts."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close_to_previous_window()
        else:
            super().keyPressEvent(event)

    def close_to_previous_window(self):
        """
        Close settings and return to previous window if available.
        Maintains workflow continuity by restoring focus to the originating window.
        """
        # Always save settings before closing
        self.save_settings_without_closing()

        # Return to previous window if it exists and is still valid
        if self.previous_window and hasattr(self.previous_window, "show"):
            # Show the previous window and give it focus
            self.previous_window.show()
            self.previous_window.raise_()
            self.previous_window.activateWindow()
            if hasattr(self.previous_window, "setFocus"):
                self.previous_window.setFocus()

        # Close this window
        self.close()

    def save_settings_without_closing(self):
        """
        Save all current settings to persistent storage without closing the window.
        Handles both general app settings and provider-specific configurations.
        """
        # Save general app settings (not in providers_only mode)
        if not self.providers_only:
            if hasattr(self, "shortcut_input") and self.shortcut_input is not None:
                self.app.settings_manager.hotkey = self.shortcut_input.text() or "ctrl+space"
            if hasattr(self, "gradient_radio") and self.gradient_radio is not None:
                theme = "gradient" if self.gradient_radio.isChecked() else "plain"
                self.app.settings_manager.theme = theme or "gradient"
            if hasattr(self, "color_mode_dropdown") and self.color_mode_dropdown is not None:
                selected_text = self.color_mode_dropdown.currentText()
                mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
                color_mode = mode_mapping.get(selected_text, "auto")
                self.app.settings_manager.color_mode = color_mode
        else:
            # Create tray icon after initial setup completion
            self.app.create_tray_icon()

        # Save provider selection using internal name from dropdown data
        if hasattr(self, "provider_dropdown") and self.provider_dropdown is not None:
            provider_internal_name = self.provider_dropdown.currentData()
            self.app.settings_manager.provider = provider_internal_name or "gemini"

        # Find the corresponding provider instance
        selected_provider = next(
            (provider for provider in self.app.providers if provider.internal_name == provider_internal_name),
            self.app.providers[0],
        )

        # Save provider-specific configuration
        selected_provider.save_config()

        # Update application's current provider
        self.app.current_provider = selected_provider

        # Load the saved configuration into the provider
        provider_config = self.app._get_provider_config(provider_internal_name)
        if self.app.current_provider:
            self.app.current_provider.load_config(provider_config)
        else:
            logging.error("Current provider not set after save")

        # Re-register hotkey with new settings
        self.app.register_hotkey()
        # Exit providers_only mode after first save
        self.providers_only = False

    def _on_provider_changed(self):
        """
        Handle provider dropdown change by rebuilding the provider-specific UI.
        This ensures the settings interface matches the selected provider's requirements.
        """
        current_internal_name = self.provider_dropdown.currentData() if self.provider_dropdown else None

        provider_instance = next(
            (provider for provider in self.app.providers if provider.internal_name == current_internal_name),
            self.app.providers[0],
        )
        self.init_provider_ui(provider_instance, self.provider_container)

    def closeEvent(self, event):
        """
        Handle window close event.
        Emits close signal for providers_only mode to notify parent about setup completion.
        """
        if self.providers_only:
            self.close_signal.emit()
        super().closeEvent(event)

    def refresh_theme(self):
        """Appelé automatiquement quand le thème change via ThemeManager."""
        # Utiliser l'ancienne méthode pour l'instant, sera refactorisée plus tard
        self._refresh_ui_styles()
