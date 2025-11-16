import logging
import os
import sys

from src.writing_tools_app import WritingToolsApp

# Check if we're running in console mode (when console=True in PyInstaller or --console flag)
CONSOLE_MODE = "--console" in sys.argv or (
    getattr(sys, "frozen", False) and os.name == "nt" and sys.stdout and sys.stdout.isatty()
)

# Set up logging to console with debug level (auto-enabled)
if CONSOLE_MODE:
    # Enhanced logging for console mode
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        handlers=[logging.StreamHandler(sys.stdout)],
    )
    print("=== Writing Tools - Console Mode ===")
    print("Logs will appear in this console window.")
    print("Press Ctrl+C to exit.")
    print("=====================================")
else:
    # Standard logging for windowed mode (e.g vsc console)
    logging.basicConfig(level=logging.DEBUG, format="%(name)s - %(levelname)s - %(message)s")


def main():
    """
    The main entry point of the application.
    """
    try:
        app = WritingToolsApp(sys.argv)
        app.setQuitOnLastWindowClosed(False) # prevent from closing the app when all windows are closed

        if CONSOLE_MODE:
            logging.debug("Application started in console mode")
            logging.debug("Check your system tray for the Writing Tools icon")

        exit_code = app.exec() # run the application event loop. Allow the app to handle events and windows.

        if CONSOLE_MODE:
            logging.debug(f"Application exited with code: {exit_code}")

        sys.exit(exit_code)  # Exit the application with the code returned by the event loop

    except KeyboardInterrupt:
        if CONSOLE_MODE:
            print("\nApplication interrupted by user (Ctrl+C)")
            logging.debug("Application interrupted by user")
        sys.exit(0)
    except Exception as e:
        if CONSOLE_MODE:
            print(f"\nCritical error: {e}")
        logging.exception(f"Critical error in main: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
