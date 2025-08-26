#!/usr/bin/env python3
"""
Script to run Ruff formatting and linting on the entire repository.
This script is cross-platform for Windows and Linux.
"""

import subprocess
import sys
from pathlib import Path


def run_command(command, description):
    """Run a command and print the result."""
    print(f"Running: {description}")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True, cwd=Path(__file__).parent.parent)
        if result.returncode == 0:
            print(f"Success: {description}")
            if result.stdout:
                print(result.stdout)
        else:
            print(f"Error in {description}:")
            if result.stderr:
                print(result.stderr)
            return False
    except Exception as e:
        print(f"Exception in {description}: {e}")
        return False
    return True

def main():
    """Main function to run Ruff commands."""
    print("Starting Ruff formatting and linting...")

    # Run ruff format
    if not run_command("ruff format .", "Ruff formatting"):
        sys.exit(1)

    # Run ruff check --fix
    if not run_command("ruff check --fix .", "Ruff linting and fixes"):
        sys.exit(1)

    print("Ruff formatting and linting completed successfully.")

if __name__ == "__main__":
    main()
