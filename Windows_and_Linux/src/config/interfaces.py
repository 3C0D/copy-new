"""
Writing Tools - Configuration Interfaces
Defines the data structures for unified settings management
"""

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Any, Callable, Optional, TypedDict

if TYPE_CHECKING:
    from ..writing_tools_app import WritingToolsApp
    from .aiprovider.aiprovider import AIProvider

# Type aliases for better code maintainability
ProviderFactory = Callable[["WritingToolsApp"], "AIProvider"]
PromptData = dict[str, Any]


class ActionConfig(TypedDict, total=False):
    """Configuration for a single writing action/command - NO defaults here, use constants.py"""

    prefix: str
    instruction: str
    icon: str
    open_in_window: Optional[bool]


class ActionConfigWithName(ActionConfig, total=False):
    """ActionConfig extended with a name field for UI operations"""

    name: str


class SystemConfig(TypedDict, total=False):
    """System-wide configuration settings - No defaults here, use constants.py"""

    # API Configuration
    provider: str
    default_provider: str

    # UI Configuration
    hotkey: str
    background_theme: str
    color_mode: str  # "auto", "light", or "dark"
    response_window_zoom: float

    # Application Settings
    language: str
    run_mode: str  # dev, build_dev, build_final
    update_available: bool
    start_on_boot: bool  # Whether the application should start on system boot

    # Provider-specific settings
    ollama_base_url: str
    ollama_keep_alive: str
    # mistral_base_url: str
    openai_base_url: str


class ProviderConfig(TypedDict, total=False):
    api_key: str
    api_model: str
    api_base: Optional[str]
    keep_alive: Optional[str]
    api_project: Optional[str]
    api_organisation: Optional[str]


class CustomDataStructure(TypedDict, total=False):
    providers: dict[str, ProviderConfig]


@dataclass
class UnifiedSettings:
    """Main settings container that holds all configuration data"""

    system: SystemConfig
    actions: dict[str, ActionConfig] = field(default_factory=dict)
    image_actions: dict[str, ActionConfig] = field(default_factory=dict)
    custom_data: CustomDataStructure = field(
        default_factory=lambda: CustomDataStructure(
            providers={},
        )
    )
