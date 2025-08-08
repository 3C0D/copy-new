"""
vérifier/comparer logic scrolling avec About window
étendre l'autostart à linux

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
        self.providers_only = providers_only
        self.gradient_radio = None
        self.plain_radio = None
        self.provider_dropdown = None
        self.provider_container = None
        self.autostart_checkbox = None
        self.shortcut_input = None
        self.previous_window = None
        self.init_ui()
        self.retranslate_ui()

    def init_ui(self):
        """
        Initialize the user interface for the settings window.
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        # Set the exact width we want (650px) as both minimum and default
        self.setMinimumWidth(650)
        self.setFixedWidth(650)  # This makes the width non-resizable

        # Set window flags to stay on top and maintain focus
        self.setWindowFlags(
            QtCore.Qt.WindowType.Window
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
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

        # Style the scroll area for transparency and proper scroll behavior
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

        # Create scroll content widget
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QtWidgets.QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        if not self.providers_only:
            title_label = QtWidgets.QLabel(_("Settings"))
            title_label.setStyleSheet(
                f"font-size: 24px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Add autostart checkbox for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QtWidgets.QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(
                    f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
                )
                self.autostart_checkbox.setChecked(AutostartManager.check_autostart())
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Add shortcut key input
            shortcut_label = QtWidgets.QLabel(_("Shortcut Key:"))
            shortcut_label.setStyleSheet(
                f"font-size: 16px; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
            )
            content_layout.addWidget(shortcut_label)

            self.shortcut_input = QtWidgets.QLineEdit(
                self.app.settings_manager.settings.system.get("hotkey, 'ctrl+space'"),
            )
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

            # Add theme selection
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
            current_theme = self.app.settings_manager.settings.system.get("theme", "dark")
            self.gradient_radio.setChecked(current_theme == "gradient")
            self.plain_radio.setChecked(current_theme == "plain")
            # Auto-save when theme changes
            self.gradient_radio.toggled.connect(self.auto_save_theme)
            self.plain_radio.toggled.connect(self.auto_save_theme)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

        # Add provider selection
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
        # Disable wheel events on dropdown to prevent scroll interference
        self.provider_dropdown.wheelEvent = lambda e: e.ignore()

        current_provider = self.app.settings_manager.settings.system.get("provider", "gemini")

        # Populate dropdown with display names but store internal names as data
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

        # Add horizontal separator
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

        # Connect provider dropdown
        self.provider_dropdown.currentIndexChanged.connect(self._on_provider_changed)

        # Add horizontal separator
        line = QtWidgets.QFrame()
        line.setFrameShape(QtWidgets.QFrame.Shape.HLine)
        line.setFrameShadow(QtWidgets.QFrame.Shadow.Sunken)
        content_layout.addWidget(line)

        # Set up scroll area with content
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

        # Only add close button to title bar if NOT in providers_only mode
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
        """
        if self.current_provider_layout:
            self.current_provider_layout.setParent(None)
            ui_utils.clear_layout(self.current_provider_layout)
            self.current_provider_layout.deleteLater()

        self.current_provider_layout = QtWidgets.QVBoxLayout()

        # Create a horizontal layout for the logo and provider name
        provider_header_layout = QtWidgets.QHBoxLayout()
        provider_header_layout.setSpacing(10)
        provider_header_layout.setAlignment(QtCore.Qt.AlignmentFlag.AlignCenter)

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

        provider_name_label = QtWidgets.QLabel(provider.provider_name)
        provider_name_label.setStyleSheet(
            f"font-size: 18px; font-weight: bold; color: {'#ffffff' if colorMode == 'dark' else '#333333'};",
        )
        provider_name_label.setAlignment(QtCore.Qt.AlignmentFlag.AlignVCenter)
        provider_header_layout.addWidget(provider_name_label)

        self.current_provider_layout.addLayout(provider_header_layout)

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
        if not self.app.settings_manager.settings.custom_data:
            self.app.settings_manager.settings.custom_data = {}
        if "providers" not in self.app.settings_manager.settings.custom_data:
            self.app.settings_manager.settings.custom_data["providers"] = {}
        if provider.internal_name not in self.app.settings_manager.settings.custom_data["providers"]:
            self.app.settings_manager.settings.custom_data["providers"][provider.internal_name] = {}

        # Add provider settings
        for setting in provider.settings:
            saved_value = self.app.settings_manager.settings.custom_data["providers"][provider.internal_name].get(
                setting.name,
                setting.default_value,
            )
            setting.set_value(saved_value)
            setting.render_to_layout(self.current_provider_layout)

        layout.addLayout(self.current_provider_layout)

        # Disable wheel events on provider setting dropdowns
        self.disable_dropdown_scroll(self.current_provider_layout)

    def disable_dropdown_scroll(self, layout):
        """
        Recursively disable wheel events on all QComboBox widgets in the layout
        to prevent them from interfering with the main scroll area.
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
        # Ensure the window gets focus when shown
        self.raise_()
        self.activateWindow()
        self.setFocus()

    def focusOutEvent(self, event):
        """Handle focus out event - allow dropdowns to work properly."""
        super().focusOutEvent(event)
        # Don't regain focus immediately - this interferes with dropdowns
        # Only regain focus if we lose it to something outside our window
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget and not self.isAncestorOf(focused_widget):
            # Only regain focus after a longer delay and only if no dropdown is open
            QtCore.QTimer.singleShot(500, self.regain_focus_if_needed)

    def regain_focus_if_needed(self):
        """Regain focus only if needed and no dropdown is open."""
        if not self.isVisible():
            return

        # Check if any dropdown is currently open
        focused_widget = QtWidgets.QApplication.focusWidget()
        if focused_widget and isinstance(focused_widget, QtWidgets.QComboBox):
            return  # Don't steal focus from dropdown

        # Check if any dropdown popup is open
        for widget in QtWidgets.QApplication.allWidgets():
            if isinstance(widget, QtWidgets.QComboBox) and widget.view().isVisible():
                return  # Don't steal focus when dropdown is open

        # Only regain focus if we really lost it to something external
        if not self.hasFocus() and not self.isAncestorOf(
            QtWidgets.QApplication.focusWidget(),
        ):
            self.raise_()
            self.activateWindow()

    def add_save_button(self, main_layout):
        """Add a save/complete setup button at the bottom of the window."""
        from ui.ui_utils import colorMode

        # Create button container
        button_container = QWidget()
        button_layout = QtWidgets.QHBoxLayout(button_container)
        button_layout.setContentsMargins(20, 10, 20, 20)

        # Add spacer to push button to the right
        button_layout.addStretch()

        # Create save button
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
        """Add a close button to the top-right corner of the window."""
        from ui.ui_utils import get_icon_path

        self.close_button = QtWidgets.QPushButton(self)
        self.close_button.setFixedSize(24, 24)

        # Try to load close icon
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

        # Position the button in the top-right corner
        self.close_button.move(self.width() - 30, 6)
        self.close_button.clicked.connect(self.close_to_previous_window)
        self.close_button.setToolTip(_("Close Settings"))

    def resizeEvent(self, event):
        """Handle window resize to reposition close button."""
        super().resizeEvent(event)
        if hasattr(self, "close_button"):
            self.close_button.move(self.width() - 30, 6)

    def auto_save_shortcut(self):
        """Auto-save shortcut when it changes."""
        if hasattr(self, "shortcut_input") and self.shortcut_input is not None and not self.providers_only:
            self.app.settings_manager.update_system_setting(
                "hotkey",
                self.shortcut_input.text(),
            )
            self.app.register_hotkey()

    def auto_save_theme(self):
        """Auto-save theme when it changes."""
        if hasattr(self, "gradient_radio") and self.gradient_radio is not None and not self.providers_only:
            theme = "gradient" if self.gradient_radio.isChecked() else "plain"
            self.app.settings_manager.update_system_setting("theme", theme)

    @staticmethod
    def toggle_autostart(state):
        """Toggle the autostart setting."""
        AutostartManager.set_autostart(state == 2)

    def save_settings(self):
        """Save the current settings and close window."""
        self.save_settings_without_closing()
        self.close()

    def keyPressEvent(self, event):
        """Handle key press events."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close_to_previous_window()
        else:
            super().keyPressEvent(event)

    def close_to_previous_window(self):
        """Close settings and return to previous window if available."""
        # Save settings before closing (same as Save & Close button)
        self.save_settings_without_closing()

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
        """Save settings without closing the window."""
        if not self.providers_only:
            if hasattr(self, "shortcut_input") and self.shortcut_input is not None:
                self.app.settings_manager.update_system_setting(
                    "hotkey",
                    self.shortcut_input.text(),
                )
            if hasattr(self, "gradient_radio") and self.gradient_radio is not None:
                theme = "gradient" if self.gradient_radio.isChecked() else "plain"
                self.app.settings_manager.update_system_setting("theme", theme)
        else:
            self.app.create_tray_icon()

        # Save provider selection - use internal name from dropdown data
        if hasattr(self, "provider_dropdown") and self.provider_dropdown is not None:
            provider_internal_name = self.provider_dropdown.currentData()
            self.app.settings_manager.update_system_setting("provider", provider_internal_name)

        # Find the provider instance by internal name
        selected_provider = next(
            (provider for provider in self.app.providers if provider.internal_name == provider_internal_name),
            self.app.providers[0],
        )

        # Save provider-specific config
        selected_provider.save_config()

        # Update current provider
        self.app.current_provider = selected_provider

        # Load provider config
        provider_config = self.app._get_provider_config(provider_internal_name)
        self.app.current_provider.load_config(provider_config)

        self.app.register_hotkey()
        self.providers_only = False

    def _on_provider_changed(self):
        """Handle provider dropdown change."""
        current_internal_name = self.provider_dropdown.currentData()
        provider_instance = next(
            (provider for provider in self.app.providers if provider.internal_name == current_internal_name),
            self.app.providers[0],
        )
        self.init_provider_ui(provider_instance, self.provider_container)

    def closeEvent(self, event):
        """Handle window close event."""
        if self.providers_only:
            self.close_signal.emit()
        super().closeEvent(event)
