"""
Page totalement revue et commentée.
vérifier/comparer logic scrolling avec About window
étendre l'autostart à linux
L285   No sure about that:      # Add save button (especially important for providers_only mode)
        self.add_save_button(main_layout)

"""

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
from ui.ui_utils import ThemedWidget, colorMode, ui_utils

_ = lambda x: x


class SettingsWindow(ThemedWidget):
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
        self.provider_dropdown = None
        self.provider_container = None
        self.autostart_checkbox = None
        self.shortcut_input = None
        # Reference to previous window to return to after closing
        self.previous_window = None
        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        """
        Initialize the user interface for the settings window.
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        # Fixed width to maintain consistent layout
        self.setMinimumWidth(650)
        self.setFixedWidth(650)

        # Window configuration to stay on top and maintain focus
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint  # useful when user needs to retrieve API keys...
            | QtCore.Qt.WindowType.WindowTitleHint,
        )

        main_layout = QtWidgets.QVBoxLayout(self.background)  # Set icon, margin, and spacing in ThemedWidget

        # Earlier scroll_area and scroll_content creation moved up
        # Create scroll area
        scroll_area = QScrollArea()
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
            title_label.setStyleSheet(
                f"font-size: 24px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Autostart functionality only for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QtWidgets.QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(
                    f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
                )
                self.autostart_checkbox.setChecked(AutostartManager.check_autostart())
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Global hotkey configuration
            shortcut_label = QtWidgets.QLabel(_("Shortcut Key:"))
            shortcut_label.setStyleSheet(
                f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            content_layout.addWidget(shortcut_label)

            self.shortcut_input = QtWidgets.QLineEdit(self.app.settings_manager.hotkey or 'ctrl+space')
            self.shortcut_input.setStyleSheet(
                f"""
                font-size: 16px;
                padding: 5px;
                background-color: {'#444' if colorMode == 'dark' else 'white'};
                color: {'#ffffff' if colorMode == 'dark' else '#000000'};
                border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
            """,
            )
            # Auto-save when shortcut changes
            self.shortcut_input.textChanged.connect(self.auto_save_shortcut)
            content_layout.addWidget(self.shortcut_input)

            # Background theme selection
            theme_label = QtWidgets.QLabel(_("Background Theme:"))
            theme_label.setStyleSheet(
                f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            content_layout.addWidget(theme_label)

            theme_layout = QHBoxLayout()
            self.gradient_radio = QRadioButton(_("Blurry Gradient"))
            self.plain_radio = QRadioButton(_("Plain"))
            self.gradient_radio.setStyleSheet(
                f"color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            self.plain_radio.setStyleSheet(
                f"color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            current_theme = self.app.settings_manager.theme or "gradient"
            self.gradient_radio.setChecked(current_theme == "gradient")
            self.plain_radio.setChecked(current_theme == "plain")
            # Auto-save theme changes for immediate visual feedback
            self.gradient_radio.toggled.connect(self.auto_save_theme)
            self.plain_radio.toggled.connect(self.auto_save_theme)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

        # AI Provider selection section
        provider_label = QtWidgets.QLabel(_("Choose AI Provider:"))
        provider_label.setStyleSheet(
            f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
        )
        content_layout.addWidget(provider_label)

        self.provider_dropdown = QtWidgets.QComboBox()
        self.provider_dropdown.setStyleSheet(
            f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if colorMode == 'dark' else 'white'};
            color: {'#ffffff' if colorMode == 'dark' else '#000000'};
            border: 1px solid {'#666' if colorMode == 'dark' else '#ccc'};
        """,
        )
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

        # React to provider changes by rebuilding the UI
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)

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
            800,
            max_height,
        )  # Cap at 800px or 85% of screen height (increased from 720px)
        self.resize(
            650,
            desired_height,
        )  # Use an exact width of 650px (increased from 592px) so stuff looks good!

        # Close button only in full settings mode, not in providers_only setup
        if not self.providers_only:
            self.add_close_button()

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
            self.current_provider_layout.setParent(None)
            ui_utils.clear_layout(self.current_provider_layout)
            self.current_provider_layout.deleteLater()

        self.current_provider_layout = QtWidgets.QVBoxLayout()

        # Provider header with logo and name
        provider_header_layout = QtWidgets.QHBoxLayout()
        provider_header_layout.setSpacing(10)
        provider_header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

        # Load and display provider logo if available
        if provider.logo:
            logo_path = os.path.join(
                os.path.dirname(sys.argv[0]),
                "icons",
                f"provider_{provider.logo}.png",
            )
            if os.path.exists(logo_path):
                targetPixmap = ui_utils.resize_and_round_image(
                    QImage(logo_path),
                    30,
                    15,
                )
                logo_label = QtWidgets.QLabel()
                logo_label.setPixmap(targetPixmap)
                logo_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
                provider_header_layout.addWidget(logo_label)

        # Provider name display
        provider_name_label = QtWidgets.QLabel(provider.provider_name)
        provider_name_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
        )
        provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

        # Provider description if available
        if provider.description:
            description_label = QtWidgets.QLabel(provider.description)
            description_label.setStyleSheet(
                f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'}; text-align: center;",
            )
            description_label.setWordWrap(True)
            self.current_provider_layout.addWidget(description_label)

        # Original single button logic
        if provider.button_text:
            button = QtWidgets.QPushButton(provider.button_text)
            button.setStyleSheet(
                f"""
                    QPushButton {{
                        background-color: {'#4CAF50' if colorMode == 'dark' else '#008CBA'};
                        color: white;
                        padding: 10px;
                        font-size: 16px;
                        border: none;
                        border-radius: 5px;
                    }}
                    QPushButton:hover {{
                        background-color: {'#45a049' if colorMode == 'dark' else '#007095'};
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
        from ui.ui_utils import colorMode

        button_container = QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)

        # Right-align the button
        button_layout.addStretch()

        # Different text for setup vs settings mode
        if self.providers_only:
            button_text = _("Complete Setup")
        else:
            button_text = _("Save Settings")

        self.save_button = QtWidgets.QPushButton(button_text)
        self.save_button.setFixedSize(150, 40)
        self.save_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: {'#0078d4' if colorMode == 'light' else '#106ebe'};
                color: white;
                border: none;
                border-radius: 6px;
                font-size: 14px;
                font-weight: bold;
                padding: 8px 16px;
            }}
            QPushButton:hover {{
                background-color: {'#106ebe' if colorMode == 'light' else '#1e88e5'};
            }}
            QPushButton:pressed {{
                background-color: {'#005a9e' if colorMode == 'light' else '#0d47a1'};
            }}
        """,
        )

        # Connect button to save function
        self.save_button.clicked.connect(self.save_settings)
        button_layout.addWidget(self.save_button)
        main_layout.addWidget(button_container)

    def add_close_button(self):
        """
        Add a close button to the top-right corner of the window.
        Only shown in full settings mode, not during initial setup.
        """
        from ui.ui_utils import get_icon_path

        self.close_button = QtWidgets.QPushButton(self)
        self.close_button.setFixedSize(24, 24)

        # Try to load themed close icon, fallback to text
        close_icon_path = get_icon_path("close", with_theme=True)
        if os.path.exists(close_icon_path):
            self.close_button.setIcon(QtGui.QIcon(close_icon_path))
        else:
            self.close_button.setText("×")

        self.close_button.setStyleSheet(
            f"""
            QPushButton {{
                background-color: transparent;
                border: none;
                border-radius: 12px;
                color: {'#ffffff' if colorMode == 'dark' else '#333333'};
                font-size: 16px;
                font-weight: bold;
            }}
            QPushButton:hover {{
                background-color: {'#ff4444' if colorMode == 'dark' else '#ff6666'};
                color: white;
            }}
        """,
        )

        # Position in top-right corner
        self.close_button.move(self.width() - 30, 6)
        self.close_button.clicked.connect(self.close_to_previous_window)
        self.close_button.setToolTip(_("Close Settings"))

    def resizeEvent(self, event):
        """Handle window resize to reposition close button."""
        super().resizeEvent(event)
        if hasattr(self, "close_button"):
            self.close_button.move(self.width() - 30, 6)

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

    @staticmethod
    def toggle_autostart(state):
        """Toggle the autostart setting based on checkbox state."""
        AutostartManager.set_autostart(state == 2)

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
        self.app.current_provider.load_config(provider_config)

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
