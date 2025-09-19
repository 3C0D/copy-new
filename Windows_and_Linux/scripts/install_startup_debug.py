#!/usr/bin/env python3
"""
Writing Tools - Startup Dev Installer

Install/uninstall dev_script.py to run at Windows startup with optional debug mode.

Usage:
    python install_startup_debug.py            # Toggle install/uninstall with normal debug
    python install_startup_debug.py --verbose  # Toggle install/uninstall with verbose debug
"""

import sys
import winreg
from pathlib import Path

FORCE_VERBOSE = True  # Set to True to always enable verbose debug mode


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


def install_startup_dev(verbose_debug: bool = False) -> bool:
    """Install dev script to run at Windows startup"""
    try:
        project_root, venv_python, dev_script = get_paths()

        if not validate_paths(project_root, venv_python, dev_script):
            return False

        # Build command with optional verbose debug - CORRECTION: utiliser dev_script complet
        debug_args = "--console --debug-verbose" if verbose_debug else "--console"
        command = f'cmd /k "cd /d "{project_root}" && "{venv_python}" "{dev_script}" {debug_args}"'

        # Add to Windows startup registry
        with winreg.OpenKey(
            winreg.HKEY_CURRENT_USER,
            r"Software\Microsoft\Windows\CurrentVersion\Run",
            0,
            winreg.KEY_WRITE,
        ) as key:
            winreg.SetValueEx(key, "WritingToolsDevStartup", 0, winreg.REG_SZ, command)

        debug_mode = "verbose debug" if verbose_debug else "normal debug"
        print(f"Startup dev entry installed with {debug_mode} mode")
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
    print("Writing Tools - Startup Dev Installer")
    print("=" * 40)

    # Check for verbose flag or force verbose
    verbose_debug = "--verbose" in sys.argv or FORCE_VERBOSE

    if FORCE_VERBOSE and "--verbose" not in sys.argv:
        print("FORCE_VERBOSE is enabled - verbose debug mode forced")
    elif verbose_debug:
        print("Verbose debug mode requested")

    if is_startup_dev_installed():
        print("Startup dev is currently INSTALLED")
        print("Uninstalling...")
        if uninstall_startup_dev():
            print("✓ Startup dev uninstalled successfully!")
        else:
            print("✗ Failed to uninstall startup dev")
            return 1
    else:
        print("Startup dev is currently NOT installed")
        print("Installing...")
        if install_startup_dev(verbose_debug):
            debug_type = "verbose debug" if verbose_debug else "normal debug"
            print(f"✓ Startup dev installed with {debug_type} mode!")
            print("The dev script will run at next Windows boot in a console window.")
            print("The console will remain open for debugging systray issues.")
        else:
            print("✗ Failed to install startup dev")
            return 1

    return 0

if __name__ == "__main__":
    sys.exit(main())
