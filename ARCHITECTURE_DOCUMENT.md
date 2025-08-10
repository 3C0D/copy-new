# Writing Tools Application Architecture

## Overview

The Writing Tools application is a Python/PySide6 application that provides AI-assisted writing tools. It uses a modular architecture with interchangeable AI providers and a window-based user interface.

## Main Modules and Exportable Functions

### 1. Module `config/data_operations.py`

**Role**: Utilities for creating and manipulating default configurations

**Used exportable functions**:

- `get_default_model_for_provider(provider: str) -> str` - Used in aiprovider.py
- `get_provider_display_name(provider: str) -> str` - Used in SettingsWindow.py and tests
- `get_provider_internal_name(display_name: str) -> str` - Used in SettingsWindow.py and tests
- `create_default_settings() -> UnifiedSettings` - Used in settings.py
- `create_unified_settings_from_data(user_data: dict) -> UnifiedSettings` - Used in settings.py
- `create_default_actions_config() -> dict[str, ActionConfig]` - Used in CustomPopupWindow.py

**Internal functions (not exported)**:

- `create_default_system_config()` - Used only by create_default_settings()
- `merge_system_data()` - Used only by create_unified_settings_from_data()
- `merge_actions_data()` - Used only by create_unified_settings_from_data()

### 2. Module `config/settings.py`

**Role**: Unified settings manager with smart attribute access

**Main class**: `SettingsManager`

- Centralized management of all application settings
- Direct property access: `settings_manager.hotkey` instead of `settings_manager.settings.system["hotkey"]`
- Automatic configuration saving/loading
- Execution mode management (dev, build-dev, build-final)

**Exportable functions**:

- `load_settings() -> UnifiedSettings`
- `save_settings() -> bool`
- `has_providers_configured() -> bool`
- `update_action(action_name: str, action_config: ActionConfig) -> bool`
- `remove_action(action_name: str) -> bool`

### 3. Module `aiprovider.py`

**Role**: AI provider architecture with abstract classes and implementations

**Abstract classes**:

- `AIProviderSetting` - Base class for provider settings
- `AIProvider` - Common interface for all providers

**Concrete implementations**:

- `GeminiProvider` - Google Gemini API
- `OpenAICompatibleProvider` - OpenAI-compatible APIs
- `OllamaProvider` - Local Ollama server
- `AnthropicProvider` - Claude API
- `MistralProvider` - Mistral AI API

**Exportable utility functions**:

- `get_ollama_models()` - Automatic detection of installed Ollama models

### 4. Module `ui/ui_utils.py`

**Role**: UI utilities and theme management

**Exportable functions**:

- `set_color_mode(theme)` - Set global color mode
- `get_icon_path(icon_name, with_theme=True) -> str` - Icon path resolution
- `get_effective_color_mode() -> str` - Get current effective color mode

**Exportable classes**:

- `ui_utils` - Static utilities (clear_layout, resize_and_round_image)
- `ThemedWidget` - Base widget with theming and standardized style methods
- `ThemeBackground` - Themed background widget

### 5. Module `ui/ThemeManager.py`

**Role**: Centralized theme management system

**Main class**: `ThemeManager` (Singleton)

- Centralized theme change notifications via Qt signals
- Widget registration system for automatic theme updates
- Standardized style definitions for consistent UI

**Exportable classes**:

- `ThemeManager` - Singleton theme manager with signal-based updates
- `ThemeAwareMixin` - Mixin class for automatic theme synchronization

**Key methods**:

- `register_widget(widget)` - Register widget for theme updates
- `change_theme(new_mode)` - Change theme and notify all registered widgets
- `get_styles() -> dict` - Get all standardized styles for current theme

## Theme Management System

### Architecture Overview

The application uses a centralized theme management system that ensures consistent styling across all UI components and automatic synchronization when themes change.

### Core Components

1. **Global Color Mode** (`ui_utils.py`)

   - `colorMode` global variable stores current effective mode ("dark" or "light")
   - `set_color_mode(theme)` - Updates global mode, handles "auto" detection
   - `get_effective_color_mode()` - Returns current effective mode

2. **ThemeManager** (`ui/ThemeManager.py`)

   - Singleton pattern for centralized theme management
   - Signal-based notification system (`theme_changed` signal)
   - Widget registration system for automatic updates
   - Standardized style definitions via `get_styles()`

3. **ThemeAwareMixin** (`ui/ThemeManager.py`)

   - Mixin class for automatic theme synchronization
   - Auto-registers widgets with ThemeManager
   - Connects to `theme_changed` signal
   - Calls `refresh_theme()` method when theme changes

4. **ThemedWidget** (`ui/ui_utils.py`)
   - Base widget class with standardized style methods
   - Provides `get_label_style()`, `get_input_style()`, `get_dropdown_style()`, `get_radio_style()`
   - Includes `ThemeBackground` for consistent backgrounds

### Theme Synchronization Flow

1. **Theme Change Trigger**:

   - User changes color mode in settings → `auto_save_color_mode()`
   - Calls `set_color_mode()` to update global variable
   - Calls `theme_manager.change_theme()` to notify all widgets

2. **Automatic Widget Updates**:

   - `ThemeManager.change_theme()` emits `theme_changed` signal
   - All registered widgets receive signal via `ThemeAwareMixin`
   - Each widget's `refresh_theme()` method is called automatically
   - Widgets update their styles using standardized methods

3. **Application Startup Synchronization**:
   - `_handle_normal_launch()` synchronizes global `colorMode` with saved settings
   - Prevents visual conflicts when launching with existing data
   - Same synchronization exists in `show_onboarding()` for first-time users

### Implementation Pattern for New Windows

To make a window theme-aware:

```python
class MyWindow(ThemeAwareMixin, ThemedWidget):
    def __init__(self):
        super().__init__()
        # Window automatically registers with ThemeManager

    def refresh_theme(self):
        """Called automatically when theme changes"""
        # Update all UI elements with current theme
        self.my_label.setStyleSheet(self.get_label_style())
        self.my_input.setStyleSheet(self.get_input_style())
        # ... update other elements
```

### Style Standardization

All UI components should use standardized style methods:

- **Labels**: `get_label_style()` - Standard text color and font size
- **Inputs**: `get_input_style()` - Input fields with proper background/border
- **Dropdowns**: `get_dropdown_style()` - Comboboxes with item view styling
- **Radio buttons**: `get_radio_style()` - Radio button text color
- **Custom styles**: Use `get_effective_color_mode()` for theme-aware custom styles

## Main Module Architecture (WritingToolApp.py)

### `WritingToolApp` Class

**Inherits from**: `QtWidgets.QApplication`

**Main responsibilities**:

1. **Application initialization** - AI provider setup, settings, hotkeys
2. **AI provider management** - Selection and configuration of active provider
3. **System interface** - System tray icon, global keyboard shortcuts
4. **Window coordination** - Managing lifecycle of different UI windows

**Managed windows**:

- `OnboardingWindow` - Initial setup (first use)
- `SettingsWindow` - Settings configuration
- `CustomPopupWindow` - Main interaction interface
- `ResponseWindow` - AI response display
- `AboutWindow` - Application information
- `NonEditableModal` - Information modal windows

**Qt Signals**:

- `output_ready_signal` - Emitted when AI response is ready
- `show_message_signal` - Error message display
- `hotkey_triggered_signal` - Keyboard shortcut trigger
- `followup_response_signal` - Follow-up responses

### Main Execution Flow

1. **First launch**:

   - Detect missing configuration → `OnboardingWindow`
   - Configure shortcuts and themes
   - Redirect to `SettingsWindow` for AI provider configuration

2. **Normal launch**:

   - Load settings via `SettingsManager`
   - Initialize configured AI provider
   - Create system icon and register shortcuts
   - Background application, activated via shortcut

3. **Usage**:
   - Keyboard shortcut → `CustomPopupWindow`
   - Action selection → AI provider call
   - Response → Text replacement or `ResponseWindow`

## UI Windows and Their Usage

### 1. `OnboardingWindow`

- **When**: First launch without configuration
- **Function**: Initial setup of shortcuts and themes
- **Transition**: To SettingsWindow for provider configuration

### 2. `SettingsWindow`

- **When**: Settings configuration (system menu or after onboarding)
- **Function**: Complete configuration (providers, actions, themes, shortcuts)
- **Modes**: Normal or providers_only (after onboarding)

### 3. `CustomPopupWindow`

- **When**: Main keyboard shortcut activation
- **Function**: Main interface - AI action selection and custom input
- **Behavior**: Contextual popup near cursor

### 4. `ResponseWindow`

- **When**: Actions configured with `open_in_window: true`
- **Function**: Display long responses with Markdown support and conversation

### 5. `AboutWindow`

- **When**: "About" menu from system icon
- **Function**: Application information and update checking

## AIProvider Module Role

The `aiprovider.py` module implements a Strategy pattern for AI providers:

1. **Abstraction**: Common interface via `AIProvider`
2. **Dynamic configuration**: Provider-specific settings via `AIProviderSetting`
3. **Extensibility**: Easy addition of new providers
4. **Error handling**: Provider-specific error messages
5. **Automatic saving**: Persistent configuration via `SettingsManager`

**Key methods**:

- `get_response(system_instruction, prompt, return_response=False)` - Content generation
- `load_config(config)` / `save_config()` - Configuration management
- `after_load()` / `before_load()` - API client lifecycle
- `cancel()` - Request cancellation

## General Organization

The application follows a layered architecture:

1. **Interface Layer**: UI windows (OnboardingWindow, SettingsWindow, etc.)
2. **Application Layer**: WritingToolApp (coordination and business logic)
3. **Services Layer**: AIProvider (AI providers), SettingsManager (configuration)
4. **Data Layer**: data_operations (configuration manipulation), constants (default values)
5. **Utilities Layer**: ui_utils (themes, icons), update_checker (updates)

This architecture enables clear separation of responsibilities and facilitates application maintenance and extension.

## Function Analysis and Potentially Unused Code

### Actually Used Functions

**Module `data_operations.py`**:
✅ **Used**:

- `get_default_model_for_provider()` - aiprovider.py (4 uses)
- `get_provider_display_name()` - SettingsWindow.py, tests
- `get_provider_internal_name()` - SettingsWindow.py, tests
- `create_default_settings()` - settings.py
- `create_unified_settings_from_data()` - settings.py
- `create_default_actions_config()` - CustomPopupWindow.py

✅ **Used internally**:

- `create_default_system_config()` - by create_default_settings()
- `merge_system_data()` - by create_unified_settings_from_data()
- `merge_actions_data()` - by create_unified_settings_from_data()

**Module `settings.py`**:
✅ **Used**:

- `load_settings()` - WritingToolApp.py
- `save_settings()` - WritingToolApp.py, aiprovider.py, update_checker.py
- `has_providers_configured()` - WritingToolApp.py
- `update_action()` - CustomPopupWindow.py (2 uses)
- `remove_action()` - Defined but no usage found

❌ **Potentially unused**:

- `get(key, default=None)` - Commented as "not used" in code
- `update(**kwargs)` - No usage found
- `update_and_save(**kwargs)` - No usage found

### Commented or Unused Code

**Module `settings.py`**:

- Lines 189-195: Commented methods `get_provider_config()` and `set_provider_config()`
- Lines 165-183: Utility methods marked as "not used"

**Module `aiprovider.py`**:

- Unused instance variables in some providers (e.g., `close_requested` sometimes None)

## Rectification Plan

### 1. Clean up `settings.py` module

- **Comment out** methods `get()`, `update()`, `update_and_save()` (lines 168-183)
- **Remove** commented methods `get_provider_config()` and `set_provider_config()` (lines 189-195)
- **Verify** usage of `remove_action()` and remove if unused

### 2. Optimize `aiprovider.py` module

- **Standardize** `close_requested` initialization in all providers
- **Check** unused instance variables

### 3. Documentation and comments

- **Remove** obsolete comments in constants.py (lines 249-262)
- **Update** documentation of cleaned modules

### 4. Regression testing

- **Run** all existing tests after cleanup
- **Verify** application works correctly
- **Test** particularly save/load functionalities

### Rectification priorities

1. **High**: Remove unused SettingsManager methods
2. **Medium**: Clean obsolete comments
3. **Low**: Standardize instance variables in aiprovider.py

This analysis reveals that the code is generally well-structured with little dead code, but some utility methods were created "just in case" without being used.

## Related Documentation

- **MODIFICATIONS_LOG.md**: Detailed log of all code modifications with access paths and implementation details
