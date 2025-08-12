#!/usr/bin/env python3
"""
Writing Tools - Development Launcher
Cross-platform development environment setup and launcher
"""

import os
import sys
import subprocess

try:
    from .utils import (
        get_project_root,
        setup_environment,
        terminate_existing_processes,
        get_activation_script,
        get_executable_name,
    )
except ImportError:
    from utils import (
        get_project_root,
        setup_environment,
        terminate_existing_processes,
        get_activation_script,
        get_executable_name,
    )


def setup_dev_settings():
    """Setup settings for dev mode using new dist/dev/ logic"""
    print("Setting up development settings...")

    # In dev mode, the application will use dist/dev/data_dev.json
    dist_dev_dir = "dist/dev"
    os.makedirs(dist_dev_dir, exist_ok=True)

    data_dev_path = os.path.join(dist_dev_dir, "data_dev.json")

    # Simple setup - no legacy compatibility needed
    if os.path.exists(data_dev_path):
        print(f"Using existing settings from: {data_dev_path}")
    else:
        print(
            "No existing settings found. Application will create settings on first run."
        )
        print(f"Settings will be saved to: {data_dev_path}")


def launch_application(venv_path, script_name="main.py", extra_args=None):
    """Launch the main application using the virtual environment"""
    python_cmd = get_activation_script(venv_path)

    if not os.path.exists(python_cmd):
        print(f"Error: Python executable not found at {python_cmd}")
        return False

    # main.py should be in the current directory (Windows_and_Linux)
    if not os.path.exists(script_name):
        print(f"Error: Main script not found: {script_name}")
        return False

    # Build command with extra arguments
    cmd = [python_cmd, script_name]
    if extra_args:
        cmd.extend(extra_args)

    print(
        f"Launching {script_name} with args: {' '.join(extra_args) if extra_args else 'none'}..."
    )
    try:
        # Launch the application
        subprocess.run(cmd, check=True)
        return True
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to launch application: {e}")
        return False
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return True


def clear_console():
    """Clear console screen (cross-platform)"""
    import os

    os.system("cls" if os.name == "nt" else "clear")


def main():
    """Main function"""
    clear_console()
    print("===== Writing Tools - Development Launcher =====")
    print()

    # Parse command line arguments (skip script name)
    extra_args = sys.argv[1:] if len(sys.argv) > 1 else None

    try:
        # Setup project root
        get_project_root()

        # Setup environment (virtual env + dependencies)
        print("Setting up development environment...")
        success, _ = setup_environment()
        if not success:
            print("\nFailed to setup environment!")

            return 1

        # Stop existing processes (both exe and script)
        terminate_existing_processes(
            exe_name=get_executable_name(), script_name="main.py"
        )

        # Setup development settings
        setup_dev_settings()

        # Launch application with extra arguments
        print()
        if not launch_application("myvenv", extra_args=extra_args):
            print("\nFailed to launch application!")

            return 1

        print("\n===== Application finished =====")
        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")

        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
