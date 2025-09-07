#!/usr/bin/env python3
"""
Writing Tools - Development Build Script
Cross-platform development build with environment setup

Usage:
    python scripts/build_dev.py                    # Build with default mode (see CONSOLE_MODE_DEFAULT)
    python scripts/build_dev.py --console          # Force console mode (visible logs)
    python scripts/build_dev.py --windowed         # Force windowed mode (logs to file)
    python scripts/build_dev.py --console --arg    # Console build with extra args

Console Mode:
    Console window stays visible with real-time logs.
    Very useful for debugging startup issues, systray problems, or provider errors.

Windowed Mode:
    Hides console window. Logs are written to build_dev_debug.log.
    Use for normal testing in production-like mode.
"""

import argparse
import os
import shutil
import subprocess
import sys
from pathlib import Path

# ===== GLOBAL CONFIGURATION =====
DEFAULT_VENV_NAME = "myvenv"
DEFAULT_SCRIPT_NAME = "main.py"
MODE = "build-dev"

# 🔧 DEFAULT CONSOLE MODE - Change this value to modify default behavior
CONSOLE_MODE_DEFAULT = True  # True = console visible by default, False = windowed by default

# Import utilities based on platform
if os.name == "nt":  # Windows
    from utils import (
        check_data,
        clear_console,
        copy_required_files,
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )
else:  # Linux/Unix
    from .utils import (
        check_data,
        clear_console,
        copy_required_files,
        get_executable_name,
        get_project_root,
        get_python_executable,
        setup_environment,
        terminate_existing_processes,
    )


def copy_required_files_dev() -> bool:
    """Copy required files for the development build to dist/dev/."""
    return copy_required_files("development", "dev")


def run_dev_build(venv_path: str = "myvenv", console_mode: bool = False) -> bool:
    """Run PyInstaller build for development (faster, less cleanup)"""

    # Remove existing .spec file if switching console mode to force regeneration
    spec_file = Path("Writing Tools.spec")
    if spec_file.exists():
        try:
            spec_file.unlink()
            print(f"Removed existing {spec_file} to regenerate with new console mode")
        except Exception as e:
            print(f"Warning: Could not remove {spec_file}: {e}")

    # Use the virtual environment's Python to run PyInstaller
    python_cmd: Path = get_python_executable(venv_path)

    # Build icon path
    icon_path = Path("config/icons/app_icon.ico")

    pyinstaller_command = [
        python_cmd,
        "-m",
        "PyInstaller",
        "--onedir",
        "--console" if console_mode else "--windowed",
        f"--icon={icon_path}",
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
        f"{DEFAULT_SCRIPT_NAME}",
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


def launch_build(extra_args: list[str] | None = None) -> bool:
    """Launch the built executable, killing any existing instance first."""
    exe_name = get_executable_name()
    exe_path = Path("dist") / "dev" / exe_name

    if not exe_path.exists():
        print(f"Error: Built executable not found at {exe_path}")
        return False

    # Build command with extra arguments
    cmd = [str(exe_path)]
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Writing Tools - Development Build")

    # Create mutually exclusive group for console/windowed modes
    mode_group = parser.add_mutually_exclusive_group()
    mode_group.add_argument(
        "--console",
        action="store_true",
        help="Force console mode (logs visible in real-time, useful for debugging)",
    )
    mode_group.add_argument(
        "--windowed",
        action="store_true",
        help="Force windowed mode (logs written to file, production-like)",
    )

    parser.add_argument(
        "extra_args", nargs="*", help="Extra arguments to pass to the built executable"
    )
    args = parser.parse_args()

    clear_console()
    print("===== Writing Tools - Development Build =====")
    print()

    # Determine console mode based on arguments or default
    if args.console:
        console_mode = True
        print("🖥️  Console mode forced via --console argument")
    elif args.windowed:
        console_mode = False
        print("🪟  Windowed mode forced via --windowed argument")
    else:
        console_mode = CONSOLE_MODE_DEFAULT
        default_text = "console" if CONSOLE_MODE_DEFAULT else "windowed"
        print(f"⚙️  Using default mode: {default_text} (CONSOLE_MODE_DEFAULT = {CONSOLE_MODE_DEFAULT})")

    extra_args = args.extra_args or None

    try:
        # Setup project root
        project_root = get_project_root()
        print(f"Project root: {project_root.name}")

        # Setup environment (virtual env + dependencies)
        print("Setting up development environment...")
        success, _ = setup_environment(DEFAULT_VENV_NAME)
        if not success:
            print("\nFailed to setup environment!")
            return 1

        # Copy required files
        if not copy_required_files_dev():
            print("\nFailed to copy required files!")
            return 1

        # Stop existing processes (both exe and script)
        print("Terminating existing processes...")
        terminate_existing_processes(
            exe_name=get_executable_name(),
            script_name=DEFAULT_SCRIPT_NAME,
        )

        # Setup development settings
        check_data(MODE)

        # Run build
        if not run_dev_build(console_mode=console_mode):
            print("\nBuild failed!")
            return 1

        # Move built application files from nested folder to dist/dev
        print("Moving built application to 'dist/dev' directory...")
        source_dir = Path("dist/dev/Writing Tools")
        target_dir = Path("dist/dev")

        for item in source_dir.iterdir():
            target_path = target_dir / item.name

            # Remove if already exists
            if target_path.exists():
                if target_path.is_dir():
                    shutil.rmtree(target_path)
                else:
                    target_path.unlink()

            shutil.move(str(item), str(target_path))

        source_dir.rmdir()

        # Launch the built application with extra arguments
        print()
        if not launch_build(extra_args=extra_args):
            print("\nFailed to launch built application!")
            return 1

        print("\n===== Development build completed and launched =====")
        print("The executable and required files are in the 'dist/dev' directory.")
        if console_mode:
            print("Console mode enabled - you should see logs directly in the terminal when the exe runs.")
        else:
            print("Windowed mode - check dist/dev/build_dev_debug.log for detailed logs.")

        return 0

    except KeyboardInterrupt:
        print(f"\n{MODE} cancelled by user.")
        return 1
    except Exception as e:
        print(f"\nUnexpected error in {MODE}: {e}")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)