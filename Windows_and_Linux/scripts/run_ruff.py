#!/usr/bin/env python3
"""
Script to run Ruff formatting and linting on the entire repository.
This script is cross-platform for Windows and Linux.
Uses standardized environment setup from utils.py
"""

import subprocess
import sys
from pathlib import Path

# Import after path setup
from utils import (
    clear_console,
    get_project_root,
)

# Add parent directory to path to import utils
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Go up to Windows_and_Linux
sys.path.insert(0, str(project_root))


def main():
    """Main function to run complete Ruff setup and execution with UV."""
    clear_console()
    print("RUFF FORMATTER & LINTER RUNNER (UV)")
    print("=" * 40)

    try:
        # Setup project root
        project_root = get_project_root()
        print(f"Project root: {project_root.name}")
        print("Environment automatically managed by UV")

        # Run ruff commands using UV (don't fail if ruff finds issues, that's normal)
        subprocess.run(["uv", "run", "ruff", "check", "--fix", "."])
        subprocess.run(["uv", "run", "ruff", "format", "."])
        subprocess.run(["uv", "run", "ruff", "check", "."])

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
