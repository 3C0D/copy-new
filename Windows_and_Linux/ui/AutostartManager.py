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

from config.settings import SettingsManager

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
        if not AutostartManager.is_compiled():
            # For development, could return the python script path
            # return f"python {os.path.abspath(sys.argv[0])}"
            return None

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
            startup_path = AutostartManager.get_startup_path()
            if not startup_path:
                logging.warning("Cannot determine startup path")
                return False

            key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"

            try:
                if enable:
                    # Open/create key and set value
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    winreg.SetValueEx(key, "WritingTools", 0, winreg.REG_SZ, startup_path)
                else:
                    # Open key and delete value if it exists
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
                    try:
                        winreg.DeleteValue(key, "WritingTools")
                    except OSError:
                        # Value doesn't exist, that's fine
                        pass

                winreg.CloseKey(key)
                logging.info(f"Windows autostart {'enabled' if enable else 'disabled'}")
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
            startup_path = AutostartManager.get_startup_path()
            if not startup_path:
                logging.warning("Cannot determine startup path")
                return False

            desktop_file_path = AutostartManager.get_linux_desktop_file_path()
            autostart_dir = AutostartManager.get_linux_autostart_dir()

            if enable:
                # Create autostart directory if it doesn't exist
                autostart_dir.mkdir(parents=True, exist_ok=True)

                # Create desktop entry file
                desktop_content = AutostartManager.DESKTOP_ENTRY_TEMPLATE.format(
                    exec_path=startup_path
                )
                desktop_file_path.write_text(desktop_content)

                # Make it executable (optional but good practice)
                os.chmod(desktop_file_path, 0o755)

                logging.info(f"Linux autostart enabled: {desktop_file_path}")
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
            startup_path = AutostartManager.get_startup_path()
            if not startup_path:
                return False

            try:
                key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Run",
                    0,
                    winreg.KEY_READ,
                )
                value, _ = winreg.QueryValueEx(key, "WritingTools")
                winreg.CloseKey(key)

                # Check if the stored path matches our current exe
                return value.lower() == startup_path.lower()

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

            # Check if the desktop file contains our executable path
            startup_path = AutostartManager.get_startup_path()
            if not startup_path:
                return False

            content = desktop_file_path.read_text()
            return f"Exec={startup_path}" in content

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

        Args:
            settings_manager: The SettingsManager instance to sync with

        Returns:
            bool: True if sync was successful, False otherwise
        """
        try:
            system_state = AutostartManager.check_autostart()
            settings_state = getattr(settings_manager, "start_on_boot", False)

            if system_state != settings_state:
                # Update settings to match system state
                settings_manager.start_on_boot = system_state
                logging.debug(f"Synchronized start_on_boot setting: {system_state}")

            return True

        except Exception as e:
            logging.exception(f"Error synchronizing autostart settings: {e}")
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
