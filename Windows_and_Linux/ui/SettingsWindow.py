"""
 SettingsWindow.py

This module implements the SettingsWindow class for the WritingToolApp.

Key features:
- Auto-save: All settings are automatically saved when changed
  - Theme changes: immediate visual feedback and save
  - Color mode: auto-applies and saves
  - Hotkey/shortcut: registers and saves on change
  - Provider selection/settings: saves on change or dropdown update
  - Autostart: synchronizes and saves on toggle
- Button role: only closes the window
- Provider-only mode: for first-time setup completion
"""

import logging
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QImage
from PySide6.QtWidgets import (
    QApplication,
    QCheckBox,
    QComboBox,
    QFrame,
    QHBoxLayout,
    QLabel,
    QLayout,
    QLineEdit,
    QPushButton,
    QRadioButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

if TYPE_CHECKING:
    from aiprovider import AIProvider
    from WritingToolApp import WritingToolApp
from config.constants import PROVIDER_DISPLAY_NAMES
from config.data_operations import get_provider_display_name
from ui.AutostartManager import AutostartManager
from ui.ui_utils import ThemedWidget, ui_utils


def _(x):
    return x


class SettingsWindow(ThemedWidget):
    """
    The settings window for the application.
    Now with scrolling support for better usability on smaller screens.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolApp", providers_only: bool = False):
        super().__init__(app)
        self.app = app
        self._logger = logging.getLogger(__name__)
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
        if self.background is not None:
            self.background.theme = self.current_theme

        self.init_ui()
        self.retranslate_ui()

    def init_ui(self) -> None:
        """
        Initialize the user interface for the settings window.
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        # Fixed width to maintain consistent layout and provide space for dropdowns
        self.setMinimumWidth(700)
        self.setFixedWidth(700)

        main_layout = QVBoxLayout(self.background)  # Set icon, margin, and spacing in ThemedWidget

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
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
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Full settings window (not provider-only mode)
        if not self.providers_only:
            title_label = QLabel(_("Settings"))
            title_label.setObjectName("title_label")  # For specific styling in refresh
            title_label.setStyleSheet(
                f"font-size: 24px; font-weight: bold; {self.get_label_style()}"
            )
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Autostart functionality only for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(self.get_checkbox_style())

                # Synchronize settings with registry state on startup
                AutostartManager.sync_with_settings(self.app.settings_manager)

                # Set checkbox state from settings (now synchronized)
                self.autostart_checkbox.setChecked(
                    getattr(self.app.settings_manager, "start_on_boot", False)
                )
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Global hotkey configuration
            shortcut_label = QLabel(_("Shortcut Key:"))
            shortcut_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(shortcut_label)

            self.shortcut_input = QLineEdit(self.app.settings_manager.hotkey or "ctrl+space")
            self.shortcut_input.setStyleSheet(self.get_input_style())
            # Auto-save when shortcut changes
            self.shortcut_input.textChanged.connect(self.auto_save_shortcut)
            content_layout.addWidget(self.shortcut_input)

            # Background theme selection
            theme_label = QLabel(_("Background Theme:"))
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
            self.gradient_radio.toggled.connect(self._on_theme_radio_changed)
            self.plain_radio.toggled.connect(self._on_theme_radio_changed)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

            # Color mode selection
            color_mode_label = QLabel(_("Color Mode:"))
            color_mode_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(color_mode_label)

            self.color_mode_dropdown = QComboBox()
            self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

            # Set current selection based on saved setting
            current_mode = self.app.settings_manager.color_mode
            mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
            self.color_mode_dropdown.setCurrentIndex(mode_index)

            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

            # Auto-save color mode changes for immediate visual feedback
            self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

            # Prevent wheel scroll from interfering with main scroll area
            self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

            content_layout.addWidget(self.color_mode_dropdown)

        # AI Provider selection section
        provider_label = QLabel(_("Choose AI Provider:"))
        provider_label.setStyleSheet(self.get_label_style())
        content_layout.addWidget(provider_label)

        self.provider_dropdown = QComboBox()
        self.provider_dropdown.setStyleSheet(self.get_dropdown_style())
        self.provider_dropdown.setInsertPolicy(
            QComboBox.InsertPolicy.NoInsert,
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
        self._logger.debug(f"Current provider: {current_provider}, Display name: {current_display_name}")
        current_index = self.provider_dropdown.findText(current_display_name)
        self._logger.debug(f"Current provider dropdown index: {current_index}")
        if current_index != -1:
            self.provider_dropdown.setCurrentIndex(current_index)
        else:
            self.provider_dropdown.setCurrentIndex(0)  # Default to first item
            self._logger.warning("Current provider not found in dropdown, defaulting to first item.")
        content_layout.addWidget(self.provider_dropdown)

        # Visual separator between provider selection and configuration
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Create container for provider UI
        self.provider_container = QVBoxLayout()
        content_layout.addLayout(self.provider_container)

        # Initialize provider UI
        current_internal_name = self.provider_dropdown.currentData()
        provider_instance = next(
            (
                provider
                for provider in self.app.providers
                if provider.internal_name == current_internal_name
            ),
            self.app.providers[0],
        )
        self.init_provider_ui(provider_instance, self.provider_container)

        # React to provider changes by rebuilding the UI and auto-saving
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)
        self.provider_dropdown.currentIndexChanged.connect(self.auto_save_provider)

        # Another visual separator before buttons
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Finalize scroll area setup
        scroll_area.setWidget(scroll_content)
        main_layout.addWidget(scroll_area)

        # Add close button (especially important for providers_only mode)
        self.add_close_button(main_layout)

        # Set appropriate window height based on screen size
        screen = QApplication.primaryScreen().geometry()
        max_height = int(screen.height() * 0.85)  # 85% of screen height
        desired_height = min(
            550,
            max_height,
        )  # Cap at 600px or 85% of screen height (reduced by 100px to force scroll bars)
        self.resize(
            700,
            desired_height,
        )  # Use an exact width of 700px to provide space for dropdowns

        # No custom close button needed - use standard window controls

        # Ensure window can receive keyboard events and maintain focus
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("Settings"))

    def init_provider_ui(self, provider: "AIProvider", layout) -> None:
        self._logger.debug(f"init_provider_ui started for provider: {provider.internal_name}")
        """
        Initialize the user interface for the provider, including logo, name, description and all settings.
        Dynamically builds UI based on provider configuration.
        """
        # Refresh provider configuration before building UI (for dynamic providers like Ollama)
        if hasattr(provider, "refresh_configuration"):
            provider.refresh_configuration()
            self._logger.debug(f"Refreshed configuration for {provider.internal_name}")
        # Clean up previous provider UI to prevent memory leaks and layout conflicts
        if self.current_provider_layout:
            # Remove the old layout from its parent container first
            parent = self.current_provider_layout.parent()
            if parent and hasattr(parent, "removeItem"):
                # Cast to layout type to access removeItem method
                if isinstance(parent, QLayout):
                    parent.removeItem(self.current_provider_layout)
            self.current_provider_layout.setParent(None)
            ui_utils.clear_layout(self.current_provider_layout)
            self.current_provider_layout.deleteLater()

        # Also clear the container layout to ensure no old widgets remain
        ui_utils.clear_layout(layout)

        self.current_provider_layout = QVBoxLayout()

        # Provider header with logo and name
        provider_header_layout = QHBoxLayout()
        provider_header_layout.setSpacing(10)
        provider_header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Load and display provider logo if available
        if provider.logo:
            logo_path = ui_utils.get_icon_path(self.app, f"provider_{provider.logo}", with_theme=False)
            if logo_path.exists():
                targetPixmap = ui_utils.resize_and_round_image(
                    QImage(logo_path),
                    30,
                    15,
                )
                logo_label = QLabel()
                logo_label.setPixmap(targetPixmap)
                logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                provider_header_layout.addWidget(logo_label)
            else:
                self._logger.debug(
                    f"Provider logo not found: {logo_path} for provider {provider.logo}"
                )

        # Provider name display
        provider_name_label = QLabel(provider.provider_name)
        # Provider title needs high contrast - force pure white/black
        # Use effective mode based on user settings
        current_mode = self.app.settings_manager.color_mode
        provider_color = "#ffffff" if current_mode == "dark" else "#000000"
        provider_name_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {provider_color};"
        )
        provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

        # Provider description if available
        if provider.description:
            description_label = QLabel(provider.description)
            description_label.setStyleSheet(f"{self.get_label_style()} text-align: center;")
            description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(description_label)

        # Button container for multiple buttons
        if provider.button_text or (
            hasattr(provider, "additional_buttons") and provider.additional_buttons
        ):
            button_container = QHBoxLayout()
            button_container.setSpacing(10)

            # Main button
            if provider.button_text:
                main_button = QPushButton(provider.button_text)
                current_mode = self.app.settings_manager.color_mode
                main_button.setStyleSheet(
                    f"""
                        QPushButton {{
                            background-color: {"#4CAF50" if current_mode == "dark" else "#008CBA"};
                            color: white;
                            padding: 10px;
                            font-size: 16px;
                            border: none;
                            border-radius: 5px;
                        }}
                        QPushButton:hover {{
                            background-color: {"#45a049" if current_mode == "dark" else "#007095"};
                        }}
                    """,
                )
                main_button.clicked.connect(provider.button_action)
                button_container.addWidget(main_button)

            # Additional buttons
            if hasattr(provider, "additional_buttons"):
                for button_config in provider.additional_buttons:
                    additional_button = QPushButton(button_config["text"])
                    current_mode = self.app.settings_manager.color_mode

                    # Different style for secondary buttons
                    if button_config.get("style") == "secondary":
                        bg_color = "#666666" if current_mode == "dark" else "#cccccc"
                        hover_color = "#555555" if current_mode == "dark" else "#bbbbbb"
                        text_color = "#ffffff" if current_mode == "dark" else "#333333"
                    else:
                        bg_color = "#4CAF50" if current_mode == "dark" else "#008CBA"
                        hover_color = "#45a049" if current_mode == "dark" else "#007095"
                        text_color = "white"

                    additional_button.setStyleSheet(
                        f"""
                            QPushButton {{
                                background-color: {bg_color};
                                color: {text_color};
                                padding: 8px 12px;
                                font-size: 14px;
                                border: none;
                                border-radius: 4px;
                            }}
                            QPushButton:hover {{
                                background-color: {hover_color};
                            }}
                        """,
                    )
                    additional_button.clicked.connect(button_config["action"])
                    button_container.addWidget(additional_button)

            # Center the button container
            button_widget = QWidget()
            button_widget.setLayout(button_container)
            self.current_provider_layout.addWidget(
                button_widget,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

        # Initialize provider config if needed
        # Initialize providers if necessary
        if not self.app.settings_manager.providers:
            self.app.settings_manager.providers = {}

        if provider.internal_name not in self.app.settings_manager.providers:
            self.app.settings_manager.providers[provider.internal_name] = {}

        # Build provider-specific settings UI dynamically
        provider_config = self.app.settings_manager.providers[provider.internal_name]
        for setting in provider.settings:
            # Load saved value or use default
            saved_value = provider_config.get(setting.name, setting.default_value)
            self._logger.debug(f"Loading setting: {setting.name}, Saved value: {saved_value}")
            setting.set_value(saved_value)
            # Set auto-save callback for immediate saving
            setting.set_auto_save_callback(lambda: self.save_provider_settings())
            # Each setting knows how to render itself to the layout
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

        # Prevent dropdown controls from interfering with main scroll area
        self.disable_dropdown_scroll(self.current_provider_layout)

        # Add italic comment about vision models
        # row_layout = QHBoxLayout()
        vision_comment = QLabel(_("* Models with vision support"))
        vision_comment.setStyleSheet(f"{self.get_label_style()} font-style: italic;")
        layout.addWidget(vision_comment)
        self._logger.debug(f"init_provider_ui finished for provider: {provider.internal_name}")

    def disable_dropdown_scroll(self, layout: QLayout) -> None:
        """
        Recursively disable wheel events on all QComboBox widgets in the layout
        to prevent them from interfering with the main scroll area.
        This ensures smooth scrolling experience when hovering over dropdowns.
        """
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget():
                widget = item.widget()
                if isinstance(widget, QComboBox):
                    widget.wheelEvent = lambda e: e.ignore()
            elif item.layout():
                # Recursively check nested layouts
                self.disable_dropdown_scroll(item.layout())

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        # Force focus to this window when shown (important for hotkey workflow)
        ui_utils.existing_window_on_top(self)

    def focusOutEvent(self, event: QtGui.QFocusEvent) -> None:
        """
        Handle focus out event - carefully manage focus to allow dropdowns to work properly
        while maintaining window focus for hotkey workflow.
        """
        super().focusOutEvent(event)
        # Don't immediately regain focus as it interferes with dropdown interactions
        # Only regain focus if we lose it to something completely outside our window
        focused_widget = QApplication.focusWidget()
        if focused_widget and not self.isAncestorOf(focused_widget):
            # Delayed focus regain with additional safety checks
            QtCore.QTimer.singleShot(500, self.regain_focus_if_needed)

    def regain_focus_if_needed(self) -> None:
        """
        Intelligently regain focus only when appropriate.
        Avoids interfering with dropdown interactions or other legitimate focus changes.
        """
        if not self.isVisible():
            return

        # Don't steal focus from active dropdowns
        focused_widget = QApplication.focusWidget()
        if focused_widget and isinstance(focused_widget, QComboBox):
            return

        # Check for any open dropdown popups in the entire application
        for widget in QApplication.allWidgets():
            if isinstance(widget, QComboBox) and widget.view().isVisible():
                return

        # Only regain focus if we genuinely lost it to something external
        if not self.hasFocus() and not self.isAncestorOf(
            QApplication.focusWidget(),
        ):
            self.raise_()
            self.activateWindow()

    def add_close_button(self, main_layout: QVBoxLayout) -> None:
        """
        Add a close/complete setup button at the bottom of the window.
        Button text varies based on context (setup vs normal settings).
        Since all settings are auto-saved, this button simply closes the window.
        """

        button_container = QWidget()
        button_layout = QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)

        # Right-align the button
        button_layout.addStretch()

        # Different text for setup vs settings mode
        if self.providers_only:
            button_text = _("Complete Setup")
        else:
            button_text = _("Close Settings")

        self.close_button = QPushButton(button_text)
        self.close_button.setFixedSize(150, 40)
        # Use effective mode based on user settings
        current_mode = self.app.settings_manager.color_mode
        self.close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {"#0078d4" if current_mode == "light" else "#106ebe"};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {"#106ebe" if current_mode == "light" else "#1e88e5"};
            }}
            QPushButton:pressed {{
                background-color: {"#005a9e" if current_mode == "light" else "#0d47a1"};
            }}
        """,
        )

        # Connect button click to save_settings method for final processing and window closing
        self.close_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.close_button)
        main_layout.addWidget(button_container)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle window resize events."""
        super().resizeEvent(event)

    def auto_save_shortcut(self) -> None:
        """
        Auto-save shortcut when it changes to provide immediate feedback.
        Automatically registers the new hotkey with the system.
        """
        if self.shortcut_input is not None and not self.providers_only:
            self.app.settings_manager.hotkey = self.shortcut_input.text() or "ctrl+space"
            self.app.register_hotkey()

    def _on_theme_radio_changed(self) -> None:
        """Handle theme radio button changes."""
        if self.gradient_radio is not None and not self.providers_only:
            theme = "gradient" if self.gradient_radio.isChecked() else "plain"
            # Log theme change with distinctive icon
            bg_icon = "🌈" if theme == "gradient" else "⚽"
            print(f"🎛️\u00a0 SettingsWindow theme change: {bg_icon} BG={theme}")
            # Use parent class method for theme change
            self.auto_save_theme(theme)

    def auto_save_color_mode(self) -> None:
        """
        Auto-save color mode when it changes for immediate visual feedback.
        """
        if self.color_mode_dropdown is not None and not self.providers_only:
            # Get the selected text and convert to internal format
            selected_text = self.color_mode_dropdown.currentText()
            mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
            color_mode = mode_mapping.get(selected_text, "auto")

            # Log color mode change with distinctive icon
            theme_icon = (
                "🌙" if color_mode == "dark" else ("☀️\u00a0" if color_mode == "light" else "🔄")
            )
            print(f"🎨 SettingsWindow color mode change: {theme_icon} Color={color_mode}")

            self.app.settings_manager.color_mode = color_mode

            # Apply theme change
            self.app.theme_manager.change_theme(color_mode)

            # Refresh UI styles with updated colorMode
            self._refresh_ui_styles()

    def _refresh_ui_styles(self) -> None:
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update provider dropdown style
        if self.provider_dropdown:
            self.provider_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update specific labels with their individual styles
        # Title label
        title_labels = self.findChildren(QLabel)
        for widget in title_labels:
            if widget.text() == _("Settings"):
                widget.setStyleSheet(
                    f"font-size: 24px; font-weight: bold; {self.get_label_style()}"
                )
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
                hasattr(widget, "text")
                and widget.text()
                and any(
                    provider in widget.text()
                    for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"]
                )
            ):
                # Provider title needs high contrast - force pure white/black
                # Use effective mode based on user settings
                current_mode = self.app.settings_manager.color_mode
                provider_color = "#ffffff" if current_mode == "dark" else "#000000"
                widget.setStyleSheet(
                    f"font-size: 18px; font-weight: bold; color: {provider_color};"
                )
            # Check if this is a description (longer text, not a simple label)
            elif hasattr(widget, "text") and widget.text() and len(widget.text()) > 50:
                widget.setStyleSheet(f"{self.get_label_style()} text-align: center;")
            # Update all other labels (field labels like "API Base URL", "API Model", etc.)
            elif (
                hasattr(widget, "text")
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
                and not any(
                    provider in widget.text()
                    for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"]
                )
            ):
                # Apply standard label style for field labels
                current_mode = self.app.settings_manager.color_mode
                label_color = "#ffffff" if current_mode == "dark" else "#333333"
                widget.setStyleSheet(f"font-size: 16px; color: {label_color};")

        # Update shortcut input if exists
        if self.shortcut_input:
            self.shortcut_input.setStyleSheet(self.get_input_style())

        # Update radio buttons if they exist
        if self.gradient_radio:
            radio_style = self.get_radio_style()
            self.gradient_radio.setStyleSheet(radio_style)
            if self.plain_radio:
                self.plain_radio.setStyleSheet(radio_style)

        # Update checkbox if it exists
        if self.autostart_checkbox:
            self.autostart_checkbox.setStyleSheet(self.get_checkbox_style())

        # Force background update
        if self.background:
            self.background.update()

    def auto_save_provider(self) -> None:
        """
        Auto-save provider selection when it changes.
        """
        if self.provider_dropdown is not None:
            provider_name = self.provider_dropdown.currentData()
            if provider_name:
                self.app.settings_manager.provider = provider_name
                # Save provider-specific settings as well
                self.save_provider_settings()

    def save_provider_settings(self) -> None:
        """
        Save current provider-specific settings.
        """
        if self.provider_dropdown is not None:
            provider_name = self.provider_dropdown.currentData()
            if provider_name:
                selected_provider = next(
                    (
                        provider
                        for provider in self.app.providers
                        if provider.internal_name == provider_name
                    ),
                    None,
                )
                if selected_provider:
                    self._logger.debug(
                        f"Saving settings for provider: {provider_name}"
                    )
                    selected_provider.save_config()

    def toggle_autostart(self, state: int) -> None:
        """Toggle the autostart setting based on checkbox state."""
        enable = state == 2  # Qt.Checked
        AutostartManager.set_autostart_with_sync(enable, self.app.settings_manager)

    def save_settings(self) -> None:
        """Save the current settings and close window."""
        self.save_settings_without_closing()
        self.close()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        """Handle key press events for keyboard shortcuts."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close_to_previous_window()
        else:
            super().keyPressEvent(event)

    def close_to_previous_window(self) -> None:
        """
        Close settings and return to previous window if available.
        Maintains workflow continuity by restoring focus to the originating window.
        """
        # Always save settings before closing
        self.save_settings_without_closing()

        # Return to previous window if it exists and is still valid (set from WritingToolApp.show_settings)
        ui_utils.existing_window_on_top(self.previous_window)

        # Close this window
        self.close()

    def save_settings_without_closing(self) -> None:
        """
        Save all current settings to persistent storage without closing the window.
        Most settings are auto-saved, so only handle setup completion tasks.
        """
        if self.providers_only:
            # Create tray icon after initial setup completion
            self.app.systray_manager.create_tray_icon()

        # Ensure shortcut is set to default if empty
        if self.shortcut_input is not None:
            self.app.settings_manager.hotkey = self.shortcut_input.text() or "ctrl+space"

        # Re-register hotkey with new settings
        self.app.register_hotkey()
        # Exit providers_only mode after first save
        self.providers_only = False

    def _on_provider_changed(self) -> None:
        """
        Handle provider dropdown change by rebuilding the provider-specific UI.
        This ensures the settings interface matches the selected provider's requirements.
        """
        current_internal_name = (
            self.provider_dropdown.currentData() if self.provider_dropdown else None
        )

        provider_instance = next(
            (
                provider
                for provider in self.app.providers
                if provider.internal_name == current_internal_name
            ),
            self.app.providers[0],
        )
        self.init_provider_ui(provider_instance, self.provider_container)

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handle window close event.
        Emits close signal for providers_only mode to notify parent about setup completion.
        """
        self._logger.debug(f"SettingsWindow closeEvent called, providers_only={self.providers_only}")
        if self.providers_only:
            self._logger.debug("Emitting close_signal in providers_only mode")
            self.close_signal.emit()
        super().closeEvent(event)
        self.app.settings_window = None
        self._logger.debug("SettingsWindow closeEvent finished")

    def refresh_theme(self) -> None:
        """Automatically called when theme changes via ThemeManager."""
        # Use the old method for now, will be refactored later
        self._refresh_ui_styles()
