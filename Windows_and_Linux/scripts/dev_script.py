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


def launch_application(
    venv_path=DEFAULT_VENV_NAME,
    script_name=DEFAULT_SCRIPT_NAME,
    extra_args=None,
):
    """Launch the main application using the virtual environment"""
    python_cmd = get_python_executable(venv_path)
    python_path = Path(python_cmd)

    if not python_path.exists():
        print(f"Error: Python executable not found at {python_path}")
        return False

    # main.py should be in the current directory (Windows_and_Linux)
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"Error: Main script not found: {script_path}")
        return False

    # Build command with extra arguments
    cmd = [str(python_path), str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(
        f"Launching {script_path.name} with args: {' '.join(extra_args) if extra_args else 'none'}...",
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
        print(f"Project root: {project_root.name}")

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
        check_data(MODE)

        # Launch application with extra arguments
        print()
        if not launch_application(DEFAULT_VENV_NAME, extra_args=extra_args):
            print("\nFailed to launch application!")
            return 1

        print("\n===== Application finished successfully =====")
        return 0

    except KeyboardInterrupt:
        print(f"\n{MODE} cancelled by user.")
        return 130  # Standard Unix exit code for SIGINT
    except Exception as e:
        print(f"\nErreur dans {MODE}: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
