#!/usr/bin/env python3
"""
Writing Tools - Development Build Script
Cross-platform development build with environment setup
"""

import os
import subprocess
import sys
import shutil
import json

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
    Create data_dev.json in dist/dev/ for build-dev mode.
    """
    dist_dev_dir = "dist/dev"
    os.makedirs(dist_dev_dir, exist_ok=True)

    data_dev_path = os.path.join(dist_dev_dir, "data_dev.json")

    # No need to create data_dev.json - app will create it from constants.py

    print(f"Build-dev data file ready: {data_dev_path}")


def run_dev_build(venv_path="myvenv"):
    """Run PyInstaller build for development (faster, less cleanup)"""
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
        print("Starting PyInstaller development build...")
        subprocess.run(pyinstaller_command, check=True)
        print("PyInstaller development build completed successfully!")
        return True

    except subprocess.CalledProcessError as e:
        print(f"Error: Build failed with error: {e}")
        return False
    except FileNotFoundError:
        print(
            "Error: PyInstaller not found. Please install it with: pip install pyinstaller"
        )
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

    print(
        f"Launching {exe_path} with args: {' '.join(extra_args) if extra_args else 'none'}..."
    )
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

    # Parse command line arguments (skip script name)
    extra_args = sys.argv[1:] if len(sys.argv) > 1 else None

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
        terminate_existing_processes(
            exe_name=get_executable_name(), script_name="main.py"
        )

        # Run build
        if not run_dev_build():
            print("\nBuild failed!")
            return 1

        # Launch the built application with extra arguments
        print()
        if not launch_build(extra_args=extra_args):
            print("\nFailed to launch built application!")
            return 1

        print("\n===== Development build completed and launched =====")
        print("The executable and required files are in the 'dist/dev' directory.")
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
