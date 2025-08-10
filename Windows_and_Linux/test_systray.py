#!/usr/bin/env python3
"""
Test script to diagnose systray icon issues
"""
import os
import sys
import logging

# Add current directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from PySide6 import QtWidgets, QtGui, QtCore
except ImportError as e:
    logging.error(f"Failed to import PySide6: {e}")
    print("This script needs to be run from the virtual environment or as a compiled exe")
    sys.exit(1)

# Set up logging
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def get_icon_path(icon_name, with_theme=False):
    """Test version of get_icon_path function"""
    # Use sys.executable for frozen apps, sys.argv[0] for scripts
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
        logging.debug(f"Running as frozen app, base_dir: {base_dir}")
    else:
        base_dir = os.path.dirname(sys.argv[0])
        logging.debug(f"Running as script, base_dir: {base_dir}")

    # Define possible extensions and filenames
    extensions = [".png", ".ico"]  # PNG and ICO for systray
    filenames = [f"{icon_name}{ext}" for ext in extensions]

    # Try multiple locations
    base_paths = [
        os.path.join(base_dir, "icons"),  # Build location (dist/dev/icons/)
        os.path.join(base_dir, "config", "icons"),  # Dev location
    ]

    for base_path in base_paths:
        logging.debug(f"Checking base path: {base_path}")
        for filename in filenames:
            full_path = os.path.join(base_path, filename)
            logging.debug(f"Checking: {full_path}")
            if os.path.exists(full_path):
                logging.info(f"Found icon at: {full_path}")
                return full_path

    logging.error(f"Icon {icon_name} not found in any location")
    return None


class TestSystrayApp(QtWidgets.QApplication):
    def __init__(self, argv):
        super().__init__(argv)
        self.setQuitOnLastWindowClosed(False)

        # Test if systray is available
        if not QtWidgets.QSystemTrayIcon.isSystemTrayAvailable():
            logging.error("System tray is not available on this system")
            return

        logging.info("System tray is available")

        # Create systray icon
        self.create_tray_icon()

    def create_tray_icon(self):
        """Create test systray icon"""
        logging.info("Creating test systray icon...")

        # Get icon path
        icon_path = get_icon_path("app_icon")

        if icon_path and os.path.exists(icon_path):
            logging.info(f"Using icon: {icon_path}")
            icon = QtGui.QIcon(icon_path)
            self.tray_icon = QtWidgets.QSystemTrayIcon(icon, self)
        else:
            logging.warning("No icon found, using default")
            self.tray_icon = QtWidgets.QSystemTrayIcon(self)

        # Set tooltip
        self.tray_icon.setToolTip("Test Writing Tools")

        # Create menu
        menu = QtWidgets.QMenu()

        # Add test action
        test_action = menu.addAction("Test Action")
        test_action.triggered.connect(lambda: logging.info("Test action clicked"))

        # Add exit action
        exit_action = menu.addAction("Exit")
        exit_action.triggered.connect(self.quit)

        self.tray_icon.setContextMenu(menu)

        # Show the icon
        self.tray_icon.show()
        logging.info("Systray icon should now be visible")

        # Test if it's actually visible
        if self.tray_icon.isVisible():
            logging.info("Systray icon reports as visible")
        else:
            logging.warning("Systray icon reports as NOT visible")


def main():
    logging.info("Starting systray test...")
    logging.info(f"Python executable: {sys.executable}")
    logging.info(f"Script path: {sys.argv[0]}")
    logging.info(f"Current working directory: {os.getcwd()}")
    logging.info(f"Frozen: {getattr(sys, 'frozen', False)}")

    app = TestSystrayApp(sys.argv)

    # Run for 30 seconds then exit
    QtCore.QTimer.singleShot(30000, app.quit)

    logging.info("App starting, will run for 30 seconds...")
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
