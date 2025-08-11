#!/usr/bin/env python3
"""
Script to rebuild the development environment and fix settings.
This script ensures all dependencies are properly installed and configured.
"""

import os
import sys
import subprocess
import json
import logging
from pathlib import Path


def setup_logging():
    """Setup logging for the rebuild process"""
    logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")
    return logging.getLogger(__name__)


def run_command(command, cwd=None, check=True):
    """Run a command and return the result"""
    logger = logging.getLogger(__name__)
    logger.info(f"Running: {command}")

    try:
        result = subprocess.run(command, shell=True, cwd=cwd, capture_output=True, text=True, check=check)

        if result.stdout:
            logger.debug(f"STDOUT: {result.stdout}")
        if result.stderr:
            logger.warning(f"STDERR: {result.stderr}")

        return result
    except subprocess.CalledProcessError as e:
        logger.error(f"Command failed: {e}")
        if e.stdout:
            logger.error(f"STDOUT: {e.stdout}")
        if e.stderr:
            logger.error(f"STDERR: {e.stderr}")
        raise


def check_python_environment():
    """Check if we're in the right Python environment"""
    logger = logging.getLogger(__name__)

    # Check if we're in the virtual environment
    venv_path = Path("Windows_and_Linux/myvenv")
    if not venv_path.exists():
        logger.error("Virtual environment not found at Windows_and_Linux/myvenv")
        return False

    # Check if we can import required packages
    try:
        import darkdetect
        import pyperclip
        import pynput
        from PySide6 import QtWidgets

        logger.info("All required packages are available")
        return True
    except ImportError as e:
        logger.warning(f"Missing package: {e}")
        return False


def install_dependencies():
    """Install or update dependencies"""
    logger = logging.getLogger(__name__)

    venv_python = "Windows_and_Linux/myvenv/Scripts/python.exe"
    venv_pip = "Windows_and_Linux/myvenv/Scripts/pip.exe"

    if not os.path.exists(venv_python):
        logger.error("Virtual environment Python not found")
        return False

    # Upgrade pip first using the recommended method
    logger.info("Upgrading pip...")
    try:
        run_command(f'"{venv_python}" -m pip install --upgrade pip')
    except subprocess.CalledProcessError:
        logger.warning("Pip upgrade failed, continuing with current version...")

    # Install requirements
    logger.info("Installing requirements...")
    run_command(f'"{venv_pip}" install -r Windows_and_Linux/requirements.txt')

    return True


def create_vscode_settings():
    """Create or update VS Code settings"""
    logger = logging.getLogger(__name__)

    vscode_dir = Path(".vscode")
    vscode_dir.mkdir(exist_ok=True)

    settings_file = vscode_dir / "settings.json"

    # Get absolute path to Python executable
    python_path = os.path.abspath("Windows_and_Linux/myvenv/Scripts/python.exe")
    python_path = python_path.replace("\\", "/")  # Use forward slashes for JSON

    settings = {
        "python.defaultInterpreter": python_path,
        "python.pythonPath": python_path,
        "python.terminal.activateEnvironment": True,
        "python.terminal.activateEnvInCurrentTerminal": True,
        "python.analysis.extraPaths": ["./Windows_and_Linux"],
        "python.analysis.autoSearchPaths": True,
        "python.analysis.autoImportCompletions": True,
        "python.linting.enabled": True,
        "python.linting.pylintEnabled": False,
        "python.linting.flake8Enabled": False,
        "python.formatting.provider": "black",
        "python.formatting.blackArgs": ["--line-length=100"],
        "files.associations": {"*.py": "python"},
        "python.analysis.typeCheckingMode": "basic",
        "python.analysis.diagnosticMode": "workspace",
        "python.analysis.include": ["./Windows_and_Linux/**"],
        "python.analysis.exclude": ["**/node_modules", "**/__pycache__", "**/build", "**/dist"],
    }

    with open(settings_file, 'w', encoding='utf-8') as f:
        json.dump(settings, f, indent=4)

    logger.info(f"VS Code settings updated: {settings_file}")


def verify_data_files():
    """Verify that data files exist and are valid"""
    logger = logging.getLogger(__name__)

    data_files = ["Windows_and_Linux/dist/dev/data_dev.json", "Windows_and_Linux/dist/final/data.json"]

    for data_file in data_files:
        if os.path.exists(data_file):
            try:
                with open(data_file, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                logger.info(f"✓ Valid data file: {data_file}")
            except json.JSONDecodeError as e:
                logger.error(f"✗ Invalid JSON in {data_file}: {e}")
        else:
            logger.warning(f"⚠ Data file not found: {data_file}")


def main():
    """Main function"""
    logger = setup_logging()

    logger.info("Starting environment rebuild...")

    # Change to project root
    script_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(script_dir)
    logger.info(f"Working directory: {os.getcwd()}")

    try:
        # Check current environment
        logger.info("Checking Python environment...")
        env_ok = check_python_environment()

        if not env_ok:
            logger.info("Installing/updating dependencies...")
            install_dependencies()

        # Create VS Code settings
        logger.info("Creating VS Code settings...")
        create_vscode_settings()

        # Verify data files
        logger.info("Verifying data files...")
        verify_data_files()

        # Final verification
        logger.info("Final verification...")
        if check_python_environment():
            logger.info("✓ Environment rebuild completed successfully!")
            logger.info("Please restart VS Code to apply the new settings.")
            return 0
        else:
            logger.error("✗ Environment rebuild failed!")
            return 1

    except Exception as e:
        logger.error(f"Error during rebuild: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
