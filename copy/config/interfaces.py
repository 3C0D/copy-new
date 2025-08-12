"""
Writing Tools - Configuration Interfaces
Defines the data structures for unified settings management
"""

from dataclasses import dataclass, field
from typing import Dict, Any, Optional


@dataclass
class ActionConfig:
    """Configuration for a single writing action/command - NO defaults here, use constants.py"""

    prefix: str
    instruction: str
    icon: str
    open_in_window: bool


@dataclass
class SystemConfig:
    """System-wide configuration settings - NO defaults here, use constants.py"""

    # API Configuration
    api_key: str
    provider: str
    model: str

    # UI Configuration
    hotkey: str
    theme: str

    # Application Settings
    language: str
    auto_update: bool
    run_mode: str  # dev, build_dev, build_final

    # Provider-specific settings
    ollama_base_url: str
    ollama_model: str
    ollama_keep_alive: str

    mistral_base_url: str
    mistral_model: str

    anthropic_model: str

    openai_base_url: str
    openai_model: str


@dataclass
class UnifiedSettings:
    """Main settings container that holds all configuration data"""

    system: SystemConfig = field(default_factory=SystemConfig)
    actions: Dict[str, ActionConfig] = field(default_factory=dict)
    custom_data: Dict[str, Any] = field(default_factory=dict)
