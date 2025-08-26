#!/usr/bin/env python3
"""
Script to run Ruff formatting and linting on the entire repository.
This script is cross-platform for Windows and Linux.
Uses standardized environment setup from utils.py
"""

import os
import subprocess
import sys
from pathlib import Path

# Configuration
DEFAULT_VENV_NAME = "myvenv"

if os.name == "nt":  # Windows
    from utils import (  # type: ignore
        clear_console,
        get_project_root,
        get_python_executable,
        setup_environment,
    )
else:  # Linux/Unix
    from .utils import (  # type: ignore
        clear_console,
        get_project_root,
        get_python_executable,
        setup_environment,
    )


def main():
    """Main function to run complete Ruff setup and execution."""
    clear_console()
    print("RUFF FORMATTER & LINTER RUNNER")
    print("=" * 40)

    try:
        # Setup project root
        project_root = get_project_root()
        print(f"Project root: {project_root.name}")

        # Setup environment (virtual env + dependencies)
        success, _ = setup_environment(DEFAULT_VENV_NAME)
        if not success:
            print("Failed to setup environment!")
            return 1

        # Get python executable from virtual environment
        python_cmd: Path = get_python_executable(DEFAULT_VENV_NAME)

        if not python_cmd.exists():
            print(f"Error: Python executable not found at {python_cmd}")
            return 1

        # Run ruff commands (don't fail if ruff finds issues, that's normal)
        subprocess.run([str(python_cmd), "-m", "ruff", "check", "--fix", "."])
        subprocess.run([str(python_cmd), "-m", "ruff", "format", "."])
        subprocess.run([str(python_cmd), "-m", "ruff", "check", "."])

        print("Ruff formatting and linting completed successfully!")
        return 0

    except subprocess.CalledProcessError as e:
        print(f"Ruff command failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("Operation cancelled by user.")
        return 130
    except Exception as e:
        print(f"Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
