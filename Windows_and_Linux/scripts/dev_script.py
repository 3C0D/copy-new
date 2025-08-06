#!/usr/bin/env python3
"""
Writing Tools - Development Launcher
Cross-platform development environment setup and launcher
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
DEFAULT_VENV_NAME = "myvenv"
DEFAULT_SCRIPT_NAME = "main.py"


if os.name == "nt":  # Windows
    from utils import (  # type: ignore
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )
else:  # Linux/Unix
    from .utils import (  # type: ignore
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )


def setup_dev_settings():
    """Setup settings for dev mode using new dist/dev/ logic"""
    print("Setting up development settings...")

    # In dev mode, the application will use dist/dev/data_dev.json
    dist_dev_dir = Path("dist/dev")
    dist_dev_dir.mkdir(parents=True, exist_ok=True)

    data_dev_path = dist_dev_dir / "data_dev.json"

    if data_dev_path.exists():
        print(f"Using existing settings from: {data_dev_path}")
    else:
        print(
            "No existing settings found. Application will create settings on first run.",
        )
        print(f"Settings will be saved to: {data_dev_path}")


def launch_application(
    venv_path=DEFAULT_VENV_NAME,
    script_name=DEFAULT_SCRIPT_NAME,
    extra_args=None,
):
    """Launch the main application using the virtual environment"""
    python_cmd = get_python_executable(venv_path)

    if not Path(python_cmd).exists():
        print(f"Error: Python executable not found at {python_cmd}")
        return False

    # main.py should be in the current directory (Windows_and_Linux)
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"Error: Main script not found: {script_name}")
        return False

    # Build command with extra arguments
    cmd = [python_cmd, str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(
        f"Launching {script_name} with args: {' '.join(extra_args) if extra_args else 'none'}...",
    )

    try:
        # Launch the application
        result = subprocess.run(cmd, check=True)
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: Failed to launch application: {e}")
        return False
    except KeyboardInterrupt:
        print("\nApplication interrupted by user.")
        return True
    except Exception as e:
        print(f"Error: Unexpected error while launching application: {e}")
        return False


def clear_console():
    """Clear console screen (cross-platform)"""
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
        project_root = get_project_root()
        print(f"Project root: {project_root}")

        # Setup environment (virtual env + dependencies)
        print("Setting up development environment...")
        success, python_exe_version = setup_environment(DEFAULT_VENV_NAME)
        if not success:
            print("\nFailed to setup environment!")
            return 1

        # Stop existing processes (both exe and script)
        print("Terminating existing processes...")
        terminate_existing_processes(
            exe_name=get_executable_name(),
            script_name=DEFAULT_SCRIPT_NAME,
        )

        # Setup development settings
        setup_dev_settings()

        # Launch application with extra arguments
        print()
        if not launch_application(DEFAULT_VENV_NAME, extra_args=extra_args):
            print("\nFailed to launch application!")
            return 1

        print("\n===== Application finished successfully =====")
        return 0

    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        return 130  # Standard Unix exit code for SIGINT
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
