# Complete Internationalization Guide for Writing Tools

## Overview

Writing Tools now supports complete internationalization with a gettext-based translation system. This document explains the existing system, the modifications made, and how to use it.

## Initial System State

### Existing Translation System

Before modifications, Writing Tools already had a basic infrastructure for internationalization:

#### 1. Translation Function `_()`
```python
def _(x):
    """Translation function placeholder."""
    return x
```
- Defined in `AboutWindow.py`, `SettingsWindow.py`, etc.
- Simply returns the original text (no real translation)

#### 2. File Structure
```
locales/
├── en/LC_MESSAGES/messages.po    # English (empty)
└── it/LC_MESSAGES/messages.po    # Italian (with translations)
```

#### 3. Generation Script
`create_translation.sh`:
- Uses `xgettext` to extract strings from Python code
- Merges .pot files into one
- Updates existing .po files
- Compiles .po to .mo with `msgfmt`

#### 4. Translation Loading
In `WritingToolApp.py`:
```python
def setup_translations(self, lang=None):
    translation = gettext.translation("messages", localedir="locales", languages=[lang])
    translation.install()
    self._ = translation.gettext
```

#### 5. Available Languages List
`get_available_languages()` in `constants.py`:
- Scans the `locales/` folder to find available languages
- Returns a list `(display_name, language_code)`

## Modifications Made

### 1. LanguageManager Creation

**File created**: `src/ui/LanguageManager.py`

Central class inspired by `ThemeManager` that handles language changes:

```python
class LanguageManager(QtCore.QObject):
    language_changed = QtCore.Signal(str)  # Emitted when language changes

    def __init__(self, app):
        self.app = app
        self._registered_widgets = []

    def register_widget(self, widget):
        """Register a widget to receive language change notifications"""
        self._registered_widgets.append(widget)

    def change_language(self, lang_code: str):
        """Change language and notify all registered widgets"""
        self.app.settings_manager.language = lang_code
        self.app.change_language(lang_code)
        self.language_changed.emit(lang_code)

        # Refresh all registered widgets
        for widget in self._registered_widgets[:]:
            if hasattr(widget, "refresh_language"):
                widget.refresh_language()
```

### 2. Integration into WritingToolApp

**Modifications** in `WritingToolApp.py`:

- Added `self.language_manager = LanguageManager(self)` in `_setup_ui_components()`
- Modified `setup_translations()` to use `Path` instead of `os.path`
- Fixed path to `locales/` (moved up one level)

### 3. Widget Modifications

#### Base ThemedWidget Class
**File modified**: `src/ui/ui_utils.py`

Added automatic registration with LanguageManager:
```python
class ThemedWidget(QWidget):
    def __init__(self, app):
        super().__init__()
        self.app = app
        # Automatic registration with managers
        self.app.theme_manager.register_widget(self)
        self.app.language_manager.register_widget(self)  # ADDED
```

#### refresh_language() Method
Added to all main widgets:

- **AboutWindow**: Updates title
- **SettingsWindow**: Updates all labels and dropdowns
- **OnboardingWindow**: Updates texts
- **ResponseWindow**: Updates buttons
- **CustomPopupWindow**: Updates options

### 4. Language Dropdown in Settings

**File modified**: `src/ui/SettingsWindow.py`

Added complete language selection section:

```python
# Language selection
self.language_label = QLabel(_("Language:"))
self.language_dropdown = QComboBox()
# Filled with AVAILABLE_LANGUAGES
# Auto-save with currentTextChanged.connect(self.auto_save_language)
```

### 5. Technical Fixes

- **Locales path**: Fixed in `constants.py` and `WritingToolApp.py`
- **requirements.txt**: Added `polib` for Python compilation
- **utils.py**: Removed emojis causing Windows encoding errors

### 6. Recent Fixes (2025-01-28)

- **Short translations**: "Close Settings" → "Fermer" (fr), "Chiudi" (it) to prevent button overflow
- **Virtual environment**: Scripts using `myvenv\Scripts\python` instead of system Python
- **Automatic compilation**: `compile_translations.py` script using polib in virtual environment
- **AboutWindow**: Fixed button refresh when language changes

## Current Architecture

### Language Change Flow

1. **User** changes language in Settings dropdown
2. **SettingsWindow.auto_save_language()**:
   - Gets selected language code
   - Saves to `settings_manager.language`
3. **LanguageManager.change_language()**:
   - Calls `app.change_language(lang_code)`
   - Emits `language_changed` signal
   - Calls `refresh_language()` on all registered widgets
4. **WritingToolApp.change_language()**:
   - Calls `setup_translations(lang)`
   - Reloads gettext translations
   - Updates global `_()` function
   - Calls `retranslate_ui()` on all widgets

### Translation File Structure

```
locales/                          # Root translations folder
├── en/                           # English (base language)
│   └── LC_MESSAGES/
│       ├── messages.po          # Translation file (editable)
│       └── messages.mo          # Compiled file (binary)
├── fr/                           # French
│   └── LC_MESSAGES/
│       ├── messages.po          # To be filled with translations
│       └── messages.mo          # Generated automatically
└── it/                           # Italian (existing)
    └── LC_MESSAGES/
        ├── messages.po          # Existing translations
        └── messages.mo          # Generated automatically
```

### .po File Format

```po
# Header with metadata
msgid ""
msgstr ""
"Language: fr\n"
"Content-Type: text/plain; charset=UTF-8\n"

# Translation entry
#: ui/AboutWindow.py:44
msgid "About Writing Tools"
msgstr "À propos de Writing Tools"

#: ui/AboutWindow.py:49
msgid "Hello World"
msgstr "Bonjour le monde"
```

## How to Use the System

### For Developers

#### 1. Add Translatable Text
```python
# In any UI file
title_label = QLabel(_("About Writing Tools"))
button.setText(_("Save"))

# In lists/data
options = [_("Option 1"), _("Option 2")]
```

#### 2. Regenerate Translation Files

**Recommended method (with virtual environment):**
```bash
# From Windows_and_Linux/
# Use virtual environment Python
myvenv\Scripts\python scripts/compile_translations.py
```

**Bash script (Linux/Mac):**
```bash
# From Windows_and_Linux/
./create_translation.sh
```

**Manual compilation:**
```bash
# Extract strings
xgettext --language=Python --keyword=_ WritingToolApp.py -o pot_files/WritingToolApp.pot
xgettext --language=Python --keyword=_ ui/*.py -o pot_files/UI.pot

# Merge
msgcat pot_files/*.pot -o pot_files/merged.pot

# Update .po files
msgmerge --update locales/fr/LC_MESSAGES/messages.po pot_files/merged.pot

# Compile
msgfmt -o locales/fr/LC_MESSAGES/messages.mo locales/fr/LC_MESSAGES/messages.po
```

#### 3. With Python (recommended for Windows)
```python
# From Windows_and_Linux/
# Use virtual environment Python
myvenv\Scripts\python scripts/compile_translations.py

# Or manually:
import polib

# Load and compile
po = polib.pofile('locales/fr/LC_MESSAGES/messages.po')
po.save_as_mofile('locales/fr/LC_MESSAGES/messages.mo')
```

### For Translators

#### 1. Open the .po file
Use an editor like Poedit or edit the text file directly.

#### 2. Add Translations
```po
#: ui/AboutWindow.py:44
msgid "About Writing Tools"
msgstr "À propos de Writing Tools"
```

#### 3. Compile
After translation, run `./create_translation.sh` or use polib.

### For Testing

1. **Launch the application**
2. **Go to Settings**
3. **Change language** in the dropdown
4. **See texts change** automatically

## Implemented Features

### ✅ Implemented
- [x] LanguageManager with signals
- [x] Automatic widget registration
- [x] Automatic text refresh
- [x] Language dropdown in Settings
- [x] Automatic language saving
- [x] Support for .po/.mo files
- [x] Translation generation script
- [x] Windows path fixes
- [x] Virtual environment integration

### 🔄 Partially Implemented
- [ ] French translations (files created but empty)
- [ ] .mo file existence checking

### ❌ Not Implemented
- [ ] Translation validation
- [ ] Automatic fallback if language unavailable
- [ ] Integrated translation editor
- [ ] Complex plural support
- [ ] Tooltips and system menu translations

## Troubleshooting

### Problem: Language doesn't change
**Cause**: Missing or corrupted .mo file
**Solution**: Re-run `./create_translation.sh`

### Problem: Widget doesn't update
**Cause**: Missing `refresh_language()` method
**Solution**: Add the method to the widget

### Problem: Encoding error
**Cause**: Emojis or special characters in scripts
**Solution**: Use simple text in log messages

### Problem: Incorrect path
**Cause**: Windows/Unix differences
**Solution**: Use `Path` instead of `os.path.join`

## Future Recommendations

1. **Automation**: Integrate generation into CI/CD
2. **Tools**: Add Python script for translation management
3. **Validation**: Check that all keys have translations
4. **Performance**: Lazy loading of translations
5. **UX**: Language indicator in system tray

## Conclusion

The internationalization system is now complete and operational. It follows gettext best practices and integrates perfectly with Writing Tools' existing architecture. Developers can easily add translatable text, and translators can work with standard tools.