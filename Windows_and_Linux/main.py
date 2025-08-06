import argparse
import logging
import sys

from WritingToolApp import WritingToolApp

# Set up logging to console
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(message)s")


def parse_arguments():
    """
    Parse command line arguments.

    Returns:
        argparse.Namespace: Parsed arguments
    """
    parser = argparse.ArgumentParser(description="Writing Tools - AI-powered writing assistant")
    parser.add_argument(
        "--theme",
        choices=["light", "dark", "auto"],
        default="auto",
        help="Force a specific theme (light/dark) or use auto-detection (default: auto)",
    )
    parser.add_argument("--debug", action="store_true", help="Enable debug logging")

    return parser.parse_args()


def main():
    """
    The main entry point of the application.
    """
    args = parse_arguments()

    # Adjust logging level if debug is requested
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)

    app = WritingToolApp(sys.argv, theme_override=args.theme)
    app.setQuitOnLastWindowClosed(False)
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
