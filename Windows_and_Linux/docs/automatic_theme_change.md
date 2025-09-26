# Automatic Theme Change System

## 1. General Architecture
The system relies on 3 main components:
- **`ThemeManager`** (in `ui/ThemeManager.py`): Central theme manager
- **`config/settings.py`**: Settings manager with automatic system theme detection
- **`systray.py`**: Theme application to the context menu

## 2. Technical Functioning

### Automatic System Theme Detection
```python
# In config/settings.py
import darkdetect

@property
def color_mode(self) -> str:
    """Current color mode ('auto', 'dark', or 'light')."""
    if "color_mode" not in self.settings.system:
        self.settings.system["color_mode"] = "auto"

    current_mode = self.settings.system["color_mode"]
    if current_mode == "auto":
        return "dark" if darkdetect.isDark() else "light"

    return current_mode
```

The system uses the `darkdetect` library to detect if the system is in dark mode. This library works on:
- **Windows**: via the IMM API (Windows Immersion Mode)
- **macOS**: via the system preference `AppleInterfaceStyle`
- **Linux**: via environment variables like `GTK_THEME`

**Note**: The current implementation only detects the theme at application startup or when manually changing settings. There is no real-time monitoring of system theme changes.

### Manual Change Management
```python
# In ThemeManager.py
color_mode_changed = QtCore.Signal(str)

def change_color_mode(self, new_mode: str) -> None:
    """Change the color mode and notify all registered widgets."""
    # Save to settings
    self.app.settings_manager.color_mode = new_mode

    # Update styles
    self.app.styles = self.get_styles()
    # Emit signal
    self.color_mode_changed.emit(new_mode)

    # Refresh all registered widgets
    for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
        if hasattr(widget, "refresh_theme"):
            try:
                widget.refresh_theme()
            except RuntimeError:
                self._registered_widgets.remove(widget)
```

The `ThemeManager` emits a `color_mode_changed` signal whenever a manual change is made.

## 3. On the Target Hardware (systray.py)

### Manual Theme Application
```python
# In systray.py update_tray_menu()
# Apply styles using the current color mode
self.apply_tray_menu_styles(self.tray_menu)

def apply_tray_menu_styles(self, menu) -> None:
    """
    Apply styles to the tray menu based on current color mode.
    """
    styles = self.app.theme_manager.get_styles()
    menu.setStyleSheet(styles.get("tray_menu", ""))
```

The systray menu styles are applied manually when the menu is updated, using the current theme from `ThemeManager.get_styles()`.

## 4. Style Application to Context Menu

```python
def apply_tray_menu_styles(self, menu) -> None:
    styles = theme_manager.get_styles()
    menu.setStyleSheet(styles.get("tray_menu", ""))
```

The system applies appropriate CSS styles according to the mode (light/dark) to the following elements:
- Menu background color (`#2d2d2d` in dark, `#ffffff` in light)
- Text color (`#ffffff` in dark, `#000000` in light)
- Separator color
- Selection color

## 5. Supported Platforms

The system works on:
- ✅ **Windows**: via `darkdetect`
- ✅ **macOS**: via `darkdetect`
- ✅ **Linux**: via `darkdetect` (supports common desktop managers)

## 6. Required Dependencies

In `requirements.txt`, you must have:
```txt
darkdetect>=0.7.0
```

## 7. How It Works in the Systray Context

1. The application starts and detects the system theme via `settings_manager.color_mode` (which uses `darkdetect` if set to "auto")
2. The `SystrayManager` creates the context menu with initial styles via `apply_tray_menu_styles()`
3. When the user manually changes the theme in settings:
   - `ThemeManager.change_color_mode()` is called
   - `ThemeManager` emits a `color_mode_changed` signal
   - All registered widgets refresh their theme
   - The systray menu is updated when `update_tray_menu()` is called

**Note**: There is currently no automatic detection of system theme changes during runtime. Theme changes only occur when the user manually selects a different mode in the settings.

## 8. The `refresh_theme` Method in the Theme System

The `refresh_theme` method is defined in the `ThemedWidget` base class (in `ui_utils.py`). All GUI widgets that need theme support inherit from this class.

### The Technical Mechanism

```python
# In ThemeManager.change_color_mode()
for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
    if hasattr(widget, "refresh_theme"):
        try:
            widget.refresh_theme()
        except RuntimeError:
            self._registered_widgets.remove(widget)
```

The `ThemeManager` calls `refresh_theme()` on all registered widgets when the color mode changes.

### How Each Widget Implements `refresh_theme`

Each widget can override `refresh_theme()` to implement specific theme refresh logic. The base implementation in `ThemedWidget` updates the background.

#### In SettingsWindow.py
```python
def refresh_theme(self) -> None:
    """Refresh all UI element styles to reflect the current color mode."""
    # Update various UI elements with new styles
    self.some_label.setStyleSheet(self.app.styles["label"])
    # ... more style updates
```

#### In OnboardingWindow.py
```python
def refresh_theme(self) -> None:
    """Refresh all UI element styles to reflect the current color mode."""
    # Update various UI elements with new styles
    self.some_label.setStyleSheet(self.app.styles["label"])
    # ... more style updates
```

#### In NonEditableModal.py
```python
def refresh_theme(self) -> None:
    """Refresh the modal's theme when color mode changes."""
    self.setStyleSheet(self.app.styles["non_editable_modal"])
```

### The System Architecture

1. **Inheritance-based**: Widgets inherit from `ThemedWidget` which provides automatic registration and base `refresh_theme()` implementation

2. **Shared Responsibility**: Each widget can override `refresh_theme()` for specific needs

3. **Runtime Safety**: The code checks `hasattr(widget, "refresh_theme")` before calling the method

### Advantages of This Approach

✅ **Automatic Registration**: Widgets are automatically registered when inheriting from `ThemedWidget`
✅ **Strong Decoupling**: Each widget controls its own refresh
✅ **Flexibility**: Easy to override for specific needs
✅ **Safety**: No error if the method is missing
✅ **Extensibility**: New widgets can easily integrate

### How It Works Concretely

When the user changes the theme in settings:

1. `ThemeManager.change_color_mode()` is called
2. It emits the `color_mode_changed` signal
3. All registered widgets (inheriting from `ThemedWidget`) have their `refresh_theme()` method called
4. Each widget updates its styles accordingly

## Real-time Theme Change Flow

### Current Architecture

```
[SettingsWindow] → [ThemeManager] → [Widgets + Systray]
       ↓               ↓               ↓
   change_color_mode()  color_mode_changed  refresh_theme() / apply_tray_menu_styles()
```

### Detailed Flow

1. **Trigger**: User changes theme in `SettingsWindow`
   - `SettingsWindow.auto_save_color_mode()` calls `theme_manager.change_color_mode()`

2. **ThemeManager Processing**: In `ThemeManager.change_color_mode()`
   ```python
   # Save to settings
   self.app.settings_manager.color_mode = new_mode
   # Update styles
   self.app.styles = self.get_styles()
   # Emit signal
   self.color_mode_changed.emit(new_mode)
   # Refresh registered widgets
   for widget in self._registered_widgets:
       if hasattr(widget, "refresh_theme"):
           widget.refresh_theme()
   ```

3. **Widget Updates**: All widgets inheriting from `ThemedWidget` receive the signal
   - `ThemedWidget._on_color_mode_changed()` calls `refresh_theme()`
   - Each widget updates its styles in real-time

4. **Systray Update**: In `SettingsWindow.refresh_theme()`
   ```python
   if self.app.systray_manager.tray_menu:
       self.app.systray_manager.apply_tray_menu_styles(self.app.systray_manager.tray_menu)
   ```
   - The systray menu styles are updated immediately

### Logic
- **Signal-based**: Changes propagate instantly via Qt signals
- **Inheritance-driven**: Widgets automatically register and update
- **Manual systray**: Systray updates through SettingsWindow for reliability
- **Real-time**: All UI elements update immediately when theme changes

The system provides instant visual feedback when users change themes! 🎨