#!/usr/bin/env python3
"""
Writing Tools - Development Startup Setup

Install/uninstall dev_script.py to run at Windows startup with console debugging.

This script automatically disables the normal application autostart if it's active,
and vice versa when the normal application autostart is enabled.

Features:
- Runs dev_script.py at Windows startup in a visible console window
- Automatically disables conflicting normal application autostart
- Console remains open for debugging systray and startup issues

Usage:
    python setup_dev_autostart.py           # Toggle install/uninstall
"""

import sys
import winreg
from pathlib import Path


def get_paths() -> tuple[Path, Path, Path]:
    """Get project paths using Path objects"""
    # Use the existing utility function
    from utils import get_project_root, get_python_executable

    project_root = get_project_root()  # Returns Windows_and_Linux directory
    venv_python = get_python_executable("myvenv")  # Uses utils function
    dev_script = project_root / "scripts" / "dev_script.py"

    return project_root, venv_python, dev_script


def validate_paths(project_root: Path, venv_python: Path, dev_script: Path) -> bool:
    """Validate that required paths exist"""
    if not dev_script.exists():
        print(f"Error: dev_script.py not found: {dev_script}")
        return False

    if not venv_python.exists():
        print(f"Error: Virtual environment Python not found: {venv_python}")
        return False

    return True


def install_startup_dev() -> bool:
    """Install dev script to run at Windows startup"""
    try:
        project_root, venv_python, dev_script = get_paths()

        if not validate_paths(project_root, venv_python, dev_script):
            return False

        # Check and disable normal startup if it exists
        normal_was_active = check_normal_startup_exists()
        if normal_was_active:
            if disable_normal_startup_if_exists():
                print("Disabled conflicting normal application startup entry")
            else:
                print("Warning: Could not disable normal startup entry")

        # Build command
        debug_args = "--console"
        command = f'cmd /k "cd /d "{project_root}" && "{venv_python}" "{dev_script}" {debug_args}"'

        # Add to Windows startup registry
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE,
        ) as key:
            winreg.SetValueEx(key, "WritingToolsDevStartup", 0, winreg.REG_SZ, command)

        return True

    except Exception as e:
        print(f"Failed to install startup dev: {e}")
        return False

def uninstall_startup_dev() -> bool:
    """Remove dev script from Windows startup"""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE,
        ) as key:
            try:
                winreg.DeleteValue(key, "WritingToolsDevStartup")
                print("Startup dev entry removed successfully")
            except OSError:
                print("Startup dev entry was not found (already removed)")

        return True

    except Exception as e:
        print(f"Failed to uninstall startup dev: {e}")
        return False


def check_normal_startup_exists() -> bool:
    """Check if the normal application startup entry exists"""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            winreg.QueryValueEx(key, "WritingTools")
            return True
    except OSError:
        return False


def disable_normal_startup_if_exists() -> bool:
    """Disable the normal application startup entry if it exists"""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE,
        ) as key:
            try:
                winreg.DeleteValue(key, "WritingTools")
                return True
            except OSError:
                # Value doesn't exist, that's fine
                return True
    except Exception as e:
        print(f"Warning: Could not disable normal startup entry: {e}")
        return False


def is_startup_dev_installed() -> bool:
    """Check if startup dev entry exists"""
    try:
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_READ,
        ) as key:
            winreg.QueryValueEx(key, "WritingToolsDevStartup")
            return True
    except OSError:
        return False


def main():
    """Main function - toggle install/uninstall"""
    print("Writing Tools - Development Startup Setup")
    print("=" * 45)

    if is_startup_dev_installed():
        print("Startup dev is currently INSTALLED")
        print("Uninstalling...")
        if uninstall_startup_dev():
            print("[SUCCESS] Startup dev uninstalled successfully!")
        else:
            print("[ERROR] Failed to uninstall startup dev")
            return 1
    else:
        print("Startup dev is currently NOT installed")
        print("Installing...")
        if install_startup_dev():
            print("[SUCCESS] Startup dev installed!")
            print("The dev script will run at next Windows boot in a console window.")
            print("The console will remain open for debugging systray issues.")
        else:
            print("[ERROR] Failed to install startup dev")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
