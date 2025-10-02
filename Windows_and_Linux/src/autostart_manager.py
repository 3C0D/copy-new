"""
Modular architecture with separation of OS-specific methods
(set_autostart_windows, set_autostart_linux, etc.). Main methods
(set_autostart, check_autostart) automatically detect the OS and call
the appropriate method

For Linux, uses XDG standard with .desktop files in ~/.config/autostart/
Automatically creates the autostart directory if it doesn't exist and generates a desktop entry file compliant with Linux standards. ~/.config/autostart/writing-tools.desktop that will be executed at session startup.

Key improvements over previous version:
- Better path handling using pathlib.Path for Linux
- XDG support with respect for XDG_CONFIG_HOME environment variable
- Standard Desktop Entry template for Linux
- Enhanced logging with detailed messages for debugging
- New get_platform_info() method to get platform information

Compatibility:
- Windows: Registry (as before)
- Linux: XDG autostart
"""

import logging
import os
import sys
from pathlib import Path

from .config.settings import SettingsManager

try:
    if sys.platform.startswith("win32"):
        import winreg
    else:
        winreg = None
except ImportError:
    winreg = None


class AutostartManager:
    """
    Manages the autostart functionality for Writing Tools.
    Handles setting/removing autostart entries on Windows and Linux.
    Synchronizes autostart state with application settings.
    """

    DESKTOP_ENTRY_TEMPLATE = """[Desktop Entry]
Type=Application
Name=Writing Tools
Comment=Writing Tools Application
Exec={exec_path}
Icon=writing-tools
Terminal=false
StartupNotify=false
X-GNOME-Autostart-enabled=true
Hidden=false
"""

    @staticmethod
    def is_compiled():
        """
        Check if we're running from a compiled exe or source.
        """
        return hasattr(sys, "frozen") and hasattr(sys, "_MEIPASS")

    @staticmethod
    def get_startup_path():
        """
        Get the path that should be used for autostart.
        Returns None if running from source.
        """
        compiled = AutostartManager.is_compiled()
        logging.debug(f"AutostartManager.is_compiled(): {compiled}")
        logging.debug(f"sys.executable: {sys.executable}")
        logging.debug(f"sys.frozen: {hasattr(sys, 'frozen')}")
        logging.debug(f"sys._MEIPASS: {hasattr(sys, '_MEIPASS')}")

        if not compiled:
            # For development, could return the python script path
            # return f"python {os.path.abspath(sys.argv[0])}"
            logging.debug("Not compiled, returning None for startup path")
            return None

        logging.debug(f"Compiled exe path: {sys.executable}")
        return sys.executable

    @staticmethod
    def get_linux_autostart_dir():
        """
        Get the autostart directory for Linux systems.
        Usually ~/.config/autostart/
        """
        xdg_config_home = os.environ.get("XDG_CONFIG_HOME")
        if xdg_config_home:
            config_dir = Path(xdg_config_home)
        else:
            config_dir = Path.home() / ".config"

        autostart_dir = config_dir / "autostart"
        return autostart_dir

    @staticmethod
    def get_linux_desktop_file_path():
        """
        Get the path for the desktop entry file on Linux.
        """
        autostart_dir = AutostartManager.get_linux_autostart_dir()
        return autostart_dir / "writing-tools.desktop"

    @staticmethod
    def check_dev_startup_exists() -> bool:
        """
        Check if the development startup entry exists.

        Returns:
            bool: True if dev startup is configured, False otherwise
        """
        if winreg is None:
            return False

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

    @staticmethod
    def disable_dev_startup_if_exists() -> bool:
        """
        Disable the development startup entry if it exists.

        Returns:
            bool: True if disabled or didn't exist, False if error occurred
        """
        if winreg is None:
            return True

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE,
            ) as key:
                try:
                    winreg.DeleteValue(key, "WritingToolsDevStartup")
                    logging.info("Disabled conflicting development startup entry")
                    return True
                except OSError:
                    # Value doesn't exist, that's fine
                    return True
        except Exception as e:
            logging.warning(f"Could not disable dev startup entry: {e}")
            return False

    @staticmethod
    def disable_normal_startup_if_exists() -> bool:
        """
        Disable the normal startup entry if it exists.

        Returns:
            bool: True if disabled or didn't exist, False if error occurred
        """
        if winreg is None:
            return True

        try:
            with winreg.OpenKey(
                winreg.HKEY_CURRENT_USER,
                r"Software\Microsoft\Windows\CurrentVersion\Run",
                0,
                winreg.KEY_WRITE,
            ) as key:
                try:
                    winreg.DeleteValue(key, "WritingTools")
                    logging.info("Disabled conflicting normal startup entry")
                    return True
                except OSError:
                    # Value doesn't exist, that's fine
                    return True
        except Exception as e:
            logging.warning(f"Could not disable normal startup entry: {e}")
            return False

    @staticmethod
    def get_dev_startup_command():
        """
        Get the command for development startup.
        """
        project_root = Path(__file__).parent.parent
        venv_python = project_root / "myvenv" / "Scripts" / "python.exe"
        dev_script = project_root / "scripts" / "dev_script.py"
        debug_args = "--console"
        command = f'cmd /k "cd /d "{project_root}" && "{venv_python}" "{dev_script}" {debug_args}"'
        return command

    @staticmethod
    def get_startup_command():
        """
        Get the command/path for autostart.
        Returns the exe path if compiled, or the dev command if in dev mode.
        """
        compiled = AutostartManager.is_compiled()
        if compiled:
            return AutostartManager.get_startup_path()
        else:
            return AutostartManager.get_dev_startup_command()

    @staticmethod
    def set_autostart_windows(enable: bool) -> bool:
        """
        Enable or disable autostart for Windows.

        Args:
            enable: True to enable autostart, False to disable

        Returns:
            bool: True if operation succeeded, False if failed
        """
        if winreg is None:
            logging.warning("Windows registry module not available")
            return False

        try:
            command = AutostartManager.get_startup_command()
            if not command:
                logging.warning("Cannot determine startup command")
                return False

            compiled = AutostartManager.is_compiled()
            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
            key_name = "WritingTools" if compiled else "WritingToolsDevStartup"

            if compiled:
                # Disable dev startup if exists
                AutostartManager.disable_dev_startup_if_exists()
            else:
                # Disable normal startup if exists
                AutostartManager.disable_normal_startup_if_exists()

            try:
                if enable:
                    # Open/create key and set value
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, key_name, 0, winreg.REG_SZ, command)
                else:
                    # Open key and delete value if it exists
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    try:
                        winreg.DeleteValue(key, key_name)
                    except OSError:
                        # Value doesn't exist, that's fine
                        pass

                winreg.CloseKey(key)
                logging.info(f"Windows autostart {'enabled' if enable else 'disabled'} ({'compiled' if compiled else 'dev'})")
                return True

            except OSError as e:
                logging.exception(f"Failed to modify autostart registry: {e}")
                return False

        except Exception as e:
            logging.exception(f"Error managing Windows autostart: {e}")
            return False

    @staticmethod
    def set_autostart_linux(enable: bool) -> bool:
        """
        Enable or disable autostart for Linux.

        Args:
            enable: True to enable autostart, False to disable

        Returns:
            bool: True if operation succeeded, False if failed
        """
        try:
            compiled = AutostartManager.is_compiled()
            desktop_file_path = AutostartManager.get_linux_desktop_file_path()
            autostart_dir = AutostartManager.get_linux_autostart_dir()

            if enable:
                # Create autostart directory if it doesn't exist
                autostart_dir.mkdir(parents=True, exist_ok=True)

                exec_path = AutostartManager.get_startup_command()
                if not exec_path:
                    logging.warning("Cannot determine startup command")
                    return False

                # Create desktop entry file
                desktop_content = AutostartManager.DESKTOP_ENTRY_TEMPLATE.format(
                    exec_path=exec_path
                )
                desktop_file_path.write_text(desktop_content)

                # Make it executable (optional but good practice)
                os.chmod(desktop_file_path, 0o755)

                logging.info(f"Linux autostart enabled: {desktop_file_path} ({'compiled' if compiled else 'dev'})")
                return True
            else:
                # Remove desktop entry file if it exists
                if desktop_file_path.exists():
                    desktop_file_path.unlink()
                    logging.info(f"Linux autostart disabled: {desktop_file_path}")
                return True

        except Exception as e:
            logging.exception(f"Error managing Linux autostart: {e}")
            return False

    @staticmethod
    def set_autostart(enable: bool) -> bool:
        """
        Enable or disable autostart for Writing Tools.

        Args:
            enable: True to enable autostart, False to disable

        Returns:
            bool: True if operation succeeded, False if failed or unsupported
        """
        if sys.platform.startswith("win32"):
            return AutostartManager.set_autostart_windows(enable)
        elif sys.platform.startswith("linux"):
            return AutostartManager.set_autostart_linux(enable)
        else:
            logging.warning(f"Autostart not supported on platform: {sys.platform}")
            return False

    @staticmethod
    def check_autostart_windows() -> bool:
        """
        Check if Writing Tools is set to start automatically on Windows.

        Returns:
            bool: True if autostart is enabled, False if disabled
        """
        if winreg is None:
            return False

        try:
            compiled = AutostartManager.is_compiled()
            key_name = "WritingTools" if compiled else "WritingToolsDevStartup"

            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ,
                )
                value, _ = winreg.QueryValueEx(key, key_name)
                winreg.CloseKey(key)

                expected_command = AutostartManager.get_startup_command()
                if not expected_command:
                    return False
                # Check if the stored value matches our expected command
                return value == expected_command

            except OSError:
                # Key or value doesn't exist
                return False

        except Exception as e:
            logging.exception(f"Error checking Windows autostart status: {e}")
            return False

    @staticmethod
    def check_autostart_linux() -> bool:
        """
        Check if Writing Tools is set to start automatically on Linux.

        Returns:
            bool: True if autostart is enabled, False if disabled
        """
        try:
            desktop_file_path = AutostartManager.get_linux_desktop_file_path()

            if not desktop_file_path.exists():
                return False

            content = desktop_file_path.read_text()
            expected_command = AutostartManager.get_startup_command()
            if not expected_command:
                return False
            return f"Exec={expected_command}" in content

        except Exception as e:
            logging.exception(f"Error checking Linux autostart status: {e}")
            return False

    @staticmethod
    def check_autostart() -> bool:
        """
        Check if Writing Tools is set to start automatically.

        Returns:
            bool: True if autostart is enabled, False if disabled or unsupported
        """
        if sys.platform.startswith("win32"):
            return AutostartManager.check_autostart_windows()
        elif sys.platform.startswith("linux"):
            return AutostartManager.check_autostart_linux()
        else:
            return False

    @staticmethod
    def sync_with_settings(settings_manager: SettingsManager) -> bool:
        """
        Synchronize autostart state between system and settings.
        Updates settings to match system state if they differ.
        Also handles mode changes (dev <-> compiled) by migrating autostart entries.

        Args:
            settings_manager: The SettingsManager instance to sync with

        Returns:
            bool: True if sync was successful, False otherwise
        """
        try:
            system_state = AutostartManager.check_autostart()
            settings_state = getattr(settings_manager, "start_on_boot", False)

            # Check if we need to migrate due to mode change
            if settings_state and AutostartManager._needs_autostart_migration():
                logging.info("Autostart mode migration needed, updating system entries")
                # Remove any conflicting entries and set the correct one for current mode
                success = AutostartManager.set_autostart(True)
                if success:
                    system_state = True  # Now it should be enabled
                else:
                    logging.warning("Failed to migrate autostart entry")

            if system_state != settings_state:
                # Update settings to match system state
                settings_manager.start_on_boot = system_state
                logging.debug(f"Synchronized start_on_boot setting: {system_state}")

            return True

        except Exception as e:
            logging.exception(f"Error synchronizing autostart settings: {e}")
            return False

    @staticmethod
    def _needs_autostart_migration() -> bool:
        """
        Check if autostart entries need migration due to mode change.

        Returns:
            bool: True if migration is needed
        """
        try:
            compiled = AutostartManager.is_compiled()

            if sys.platform.startswith("win32"):
                if winreg is None:
                    return False

                # Check if the wrong key exists
                wrong_key = "WritingToolsDevStartup" if compiled else "WritingTools"
                try:
                    with winreg.OpenKey(
                        winreg.HKEY_CURRENT_USER,
                        r"Software\Microsoft\Windows\CurrentVersion\Run",
                        0,
                        winreg.KEY_READ,
                    ) as key:
                        winreg.QueryValueEx(key, wrong_key)
                        return True  # Wrong key exists, migration needed
                except OSError:
                    return False  # Wrong key doesn't exist, no migration needed

            elif sys.platform.startswith("linux"):
                desktop_file_path = AutostartManager.get_linux_desktop_file_path()
                if not desktop_file_path.exists():
                    return False

                content = desktop_file_path.read_text()
                if compiled:
                    # In compiled mode, should not have python dev_script
                    return "dev_script.py" in content
                else:
                    # In dev mode, should not have exe path
                    startup_path = AutostartManager.get_startup_path()
                    if startup_path:
                        return f"Exec={startup_path}" in content
                    return False

            return False

        except Exception as e:
            logging.exception(f"Error checking autostart migration need: {e}")
            return False

    @staticmethod
    def set_autostart_with_sync(enable: bool, settings_manager: SettingsManager) -> bool:
        """
        Set autostart state and synchronize with settings.

        Args:
            enable: Whether to enable autostart
            settings_manager: The SettingsManager instance to sync with

        Returns:
            bool: True if operation succeeded, False otherwise
        """
        try:
            # Update system autostart
            success = AutostartManager.set_autostart(enable)

            if success:
                # Update settings to match
                settings_manager.start_on_boot = enable
                logging.debug(f"Set autostart to {enable} and updated settings")

            return success

        except Exception as e:
            logging.exception(f"Error setting autostart with sync: {e}")
            return False

    # not used. used for testing?
    @staticmethod
    def get_platform_info() -> dict:
        """
        Get information about the current platform and autostart support.

        Returns:
            dict: Platform information including OS, support status, and method
        """
        info = {
            "platform": sys.platform,
            "os_name": None,
            "autostart_supported": False,
            "autostart_method": None,
            "is_compiled": AutostartManager.is_compiled(),
            "startup_path": AutostartManager.get_startup_path(),
        }

        if sys.platform.startswith("win32"):
            info["os_name"] = "Windows"
            info["autostart_supported"] = True
            info["autostart_method"] = "Registry"
        elif sys.platform.startswith("linux"):
            info["os_name"] = "Linux"
            info["autostart_supported"] = True
            info["autostart_method"] = "XDG Desktop Entry"
            info["autostart_location"] = str(AutostartManager.get_linux_desktop_file_path())
        else:
            info["os_name"] = "Unknown"

        return info
