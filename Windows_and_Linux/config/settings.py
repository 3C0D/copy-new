"""
Writing Tools - Unified Settings Manager
Handles loading, saving, and merging of all application settings with smart attribute access
"""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path
from typing import Any

import darkdetect

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

    IMPORTANT: Auto-save limitations
    - ✅ settings_manager.provider = "openai"           # Auto-saves
    - ✅ settings_manager.actions = {...}               # Auto-saves
    - ❌ settings_manager.providers[key] = value        # Requires manual save()
    - ❌ settings_manager.actions[key] = value          # Requires manual save()

    For dict modifications, call save() manually or use helper methods.
    """

    # File system constants
    DIST_DEV_PATH = "dist/dev"
    DATA_FILE = "data.json"
    DATA_DEV_FILE = "data_dev.json"

    # Logging constants
    LOG_MAX_BYTES = 1024 * 1024  # 1MB
    LOG_BACKUP_COUNT = 1

    # Internal attributes that shouldn't be proxied to settings
    _INTERNAL_ATTRS = {
        "mode",
        "base_dir",
        "settings",
        "_logger",
        "data_file",
        "default_settings",
        "actions",  # Handled by explicit property
        "providers",  # Handled by explicit property
        "color_mode",  # Handled by explicit property
        "DIST_DEV_PATH",
        "DATA_FILE",
        "DATA_DEV_FILE",
        "LOG_MAX_BYTES",
        "LOG_BACKUP_COUNT",
        "_INTERNAL_ATTRS",
    }

    def __init__(self, mode: str = "dev"):
        """Initialize the settings manager with intelligent mode detection and fallback logic."""
        self._logger = logging.getLogger(__name__)
        self.mode: str = mode
        self._logger.debug(f"Set mode in settings: {self.mode}")
        self.base_dir: Path = self._get_base_directory()
        self._logger.debug(f"Base directory in settings: {self.base_dir.absolute().name}")
        self.default_settings: UnifiedSettings = create_default_settings()  # Always initialized!
        self.data_file: Path = self._resolve_data_file_path()
        self.settings: UnifiedSettings = self.load_settings()

        # Setup logging (with build context detection inside _setup_logging)
        self._setup_logging()

        self._log_initialization_info()

    def __getattr__(self, name: str) -> Any:
        """
        Smart attribute access for system settings only.
        Special cases (actions, providers) are handled by explicit properties.

        Example:
            settings_manager.hotkey  # -> settings.system["hotkey"]
        """
        # Don't intercept internal attributes or handled properties
        if name in self._INTERNAL_ATTRS:
            raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

        # System settings only - special cases handled by properties
        try:
            settings = object.__getattribute__(self, "settings")
            if name in settings.system:
                return settings.system[name]
        except AttributeError:
            # settings n'existe pas encore (pendant __init__)
            pass

        # Not found - raise standard AttributeError
        raise AttributeError(f"'{self.__class__.__name__}' object has no attribute '{name}'")

    def __setattr__(self, name: str, value: Any) -> None:
        """
        Smart attribute assignment for settings.

        Example:
            settings_manager.hotkey = "ctrl+space"  # -> settings.system["hotkey"]
        """
        # Internal class attributes and private attributes
        if name in self._INTERNAL_ATTRS or name.startswith("_"):
            super().__setattr__(name, value)
            return

        # During __init__, settings doesn't exist yet
        if hasattr(self, "settings"):
            self.settings.system[name] = value
            self.save()  # Save immediately
        else:
            super().__setattr__(name, value)

    @property
    def actions(self) -> dict[str, ActionConfig]:
        """Access to action configurations."""
        return self.settings.actions

    @actions.setter
    def actions(self, value: dict[str, ActionConfig]) -> None:
        """Set action configurations."""
        self.settings.actions = value
        self.save()

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
        self.save()

    @property
    def color_mode(self) -> str:
        """Current color mode ('auto', 'dark', or 'light')."""
        if "color_mode" not in self.settings.system:
            self.settings.system["color_mode"] = "auto"

        current_mode = self.settings.system["color_mode"]
        if current_mode == "auto":
            return "dark" if darkdetect.isDark() else "light"

        return current_mode

    @color_mode.setter
    def color_mode(self, value: str) -> None:
        """Set the color mode."""
        self.settings.system["color_mode"] = value
        self.save()

    #
    # CORE SETTINGS OPERATIONS
    #

    def load_settings(self) -> UnifiedSettings:
        """Load settings from file and merge with defaults."""
        # self._ensure_directories_exist() redundant

        if self.data_file.exists():
            user_data = self._load_user_data()
            if user_data is not None:
                self.settings = create_unified_settings_from_data(user_data)
        else:
            self._logger.debug(f"No settings file found at {self.data_file}, using defaults")
            self.settings = self.default_settings

        # Update run_mode to match current execution mode
        self.settings.system["run_mode"] = self.mode
        return self.settings

    def save(self) -> bool:
        """Save the current settings to file."""
        if not self.settings:
            self._logger.error("No settings to save")
            return False

        self._ensure_directories_exist()
        return self._write_settings_to_file()

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

        # For Ollama, we need both a valid model AND Ollama to be installed
        if active_provider == "ollama":
            # Check if api_model is configured and not empty
            api_model = provider_config.get("api_model", "")
            model_configured = bool(api_model and api_model.strip())

            # Also check if Ollama is actually installed and available
            if model_configured:
                try:
                    # Import here to avoid circular imports
                    from aiprovider import is_ollama_installed

                    ollama_available = is_ollama_installed()
                    return ollama_available
                except ImportError:
                    # If we can't import the function, assume Ollama is not available
                    return False
            return False

        # For all other providers, we require a valid API key
        if "api_key" in provider_config:
            api_key_valid = bool(provider_config["api_key"])
            # Also check if api_model is configured for providers that use it
            if "api_model" in provider_config:
                api_model = provider_config.get("api_model", "")
                api_model_valid = bool(api_model and api_model.strip())
                return api_key_valid and api_model_valid
            return api_key_valid

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

    def _get_base_directory(self) -> Path:
        """Get the base directory based on execution context."""
        if getattr(sys, "frozen", False):
            return Path(sys.executable).parent
        return Path(sys.argv[0]).parent

    def _resolve_data_file_path(self) -> Path:
        """Determine the data file path with intelligent fallback logic."""
        if self._is_build_final():
            return self.base_dir / self.DATA_FILE
        elif self._is_build_dev():
            return self.base_dir / self.DATA_DEV_FILE
        else:
            return self.base_dir / self.DIST_DEV_PATH / self.DATA_DEV_FILE

    def _ensure_directories_exist(self) -> None:
        """Ensure necessary directories exist for dev and build-dev modes."""
        if self._is_build_final():
            return

        # Check if we're already in a dist directory to avoid creating nested dist/dev
        if "dist" not in str(self.base_dir):
            dist_dev_dir = self.base_dir / self.DIST_DEV_PATH
            dist_dev_dir.mkdir(parents=True, exist_ok=True)

    def _load_user_data(self) -> dict[str, Any] | None:
        """Load user data from the data file."""
        try:
            with open(self.data_file, encoding="utf-8") as f:
                raw_data = json.load(f)

            # Validate that it's a dictionary
            if not isinstance(raw_data, dict):
                self._logger.error(
                    f"Invalid data format in {self.data_file}: expected dict, got {type(raw_data)}"
                )
                return None

            self._logger.debug(f"Loaded user data from {self.data_file}")
            return raw_data
        except (json.JSONDecodeError, Exception) as e:
            self._logger.error(f"Error loading settings from {self.data_file}: {e}")
            self._logger.debug("Using default settings")
            return None

    def _write_settings_to_file(self) -> bool:
        """Write settings data to the file."""
        try:
            self._logger.debug("Saving settings:")
            self._logger.debug(f"  data_file: {self.data_file}")

            data = self._serialize_settings()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._logger.debug(f"Settings saved to {self.data_file}")
            return True
        except Exception as e:
            self._logger.error(f"Failed to write settings: {e}")
            return False

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

    def _setup_logging(self) -> None:
        """Setup file logging for dev and build-dev modes."""
        if not self._is_development_mode():
            return

        try:
            self._configure_file_handler()
        except Exception as e:
            self._logger.error(f"Failed to setup file logging: {e}")

    def _configure_file_handler(self) -> None:
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
        file_handler.setFormatter(
            logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        )

        root_logger = logging.getLogger()
        root_logger.addHandler(file_handler)
        self._logger.debug(f"File logging enabled: {log_file}")

    def _get_log_file_path(self) -> Path:
        """Get the appropriate log file path based on mode."""
        base_dir_name = Path(self.base_dir.absolute().name)
        if self.mode == "build-dev":
            # same directory as the executable
            self._logger.debug(f"'build-dev' logging path: {base_dir_name / 'build_dev_debug.log'}")
            return self.base_dir / "build_dev_debug.log"
        else:  # dev
            # in dist/dev/
            self._logger.debug(
                f"'dev' logging path: {base_dir_name / self.DIST_DEV_PATH / 'dev_debug.log'}"
            )
            return self.base_dir / self.DIST_DEV_PATH / "dev_debug.log"

    def _log_initialization_info(self) -> None:
        """Log debug information about initialization."""
        self._logger.debug("SettingsManager initialized:")
        self._logger.debug(f"  base_dir: {self.base_dir.name}")
        self._logger.debug(f"  mode: {self.mode}")
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

    def _is_build_dev(self) -> bool:
        """Check if running in build-dev mode."""
        return self.mode == "build-dev"
