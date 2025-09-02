import logging
import time
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtWidgets import QMenu, QSystemTrayIcon

from ui.ThemeManager import theme_manager
from ui.ui_utils import get_icon_path

if TYPE_CHECKING:
    from WritingToolApp import WritingToolApp


def _(x):
    return x


class SystrayManager:
    def __init__(self, app: "WritingToolApp"):
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.tray_icon = None
        self.tray_menu = None
        self.last_tray_click_time = 0
        self.tray_click_debounce_ms = 300
        self.toggle_action = None
        self.paused = False

    def create_tray_icon(self) -> None:
        """
        Create the system tray icon for the application.
        """
        if self.tray_icon:
            self._logger.debug("Tray icon already exists")
            return

        self._logger.debug("Creating system tray icon")

        # Check if system tray is available with retry mechanism for startup
        if not self._is_system_tray_available_with_retry():
            self._logger.error("System tray is not available on this system after retries")
            return

        icon_path = get_icon_path("app_icon", with_theme=False)
        self._logger.debug(f"Icon path resolved to: {icon_path}")

        if not icon_path.exists():
            self._logger.warning(f"Tray icon not found at {icon_path}")
            # Use a default icon if not found
            self.tray_icon = QSystemTrayIcon(self.app)
        else:
            self._logger.debug(f"Loading icon from: {icon_path}")
            icon = QtGui.QIcon(icon_path.as_posix())
            if icon.isNull():
                self._logger.warning(f"Failed to load icon from {icon_path}")
            self.tray_icon = QSystemTrayIcon(icon, self.app)
        # Set the tooltip (hover name) for the tray icon
        self.tray_icon.setToolTip("WritingTools")
        self.tray_menu = QMenu()

        self.tray_icon.setContextMenu(self.tray_menu)

        # Timer to prevent rapid successive clicks that could accidentally trigger menu items
        # This prevents the bug where rapid right-clicks open Settings accidentally
        self.last_tray_click_time = 0
        self.tray_click_debounce_ms = 300  # 300ms debounce period

        self.update_tray_menu()
        self.tray_icon.show()
        self._logger.debug("Tray icon show() called")

        # Verify if it's actually visible with retry
        self._verify_tray_icon_visibility()

        # Auto change context menu on theme change
        self.app.register_for_theme_changes()
        self._logger.debug("Tray icon setup completed")

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
        settings_action.triggered.connect(self.app.show_settings)

        # Pause/Resume toggle action
        self.toggle_action = self.tray_menu.addAction(_("Resume") if self.paused else _("Pause"))
        self.toggle_action.triggered.connect(self.toggle_paused)

        # About menu item
        about_action = self.tray_menu.addAction(_("About"))
        about_action.triggered.connect(self.app.show_about)

        help_action = self.tray_menu.addAction(_("Help"))
        help_action.triggered.connect(self.app.show_help)

        # Exit menu item
        exit_action = self.tray_menu.addAction(_("Exit"))
        exit_action.triggered.connect(self.app.exit_app)

    def toggle_paused(self) -> None:
        """Toggle the paused state of the application."""
        self._logger.debug("Toggle paused state")
        self.paused = not self.paused
        if self.toggle_action is not None:
            self.toggle_action.setText(_("Resume") if self.paused else _("Pause"))
        self._logger.debug("App is paused" if self.paused else "App is resumed")

    def apply_tray_menu_styles(self, menu) -> None:
        """
        Apply styles to the tray menu based on current color mode.
        """
        styles = theme_manager.get_styles()
        menu.setStyleSheet(styles.get("tray_menu", ""))

    def _is_system_tray_available_with_retry(
        self, max_retries: int = 5, delay_ms: int = 1000
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
        for attempt in range(max_retries):
            if QSystemTrayIcon.isSystemTrayAvailable():
                if attempt > 0:
                    self._logger.debug(f"System tray became available after {attempt + 1} attempts")
                return True

            if attempt < max_retries - 1:  # Don't wait after the last attempt
                self._logger.debug(
                    f"System tray not available, attempt {attempt + 1}/{max_retries}, retrying in {delay_ms}ms..."
                )
                QtCore.QTimer.singleShot(delay_ms, lambda: None)
                self.app.processEvents()  # Process pending events
                time.sleep(delay_ms / 1000.0)  # Convert to seconds

        self._logger.warning(f"System tray not available after {max_retries} attempts")
        return False

    def _verify_tray_icon_visibility(self, max_retries: int = 2, delay_ms: int = 250) -> None:
        """
        Verify that the tray icon is actually visible with retry mechanism.

        Args:
            max_retries: Maximum number of retry attempts
            delay_ms: Delay between retries in milliseconds
        """
        for attempt in range(max_retries):
            if self.tray_icon and self.tray_icon.isVisible():
                self._logger.debug(f"Tray icon confirmed visible after {attempt + 1} attempts")
                return

            if attempt < max_retries - 1:  # Don't wait after the last attempt
                self._logger.debug(
                    f"Tray icon not visible, attempt {attempt + 1}/{max_retries}, retrying..."
                )
                QtCore.QTimer.singleShot(delay_ms, lambda: None)
                self.app.processEvents()  # Process pending events
                time.sleep(delay_ms / 1000.0)  # Convert to seconds
                if self.tray_icon:
                    self.tray_icon.show()  # Try showing again

        if self.tray_icon and not self.tray_icon.isVisible():
            self._logger.warning("Tray icon reports as NOT visible after retries")
        else:
            self._logger.debug("Tray icon visibility verification completed")
