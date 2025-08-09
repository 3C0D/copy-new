"""
Writing Tools - Unified Settings Manager
Handles loading, saving, and merging of all application settings with smart attribute access
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from .data_operations import (
    create_default_settings,
    create_unified_settings_from_data,
)
from .interfaces import ActionConfig, ProviderConfig, UnifiedSettings


class SettingsManager:
    """
    Unified settings manager with smart attribute access.

    Features:
    - Direct access: settings_manager.hotkey instead of settings_manager.settings.system["hotkey"]
    - Direct assignment: settings_manager.hotkey = "new_value"
    - Automatic defaults: never returns None
    - Extensible: add new properties dynamically without modifying the class
    """

    # File system constants
    DIST_DEV_PATH = "dist/dev"
    DATA_FILE = "data.json"
    DATA_DEV_FILE = "data_dev.json"

    # Logging constants
    LOG_MAX_BYTES = 1024 * 1024  # 1MB
    LOG_BACKUP_COUNT = 2

    # Internal attributes that shouldn't be proxied to settings
    _INTERNAL_ATTRS = {
        'mode',
        'base_dir',
        'config_dir',
        'settings',
        '_logger',
        'data_file',
        'DIST_DEV_PATH',
        'DATA_FILE',
        'DATA_DEV_FILE',
        'LOG_MAX_BYTES',
        'LOG_BACKUP_COUNT',
        '_INTERNAL_ATTRS',
    }

    def __init__(self, mode: str = ""):
        """Initialize the settings manager with intelligent mode detection and fallback logic."""
        self.mode = self._detect_mode(mode)
        self.base_dir = self._get_base_directory()
        self.config_dir = self._resolve_config_directory()
        self.settings: UnifiedSettings = create_default_settings()  # Always initialized!
        self._logger = logging.getLogger(__name__)
        self._setup_logging()
        self.data_file = self._resolve_data_file_path()
        self._log_initialization_info()

    @property
    def actions(self) -> dict[str, ActionConfig]:
        """Access to action configurations."""
        return self.settings.actions

    @actions.setter
    def actions(self, value: dict[str, ActionConfig]) -> None:
        """Set action configurations."""
        self.settings.actions = value

    @property
    def providers(self) -> dict[str, ProviderConfig]:
        """Access to provider configurations."""
        # Ensure providers key exists in custom_data
        if "providers" not in self.settings.custom_data:
            self.settings.custom_data["providers"] = {}
        return self.settings.custom_data["providers"]

    @providers.setter
    def providers(self, value: dict[str, ProviderConfig]) -> None:
        """Set provider configurations."""
        self.settings.custom_data["providers"] = value

    def __getattr__(self, name: str):
        """
        Smart attribute access for system settings only.
        Special cases (actions, providers) are handled by explicit properties.

        Example:
            settings_manager.hotkey  # -> settings.system["hotkey"]
        """
        # System settings only - special cases handled by properties
        if name in self.settings.system:
            return self.settings.system[name]

        # Not found - raise standard AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value):
        """
        Smart attribute assignment for settings.

        Example:
            settings_manager.hotkey = "ctrl+space"  # -> settings.system["hotkey"]
        """
        # Internal class attributes and private attributes
        if name in self._INTERNAL_ATTRS or name.startswith('_'):
            super().__setattr__(name, value)
            return

        # During __init__, settings doesn't exist yet
        if not hasattr(self, 'settings'):
            super().__setattr__(name, value)
            return

        # Special cases are now handled by properties, so we can remove them here
        # Default: assign to system settings
        self.settings.system[name] = value

    #
    # CORE SETTINGS OPERATIONS
    #

    def load_settings(self) -> UnifiedSettings:
        """Load settings from file and merge with defaults."""
        self._ensure_directories_exist()

        if self.data_file.exists():
            user_data = self._load_user_data()
            if user_data is not None:
                self.settings = create_unified_settings_from_data(user_data)
        else:
            self._logger.debug(f"No settings file found at {self.data_file}, using defaults")

        # Update run_mode to match current execution mode
        self.settings.system["run_mode"] = self.mode
        return self.settings

    def save_settings(self) -> bool:
        """Save the current settings to file."""
        if not self.settings:
            self._logger.error("No settings to save")
            return False

        self._ensure_directories_exist()

        try:
            return self._write_settings_to_file()
        except Exception as e:
            self._logger.error(f"Error saving settings to {self.data_file}: {e}")
            return False

    def save(self) -> bool:
        """Convenience method for save_settings()."""
        return self.save_settings()

    #
    # PROVIDER-SPECIFIC OPERATIONS
    #

    def has_providers_configured(self) -> bool:
        """Check if the active provider is properly configured."""
        providers = self.providers
        active_provider = getattr(self, "provider", None)

        if not active_provider or active_provider not in providers:
            return False

        provider_config = providers[active_provider]

        # For Ollama, we don't require an API key
        if active_provider == "ollama":
            return True

        # For all other providers, we require a valid API key
        if "api_key" in provider_config:
            return bool(provider_config["api_key"])

        # If no api_key field exists, the provider is not configured
        return False

    #
    # ACTION MANAGEMENT (simplified)
    #

    def update_action(self, action_name: str, action_config: ActionConfig) -> bool:
        """Update or add an action configuration and save immediately."""
        self.settings.actions[action_name] = action_config
        return self.save()

    def remove_action(self, action_name: str) -> bool:
        """Remove an action configuration and save immediately."""
        if action_name in self.settings.actions:
            del self.settings.actions[action_name]
            return self.save()

        self._logger.warning(f"Action not found: {action_name}")
        return False

    #
    # INTERNAL METHODS - FILE SYSTEM OPERATIONS
    #

    def _detect_mode(self, provided_mode: str) -> str:
        """Detect the operating mode with intelligent fallback logic."""
        if provided_mode:
            return provided_mode

        if not getattr(sys, "frozen", False):
            return "dev"

        # Running as compiled executable - auto-detect mode
        exe_dir = os.path.dirname(sys.executable)
        if os.path.exists(os.path.join(exe_dir, self.DATA_FILE)):
            return "build-final"
        if os.path.exists(os.path.join(exe_dir, self.DATA_DEV_FILE)):
            return "build-dev"
        return "build-dev"  # fallback

    def _get_base_directory(self) -> Path:
        """Get the base directory based on execution context."""
        if getattr(sys, "frozen", False):
            return Path(os.path.dirname(sys.executable))
        return Path(os.path.dirname(sys.argv[0]))

    def _resolve_config_directory(self) -> Path:
        """Resolve the configuration directory based on mode."""
        if self._is_build_final():
            return self.base_dir
        return self.base_dir / "config"

    def _resolve_data_file_path(self) -> Path:
        """Determine the data file path with intelligent fallback logic."""
        if self._is_build_final():
            return self.base_dir / self.DATA_FILE
        if self.mode == "build-dev":
            return self.base_dir / self.DATA_DEV_FILE
        # Dev mode: data_dev.json in dist/dev/
        return self.base_dir / self.DIST_DEV_PATH / self.DATA_DEV_FILE

    def _ensure_directories_exist(self):
        """Ensure necessary directories exist for dev and build-dev modes."""
        if self._is_build_final():
            return

        # Check if we're already in a dist directory to avoid creating nested dist/dev
        if "dist" not in str(self.base_dir):
            dist_dev_dir = self.base_dir / self.DIST_DEV_PATH
            dist_dev_dir.mkdir(parents=True, exist_ok=True)

    def _load_user_data(self) -> Optional[Dict[str, Any]]:
        """Load user data from the data file."""
        try:
            with open(self.data_file, encoding="utf-8") as f:
                raw_data = json.load(f)

            # Validate that it's a dictionary
            if not isinstance(raw_data, dict):
                self._logger.error(f"Invalid data format in {self.data_file}: expected dict, got {type(raw_data)}")
                return None

            self._logger.debug(f"Loaded user data from {self.data_file}")
            return raw_data
        except (json.JSONDecodeError, Exception) as e:
            self._logger.error(f"Error loading settings from {self.data_file}: {e}")
            self._logger.info("Using default settings")
            return None

    def _write_settings_to_file(self) -> bool:
        """Write settings data to the file."""
        self._logger.debug("Saving settings:")
        self._logger.debug(f"  mode: {self.mode}")
        self._logger.debug(f"  data_file: {self.data_file}")

        # Ensure the directory exists
        self.data_file.parent.mkdir(parents=True, exist_ok=True)

        data = self._serialize_settings()
        with open(self.data_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        self._logger.debug(f"Settings saved to {self.data_file}")
        return True

    def _serialize_settings(self) -> dict[str, Any]:
        """Convert settings to dictionary for JSON serialization."""
        if self.settings is None:
            raise ValueError("Cannot serialize settings: settings not loaded")

        # Ensure run_mode is up to date before serialization
        self.settings.system["run_mode"] = self.mode

        return {
            "system": dict(self.settings.system),  # Convert TypedDict to regular dict
            "actions": {
                name: dict(action) for name, action in self.settings.actions.items()
            },  # Convert ActionConfig TypedDict to dict
            "custom_data": {
                "update_available": self.settings.custom_data.get("update_available", False),
                "providers": self.providers,
            },
        }

    #
    # LOGGING SETUP
    #

    def _setup_logging(self):
        """Setup file logging for dev and build-dev modes."""
        if not self._is_development_mode():
            return

        try:
            self._configure_file_handler()
        except Exception as e:
            self._logger.error(f"Failed to setup file logging: {e}")

    def _configure_file_handler(self):
        """Configure the rotating file handler for logging."""
        log_file = self._get_log_file_path()
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = RotatingFileHandler(
            log_file,
            mode="a",
            maxBytes=self.LOG_MAX_BYTES,
            backupCount=self.LOG_BACKUP_COUNT,
            encoding="utf-8",
        )
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        self._logger.debug(f"File logging enabled: {log_file}")

    def _get_log_file_path(self) -> Path:
        """Get the appropriate log file path based on mode."""
        if self.mode == "build-dev":
            return self.base_dir / "build_dev_debug.log"
        return self.base_dir / self.DIST_DEV_PATH / "dev_debug.log"

    def _log_initialization_info(self):
        """Log debug information about initialization."""
        self._logger.debug("SettingsManager initialized:")
        self._logger.debug(f"  base_dir: {self.base_dir}")
        self._logger.debug(f"  mode: {self.mode}")
        self._logger.debug(f"  config_dir: {self.config_dir}")
        self._logger.debug(f"  data_file: {self.data_file}")

    #
    # HELPER METHODS
    #

    def _is_build_final(self) -> bool:
        """Check if running in build-final mode."""
        return self.mode == "build-final"

    def _is_development_mode(self) -> bool:
        """Check if running in development mode (dev or build-dev)."""
        return self.mode in ["dev", "build-dev"]
