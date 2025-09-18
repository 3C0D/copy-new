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
        self.shortcut_label = None
        self.theme_label = None
        self.color_mode_label = None
        self.provider_label = None
        self.provider_name_label = None
        self.description_label = None
        # Reference to previous window to return to after closing
        self.previous_window = None

        # Store current background_theme as instance variable for use throughout the class
        self.current_background_theme = self.app.settings_manager.background_theme or "gradient"

        # Set the correct background_theme from saved settings
        if self.background is not None:
            self.background.background_theme = self.current_background_theme

        self.init_ui()
        self.retranslate_ui()

    def init_ui(self) -> None:
        """
        Initialize the user interface for the settings window.
        Window size: 700px width (fixed), height calculated as min(550px, 85% screen height).
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        self.min_width = 700
        self.min_height = 550
        self._calculate_window_size()

        main_layout = QVBoxLayout(self.background)  # Set icon, margin, and spacing in ThemedWidget

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)  # No border/frame

        # Custom styling for transparent and aesthetic scroll bars
        scroll_area.setStyleSheet(self.app.styles["scroll_area"])

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
            title_label.setStyleSheet(self.app.styles["label_title"])
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Autostart functionality only for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(self.app.styles["checkbox"])

                # Synchronize settings with registry state on startup
                AutostartManager.sync_with_settings(self.app.settings_manager)

                # Set checkbox state from settings (now synchronized)
                self.autostart_checkbox.setChecked(
                    getattr(self.app.settings_manager, "start_on_boot", False)
                )
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Global hotkey configuration
            self.shortcut_label = QLabel(_("Shortcut Key:"))
            self.shortcut_label.setStyleSheet(self.app.styles["label"])
            content_layout.addWidget(self.shortcut_label)

            self.shortcut_input = QLineEdit(self.app.settings_manager.hotkey or "ctrl+space")
            self.shortcut_input.setStyleSheet(self.app.styles["input"])
            self.shortcut_input.setPlaceholderText("e.g., ctrl+space, ctrl+shift+a")
            # Auto-save when shortcut changed and focus lost
            self.shortcut_input.editingFinished.connect(self.auto_save_shortcut)
            content_layout.addWidget(self.shortcut_input)

            # Background theme selection
            self.theme_label = QLabel(_("Background Theme:"))
            self.theme_label.setStyleSheet(self.app.styles["label"])
            content_layout.addWidget(self.theme_label)

            theme_layout = QHBoxLayout()
            self.gradient_radio = QRadioButton(_("Blurry Gradient"))
            self.plain_radio = QRadioButton(_("Plain"))
            self.gradient_radio.setStyleSheet(self.app.styles["radio"])
            self.plain_radio.setStyleSheet(self.app.styles["radio"])
            # Use the instance variable instead of re-reading from settings
            self.gradient_radio.setChecked(self.current_background_theme == "gradient")
            self.plain_radio.setChecked(self.current_background_theme == "plain")
            # Auto-save background_theme changes for immediate visual feedback
            self.gradient_radio.toggled.connect(self._on_theme_radio_changed)
            self.plain_radio.toggled.connect(self._on_theme_radio_changed)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

            # Color mode selection
            self.color_mode_label = QLabel(_("Color Mode:"))
            self.color_mode_label.setStyleSheet(self.app.styles["label"])
            content_layout.addWidget(self.color_mode_label)

            self.color_mode_dropdown = QComboBox()
            self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

            # Set current selection based on saved setting
            current_mode = self.app.settings_manager.color_mode
            mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
            self.color_mode_dropdown.setCurrentIndex(mode_index)

            self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])

            # Auto-save color mode changes for immediate visual feedback
            self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

            # Prevent wheel scroll from interfering with main scroll area
            self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

            content_layout.addWidget(self.color_mode_dropdown)

        # AI Provider selection section
        self.provider_label = QLabel(_("Choose AI Provider:"))
        self.provider_label.setStyleSheet(self.app.styles["label"])
        content_layout.addWidget(self.provider_label)

        self.provider_dropdown = QComboBox()
        self.provider_dropdown.setStyleSheet(self.app.styles["dropdown"])
        # Prevent wheel scroll from interfering with main scroll area
        self.provider_dropdown.wheelEvent = lambda e: e.ignore()

        current_provider = self.app.settings_manager.provider

        # Populate dropdown with display names while storing internal names as data
        # This separation allows for localized display names while maintaining stable internal identifiers
        for internal_name, display_name in PROVIDER_DISPLAY_NAMES.items():
            self.provider_dropdown.addItem(display_name, internal_name)

        # Set current selection based on internal name
        current_display_name = get_provider_display_name(current_provider)
        self._logger.debug(
            f"Current provider: {current_provider}, Display name: {current_display_name}"
        )

        # Find index of current provider in dropdown
        current_index = self.provider_dropdown.findText(current_display_name)
        self._logger.debug(f"Current provider dropdown index: {current_index}")

        # Restore previously selected provider from settings
        if current_index != -1:
            self.provider_dropdown.setCurrentIndex(current_index)
        else:
            self.provider_dropdown.setCurrentIndex(0)  # Default to first item
            self._logger.warning(
                "Current provider not found in dropdown, defaulting to first item."
            )
        content_layout.addWidget(self.provider_dropdown)

        # Visual separator between provider selection and configuration
        line = QFrame()
        line.setFrameShape(QFrame.Shape.HLine)
        line.setFrameShadow(QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Create container for provider UI
        self.provider_container = QVBoxLayout()
        content_layout.addLayout(self.provider_container)

        # Retrieves the data from the selected element.
        current_internal_name = self.provider_dropdown.currentData()

        # Find the corresponding provider instance
        provider_instance = next(
            (
                provider
                for provider in self.app.providers
                if provider.internal_name == current_internal_name
            ),
            self.app.providers[0],
        )

        # Initial UI setup for the selected provider
        self.init_provider_ui(provider_instance, self.provider_container)

        # React to provider changes by rebuilding the UI and auto-saving
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)

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

        # Ensure window can receive keyboard events and maintain focus
        self.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.setFocus()

    def retranslate_ui(self) -> None:
        self.setWindowTitle(_("Settings"))

    def init_provider_ui(self, provider: "AIProvider", layout) -> None:
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
            logo_path = ui_utils.get_icon_path(
                self.app, f"provider_{provider.logo}", with_theme=False
            )
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
        self.provider_name_label = QLabel(provider.provider_name)
        self.provider_name_label.setStyleSheet(
            f"{self.app.styles['label_title']}; font-size: 18px;"
        )
        self.provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(self.provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

        # Provider description if available
        if provider.description:
            self.description_label = QLabel(provider.description)
            self.description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")
            self.description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(self.description_label)

        # Button container for multiple buttons
        if provider.button_text or (
            hasattr(provider, "additional_buttons") and provider.additional_buttons
        ):
            button_container = QHBoxLayout()
            button_container.setSpacing(10)

            # Main button
            if provider.button_text:
                self.main_button = QPushButton(provider.button_text)
                self.main_button.setStyleSheet(self.app.styles["primary_button"])
                self.main_button.clicked.connect(provider.button_action)
                button_container.addWidget(self.main_button)

            # Additional buttons
            if hasattr(provider, "additional_buttons"):
                for button_config in provider.additional_buttons:
                    additional_button = QPushButton(button_config["text"])

                    # Use appropriate style based on button type
                    if button_config.get("style") == "secondary":
                        additional_button.setStyleSheet(self.app.styles["secondary_button"])
                    else:
                        additional_button.setStyleSheet(self.app.styles["primary_button"])

                    additional_button.clicked.connect(button_config["action"])
                    button_container.addWidget(additional_button)

            # Center the button container
            button_widget = QWidget()
            button_widget.setLayout(button_container)
            self.current_provider_layout.addWidget(
                button_widget,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

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
            setting.set_value(saved_value)

            # immediate saving
            setting.set_auto_save_callback(self.save_current_provider_settings)

            # Each setting knows how to render itself to the layout
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

        # Prevent dropdown controls from interfering with main scroll area
        self.disable_dropdown_scroll(self.current_provider_layout)

        # Add italic comment about vision models
        # row_layout = QHBoxLayout()
        self.vision_comment = QLabel(_("* Models with vision support"))
        self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")
        layout.addWidget(self.vision_comment)
        self._logger.debug(f"init_provider_ui finished for provider: {provider.internal_name}")

    def save_current_provider_settings(self) -> None:
        """
        Save settings for the currently selected provider.
        Called when individual settings change.
        """
        if not self.app.current_provider:
            return

        # Save current provider's config
        self.app.current_provider.save_config()
        self._logger.debug(f"Saved settings for: {self.app.current_provider.internal_name}")

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
        self.close_button.setStyleSheet(self.app.styles["close_button"])

        # Connect button click to save_settings method for final processing and window closing
        self.close_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.close_button)
        main_layout.addWidget(button_container)

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
            print(f"🎛️\u00a0 SettingsWindow background theme change: {bg_icon} BG={theme}")
            # Use parent class method for theme change
            self.app.theme_manager.change_background_theme(theme)

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
            self._logger.debug(
                f"🎨 SettingsWindow color mode change: {theme_icon} Color={color_mode}"
            )

            # Apply theme change
            self.app.theme_manager.change_color_mode(color_mode)

            # Refresh UI styles with updated colorMode
            self.refresh_theme()

    def refresh_theme(self) -> None:
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update provider dropdown style
        if self.provider_dropdown:
            self.provider_dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update static labels directly
        if hasattr(self, "shortcut_label") and self.shortcut_label:
            self.shortcut_label.setStyleSheet(self.app.styles["label"])
        if hasattr(self, "theme_label") and self.theme_label:
            self.theme_label.setStyleSheet(self.app.styles["label"])
        if hasattr(self, "color_mode_label") and self.color_mode_label:
            self.color_mode_label.setStyleSheet(self.app.styles["label"])
        if hasattr(self, "provider_label") and self.provider_label:
            self.provider_label.setStyleSheet(self.app.styles["label"])

        # Update title label
        title_label = self.findChild(QLabel, "title_label")
        if title_label:
            title_label.setStyleSheet(self.app.styles["label_title"])

        # Update provider name and description labels directly if they exist
        if hasattr(self, "provider_name_label") and self.provider_name_label:
            self.provider_name_label.setStyleSheet(
                f"{self.app.styles['label_title']}; font-size: 18px;"
            )

        if hasattr(self, "description_label") and self.description_label:
            self.description_label.setStyleSheet(f"{self.app.styles['label']}; text-align: center;")
            self.description_label.setWordWrap(True)

        # Update other provider-specific labels by traversing the current provider layout only (avoids global search)
        if self.current_provider_layout:
            for i in range(self.current_provider_layout.count()):
                item = self.current_provider_layout.itemAt(i)
                if item and item.widget() and isinstance(item.widget(), QLabel):
                    widget = item.widget()
                    # Skip name and description
                    if widget == getattr(self, "provider_name_label", None) or widget == getattr(
                        self, "description_label", None
                    ):
                        continue
                    # Update field labels (e.g., "API Base URL")
                    if isinstance(widget, QLabel) and widget.text() and len(widget.text()) <= 50:
                        widget.setStyleSheet(self.app.styles["label"])

        # Update shortcut input if exists
        if self.shortcut_input:
            self.shortcut_input.setStyleSheet(self.app.styles["input"])

        # Update radio buttons if they exist
        if self.gradient_radio and self.plain_radio:
            radio_style = self.app.styles["radio"]
            self.gradient_radio.setStyleSheet(radio_style)
            self.plain_radio.setStyleSheet(radio_style)

        # Update checkbox if it exists
        if self.autostart_checkbox:
            self.autostart_checkbox.setStyleSheet(self.app.styles["checkbox"])

        # Update main button if exists
        if hasattr(self, "main_button") and self.main_button:
            self.main_button.setStyleSheet(self.app.styles["primary_button"])

        # Update vision comment if exists
        if hasattr(self, "vision_comment") and self.vision_comment:
            self.vision_comment.setStyleSheet(f"{self.app.styles['label']}; font-style: italic;")

        # Update provider buttons
        self._update_provider_buttons()

        # Update close button
        if hasattr(self, "close_button") and self.close_button:
            self.close_button.setStyleSheet(self.app.styles["close_button"])

        if self.app.systray_manager.tray_menu:
            self.app.systray_manager.apply_tray_menu_styles(self.app.systray_manager.tray_menu)

        # Refresh styles in the current provider if applicable (in aiprovider.py)
        if self.app.current_provider:
            self.app.current_provider.refresh_styles()

        # Refresh background theme
        super().refresh_theme()

    def _update_provider_buttons(self) -> None:
        """Update styles for all provider buttons when theme changes."""
        if not self.current_provider_layout:
            return

        def update_buttons_in_layout(layout):
            for i in range(layout.count()):
                item = layout.itemAt(i)
                if item.widget() and isinstance(item.widget(), QPushButton):
                    button = item.widget()
                    # Skip close button
                    if button == getattr(self, "close_button", None):
                        continue

                    # Determine button type and apply appropriate style
                    button_text = button.text().lower() if button.text() else ""

                    # Check if it's a secondary button (based on common patterns)
                    if any(
                        keyword in button_text
                        for keyword in ["cancel", "reset", "clear", "remove", "delete"]
                    ):
                        button.setStyleSheet(self.app.styles["secondary_button"])
                    else:
                        # Default to primary button style
                        button.setStyleSheet(self.app.styles["primary_button"])

                elif item.layout():
                    update_buttons_in_layout(item.layout())

        update_buttons_in_layout(self.current_provider_layout)

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

        self.save_current_provider_settings()

        # Re-register hotkey with new settings
        self.app.register_hotkey()
        # Exit providers_only mode after first save
        self.providers_only = False

    def _on_provider_changed(self) -> None:
        """
        Handle provider change: update UI and save automatically.
        """
        if not self.provider_dropdown:
            return

        current_internal_name = self.provider_dropdown.currentData()
        if not current_internal_name:
            return

        # Find the new provider
        new_provider = self._find_provider_by_name(current_internal_name)
        if not new_provider:
            self._logger.warning(f"Provider {current_internal_name} not found")
            return

        # Update the application
        self.app.current_provider = new_provider
        self.app.settings_manager.provider = current_internal_name

        # Reload config for the new provider
        provider_config = self.app.settings_manager.providers.get(current_internal_name, {})
        new_provider.load_config(provider_config)

        # Rebuild UI for the new provider
        self.init_provider_ui(new_provider, self.provider_container)

        self._logger.debug(f"Switched to provider: {current_internal_name}")

    def _find_provider_by_name(self, internal_name: str) -> "AIProvider | None":
        """Find a provider by its internal name."""
        return next(
            (
                provider
                for provider in self.app.providers
                if provider.internal_name == internal_name
            ),
            None,
        )

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """
        Handle window close event.
        Emits close signal for providers_only mode to notify parent about setup completion.
        """
        self._logger.debug(
            f"SettingsWindow closeEvent called, providers_only={self.providers_only}"
        )
        if self.providers_only:
            self._logger.debug("Emitting close_signal in providers_only mode")
            self.close_signal.emit()
        super().closeEvent(event)
        self.app.settings_window = None
        self._logger.debug("SettingsWindow closeEvent finished")
