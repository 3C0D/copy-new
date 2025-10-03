import logging
import time
from typing import TYPE_CHECKING, Optional

from PySide6 import QtGui
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from .autostart_manager import AutostartManager
from .ui import about_window, help_window
from .ui.SettingsWindow.settings_window import SettingsWindow
from .ui.ui_utils import ui_utils

if TYPE_CHECKING:
    from .writing_tools_app import WritingToolsApp


# Placeholder for future i18n (internationalization)
def _(x):
    return x


class SystrayManager:
    # Constants for retry mechanisms
    DEFAULT_MAX_RETRIES = 5
    DEFAULT_RETRY_DELAY_MS = 1000
    TRAY_VISIBILITY_MAX_RETRIES = 2
    TRAY_VISIBILITY_RETRY_DELAY_MS = 250

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.tray_icon = None
        self.tray_menu = None
        self.toggle_action = None
        self.autostart_action = None
        self.paused = False
        self.about_window = None
        self.help_window = None
        self.settings_window = None

    def create_tray_icon(self) -> None:
        """
        Create the system tray icon for the application.
        """
        if self.tray_icon and self.tray_icon.isVisible():
            self._logger.debug("Tray icon already exists and is visible")
            return

        self._logger.debug("Creating system tray icon")

        # Check if system tray is available with retry mechanism for startup
        if not self._is_system_tray_available_with_retry():
            self._logger.error("System tray is not available on this system after retries")
            return

        icon_path = ui_utils.get_icon_path(self.app, "app_icon", with_theme=False)

        if not icon_path.exists():
            self._logger.warning(f"Tray icon not found at {icon_path}")
            # Use a default icon if not found
            self.tray_icon = QSystemTrayIcon(self.app)
        else:
            icon = QtGui.QIcon(icon_path.as_posix())
            if icon.isNull():
                self._logger.warning(f"Failed to load icon from {icon_path}")
            self.tray_icon = QSystemTrayIcon(icon, self.app)
        # Set the tooltip (hover name) for the tray icon
        self.tray_icon.setToolTip("WritingTools")
        self.tray_menu = QMenu()

        self.tray_icon.setContextMenu(self.tray_menu)

        self.update_tray_menu()
        self.tray_icon.show()

        # Verify if it's actually visible with retry
        self._verify_tray_icon_visibility()

        self._logger.info("Tray icon setup completed")

    def update_tray_menu(self) -> None:
        """
        Update the tray menu with all menu items, including pause functionality
        and proper translations.
        """
        if self.tray_menu is None:
            return

        self.tray_menu.clear()

        # Apply styles using the current color mode
        self.apply_tray_menu_styles(self.tray_menu)

        # Settings menu item
        settings_action = self.tray_menu.addAction(_("Settings"))
        settings_action.triggered.connect(lambda: self.app.ui_manager.show_settings)

        # Start on boot menu item
        self.autostart_action = self.tray_menu.addAction(_("Start on boot"))
        self.autostart_action.setCheckable(True)
        self.autostart_action.setChecked(self.app.settings_manager.start_on_boot)
        self.autostart_action.triggered.connect(self._on_autostart_changed)

        # Pause/Resume toggle action
        self.toggle_action = self.tray_menu.addAction(_("Resume") if self.paused else _("Pause"))
        self.toggle_action.triggered.connect(self.toggle_paused)

        # About menu item
        about_action = self.tray_menu.addAction(_("About"))
        about_action.triggered.connect(self.show_about)

        help_action = self.tray_menu.addAction(_("Help"))
        help_action.triggered.connect(self.show_help)

        # Exit menu item
        exit_action = self.tray_menu.addAction(_("Exit"))
        exit_action.triggered.connect(self.app.lifecycle_manager.exit_app)

    def show_about(self) -> None:
        """
        Show the about window.
        """
        self._logger.debug("Showing about window")
        self._show_window("about_window", about_window.AboutWindow, "help_window")

    def show_help(self) -> None:
        """
        Show the help window.
        """
        self._logger.debug("Showing help window")
        self._show_window("help_window", help_window.HelpWindow, "about_window")

    def show_settings(self) -> None:
        """
        Show the settings window.
        Unlike other windows, this doesn't close other windows since settings
        should remain open to see interface changes effects.
        """
        self._logger.debug("Showing settings window")
        self._show_window("settings_window", SettingsWindow, None)
        # Apply retranslate_ui for settings window specifically
        if self.settings_window:
            self.settings_window.retranslate_ui()

    def toggle_paused(self) -> None:
        """Toggle the paused state of the application."""
        self._logger.debug("Toggle paused state")
        self.paused = not self.paused
        if self.toggle_action is not None:
            self.toggle_action.setText(_("Resume") if self.paused else _("Pause"))
        self._logger.debug("App is paused" if self.paused else "App is resumed")

    def _show_window(
        self, window_attr: str, window_class, other_window_attr: Optional[str] = None
    ) -> None:
        """Generic method to show a window and optionally close another."""
        if other_window_attr:
            other_window = getattr(self, other_window_attr, None)
            if other_window:
                other_window.close()

        window = getattr(self, window_attr, None)
        if not window:
            window = window_class(self.app)
            setattr(self, window_attr, window)
            window.show()
        else:
            ui_utils.existing_window_on_top(window)

    def _update_settings_checkbox(self, enable: bool) -> None:
        """Update the autostart checkbox in settings window if open."""
        settings_window = self.settings_window
        if not settings_window:
            return

        general_settings = getattr(settings_window, "general_settings", None)
        if not general_settings:
            return

        checkbox = getattr(general_settings, "autostart_checkbox", None)
        if checkbox:
            checkbox.setChecked(enable)

    def _on_autostart_changed(self) -> None:
        """Handle autostart toggle from systray menu."""
        if self.autostart_action is None:
            return
        enable = self.autostart_action.isChecked()
        AutostartManager.set_autostart_with_sync(enable, self.app.settings_manager)
        self._logger.debug(f"Autostart changed from systray: {enable}")

        # Update settings checkbox state if settings window is open
        self._update_settings_checkbox(enable)

    def apply_tray_menu_styles(self, menu) -> None:
        """
        Apply styles to the tray menu based on current color mode.
        """
        styles = self.app.theme_manager.get_styles()
        menu.setStyleSheet(styles.get("tray_menu", ""))

    def _retry_with_delay(
        self,
        check_func,
        max_retries: int = DEFAULT_MAX_RETRIES,
        delay_ms: int = DEFAULT_RETRY_DELAY_MS,
        operation_name: str = "operation",
    ) -> bool:
        """Generic retry mechanism with delay."""
        for attempt in range(max_retries):
            if check_func():
                if attempt > 0:
                    self._logger.debug(f"{operation_name} succeeded after {attempt + 1} attempts")
                return True

            if attempt < max_retries - 1:
                self._logger.debug(
                    f"{operation_name} failed, attempt {attempt + 1}/{max_retries}, retrying in {delay_ms}ms..."
                )
                self.app.processEvents()
                time.sleep(delay_ms / 1000.0)

        self._logger.warning(f"{operation_name} failed after {max_retries} attempts")
        return False

    def _is_system_tray_available_with_retry(
        self, max_retries: int = DEFAULT_MAX_RETRIES, delay_ms: int = DEFAULT_RETRY_DELAY_MS
    ) -> bool:
        """
        Check if system tray is available with retry mechanism.
        This is especially important during Windows startup when the system tray
        might not be immediately available.

        Args:
            max_retries: Maximum number of retry attempts
            delay_ms: Delay between retries in milliseconds

        Returns:
            bool: True if system tray becomes available, False otherwise
        """
        return self._retry_with_delay(
            check_func=QSystemTrayIcon.isSystemTrayAvailable,
            max_retries=max_retries,
            delay_ms=delay_ms,
            operation_name="System tray availability check",
        )

    def _verify_tray_icon_visibility(
        self,
        max_retries: int = TRAY_VISIBILITY_MAX_RETRIES,
        delay_ms: int = TRAY_VISIBILITY_RETRY_DELAY_MS,
    ) -> None:
        """
        Verify that the tray icon is actually visible with retry mechanism.

        Args:
            max_retries: Maximum number of retry attempts
            delay_ms: Delay between retries in milliseconds
        """

        def check_visibility():
            return self.tray_icon and self.tray_icon.isVisible()

        success = self._retry_with_delay(
            check_func=check_visibility,
            max_retries=max_retries,
            delay_ms=delay_ms,
            operation_name="Tray icon visibility check",
        )

        if not success and self.tray_icon:
            self._logger.warning("Tray icon reports as NOT visible after retries")
            self.tray_icon.show()  # Try showing again as last attempt
        elif success:
            self._logger.debug("Tray icon visibility verification completed")
