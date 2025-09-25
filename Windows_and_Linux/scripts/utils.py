#!/usr/bin/env python3
"""
Writing Tools - Utility Functions
Common functions shared across build and launch scripts
"""

import hashlib
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path


def get_project_root() -> Path:
    """Get the Windows_and_Linux directory (the working directory for the project)"""
    script_dir = Path(__file__).parent  # scripts/
    windows_linux_dir = script_dir.parent  # Windows_and_Linux/
    os.chdir(windows_linux_dir)
    return windows_linux_dir


def check_data(mode: str) -> None:
    """Checks data file path to provide feedback to the user based on build mode"""

    if mode == "build-final":
        print("Setting up production settings...")
        dist_dir = Path("dist/production")
        data_filename = "data.json"
        settings_type = "production"
    else:  # build-dev and dev (dev_script.py)
        print("Setting up development settings...")
        dist_dir = Path("dist/dev")
        data_filename = "data_dev.json"
        settings_type = "development"

    data_path = dist_dir / data_filename
    cwd = Path(".")

    if data_path.exists():
        print(f"Using existing {settings_type} settings from: {cwd / data_path}")
    else:
        print(
            f"No existing {settings_type} settings found. Application will create settings on first run.",
        )
        print(f"Settings will be saved to: {cwd / data_path}")


def clear_console() -> None:
    """Clear console screen (cross-platform)"""
    os.system("cls" if os.name == "nt" else "clear")


def copy_required_files(build_type: str, target_dir: str) -> bool:
    """
    Copy required files for build to the specified target directory.

    Args:
        build_type (str): Type of build ('development' or 'production')
        target_dir (str): Target directory name (e.g., 'dev', 'production')
    """
    # Create target directory
    dist_target_dir = Path(f"dist/{target_dir}")
    dist_target_dir.mkdir(parents=True, exist_ok=True)
    cwd = Path(".")

    # --- Asset files (always copied) ---
    assets_to_copy = [
        (Path("src/config/icons"), dist_target_dir / "icons"),
        (Path("src/config/backgrounds/background.png"), dist_target_dir / "background.png"),
        (
            Path("src/config/backgrounds/background_dark.png"),
            dist_target_dir / "background_dark.png",
        ),
        (
            Path("src/config/backgrounds/background_popup.png"),
            dist_target_dir / "background_popup.png",
        ),
        (
            Path("src/config/backgrounds/background_popup_dark.png"),
            dist_target_dir / "background_popup_dark.png",
        ),
    ]

    print(f"Copying required files for {build_type} build to {cwd}/dist/{target_dir}/...")

    # --- Copy assets ---
    for src, dst in assets_to_copy:
        try:
            if not src.exists():
                print(f"Warning: Asset file/directory not found: {src}")
                continue
            if src.is_dir():
                if dst.exists():
                    shutil.rmtree(dst)
                shutil.copytree(src, dst)
            else:
                dst.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(src, dst)
            print(f"Copied asset: {src} -> {dst}")
        except Exception as e:
            print(f"Error copying asset {src}: {e}")
            return False

    # --- Notes spécifiques selon le type de build ---
    if build_type == "development":
        print("Note: build-dev mode - settings will be saved to dist/dev/data_dev.json")
    else:  # production
        print("Note: final-dev mode - settings will be saved to dist/dev/data_dev.json")

    return True


def python_exe_version() -> str:
    """Find the best Python executable available"""
    python_candidates = ["python3", "python", "py"]

    for candidate in python_candidates:
        if shutil.which(candidate):
            try:
                # Test if it's Python 3
                result = subprocess.run(
                    [candidate, "--version"],
                    check=False,
                    capture_output=True,
                    text=True,
                )
                if result.returncode == 0 and "Python 3" in result.stdout:
                    return candidate
            except Exception:
                continue

    raise RuntimeError("Python 3 not found. Please install Python 3.")


def calculate_file_hash(file_path: Path) -> str | None:
    """Calculate SHA256 hash of a file"""
    if not os.path.exists(file_path):
        return None

    sha256_hash = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            sha256_hash.update(chunk)
    return sha256_hash.hexdigest()


def create_virtual_environment(venv_path: str, python_cmd: str) -> bool:
    """Create a virtual environment if it doesn't exist"""
    if os.path.exists(venv_path):
        print("Virtual environment already exists.")
        return True

    print("Creating virtual environment...")
    try:
        # Try using venv module first (preferred)
        subprocess.run([python_cmd, "-m", "venv", venv_path], check=True)
        print("Virtual environment created successfully.")
        return True
    except subprocess.CalledProcessError:
        try:
            # Fallback: try virtualenv
            print("Trying virtualenv as fallback...")
            subprocess.run(
                [python_cmd, "-m", "pip", "install", "virtualenv"],
                check=True,
            )
            subprocess.run([python_cmd, "-m", "virtualenv", venv_path], check=True)
            print("Virtual environment created with virtualenv.")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to create virtual environment: {e}")
            return False


def get_python_executable(venv_path: str) -> Path:
    """Get the appropriate activation script path for the platform"""
    venv_dir = Path(venv_path)
    if sys.platform.startswith("win"):
        return venv_dir / "Scripts" / "python.exe"
    return venv_dir / "bin" / "python"


def get_pip_executable(venv_path: str) -> Path:
    """Get the pip executable path for the virtual environment"""
    venv = Path(venv_path)

    if sys.platform.startswith("win"):
        return (venv / "Scripts" / "pip.exe").resolve()
    return (venv / "bin" / "pip").resolve()


def install_dependencies(venv_path: str, requirements_path: str) -> bool:
    """Install or update dependencies and remove unused ones using hash comparison"""
    venv = Path(venv_path)
    requirements = Path(requirements_path)

    hash_file = venv / "installed_requirements.hash"
    previous_requirements_file = venv / "previous_requirements.txt"

    # Calculate current requirements hash
    current_hash = calculate_file_hash(requirements)
    if not current_hash:
        print("Warning: requirements.txt not found. Skipping dependency installation.")
        return True

    # Check if dependencies are already installed
    installed_hash = ""
    if hash_file.exists():
        try:
            with open(hash_file, encoding="utf-8") as f:
                installed_hash = f.read().strip()
        except Exception:
            pass

    if current_hash != installed_hash:
        print("Requirements changed, synchronizing dependencies...")

        try:
            python_cmd = get_python_executable(venv_path)
            requirements_abs_path = requirements.resolve()

            # Read current requirements
            with open(requirements, encoding="utf-8") as f:
                current_requirements = set()
                for line in f:
                    line = line.strip()
                    if line and not line.startswith("#"):
                        # Extract package name (before ==, >=, <=, etc.)
                        pkg_name = (
                            line.split("==")[0]
                            .split(">=")[0]
                            .split("<=")[0]
                            .split("<")[0]
                            .split(">")[0]
                            .strip()
                        )
                        current_requirements.add(pkg_name.lower())

            # Read previous requirements if exists
            previous_requirements = set()
            if previous_requirements_file.exists():
                try:
                    with open(previous_requirements_file, encoding="utf-8") as f:
                        for line in f:
                            line = line.strip()
                            if line and not line.startswith("#"):
                                pkg_name = (
                                    line.split("==")[0]
                                    .split(">=")[0]
                                    .split("<=")[0]
                                    .split("<")[0]
                                    .split(">")[0]
                                    .strip()
                                )
                                previous_requirements.add(pkg_name.lower())
                except Exception:
                    pass

            # Find packages to remove (in previous but not in current)
            packages_to_remove = previous_requirements - current_requirements

            # Remove obsolete packages
            if packages_to_remove:
                print(f"🗑️  Removing obsolete packages: {', '.join(packages_to_remove)}")
                cmd_uninstall = [python_cmd, "-m", "pip", "uninstall", "-y"] + list(
                    packages_to_remove
                )
                try:
                    subprocess.run(cmd_uninstall, check=True, capture_output=True)
                    print("✅ Obsolete packages removed successfully.")
                except subprocess.CalledProcessError as e:
                    print(f"⚠️  Warning: Some packages could not be removed: {e}")

            # Install/update current requirements.-q silent install
            print("📦 Installing/updating dependencies...")
            cmd_install = [
                python_cmd,
                "-m",
                "pip",
                "install",
                "-q",
                "-r",
                str(requirements_abs_path),
            ]
            subprocess.run(cmd_install, check=True)

            # Save current state for next time
            shutil.copy2(requirements, previous_requirements_file)
            with open(hash_file, "w", encoding="utf-8") as f:
                f.write(current_hash)

            print("Dependencies synchronized successfully.")
            return True

        except subprocess.CalledProcessError as e:
            print(f"Error: Failed to synchronize dependencies: {e}")
            return False
    else:
        print("Dependencies already up to date.")
        return True


def kill_existing_exe_process(process_name: str) -> None:
    """Terminate an existing process by its name."""
    try:
        if sys.platform.startswith("win"):
            # Use taskkill to force termination of the process by its image name
            command = ["taskkill", "/F", "/IM", process_name]
            result = subprocess.run(command, check=False, capture_output=True, text=True)

            # Check result and provide appropriate feedback
            if result.returncode == 0:
                print(f"Successfully terminated existing process: {process_name}")
            elif result.returncode == 128:
                # Process not found - this is normal
                print(f"No existing process found for: {process_name}")
            else:
                # Check if the error message indicates "not found"
                if "not found" in result.stderr.lower() or "cannot find" in result.stderr.lower():
                    print(f"No existing process found for: {process_name}")
                else:
                    # Actual error
                    print(
                        f"Warning: Could not terminate {process_name}. Exit code: {result.returncode}"
                    )
                    if result.stderr:
                        print(f"Error: {result.stderr.strip()}")

        else:
            # For Linux/macOS, use pkill with exact process name matching
            # First try exact match
            command = ["pkill", "-x", process_name]
            result = subprocess.run(command, check=False, capture_output=True, text=True)

            if result.returncode == 0:
                print(f"Successfully terminated existing process: {process_name}")
            else:
                # Try fuzzy match as fallback
                command = ["pkill", "-f", process_name]
                result = subprocess.run(command, check=False, capture_output=True, text=True)

                if result.returncode == 0:
                    print(f"Successfully terminated existing process (fuzzy match): {process_name}")
                else:
                    print(f"No existing process found for: {process_name}")

    except Exception as e:
        print(f"Warning: Error while trying to kill process {process_name}: {e}")


def kill_python_script_process(script_name: str) -> None:
    """Terminate a Python script process by its command line."""
    try:
        if sys.platform.startswith("win"):
            # Method 1: Use tasklist + taskkill for more reliable process detection
            # First, get the list of processes with command lines
            list_command = [
                "wmic",
                "process",
                "where",
                f"name='python.exe' and commandline like '%{script_name}%'",
                "get",
                "processid",
                "/format:value",
            ]

            result = subprocess.run(list_command, check=False, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout:
                # Extract process IDs
                pids = []
                for line in result.stdout.split("\n"):
                    if line.startswith("ProcessId=") and line.strip() != "ProcessId=":
                        pid = line.split("=")[1].strip()
                        if pid:
                            pids.append(pid)

                if pids:
                    # Kill each process by PID
                    killed_count = 0
                    for pid in pids:
                        kill_cmd = ["taskkill", "/F", "/PID", pid]
                        kill_result = subprocess.run(
                            kill_cmd, check=False, capture_output=True, text=True
                        )
                        if kill_result.returncode == 0:
                            killed_count += 1

                    if killed_count > 0:
                        print(
                            f"Successfully terminated {killed_count} Python process(es) running: {script_name}"
                        )
                    else:
                        print(
                            f"Found Python processes for {script_name} but failed to terminate them"
                        )
                else:
                    print(f"No existing Python process found for: {script_name}")
            else:
                print(f"No existing Python process found for: {script_name}")

        else:
            # For macOS and Linux, use more precise matching
            # Use pgrep to find processes first, then pkill
            grep_command = ["pgrep", "-f", f"python.*{script_name}"]
            result = subprocess.run(grep_command, check=False, capture_output=True, text=True)

            if result.returncode == 0 and result.stdout.strip():
                # Found processes, now kill them
                kill_command = ["pkill", "-f", f"python.*{script_name}"]
                kill_result = subprocess.run(
                    kill_command, check=False, capture_output=True, text=True
                )

                if kill_result.returncode == 0:
                    pids = result.stdout.strip().split("\n")
                    print(
                        f"Successfully terminated {len(pids)} Python process(es) running: {script_name}"
                    )
                else:
                    print(f"Found Python processes for {script_name} but failed to terminate them")
            else:
                print(f"No existing Python process found for: {script_name}")

    except Exception as e:
        print(f"Warning: Error while trying to kill Python script process {script_name}: {e}")


def get_executable_name(base_name: str = "Writing Tools") -> str:
    """Get the correct executable name for the current platform"""
    if sys.platform.startswith("win"):
        return f"{base_name}.exe"
    return base_name


def terminate_existing_processes(
    exe_name: str | None = None, script_name: str | None = None
) -> None:
    """Terminate any existing Writing Tools processes (both exe and script)"""
    print("Checking for and terminating any existing Writing Tools processes...")

    # Kill Python script first (to avoid conflicts)
    if script_name:
        print(f"Looking for Python script processes: {script_name}")
        kill_python_script_process(script_name)

    # Then kill executable processes
    if exe_name:
        print(f"Looking for executable processes: {exe_name}")
        kill_existing_exe_process(exe_name)

    # Small delay to ensure processes are fully terminated
    time.sleep(0.5)
    print("Process termination check completed.")


def verify_requirements(required_files: list[Path]) -> bool:
    """Verify that required files exist before building"""
    missing_files = []
    for file_path in required_files:
        if not os.path.exists(file_path):
            missing_files.append(file_path)

    if missing_files:
        print("Error: Missing required files:")
        for file_path in missing_files:
            print(f"  - {file_path}")
        return False

    return True


# Removed copy_newer_file - no longer needed with new config structure


def setup_environment(
    venv_path: str = "myvenv", requirements_path: str = "requirements.txt"
) -> tuple[bool, str | None]:
    """Setup virtual environment and install dependencies

    Returns a tuple of two values:
    - a boolean indicating whether the setup was successful
    - the path to the Python executable used in the virtual environment
    """
    try:
        # Find Python executable
        python_cmd = python_exe_version()
        print(f"Using Python: {python_cmd}")

        # Create virtual environment
        if not create_virtual_environment(venv_path, python_cmd):
            print("\nFailed to create virtual environment!")
            return False, None

        # Install dependencies
        if not install_dependencies(venv_path, requirements_path):
            print("\nFailed to install dependencies!")
            return False, None

        return True, python_cmd

    except Exception as e:
        print(f"Error setting up environment: {e}")
        return False, None


class BuildTimer:
    """A simple timer class to measure build duration"""

    def __init__(self):
        self.start_time = None
        self.end_time = None

    def start(self):
        """Start the timer"""
        self.start_time = time.time()
        print("⏱️  Build timer started...")

    def stop(self):
        """Stop the timer and return elapsed time"""
        if self.start_time is None:
            return 0.0

        self.end_time = time.time()
        return self.end_time - self.start_time

    def get_elapsed_time(self):
        """Get elapsed time without stopping the timer"""
        if self.start_time is None:
            return 0.0
        return time.time() - self.start_time

    def print_duration(self, build_type: str = "build"):
        """Print the build duration in a formatted way"""
        if self.start_time is None:
            return

        if self.end_time is None:
            elapsed = self.stop()
        else:
            elapsed = self.end_time - self.start_time

        # Format time nicely
        if elapsed < 60:
            time_str = f"{elapsed:.1f} seconds"
        elif elapsed < 3600:
            minutes = int(elapsed // 60)
            seconds = elapsed % 60
            time_str = f"{minutes} minute{'s' if minutes > 1 else ''} and {seconds:.1f} seconds"
        else:
            hours = int(elapsed // 3600)
            minutes = int((elapsed % 3600) // 60)
            seconds = elapsed % 60
            time_str = f"{hours} hour{'s' if hours > 1 else ''}, {minutes} minute{'s' if minutes > 1 else ''} and {seconds:.1f} seconds"

        print(f"⏱️  {build_type.capitalize()} completed in {time_str}")


# PyInstaller exclusions shared between build scripts
PYINSTALLER_EXCLUSIONS = [
    "tkinter",
    "unittest",
    "IPython",
    "jedi",
    "email_validator",
    "cryptography",
    "psutil",
    "pyzmq",
    "tornado",
    # PySide6 unused modules
    "PySide6.QtNetwork",
    "PySide6.QtXml",
    "PySide6.QtQml",
    "PySide6.QtQuick",
    "PySide6.QtQuickWidgets",
    "PySide6.QtPrintSupport",
    "PySide6.QtSql",
    "PySide6.QtTest",
    "PySide6.QtSvg",
    "PySide6.QtSvgWidgets",
    "PySide6.QtHelp",
    "PySide6.QtMultimedia",
    "PySide6.QtMultimediaWidgets",
    "PySide6.QtOpenGL",
    "PySide6.QtOpenGLWidgets",
    "PySide6.QtPositioning",
    "PySide6.QtLocation",
    "PySide6.QtSerialPort",
    "PySide6.QtWebChannel",
    "PySide6.QtWebSockets",
    "PySide6.QtWinExtras",
    "PySide6.QtNetworkAuth",
    "PySide6.QtRemoteObjects",
    "PySide6.QtTextToSpeech",
    "PySide6.QtWebEngineCore",
    "PySide6.QtWebEngineWidgets",
    "PySide6.QtWebEngine",
    "PySide6.QtBluetooth",
    "PySide6.QtNfc",
    "PySide6.QtWebView",
    "PySide6.QtCharts",
    "PySide6.QtDataVisualization",
    "PySide6.QtPdf",
    "PySide6.QtPdfWidgets",
    "PySide6.QtQuick3D",
    "PySide6.QtQuickControls2",
    "PySide6.QtQuickParticles",
    "PySide6.QtQuickTest",
    "PySide6.QtQuickWidgets",
    "PySide6.QtSensors",
    "PySide6.QtStateMachine",
    "PySide6.Qt3DCore",
    "PySide6.Qt3DRender",
    "PySide6.Qt3DInput",
    "PySide6.Qt3DLogic",
    "PySide6.Qt3DAnimation",
    "PySide6.Qt3DExtras",
]
