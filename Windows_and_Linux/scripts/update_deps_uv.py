#!/usr/bin/env python3
"""
Install development dependencies using UV
Modern replacement for traditional venv-based dependency management
"""

import os
import subprocess
import sys
import time
from pathlib import Path


def clear_console() -> None:
    """Clear console screen (cross-platform)"""
    os.system("cls" if os.name == "nt" else "clear")


def check_uv_installed() -> bool:
    """Check if UV is installed on the system"""
    try:
        result = subprocess.run(
            ["uv", "--version"],
            check=True,
            capture_output=True,
            text=True
        )
        print(f"UV version: {result.stdout.strip()}")
        return True
    except (subprocess.CalledProcessError, FileNotFoundError):
        return False


def install_uv() -> bool:
    """Install UV using pip or download from official source"""
    print("UV not found. Installing UV...")

    # Method 1: Try pip install
    try:
        subprocess.run(
            [sys.executable, "-m", "pip", "install", "uv"],
            check=True
        )
        print("UV installed successfully via pip")
        return True
    except subprocess.CalledProcessError:
        pass

    # Method 2: Try official installer
    try:
        import urllib.request
        import tempfile
        import shutil

        print("Trying official UV installer...")

        # This is a simplified approach - in production you'd want more robust error handling
        print("Please install UV manually:")
        print("1. Visit: https://docs.astral.sh/uv/getting-started/installation/")
        print("2. Download and install UV for your platform")
        print("3. Run this script again")
        return False

    except Exception as e:
        print(f"Error installing UV: {e}")
        return False


def setup_uv_environment() -> bool:
    """Set up UV environment for the project"""
    print("Setting up UV environment...")

    # Change to Windows_and_Linux directory
    script_dir = Path(__file__).parent
    project_root = script_dir.parent
    os.chdir(project_root)

    try:
        # Initialize UV project if not already done
        if not (project_root / "uv.lock").exists():
            print("Initializing UV project...")
            subprocess.run(["uv", "init", "--name", "writing-tools"], check=True)
            print("UV project initialized")
        else:
            print("UV project already initialized")

        # Sync dependencies
        print("Syncing dependencies with UV...")
        subprocess.run(["uv", "sync"], check=True)
        print("Dependencies synchronized successfully")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error setting up UV environment: {e}")
        return False


def run_dev_script_with_uv() -> bool:
    """Run the development script using UV"""
    print("Running development script with UV...")

    try:
        # Run the main dev script using UV
        result = subprocess.run(
            ["uv", "run", "python", "scripts/dev_script.py"],
            check=True
        )
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error running dev script: {e}")
        return False


def main():
    """Main function"""
    clear_console()
    print("===== Setting up Writing Tools with UV =====")
    print()

    try:
        # Check if UV is installed
        if not check_uv_installed():
            if not install_uv():
                print("\nFailed to install UV. Please install manually and try again.")
                print("Visit: https://docs.astral.sh/uv/getting-started/installation/")
                return 1

        # Setup UV environment
        if not setup_uv_environment():
            print("\nFailed to setup UV environment")
            return 1

        print("\nUV setup completed successfully!")
        print("\nTo run the application:")
        print("  cd Windows_and_Linux")
        print("  uv run python scripts/dev_script.py")

        # Optionally run the dev script
        print("\nWould you like to run the development script now? (y/n): ", end="")
        # In a real script, you'd handle user input here
        # For now, we'll just proceed

        return 0

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