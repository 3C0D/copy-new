#!/usr/bin/env python3
"""
Script to run Ruff formatting and linting on the entire repository.
This script is cross-platform for Windows and Linux.
Includes dependency setup using update_deps.py
"""

import subprocess
import sys
import os
from pathlib import Path


def run_command(command, description, cwd=None):
    """Run a command and print the result."""
    print(f"🔄 Running: {description}")
    try:
        if cwd is None:
            cwd = Path(__file__).parent.parent

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=cwd
        )

        if result.returncode == 0:
            print(f"✅ Success: {description}")
            if result.stdout.strip():
                print(f"📋 Output:\n{result.stdout}")
        else:
            print(f"❌ Error in {description}:")
            if result.stderr.strip():
                print(f"🚨 Error details:\n{result.stderr}")
            if result.stdout.strip():
                print(f"📋 Output:\n{result.stdout}")
            return False
    except Exception as e:
        print(f"💥 Exception in {description}: {e}")
        return False
    return True


def check_ruff_installed():
    """Check if Ruff is available in the virtual environment."""
    print("🔍 Checking if Ruff is available...")

    # Try to find ruff in virtual environment
    venv_path = Path(__file__).parent.parent / "myvenv"

    if os.name == "nt":  # Windows
        ruff_path = venv_path / "Scripts" / "ruff.exe"
        python_path = venv_path / "Scripts" / "python.exe"
    else:  # Linux/Unix
        ruff_path = venv_path / "bin" / "ruff"
        python_path = venv_path / "bin" / "python"

    if ruff_path.exists():
        print(f"✅ Ruff found at: {ruff_path}")
        return True

    # Try with python -m ruff
    try:
        result = subprocess.run(
            [str(python_path), "-m", "ruff", "--version"],
            capture_output=True,
            text=True
        )
        if result.returncode == 0:
            print(f"✅ Ruff available via python -m ruff")
            return True
    except:
        pass

    print("❌ Ruff not found in virtual environment")
    return False


def setup_dependencies():
    """Run update_deps.py to install dependencies including Ruff."""
    print("🔧 Setting up dependencies...")

    update_deps_path = Path(__file__).parent / "update_deps.py"

    if not update_deps_path.exists():
        print(f"❌ update_deps.py not found at {update_deps_path}")
        return False

    # Run update_deps.py
    python_exe = sys.executable
    cmd = f'"{python_exe}" "{update_deps_path}"'

    return run_command(cmd, "Installing dependencies via update_deps.py")


def run_ruff_commands():
    """Run Ruff formatting and linting commands."""
    print("\n🎯 Starting Ruff formatting and linting...")

    project_root = Path(__file__).parent.parent
    venv_path = project_root / "myvenv"

    # Determine python executable in venv
    if os.name == "nt":  # Windows
        python_exe = venv_path / "Scripts" / "python.exe"
        ruff_exe = venv_path / "Scripts" / "ruff.exe"
    else:  # Linux/Unix
        python_exe = venv_path / "bin" / "python"
        ruff_exe = venv_path / "bin" / "ruff"

    # Use ruff executable if available, otherwise python -m ruff
    if ruff_exe.exists():
        ruff_cmd = str(ruff_exe)
    else:
        ruff_cmd = f'"{python_exe}" -m ruff'

    print(f"📍 Working directory: {project_root}")
    print(f"🛠️  Using Ruff command: {ruff_cmd}")

    # Run ruff check --fix first (fixes issues)
    print("\n1️⃣ Running Ruff linting and auto-fixes...")
    if not run_command(f"{ruff_cmd} check --fix .", "Ruff linting and fixes", cwd=project_root):
        print("⚠️  Warning: Some linting issues couldn't be fixed automatically")
        # Don't return False here, continue with formatting

    # Run ruff format (formats code)
    print("\n2️⃣ Running Ruff formatting...")
    if not run_command(f"{ruff_cmd} format .", "Ruff formatting", cwd=project_root):
        return False

    # Final check without fixes (just report remaining issues)
    print("\n3️⃣ Final check for remaining issues...")
    run_command(f"{ruff_cmd} check .", "Final Ruff check (report only)", cwd=project_root)

    return True


def main():
    """Main function to run complete Ruff setup and execution."""
    print("=" * 60)
    print("🐍 RUFF FORMATTER & LINTER RUNNER")
    print("=" * 60)

    try:
        # Step 1: Check if Ruff is installed
        if not check_ruff_installed():
            print("\n🔧 Ruff not found. Running dependency setup...")
            if not setup_dependencies():
                print("❌ Failed to setup dependencies")
                sys.exit(1)

            # Recheck after installation
            if not check_ruff_installed():
                print("❌ Ruff still not available after installation")
                sys.exit(1)

        # Step 2: Run Ruff commands
        if not run_ruff_commands():
            print("\n❌ Ruff execution failed")
            sys.exit(1)

        print("\n" + "=" * 60)
        print("🎉 Ruff formatting and linting completed successfully!")
        print("=" * 60)

    except KeyboardInterrupt:
        print("\n\n⏹️  Operation cancelled by user")
        sys.exit(130)
    except Exception as e:
        print(f"\n💥 Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()