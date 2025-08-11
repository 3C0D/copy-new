import logging
import sys
import os

from WritingToolApp import WritingToolApp

# Check if we're running in console mode (when console=True in PyInstaller)
CONSOLE_MODE = hasattr(sys, 'frozen') and sys.frozen and os.name == 'nt' and sys.stdout.isatty()

# Set up logging to console with debug level (auto-enabled)
if CONSOLE_MODE:
    # Enhanced logging for console mode
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout), logging.StreamHandler(sys.stderr)],
    )
    print("=== Writing Tools - Console Mode ===")
    print("Logs will appear in this console window.")
    print("Press Ctrl+C to exit.")
    print("=====================================")
else:
    # Standard logging for windowed mode
    logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def main():
    """
    The main entry point of the application.
    """
    try:
        app = WritingToolApp(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        if CONSOLE_MODE:
            logging.info("Application started in console mode")
            logging.info("Check your system tray for the Writing Tools icon")

        exit_code = app.exec()

        if CONSOLE_MODE:
            logging.info(f"Application exited with code: {exit_code}")

        sys.exit(exit_code)

    except KeyboardInterrupt:
        if CONSOLE_MODE:
            print("\nApplication interrupted by user (Ctrl+C)")
            logging.info("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        if CONSOLE_MODE:
            print(f"\nCritical error: {e}")
        logging.exception(f"Critical error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
