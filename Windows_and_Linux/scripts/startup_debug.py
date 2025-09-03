#!/usr/bin/env python3
"""
Writing Tools - Startup Debug Script

This script captures detailed startup logs to diagnose systray issues at boot.
Useful for debugging when the application starts but the systray icon doesn't appear.

Usage:
    python scripts/startup_debug.py

The script will:
1. Launch Writing Tools with detailed logging
2. Monitor systray icon creation and visibility
3. Save logs to startup_logs/ directory
4. Display real-time status in console

When to use:
- Application launches but systray icon is missing
- Silent startup failures
- Boot-time systray issues
- Need detailed startup diagnostics
"""

import logging
import os
import sys
import time
import traceback
from datetime import datetime


# Detailed logging configuration
def setup_detailed_logging() -> tuple[logging.Logger, str]:
    """Configure very detailed logging for startup debugging"""

    # Create logs directory if it doesn't exist
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_logs")
    os.makedirs(log_dir, exist_ok=True)

    # Log file name with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"startup_debug_{timestamp}.log")

    # Logging configuration
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[
            logging.FileHandler(log_file, encoding="utf-8"),
            logging.StreamHandler(sys.stdout),
        ],
    )

    # Log system information at startup
    logger = logging.getLogger("STARTUP_DEBUG")
    logger.debug("=" * 80)
    logger.debug("WRITING TOOLS - STARTUP DEBUG SESSION")
    logger.debug("=" * 80)
    logger.debug(f"Log file: {log_file}")
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Python executable: {sys.executable}")
    logger.debug(f"Script path: {sys.argv[0]}")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Frozen: {getattr(sys, 'frozen', False)}")

    if getattr(sys, "frozen", False):
        logger.debug(f"Executable path: {sys.executable}")
        logger.debug(f"Base directory: {os.path.dirname(sys.executable)}")

    # Windows environment information
    try:
        import platform

        logger.debug(f"Platform: {platform.platform()}")
        logger.debug(f"Machine: {platform.machine()}")
        logger.debug(f"Processor: {platform.processor()}")
    except Exception as e:
        logger.error(f"Error getting platform info: {e}")

    # Important environment variables
    env_vars = ["PATH", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP"]
    for var in env_vars:
        value = os.environ.get(var, "NOT_SET")
        logger.debug(f"ENV {var}: {value}")

    return logger, log_file


def log_systray_environment() -> bool:
    """Log the state of the systray environment"""
    logger = logging.getLogger("SYSTRAY_ENV")

    try:
        # Import PySide6 and check availability
        logger.debug("Importing PySide6...")
        from PySide6 import QtGui, QtWidgets

        logger.debug("PySide6 imported successfully")

        # Create a temporary application to test systray
        logger.debug("Creating temporary QApplication...")
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
            logger.debug("New QApplication created")
        else:
            logger.debug("Using existing QApplication instance")

        # Test systray availability
        logger.debug("Testing system tray availability...")
        systray_available = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
        logger.debug(f"System tray available: {systray_available}")

        # Screen information
        logger.debug("Screen information:")
        screens = QtGui.QGuiApplication.screens()
        logger.debug(f"Number of screens: {len(screens)}")
        for i, screen in enumerate(screens):
            logger.debug(f"Screen {i}: {screen.name()} - {screen.geometry()}")

        # Test creation of systray icon
        if systray_available:
            logger.debug("Attempting to create test system tray icon...")
            try:
                test_icon = QtWidgets.QSystemTrayIcon()
                test_icon.setToolTip("Writing Tools Debug Test")
                test_icon.show()

                # Check if it's visible
                time.sleep(0.5)  # Small delay
                is_visible = test_icon.isVisible()
                logger.debug(f"Test tray icon visible: {is_visible}")

                test_icon.hide()
                logger.debug("Test tray icon cleaned up")

            except Exception as e:
                logger.error(f"Error creating test tray icon: {e}")
                logger.error(traceback.format_exc())

        return True

    except Exception as e:
        logger.error(f"Error in systray environment check: {e}")
        logger.error(traceback.format_exc())
        return False


def find_project_python() -> str:
    """Find the correct Python executable for the project"""
    logger = logging.getLogger("PYTHON_FINDER")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Possible paths for virtual environment
    possible_venv_paths = [
        os.path.join(script_dir, "Windows_and_Linux", "myvenv", "Scripts", "python.exe"),
        os.path.join(script_dir, "Windows_and_Linux", "venv", "Scripts", "python.exe"),
        os.path.join(script_dir, "Windows_and_Linux", ".venv", "Scripts", "python.exe"),
        os.path.join(script_dir, "myvenv", "Scripts", "python.exe"),
        os.path.join(script_dir, "venv", "Scripts", "python.exe"),
        os.path.join(script_dir, ".venv", "Scripts", "python.exe"),
    ]

    # Test each path
    for venv_path in possible_venv_paths:
        if os.path.exists(venv_path):
            logger.debug(f"Found virtual environment Python: {venv_path}")
            return venv_path

    # Fallback to system Python
    logger.warning("No virtual environment found, using system Python")
    return sys.executable


def main():
    """Main debug script function"""

    # Setup detailed logging
    logger, log_file = setup_detailed_logging()

    try:
        logger.debug("Starting Writing Tools startup debug...")

        # Find the correct Python
        project_python = find_project_python()
        logger.debug(f"Using Python: {project_python}")

        # If we are not using the correct Python, relaunch with it
        if project_python != sys.executable and os.path.exists(project_python):
            logger.debug("Relaunching with project Python environment...")
            import subprocess

            script_path = os.path.abspath(__file__)
            result = subprocess.run([project_python, script_path], capture_output=True, text=True)

            logger.debug(f"Subprocess exit code: {result.returncode}")
            if result.stdout:
                logger.debug(f"Subprocess stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Subprocess stderr:\n{result.stderr}")

            return result.returncode

        # Log systray environment
        logger.debug("Checking systray environment...")
        systray_ok = log_systray_environment()

        if not systray_ok:
            logger.error("Systray environment check failed!")
            return 1

        # Now launch the main application
        logger.debug("Launching main Writing Tools application...")

        # Add Windows_and_Linux directory to path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        windows_linux_dir = os.path.join(script_dir, "Windows_and_Linux")
        if os.path.exists(windows_linux_dir):
            sys.path.insert(0, windows_linux_dir)
            logger.debug(f"Added to path: {windows_linux_dir}")

        # Clean up temporary application before creating WritingToolApp
        logger.debug("Cleaning up temporary QApplication...")
        from PySide6 import QtWidgets

        temp_app = QtWidgets.QApplication.instance()
        if temp_app:
            temp_app.quit()
            temp_app = None

        # Import and launch the application
        from WritingToolApp import WritingToolApp

        logger.debug("Creating WritingToolApp instance...")
        app = WritingToolApp(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Log the application state after creation
        logger.debug(f"App created. Tray icon exists: {app.tray_icon is not None}")
        if app.tray_icon:
            logger.debug(f"Tray icon visible: {app.tray_icon.isVisible()}")

        # Wait a bit to see if systray appears
        logger.debug("Waiting 10 seconds to monitor tray icon status...")
        for i in range(10):
            time.sleep(1)
            if app.tray_icon:
                visible = app.tray_icon.isVisible()
                logger.debug(f"Second {i + 1}: Tray icon visible = {visible}")

                # Log icon details
                if hasattr(app.tray_icon, "icon") and not app.tray_icon.icon().isNull():
                    logger.debug(f"Second {i + 1}: Icon is set and valid")
                else:
                    logger.warning(f"Second {i + 1}: Icon is null or not set")
            else:
                logger.debug(f"Second {i + 1}: No tray icon object")

        logger.debug("Debug session completed successfully")
        logger.debug(f"Full log saved to: {log_file}")

        # Keep the application open for observation
        logger.debug("Application will remain running for observation...")
        return app.exec()

    except Exception as e:
        logger.error(f"Critical error in startup debug: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
