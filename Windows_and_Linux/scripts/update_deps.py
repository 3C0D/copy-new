#!/usr/bin/env python3
"""
Install development dependencies
Simple script to setup venv and install requirements.txt
"""

import os
import sys
from pathlib import Path

# Configuration
DEFAULT_VENV_NAME = "myvenv"
REQUIREMENTS_FILE = "requirements.txt"

if os.name == "nt":  # Windows
    from utils import (  # type: ignore
        get_project_root,
        setup_environment,
    )
else:  # Linux/Unix
    from .utils import (  # type: ignore
        get_project_root,
        setup_environment,
    )


def install_requirements():
    """Install requirements using existing utils logic"""
    print("Installing development dependencies...")

    # Check if requirements.txt exists
    req_file = Path(REQUIREMENTS_FILE)
    if not req_file.exists():
        print(f"Error: {REQUIREMENTS_FILE} not found")
        return False

    # Setup environment (creates venv + installs requirements)
    print("Setting up virtual environment and installing dependencies...")
    success, python_version = setup_environment(DEFAULT_VENV_NAME, REQUIREMENTS_FILE)

    if success:
        print("Dependencies installed successfully")
        return True
    print("Failed to install dependencies")
    return False


def clear_console():
    """Clear console screen (cross-platform)"""
    os.system("cls" if os.name == "nt" else "clear")


def main():
    """Main function"""
    clear_console()
    print("===== Installing Development Dependencies =====")
    print()

    try:
        # Setup project root
        project_root = get_project_root()
        print(f"Project root: {project_root}")

        # Install requirements
        if install_requirements():
            print("\nInstallation completed successfully")
            print("You can now run: python dev_script.py")
            return 0
        print("\nInstallation failed")
        return 1

    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
