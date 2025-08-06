"""
Writing Tools - Data Operations Module
Contains all functions for creating, modifying, and manipulating configuration data
"""

from .constants import (
    DEFAULT_ACTIONS_VALUES,
    DEFAULT_MODELS,
    DEFAULT_SYSTEM_VALUES,
    PROVIDER_DISPLAY_NAMES,
)
from .interfaces import ActionConfig, SystemConfig, UnifiedSettings


def get_default_model_for_provider(provider: str) -> str:
    """Get the default model for a given provider"""
    return DEFAULT_MODELS.get(provider, "")


def get_provider_display_name(provider: str) -> str:
    """Get the display name for a provider"""
    return PROVIDER_DISPLAY_NAMES.get(provider, provider)


def get_provider_internal_name(display_name: str) -> str:
    """Get the internal name from display name"""
    return next(
        (internal for internal, display in PROVIDER_DISPLAY_NAMES.items() if display == display_name),
        display_name,
    )


def create_default_system_config() -> SystemConfig:
    """Create a fresh SystemConfig instance with default values"""
    return DEFAULT_SYSTEM_VALUES.copy()


def create_default_actions_config() -> dict[str, ActionConfig]:
    """Create a dictionary of ActionConfig instances from default values"""
    return DEFAULT_ACTIONS_VALUES.copy()


def create_default_settings() -> UnifiedSettings:
    """Create a complete UnifiedSettings instance with all default configurations"""
    return UnifiedSettings(
        system=create_default_system_config(),
        actions=create_default_actions_config(),
        custom_data={},
    )


def merge_system_data(
    user_data: dict[str, object] | None,
    default_values: SystemConfig,
) -> SystemConfig:
    """Merge user system data with default values, filtering out invalid fields"""
    result = default_values.copy()

    if user_data and isinstance(user_data, dict):
        # Only merge fields that exist in default_values (valid SystemConfig fields)
        for key, value in user_data.items():
            if key in default_values:
                result[key] = value

    return result


def merge_actions_data(
    user_data: dict[str, dict] | None,
    default_values: dict[str, ActionConfig],
) -> dict[str, ActionConfig]:
    """Merge user actions data with default values and create ActionConfig instances"""
    result = default_values.copy()

    if user_data and isinstance(user_data, dict):
        # Convert user data to ActionConfig instances
        for name, values in user_data.items():
            if isinstance(values, dict):
                result[name] = ActionConfig(**values)

    return result


def create_unified_settings_from_data(user_data: dict) -> UnifiedSettings:
    """
    Create UnifiedSettings from user data, merging with defaults.
    """
    system_user_data = user_data.get("system", {})
    if not isinstance(system_user_data, dict):
        system_user_data = {}

    system_data = merge_system_data(system_user_data, DEFAULT_SYSTEM_VALUES)
    actions_data = merge_actions_data(user_data.get("actions"), DEFAULT_ACTIONS_VALUES)
    custom_data = user_data.get("custom_data", {})

    return UnifiedSettings(
        system=system_data,
        actions=actions_data,
        custom_data=custom_data,
    )
