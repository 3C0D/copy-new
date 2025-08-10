"""
Writing Tools - Configuration Interfaces
Defines the data structures for unified settings management
"""

from dataclasses import dataclass, field
from typing import TypedDict


class ActionConfig(TypedDict, total=False):
    """Configuration for a single writing action/command - NO defaults here, use constants.py"""

    prefix: str
    instruction: str
    icon: str
    open_in_window: bool


class SystemConfig(TypedDict, total=False):
    """System-wide configuration settings - No defaults here, use constants.py"""

    # API Configuration
    provider: str
    model: str

    # UI Configuration
    hotkey: str
    theme: str
    color_mode: str  # "auto", "light", or "dark"

    # Application Settings
    language: str
    run_mode: str  # dev, build_dev, build_final
    update_available: bool
    start_on_boot: bool  # Whether the application should start on system boot

    # Provider-specific settings
    ollama_base_url: str
    ollama_keep_alive: str
    mistral_base_url: str
    openai_base_url: str


class ProviderConfig(TypedDict, total=False):
    api_key: str
    model_name: str


class CustomDataStructure(TypedDict, total=False):
    providers: dict[str, ProviderConfig]


@dataclass
class UnifiedSettings:
    """Main settings container that holds all configuration data"""

    system: SystemConfig
    actions: dict[str, ActionConfig] = field(default_factory=dict)
    custom_data: CustomDataStructure = field(
        default_factory=lambda: CustomDataStructure(
            providers={},
        )
    )
