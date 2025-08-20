#!/usr/bin/env python3
"""
Writing Tools - Final Build Script
Cross-platform final release build with environment setup
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

# Configuration
DEFAULT_VENV_NAME = "myvenv"
DEFAULT_SCRIPT_NAME = "main.py"
MODE = "build-final"

if os.name == "nt":  # Windows
    from utils import (
        check_data,
        clear_console,
        copy_required_files,
        get_activation_script,
        get_executable_name,
        get_project_root,
        setup_environment,
        terminate_existing_processes,
    )
else:  # Linux/Unix
    from .utils import (
        check_data,
        clear_console,
        copy_required_files,
        get_activation_script,
        get_executable_name,
        get_project_root,
        setup_environment,
        terminate_existing_processes,
    )


def copy_required_files_production():
    """Copy required files for final release build to dist/production/"""
    return copy_required_files("production", "production")


def clean_build_directories():
    """Clean build directories for a fresh build, preserving dist/dev/"""
    print("Cleaning build directories...")

    # Clean build and __pycache__ completely
    directories_to_clean = [Path("build"), Path("__pycache__")]
    for directory in directories_to_clean:
        if directory.exists():
            try:
                shutil.rmtree(directory)
                print(f"Cleaned: {directory}")
            except Exception as e:
                print(f"Warning: Could not clean {directory}: {e}")

    # For dist/, only clean production directory and old files in root
    dist_dir = Path("dist")
    if dist_dir.exists():
        # Remove dist/production if it exists
        dist_production_dir = dist_dir / "production"
        if dist_production_dir.exists():
            try:
                shutil.rmtree(dist_production_dir)
                print(f"Cleaned: {dist_production_dir}")
            except Exception as e:
                print(f"Warning: Could not clean {dist_production_dir}: {e}")

        # Remove any old files in dist root (from previous builds)
        try:
            for item in dist_dir.iterdir():
                if item.is_file():
                    item.unlink()
                    print(f"Cleaned old file: {item}")
                elif item.name != "dev":  # Keep dist/dev/ directory
                    if item.is_dir():
                        shutil.rmtree(item)
                        print(f"Cleaned old directory: {item}")
        except Exception as e:
            print(f"Warning: Could not clean dist root: {e}")

        print("Preserved: dist/dev/ (if exists)")
    else:
        print("Directory not found (skipping): dist")

    # Also clean .spec files
    current_dir = Path(".")
    for file in current_dir.glob("*.spec"):
        try:
            file.unlink()
            print(f"Cleaned: {file}")
        except Exception as e:
            print(f"Warning: Could not clean {file}: {e}")


def run_build_final(venv_path="myvenv"):
    """Run PyInstaller build for final release (clean, optimized)"""
    # Use the virtual environment's Python to run PyInstaller
    python_cmd = get_activation_script(venv_path)

    # Build icon path
    icon_path = Path("config/icons/app_icon.ico")

    pyinstaller_command = [
        python_cmd,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        f"--icon={icon_path}",
        "--name=Writing Tools",
        "--distpath=dist/production",  # Output to dist/production/
        "--clean",  # Clean build for final release
        "--noconfirm",
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
        print("Starting PyInstaller final build...")
        subprocess.run(pyinstaller_command, check=True)
        print("PyInstaller final build completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with error: {e}")
        return False
    except FileNotFoundError:
        print("Error: PyInstaller not found. Please install it with: pip install pyinstaller")
        return False


def main():
    """Main function"""
    clear_console()
    print("===== Writing Tools - Final Release Build =====")
    print()

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

        # Clean build directories
        clean_build_directories()

        # Setup environment (virtual env + dependencies)
        print("Setting up build environment...")
        success, _ = setup_environment()
        if not success:
            print("\nFailed to setup environment!")
            return 1

        # Copy required files
        if not copy_required_files_production():
            print("\nFailed to copy required files!")
            return 1

        # Stop existing processes (both exe and script)
        print("Terminating existing processes...")
        terminate_existing_processes(exe_name=get_executable_name(), script_name=DEFAULT_SCRIPT_NAME)

        check_data(MODE)

        # Run build
        if not run_build_final():
            print("\nBuild failed!")
            return 1

        print("\n===== Final release build completed =====")
        print("The executable and required files are in the 'dist/production' directory.")
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
