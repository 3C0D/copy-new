#!/usr/bin/env python3
"""
Writing Tools - Development Build Script
Cross-platform development build with environment setup

Usage:
    python scripts/dev_build.py                    # Standard windowed build
    python scripts/dev_build.py --console          # Console mode build (for debugging)
    python scripts/dev_build.py --console --arg    # Console build with extra args

Console Mode:
    Use --console when you need to see real-time logs and debug output.
    The executable will show a console window with live application logs.
    Useful for debugging startup issues, systray problems, or provider errors.

Standard Mode:
    Default windowed mode hides the console. Logs are written to build_dev_debug.log.
    Use this for normal development and testing.
"""

import os
import subprocess
import sys
import shutil
import json
import argparse
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config.data_operations import create_default_settings
from config.settings import SettingsManager

try:
    from .utils import (
        get_project_root,
        setup_environment,
        terminate_existing_processes,
        verify_requirements,
        get_activation_script,
        get_executable_name,
    )
except ImportError:
    from utils import (
        get_project_root,
        setup_environment,
        terminate_existing_processes,
        verify_requirements,
        get_activation_script,
        get_executable_name,
    )


def copy_required_files():
    """
    Copy required files for the development build to dist/dev/.
    """
    # Create dist/dev directory
    dev_dir = "dist/dev"
    os.makedirs(dev_dir, exist_ok=True)

    # --- Asset files (always copied) ---
    assets_to_copy = [
        ("config/icons", f"{dev_dir}/icons"),
        ("config/backgrounds/background.png", f"{dev_dir}/background.png"),
        ("config/backgrounds/background_dark.png", f"{dev_dir}/background_dark.png"),
        ("config/backgrounds/background_popup.png", f"{dev_dir}/background_popup.png"),
        (
            "config/backgrounds/background_popup_dark.png",
            f"{dev_dir}/background_popup_dark.png",
        ),
    ]

    print("Copying required files for development build to dist/dev/...")

    # --- Copy assets ---
    for src, dst in assets_to_copy:
        try:
            if not os.path.exists(src):
                print(f"Warning: Asset file/directory not found: {src}")
                continue

            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            print(f"Copied asset: {src} -> {dst}")
        except Exception as e:
            print(f"Error copying asset {src}: {e}")
            return False

    # --- Create data_dev.json in dist/dev/ for build-dev mode ---
    setup_build_dev_mode()

    print("Note: Build-dev mode - settings will be saved to dist/dev/data_dev.json")
    return True


def setup_build_dev_mode():
    """
    Create or update data_dev.json in dist/dev/ for build-dev mode with correct run_mode.
    Preserves existing configuration if file already exists.
    """
    sys.path.insert(0, os.path.abspath('.'))

    dist_dev_dir = Path("dist/dev")
    dist_dev_dir.mkdir(parents=True, exist_ok=True)

    data_dev_path = dist_dev_dir / "data_dev.json"

    if data_dev_path.exists():
        # File exists - load existing settings and only update run_mode
        print(f"Found existing data_dev.json, preserving configuration: {data_dev_path}")

        # Create a temporary SettingsManager to load existing settings
        temp_manager = SettingsManager(mode="dev")  # Use dev mode to load from dist/dev/
        temp_manager.data_file = data_dev_path
        existing_settings = temp_manager.load_settings()

        # Only update the run_mode to match build context
        existing_settings.system["run_mode"] = "dev"  # Keep as dev mode for consistency

        # Save the updated settings
        temp_manager.settings = existing_settings
        settings_dict = temp_manager._serialize_settings()

        with open(data_dev_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=2, ensure_ascii=False)

        print(f"Updated existing data_dev.json with preserved configuration")
    else:
        # File doesn't exist - create new with default settings
        print(f"Creating new data_dev.json with default settings: {data_dev_path}")

        settings = create_default_settings()
        settings.system["run_mode"] = "dev"  # Use dev mode for consistency

        # Create a temporary SettingsManager to use _serialize_settings
        temp_manager = SettingsManager(mode="dev")
        temp_manager.settings = settings

        # Use _serialize_settings instead of manual dictionary creation
        settings_dict = temp_manager._serialize_settings()

        # Save to data_dev.json
        with open(data_dev_path, 'w', encoding='utf-8') as f:
            json.dump(settings_dict, f, indent=2, ensure_ascii=False)

        print(f"Created new data_dev.json with default settings")


def run_dev_build(venv_path="myvenv", console_mode=False):
    """Run PyInstaller build for development (faster, less cleanup)"""

    # Remove existing .spec file if switching console mode to force regeneration
    spec_file = "Writing Tools.spec"
    if os.path.exists(spec_file):
        try:
            os.remove(spec_file)
            print(f"Removed existing {spec_file} to regenerate with new console mode")
        except Exception as e:
            print(f"Warning: Could not remove {spec_file}: {e}")

    # Use the virtual environment's Python to run PyInstaller
    python_cmd = get_activation_script(venv_path)
    pyinstaller_command = [
        python_cmd,
        "-m",
        "PyInstaller",
        "--onefile",
        "--console" if console_mode else "--windowed",
        "--icon=config/icons/app_icon.ico",
        "--name=Writing Tools",
        "--distpath=dist/dev",  # Output to dist/dev/
        "--noconfirm",  # Removed --clean for faster builds
        # Exclude unnecessary modules
        "--exclude-module",
        "tkinter",
        "--exclude-module",
        "unittest",
        "--exclude-module",
        "IPython",
        "--exclude-module",
        "jedi",
        "--exclude-module",
        "email_validator",
        "--exclude-module",
        "cryptography",
        "--exclude-module",
        "psutil",
        "--exclude-module",
        "pyzmq",
        "--exclude-module",
        "tornado",
        # Exclude modules related to PySide6 that are not used
        "--exclude-module",
        "PySide6.QtNetwork",
        "--exclude-module",
        "PySide6.QtXml",
        "--exclude-module",
        "PySide6.QtQml",
        "--exclude-module",
        "PySide6.QtQuick",
        "--exclude-module",
        "PySide6.QtQuickWidgets",
        "--exclude-module",
        "PySide6.QtPrintSupport",
        "--exclude-module",
        "PySide6.QtSql",
        "--exclude-module",
        "PySide6.QtTest",
        "--exclude-module",
        "PySide6.QtSvg",
        "--exclude-module",
        "PySide6.QtSvgWidgets",
        "--exclude-module",
        "PySide6.QtHelp",
        "--exclude-module",
        "PySide6.QtMultimedia",
        "--exclude-module",
        "PySide6.QtMultimediaWidgets",
        "--exclude-module",
        "PySide6.QtOpenGL",
        "--exclude-module",
        "PySide6.QtOpenGLWidgets",
        "--exclude-module",
        "PySide6.QtPositioning",
        "--exclude-module",
        "PySide6.QtLocation",
        "--exclude-module",
        "PySide6.QtSerialPort",
        "--exclude-module",
        "PySide6.QtWebChannel",
        "--exclude-module",
        "PySide6.QtWebSockets",
        "--exclude-module",
        "PySide6.QtWinExtras",
        "--exclude-module",
        "PySide6.QtNetworkAuth",
        "--exclude-module",
        "PySide6.QtRemoteObjects",
        "--exclude-module",
        "PySide6.QtTextToSpeech",
        "--exclude-module",
        "PySide6.QtWebEngineCore",
        "--exclude-module",
        "PySide6.QtWebEngineWidgets",
        "--exclude-module",
        "PySide6.QtWebEngine",
        "--exclude-module",
        "PySide6.QtBluetooth",
        "--exclude-module",
        "PySide6.QtNfc",
        "--exclude-module",
        "PySide6.QtWebView",
        "--exclude-module",
        "PySide6.QtCharts",
        "--exclude-module",
        "PySide6.QtDataVisualization",
        "--exclude-module",
        "PySide6.QtPdf",
        "--exclude-module",
        "PySide6.QtPdfWidgets",
        "--exclude-module",
        "PySide6.QtQuick3D",
        "--exclude-module",
        "PySide6.QtQuickControls2",
        "--exclude-module",
        "PySide6.QtQuickParticles",
        "--exclude-module",
        "PySide6.QtQuickTest",
        "--exclude-module",
        "PySide6.QtQuickWidgets",
        "--exclude-module",
        "PySide6.QtSensors",
        "--exclude-module",
        "PySide6.QtStateMachine",
        "--exclude-module",
        "PySide6.Qt3DCore",
        "--exclude-module",
        "PySide6.Qt3DRender",
        "--exclude-module",
        "PySide6.Qt3DInput",
        "--exclude-module",
        "PySide6.Qt3DLogic",
        "--exclude-module",
        "PySide6.Qt3DAnimation",
        "--exclude-module",
        "PySide6.Qt3DExtras",
        "main.py",
    ]

    try:
        mode_text = "console" if console_mode else "windowed"
        print(f"Starting PyInstaller development build ({mode_text} mode)...")
        subprocess.run(pyinstaller_command, check=True)
        print(f"PyInstaller development build completed successfully ({mode_text} mode)!")

        if console_mode:
            print("Console mode enabled - logs will be visible in terminal when running the exe")
        else:
            print("Windowed mode - logs will be written to dist/dev/build_dev_debug.log")

        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with error: {e}")
        return False
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it with: pip install pyinstaller")
        return False


def launch_build(extra_args=None):
    """Launch the built executable, killing any existing instance first."""
    exe_name = get_executable_name()
    exe_path = os.path.join("dist", "dev", exe_name)

    if not os.path.exists(exe_path):
        print(f"Error: Built executable not found at {exe_path}")
        return False

    # Build command with extra arguments
    cmd = [exe_path]
    if extra_args:
        cmd.extend(extra_args)

    print(f"Launching {exe_path} with args: {' '.join(extra_args) if extra_args else 'none'}...")
    try:
        if sys.platform.startswith("win"):
            subprocess.Popen(cmd, shell=False)
        else:
            subprocess.Popen(cmd)
        return True
    except Exception as e:
        print(f"Error launching executable: {e}")
        return False


def main():
    """Main function"""
    print("===== Writing Tools - Development Build =====")
    print()

    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Writing Tools - Development Build")
    parser.add_argument(
        "--console",
        action="store_true",
        help="Build with console visible (useful for debugging and seeing logs in real-time)",
    )
    parser.add_argument("extra_args", nargs="*", help="Extra arguments to pass to the built executable")
    args = parser.parse_args()

    console_mode = args.console
    extra_args = args.extra_args or None

    try:
        # Setup project root
        get_project_root()

        # Verify required files exist
        required_files = ["main.py", "requirements.txt"]
        if not verify_requirements(required_files):
            return 1

        # Setup environment (virtual env + dependencies)
        print("Setting up build environment...")
        success, _ = setup_environment()
        if not success:
            print("\nFailed to setup environment!")
            return 1

        # Copy required files
        if not copy_required_files():
            print("\nFailed to copy required files!")
            return 1

        # Stop existing processes (both exe and script)
        terminate_existing_processes(exe_name=get_executable_name(), script_name="main.py")

        # Run build
        if not run_dev_build(console_mode=console_mode):
            print("\nBuild failed!")
            return 1

        # Launch the built application with extra arguments
        print()
        if not launch_build(extra_args=extra_args):
            print("\nFailed to launch built application!")
            return 1

        print("\n===== Development build completed and launched =====")
        print("The executable and required files are in the 'dist/dev' directory.")
        if console_mode:
            print("Console mode was enabled - you should see logs directly in the terminal when the exe runs.")
        else:
            print("Windowed mode - check dist/dev/build_dev_debug.log for detailed logs.")
        return 0

    except KeyboardInterrupt:
        print("\nBuild cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
