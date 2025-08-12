"""
Writing Tools - Unified Settings Manager
Handles loading, saving, and merging of all application settings
"""

import json
import logging
import os
import sys
from pathlib import Path
from typing import Dict, Any

from .interfaces import UnifiedSettings, SystemConfig, ActionConfig
from .constants import DEFAULT_SYSTEM, DEFAULT_ACTIONS


class SettingsManager:
    """
    Unified settings manager inspired by Obsidian's approach.
    Handles loading, saving, and intelligent merging of settings.
    """

    def __init__(self, mode: str = None):
        """
        Initialize the settings manager with intelligent mode detection and fallback logic.

        Args:
            mode: Operating mode ("dev", "build-dev", "build-final"). If None, auto-detect.
        """
        # Get the directory where the executable/script is located and set mode
        if mode is not None:
            # Use provided mode
            self.mode = mode
        elif getattr(sys, "frozen", False):
            # Running as compiled executable - auto-detect mode
            exe_dir = os.path.dirname(sys.executable)
            if os.path.exists(os.path.join(exe_dir, "data.json")):
                self.mode = "build-final"
            elif os.path.exists(os.path.join(exe_dir, "data_dev.json")):
                self.mode = "build-dev"
            else:
                self.mode = "build-dev"  # fallback
        else:
            # Running as script
            self.mode = "dev"

        # Set base directory
        if getattr(sys, "frozen", False):
            base_dir = os.path.dirname(sys.executable)
        else:
            base_dir = os.path.dirname(sys.argv[0])

        self.base_dir = Path(base_dir)

        # Set paths based on mode
        if self.mode == "build-final":
            # Final build: no config subdirectory structure
            self.config_dir = self.base_dir
        else:
            # Dev and build-dev: use config subdirectory structure
            self.config_dir = self.base_dir / "config"

        self.settings: UnifiedSettings = None
        self._logger = logging.getLogger(__name__)

        # Setup file logging for build-dev mode
        self._setup_file_logging()

        # Debug logging for path resolution
        self._logger.debug(f"SettingsManager initialized:")
        self._logger.debug(f"  base_dir: {self.base_dir}")
        self._logger.debug(f"  mode: {self.mode}")
        self._logger.debug(f"  config_dir: {self.config_dir}")

        # Determine data file location with intelligent fallback
        self.data_file = self._determine_data_file_path()
        self._logger.debug(f"  data_file: {self.data_file}")

    def _setup_file_logging(self):
        """
        Setup file logging for dev and build-dev modes.
        Logs debug information to debug.log for development analysis.
        """

        # Only enable file logging for development modes, not production
        if self.mode in ["dev", "build-dev"]:
            try:
                # Determine log file location based on mode
                if self.mode == "build-dev":
                    # For build-dev, log file goes in the same directory as the executable
                    log_file = self.base_dir / "build_dev_debug.log"
                else:
                    # For dev mode, log file goes in dist/dev/
                    log_file = self.base_dir / "dist" / "dev" / "dev_debug.log"
                    # Ensure the directory exists
                    log_file.parent.mkdir(parents=True, exist_ok=True)

                # Setup rotating file handler to limit log size
                from logging.handlers import RotatingFileHandler

                file_handler = RotatingFileHandler(
                    log_file,
                    mode="a",
                    maxBytes=1024 * 1024,  # 1MB max file size
                    backupCount=2,  # Keep 2 backup files if log exceeds max size
                    encoding="utf-8",
                )
                file_handler.setLevel(logging.DEBUG)

                # Create formatter for file logging
                formatter = logging.Formatter(
                    "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
                )
                file_handler.setFormatter(formatter)

                # Add handler to root logger to capture all debug messages
                root_logger = logging.getLogger()
                root_logger.addHandler(file_handler)

                self._logger.debug(f"File logging enabled: {log_file}")
                self._logger.debug(f"SettingsManager initialized in mode: {self.mode}")

            except Exception as e:
                self._logger.error(f"Failed to setup file logging: {e}")

    def _determine_data_file_path(self) -> Path:
        """
        Determine the data file path with intelligent fallback logic.
        Dev and build-dev modes use dist/dev/data_dev.json.
        Final build uses data.json. 

        Returns:
            Path: The path to the data.json file to use
        """

        if self.mode == "build-final":
            # Final build: data.json directly in exe directory
            final_data_file = self.base_dir / "data.json"
            self._logger.debug(f"Using build-final data file: {final_data_file}")
            return final_data_file
        elif self.mode == "build-dev":
            # Build-dev: data_dev.json directly in exe directory
            data_dev_file = self.base_dir / "data_dev.json"
            self._logger.debug(
                    f"Using build-dev data file in dist: {data_dev_file}"
                )
            return data_dev_file
        else:
            # Dev mode: data_dev.json in dist/dev/
            dist_dev_dir = self.base_dir / "dist" / "dev"
            data_dev_file = dist_dev_dir / "data_dev.json"
            self._logger.debug(f"Using dev data file: {data_dev_file}")
            return data_dev_file

    def load_settings(self) -> UnifiedSettings:
        """
        Load settings using Obsidian-style logic:
        this.settings = Object.assign({}, DEFAULT_SETTINGS, await this.loadData());

        Returns:
            UnifiedSettings: The loaded and merged settings
        """
        # Ensure dist/dev directory exists for dev and build-dev modes
        if self.mode != "build-final":
            # Check if we're already in a dist directory to avoid creating nested dist/dev
            in_dist = "dist" in str(self.base_dir)
            if not in_dist:
                dist_dev_dir = self.base_dir / "dist" / "dev"
                dist_dev_dir.mkdir(parents=True, exist_ok=True)

        # Start with DEFAULT_SETTINGS from constants.py
        self.settings = self._create_default_settings()

        # If user data file exists, merge it with defaults
        if self.data_file.exists():
            try:
                with open(self.data_file, "r", encoding="utf-8") as f:
                    user_data = json.load(f)

                self._logger.debug(f"Loaded user data from {self.data_file}")
                self.settings = self._merge_with_defaults(user_data)

            except (json.JSONDecodeError, Exception) as e:
                self._logger.error(f"Error loading settings from {self.data_file}: {e}")
                self._logger.info("Using default settings")
                # Keep default settings on error
        else:
            self._logger.debug(
                f"No settings file found at {self.data_file}, using defaults"
            )

        # Update run_mode in settings to match current mode
        if self.settings:
            self.settings.system.run_mode = self.mode

        return self.settings

    def has_providers_configured(self) -> bool:
        """
        Check if any providers are configured.

        A provider is considered configured if:
        1. There are providers in custom_data, OR
        2. The system has a non-empty provider and api_key

        Returns:
            bool: True if providers are configured, False otherwise
        """
        if not self.settings:
            return False

        # Check custom_data providers first
        if self.settings.custom_data:
            providers = self.settings.custom_data.get("providers", {})
            if providers and len(providers) > 0:
                return True

        # Check system settings for basic configuration
        system = self.settings.system
        if (
            system.provider
            and system.provider.strip()
            and system.api_key
            and system.api_key.strip()
        ):
            return True

        return False

    def save_settings(self) -> bool:
        """
        Save the current settings.

        Returns:
            bool: True if save was successful, False otherwise
        """
        if not self.settings:
            self._logger.error("No settings to save")
            return False

        # For dev and build-dev modes, handle dist/dev/ logic
        if self.mode != "build-final":
            # Check if we're already in a dist directory to avoid creating nested dist/dev
            in_dist = "dist" in str(self.base_dir)
            if not in_dist:
                # Ensure dist/dev directory exists
                dist_dev_dir = self.base_dir / "dist" / "dev"
                dist_dev_dir.mkdir(parents=True, exist_ok=True)

        try:
            # Debug logging before saving
            self._logger.debug(f"Saving settings:")
            self._logger.debug(f"  mode: {self.mode}")
            self._logger.debug(f"  data_file: {self.data_file}")
            self._logger.debug(f"  data_file.parent: {self.data_file.parent}")

            # Ensure the directory exists
            self.data_file.parent.mkdir(parents=True, exist_ok=True)
            self._logger.debug(f"Created directory: {self.data_file.parent}")

            data = self._serialize_settings()
            with open(self.data_file, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)

            self._logger.debug(f"Settings saved to {self.data_file}")
            return True

        except Exception as e:
            self._logger.error(f"Error saving settings to {self.data_file}: {e}")
            return False

    def update_system_setting(self, key: str, value: Any) -> bool:
        """
        Update a system setting and save immediately.

        Args:
            key: The setting key to update
            value: The new value

        Returns:
            bool: True if update and save were successful
        """
        if not self.settings:
            self._logger.error("Settings not loaded")
            return False

        if hasattr(self.settings.system, key):
            setattr(self.settings.system, key, value)
            return self.save_settings()
        else:
            self._logger.error(f"Unknown system setting: {key}")
            return False

    def update_action(self, action_name: str, action_config: ActionConfig) -> bool:
        """
        Update or add an action configuration and save immediately.

        Args:
            action_name: Name of the action
            action_config: The action configuration

        Returns:
            bool: True if update and save were successful
        """
        if not self.settings:
            self._logger.error("Settings not loaded")
            return False

        self.settings.actions[action_name] = action_config
        return self.save_settings()

    def remove_action(self, action_name: str) -> bool:
        """
        Remove an action configuration and save immediately.

        Args:
            action_name: Name of the action to remove

        Returns:
            bool: True if removal and save were successful
        """
        if not self.settings:
            self._logger.error("Settings not loaded")
            return False

        if action_name in self.settings.actions:
            del self.settings.actions[action_name]
            return self.save_settings()
        else:
            self._logger.warning(f"Action not found: {action_name}")
            return False

    def _create_default_settings(self) -> UnifiedSettings:
        """Create a copy of the default settings"""
        return UnifiedSettings(
            system=SystemConfig(**DEFAULT_SYSTEM.__dict__),
            actions={k: ActionConfig(**v.__dict__) for k, v in DEFAULT_ACTIONS.items()},
            custom_data={},
        )

    def _merge_with_defaults(self, user_data: Dict[str, Any]) -> UnifiedSettings:
        """
        Merge user data with default settings.
        User data overrides defaults.

        Args:
            user_data: User configuration data from JSON

        Returns:
            UnifiedSettings: Merged settings
        """
        # Merge system settings
        system_data = {**DEFAULT_SYSTEM.__dict__}

        # Handle system data (modern format only)
        user_system_data = {}
        if "system" in user_data and isinstance(user_data["system"], dict):
            user_system_data = user_data["system"].copy()

            self._logger.debug(f"Merging system data: {user_system_data}")
            system_data.update(user_system_data)

        # Merge actions settings
        actions_data = {}
        # Start with defaults
        for name, action in DEFAULT_ACTIONS.items():
            actions_data[name] = ActionConfig(**action.__dict__)

        # Override with user actions
        if "actions" in user_data and isinstance(user_data["actions"], dict):
            for name, action_dict in user_data["actions"].items():
                if isinstance(action_dict, dict):
                    # Merge with default action if it exists, otherwise create new
                    if name in DEFAULT_ACTIONS:
                        merged_action = {**DEFAULT_ACTIONS[name].__dict__}
                        merged_action.update(action_dict)
                        actions_data[name] = ActionConfig(**merged_action)
                    else:
                        # New custom action - ensure all required fields are present
                        action_data = {
                            "prefix": action_dict.get("prefix", ""),
                            "instruction": action_dict.get("instruction", ""),
                            "icon": action_dict.get("icon", "icons/custom"),
                            "open_in_window": action_dict.get("open_in_window", False),
                        }
                        actions_data[name] = ActionConfig(**action_data)

        # Merge custom data
        custom_data = user_data.get("custom_data", {})

        return UnifiedSettings(
            system=SystemConfig(**system_data),
            actions=actions_data,
            custom_data=custom_data,
        )

    def _serialize_settings(self) -> Dict[str, Any]:
        """
        Convert settings to dictionary for JSON serialization.

        Returns:
            Dict: Serializable settings data
        """
        # Ensure run_mode is up to date before serialization
        if self.settings:
            self.settings.system.run_mode = self.mode

        return {
            "system": self.settings.system.__dict__,
            "actions": {
                name: action.__dict__ for name, action in self.settings.actions.items()
            },
            "custom_data": self.settings.custom_data,
        }
