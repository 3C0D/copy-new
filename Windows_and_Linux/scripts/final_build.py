#!/usr/bin/env python3
"""
Writing Tools - Final Build Script
Cross-platform final release build with environment setup
"""

import os
import subprocess
import sys
import shutil
import argparse


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
    """Copy required files for final release build to dist/production/"""
    # Create dist/production directory
    production_dir = "dist/production"
    os.makedirs(production_dir, exist_ok=True)

    files_to_copy = [
        ("config/icons", f"{production_dir}/icons"),
        ("config/backgrounds/background.png", f"{production_dir}/background.png"),
        (
            "config/backgrounds/background_dark.png",
            f"{production_dir}/background_dark.png",
        ),
        (
            "config/backgrounds/background_popup.png",
            f"{production_dir}/background_popup.png",
        ),
        (
            "config/backgrounds/background_popup_dark.png",
            f"{production_dir}/background_popup_dark.png",
        ),
    ]

    print("Copying required files for final release to dist/production/...")
    for src, dst in files_to_copy:
        try:
            if os.path.isdir(src):
                if os.path.exists(dst):
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                os.makedirs(os.path.dirname(dst), exist_ok=True)
                shutil.copy2(src, dst)
            print(f"Copied: {src} -> {dst}")
        except Exception as e:
            print(f"Error copying {src}: {e}")
            return False

    # --- Set run_mode to 'build_final' in the copied data.json ---
    setup_build_final_mode()

    print("Note: App will create data.json from constants.py on first run.")
    return True


def setup_build_final_mode():
    """
    Create data.json in dist/production/ for build-final mode with correct run_mode.
    """
    import json
    import os
    from pathlib import Path

    # Import the default configuration
    import sys

    sys.path.insert(0, os.path.abspath('.'))
    from config.data_operations import create_default_settings

    production_dir = Path("dist/production")
    production_dir.mkdir(parents=True, exist_ok=True)

    data_file_path = production_dir / "data.json"

    # Create default settings with build-final run_mode
    settings = create_default_settings()
    settings.system["run_mode"] = "build-final"

    # Convert to dictionary for JSON serialization
    settings_dict = {
        "system": dict(settings.system),
        "actions": {name: dict(action) for name, action in settings.actions.items()},
        "custom_data": settings.custom_data,
    }

    # Save to data.json
    with open(data_file_path, 'w', encoding='utf-8') as f:
        json.dump(settings_dict, f, indent=2, ensure_ascii=False)

    print(f"Created data.json with build-final mode: {data_file_path}")


def clean_build_directories():
    """Clean build directories for a fresh build, preserving dist/dev/"""
    print("Cleaning build directories...")

    # Clean build and __pycache__ completely
    directories_to_clean = ["build", "__pycache__"]
    for directory in directories_to_clean:
        if os.path.exists(directory):
            try:
                shutil.rmtree(directory)
                print(f"Cleaned: {directory}")
            except Exception as e:
                print(f"Warning: Could not clean {directory}: {e}")

    # For dist/, only clean production directory and old files in root
    if os.path.exists("dist"):
        # Remove dist/production if it exists
        production_dir = "dist/production"
        if os.path.exists(production_dir):
            try:
                shutil.rmtree(production_dir)
                print(f"Cleaned: {production_dir}")
            except Exception as e:
                print(f"Warning: Could not clean {production_dir}: {e}")

        # Remove any old files in dist root (from previous builds)
        try:
            for item in os.listdir("dist"):
                item_path = os.path.join("dist", item)
                if os.path.isfile(item_path):
                    os.remove(item_path)
                    print(f"Cleaned old file: {item_path}")
                elif item != "dev":  # Keep dist/dev/ directory
                    if os.path.isdir(item_path):
                        shutil.rmtree(item_path)
                        print(f"Cleaned old directory: {item_path}")
        except Exception as e:
            print(f"Warning: Could not clean dist root: {e}")
        print("Preserved: dist/dev/ (if exists)")
    else:
        print("Directory not found (skipping): dist")

    # Also clean .spec files
    for file in os.listdir("."):
        if file.endswith(".spec"):
            try:
                os.remove(file)
                print(f"Cleaned: {file}")
            except Exception as e:
                print(f"Warning: Could not clean {file}: {e}")


def run_final_build(venv_path="myvenv"):
    """Run PyInstaller build for final release (clean, optimized)"""
    # Use the virtual environment's Python to run PyInstaller
    python_cmd = get_activation_script(venv_path)
    pyinstaller_command = [
        python_cmd,
        "-m",
        "PyInstaller",
        "--onefile",
        "--windowed",
        "--icon=config/icons/app_icon.ico",
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
        "main.py",
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
    # Parse command line arguments
    parser = argparse.ArgumentParser(description="Writing Tools - Final Release Build")
    parser.add_argument(
        "--no-clean",
        action="store_true",
        help="Skip cleaning build directories (faster for development)",
    )
    args = parser.parse_args()

    print("===== Writing Tools - Final Release Build =====")
    print()

    try:
        # Setup project root
        get_project_root()

        # Verify required files exist
        required_files = ["main.py", "requirements.txt"]
        if not verify_requirements(required_files):
            return 1

        # Clean build directories (unless --no-clean is specified)
        if not args.no_clean:
            clean_build_directories()
        else:
            print("Skipping build directory cleanup (--no-clean specified)")

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
        if not run_final_build():
            print("\nBuild failed!")
            return 1

        print("\n===== Final release build completed =====")
        print("The executable and required files are in the 'dist/production' directory.")
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
