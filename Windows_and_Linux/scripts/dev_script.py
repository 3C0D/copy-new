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

DEFAULT_SCRIPT_NAME = "main.py"
MODE = "dev"


if os.name == "nt":  # Windows
    from utils import (  # type: ignore
        check_data,
        clear_console,
        get_executable_name,
        get_project_root,
        terminate_existing_processes,
    )
else:  # Linux/Unix
    from .utils import (  # type: ignore
        check_data,
        clear_console,
        get_executable_name,
        get_project_root,
        terminate_existing_processes,
    )


def launch_application(
    script_name: str = DEFAULT_SCRIPT_NAME,
    extra_args: list[str] | None = None,
) -> bool:
    """Launch the main application using UV"""
    # main.py should be in the current directory (Windows_and_Linux)
    script_path = Path(script_name)
    if not script_path.exists():
        print(f"Error: Main script not found: {script_path}")
        return False

    # Build UV command with extra arguments
    cmd = ["uv", "run", str(script_path)]
    if extra_args:
        cmd.extend(extra_args)

    print(
        f"Launching {script_path.name} with args: {' '.join(extra_args) if extra_args else 'none'}...",
    )

    try:
        # Launch the application with UV
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

        # With UV, environment is automatically managed - no setup needed
        print("Environment automatically managed by UV")

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
        if not launch_application(extra_args=extra_args):
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
