#!/usr/bin/env python3
"""
Writing Tools - Development Launcher
Cross-platform development environment setup and launcher with optional verbose debugging
"""

import logging
import os
import subprocess
import sys
import time
import traceback
from datetime import datetime
from pathlib import Path

# Configuration
DEFAULT_VENV_NAME = "myvenv"
DEFAULT_SCRIPT_NAME = "main.py"
MODE = "dev"


if os.name == "nt":  # Windows
    from utils import (  # type: ignore
        check_data,
        clear_console,
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )
else:  # Linux/Unix
    from .utils import (  # type: ignore
        check_data,
        clear_console,
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )


def setup_verbose_logging() -> Path:
    """Setup detailed logging for verbose debug mode"""
    # Create logs directory
    log_dir = Path("startup_logs")
    log_dir.mkdir(exist_ok=True)

    # Log file with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = log_dir / f"dev_verbose_{timestamp}.log"

    # Add file handler for verbose logs
    file_handler = logging.FileHandler(log_file, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(
        logging.Formatter(
            "%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    )

    # Add to root logger
    root_logger = logging.getLogger()
    root_logger.addHandler(file_handler)

    print(f"Verbose debug logs will be saved to: {log_file}")
    return log_file


def log_system_environment() -> None:
    """Log detailed system information for debugging"""
    logger = logging.getLogger("SYSTEM_DEBUG")

    logger.debug("=" * 60)
    logger.debug("SYSTEM ENVIRONMENT DEBUG INFO")
    logger.debug("=" * 60)

    # Python info
    logger.debug(f"Python version: {sys.version}")
    logger.debug(f"Python executable: {sys.executable}")
    logger.debug(f"Working directory: {os.getcwd()}")
    logger.debug(f"Frozen: {getattr(sys, 'frozen', False)}")

    # Platform info
    try:
        import platform

        logger.debug(f"Platform: {platform.platform()}")
        logger.debug(f"Machine: {platform.machine()}")
        logger.debug(f"Processor: {platform.processor()}")
    except Exception as e:
        logger.debug(f"Error getting platform info: {e}")

    # Environment variables
    env_vars = ["PATH", "USERPROFILE", "APPDATA", "LOCALAPPDATA", "TEMP"]
    for var in env_vars:
        value = os.environ.get(var, "NOT_SET")
        logger.debug(f"ENV {var}: {value}")


def test_systray_environment() -> bool:
    """Test and log systray environment"""
    logger = logging.getLogger("SYSTRAY_DEBUG")

    try:
        logger.debug("Testing PySide6 availability...")
        from PySide6 import QtGui, QtWidgets

        logger.debug("PySide6 imported successfully")

        # Test QApplication
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
            logger.debug("New QApplication created for testing")
        else:
            logger.debug("Using existing QApplication instance")

        # Test systray availability
        systray_available = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
        logger.debug(f"System tray available: {systray_available}")

        # Screen information
        screens = QtGui.QGuiApplication.screens()
        logger.debug(f"Number of screens: {len(screens)}")
        for i, screen in enumerate(screens):
            logger.debug(f"Screen {i}: {screen.name()} - {screen.geometry()}")

        # Test systray icon creation
        if systray_available:
            logger.debug("Testing systray icon creation...")
            test_icon = QtWidgets.QSystemTrayIcon()
            test_icon.setToolTip("Writing Tools Debug Test")
            test_icon.show()

            time.sleep(0.5)
            is_visible = test_icon.isVisible()
            logger.debug(f"Test tray icon visible: {is_visible}")

            test_icon.hide()
            logger.debug("Test tray icon cleaned up")

        return systray_available

    except Exception as e:
        logger.debug(f"Error in systray environment test: {e}")
        logger.debug(traceback.format_exc())
        return False


def monitor_application_startup(verbose_debug: bool) -> None:
    """Monitor application startup if verbose debug is enabled"""
    if not verbose_debug:
        return

    logger = logging.getLogger("APP_MONITOR")

    try:
        # Wait a bit for app to initialize
        time.sleep(2)

        logger.debug("Starting application monitoring for 10 seconds...")

        # Try to get the application instance and monitor tray icon
        from PySide6 import QtWidgets

        for i in range(10):
            time.sleep(1)

            app = QtWidgets.QApplication.instance()
            if app:
                logger.debug(f"Monitor second {i + 1}: Application instance found")

                # Try to access WritingToolApp attributes if available
                if hasattr(app, 'tray_icon'):
                    tray_icon = getattr(app, 'tray_icon', None)
                    if tray_icon:
                        visible = tray_icon.isVisible()
                        logger.debug(f"Monitor second {i + 1}: Tray icon visible = {visible}")
                    else:
                        logger.debug(f"Monitor second {i + 1}: No tray icon object")
                else:
                    logger.debug(f"Monitor second {i + 1}: Application running but no tray_icon attribute")
            else:
                logger.debug(f"Monitor second {i + 1}: No application instance found")

    except Exception as e:
        logger.debug(f"Error during application monitoring: {e}")
        logger.debug(traceback.format_exc())

def launch_application(
    venv_path: str = DEFAULT_VENV_NAME,
    script_name: str = DEFAULT_SCRIPT_NAME,
    extra_args: list[str] | None = None,
    verbose_debug: bool = False,
) -> bool:
    """Launch the main application using the virtual environment"""
    python_cmd: Path = get_python_executable(venv_path)

    if not python_cmd.exists():
        print(f"Error: Python executable not found at {python_cmd}")
        return False

    # main.py should be in the current directory (Windows_and_Linux)
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"Error: Main script not found: {script_path}")
        return False

    # Build command with extra arguments
    cmd = [str(python_cmd), str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    args_display = " ".join(extra_args) if extra_args else "none"
    print(f"Launching {script_path.name} with args: {args_display}...")

    if verbose_debug:
        logging.getLogger("LAUNCH").debug(f"Launch command: {' '.join(cmd)}")

    try:
        # Start monitoring in verbose mode (in background)
        if verbose_debug:
            import threading

            monitor_thread = threading.Thread(
                target=monitor_application_startup, args=(verbose_debug,), daemon=True
            )
            monitor_thread.start()

        # Launch the application
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0

    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to launch application: {e}")
        if verbose_debug:
            logging.getLogger("LAUNCH").debug(f"Launch error: {e}")
        return False
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return True
    except Exception as e:
        print(f"Error: Unexpected error while launching application: {e}")
        if verbose_debug:
            logging.getLogger("LAUNCH").debug(f"Unexpected launch error: {e}")
            logging.getLogger("LAUNCH").debug(traceback.format_exc())
        return False


def main():
    """Main function"""
    clear_console()
    print("===== Writing Tools - Development Launcher =====")
    print()

    # Parse command line arguments
    args = sys.argv[1:] if len(sys.argv) > 1 else []

    # Check for debug flags
    verbose_debug = "--debug-verbose" in args
    console_mode = "--console" in args

    # Remove our flags from args to pass to main app
    extra_args = [arg for arg in args if arg not in ["--debug-verbose", "--console"]]

    # Add console flag back if it was specified (for main.py)
    if console_mode:
        extra_args.append("--console")

    if verbose_debug:
        print("VERBOSE DEBUG MODE ENABLED")
        print("-" * 30)

    try:
        # Setup project root
        project_root = get_project_root()
        print(f"Project root: {project_root.name}")

        # Setup verbose logging if requested
        log_file = None
        if verbose_debug:
            log_file = setup_verbose_logging()
            log_system_environment()

        # Setup environment (virtual env + dependencies)
        print("Setting up development environment...")
        success, _ = setup_environment(DEFAULT_VENV_NAME)
        if not success:
            print("\nFailed to setup environment!")
            return 1

        # Test systray environment in verbose mode
        if verbose_debug:
            print("Testing systray environment...")
            systray_ok = test_systray_environment()
            if not systray_ok:
                print("Warning: Systray environment test failed!")
                logging.getLogger("SYSTRAY_DEBUG").warning("Systray test failed, but continuing...")

        # Stop existing processes (both exe and script)
        print("Terminating existing processes...")
        terminate_existing_processes(
            exe_name=get_executable_name(),
            script_name=DEFAULT_SCRIPT_NAME,
        )

        # Setup development settings
        check_data(MODE)

        # Launch application with extra arguments
        print()
        if not launch_application(
            DEFAULT_VENV_NAME, extra_args=extra_args, verbose_debug=verbose_debug
        ):
            print("\nFailed to launch application!")
            return 1

        if verbose_debug and log_file:
            print(f"\nVerbose debug logs saved to: {log_file}")

        print("\n===== Application finished successfully =====")
        return 0

    except KeyboardInterrupt:
        print(f"\n{MODE} cancelled by user.")
        return 130  # Standard Unix exit code for SIGINT
    except Exception as e:
        print(f"\nError in {MODE}: {e}")
        if verbose_debug:
            logging.getLogger("MAIN").debug(f"Main error: {e}")
            logging.getLogger("MAIN").debug(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
