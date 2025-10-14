Parfait ! Voici l'analyse détaillée des changements à apporter :

## Structure proposée

```
general_settings/
├── __init__.py
├── general_settings_widget.py
├── ui_components.py
├── settings_handlers.py
└── refresh_manager.py
```

## Changements détaillés

### 1. **`__init__.py`** (nouveau)
```python
from .general_settings_widget import GeneralSettings

__all__ = ["GeneralSettings"]
```

### 2. **`ui_components.py`** (nouveau)
Extrait la création répétitive des widgets avec un pattern factory :

**Fonction principale :**
```python
def create_styled_widget(widget_class, style_key, app, **kwargs):
    """Factory générique pour créer des widgets stylisés"""
    widget = widget_class(**kwargs)
    widget.setStyleSheet(app.styles[style_key])
    return widget
```

**Fonctions spécialisées :**
- `create_language_section(app, settings_manager)` → retourne (label, dropdown)
- `create_shortcut_section(app, settings_manager)` → retourne (label, input)
- `create_theme_section(app, parent_window)` → retourne (label, layout avec radios)
- `create_color_mode_section(app, settings_manager)` → retourne (label, dropdown)
- `create_autostart_section(app, settings_manager)` → retourne checkbox

Chaque fonction encapsule :
- Création du widget
- Application du style
- Configuration initiale (valeurs par défaut)
- Désactivation du wheel pour les dropdowns

### 3. **`settings_handlers.py`** (nouveau)
Extrait toute la logique métier des callbacks :

**Classe principale :**
```python
class SettingsHandlers:
    def __init__(self, app, parent_window):
        self.app = app
        self.parent_window = parent_window
        self._changing_language = False
```

**Méthodes (logique identique au code original, juste déplacée) :**
- `handle_autostart_changed(state: int)` 
- `handle_language_changed(language_dropdown: QComboBox)`
- `handle_shortcut_changed(shortcut_input: QLineEdit)`
- `handle_theme_changed(gradient_radio: QRadioButton)`
- `handle_color_mode_changed(color_mode_dropdown: QComboBox)`

**Avantage :** Sépare le "quoi faire" du "quand le faire"

### 4. **`refresh_manager.py`** (nouveau)
Unifie les méthodes `refresh_theme()` et `refresh_language()` :

**Approche :**
```python
class RefreshManager:
    @staticmethod
    def refresh_theme(widgets_dict, app_styles):
        """
        widgets_dict = {
            'label': [widget1, widget2, ...],
            'dropdown': [widget3, widget4, ...],
            ...
        }
        """
        for style_key, widgets in widgets_dict.items():
            for widget in widgets:
                if widget:
                    widget.setStyleSheet(app_styles[style_key])
    
    @staticmethod
    def refresh_language(components, translator_func):
        """
        components = [
            (widget, 'text_key' ou lambda),
            ...
        ]
        """
        # Bloque signaux, met à jour textes, restaure signaux
```

**Élimine :** 40 lignes de if répétitifs

### 5. **`general_settings_widget.py`** (refactoré)

**Ce qui CHANGE :**

#### Imports ajoutés :
```python
from .ui_components import (
    create_language_section,
    create_shortcut_section,
    create_theme_section,
    create_color_mode_section,
    create_autostart_section,
)
from .settings_handlers import SettingsHandlers
from .refresh_manager import RefreshManager
```

#### `__init__` simplifié :
```python
def __init__(self, app, parent):
    super().__init__(parent)
    self.app = app
    self.parent_window = parent
    self._logger = logging.getLogger(__name__)
    
    # Nouveau : délégation
    self.handlers = SettingsHandlers(app, parent)
    
    # Plus besoin de ces attributs (gérés par handlers) :
    # ❌ self._changing_language = False
    
    # Garde les références aux widgets (pour refresh)
    # ... (identique)
    
    self.init_ui()
```

#### `init_ui()` drastiquement simplifié :
```python
def init_ui(self):
    layout = QVBoxLayout(self)
    layout.setSpacing(15)
    layout.setContentsMargins(0, 0, 0, 0)
    
    # Autostart
    self.autostart_checkbox = create_autostart_section(self.app, self.app.settings_manager)
    self.autostart_checkbox.stateChanged.connect(
        lambda state: self.handlers.handle_autostart_changed(state)
    )
    layout.addWidget(self.autostart_checkbox)
    
    # Language
    self.language_label, self.language_dropdown = create_language_section(
        self.app, self.app.settings_manager
    )
    self.language_dropdown.currentIndexChanged.connect(
        lambda: self.handlers.handle_language_changed(self.language_dropdown)
    )
    layout.addWidget(self.language_label)
    layout.addWidget(self.language_dropdown)
    
    # Shortcut
    # ... pattern similaire
    
    # Theme
    # ... pattern similaire
    
    # Color mode
    # ... pattern similaire
```

**Réduction :** ~80 lignes → ~40 lignes

#### Callbacks supprimés (déplacés vers SettingsHandlers) :
- ❌ `_on_autostart_changed()`
- ❌ `_on_language_changed()`
- ❌ `_on_shortcut_changed()`
- ❌ `_on_theme_changed()`
- ❌ `_on_color_mode_changed()`

#### `refresh_theme()` refactoré :
```python
def refresh_theme(self):
    widgets_dict = {
        'label': [self.language_label, self.shortcut_label, self.theme_label, self.color_mode_label],
        'dropdown': [self.language_dropdown, self.color_mode_dropdown],
        'input': [self.shortcut_input],
        'radio': [self.gradient_radio, self.plain_radio],
        'checkbox': [self.autostart_checkbox],
    }
    RefreshManager.refresh_theme(widgets_dict, self.app.styles)
```

**Réduction :** 20 lignes → 8 lignes

#### `refresh_language()` refactoré :
```python
def refresh_language(self):
    components = [
        (self.language_label, lambda: _("Language:")),
        (self.shortcut_label, lambda: _("Shortcut Key:")),
        # ... etc
    ]
    RefreshManager.refresh_language(
        components,
        self.color_mode_dropdown,
        self.app.settings_manager.color_mode,
        translator_func=_
    )
```

**Réduction :** 40 lignes → 15 lignes

## Résumé des gains

| Métrique | Avant | Après | Gain |
|----------|-------|-------|------|
| Lignes dans widget principal | ~230 | ~120 | -48% |
| Nombre de fichiers | 1 | 5 | Meilleure organisation |
| Duplication | Élevée | Minimale | -70% |
| Testabilité | Faible | Élevée | ++++++ |
| Couplage | Fort | Faible | ++++++ |

## Instructions pour l'application

1. Créer le dossier `general_settings/`
2. Créer les 4 nouveaux fichiers avec le code fourni
3. Modifier `general_settings_widget.py` selon les changements indiqués
4. Mettre à jour l'import dans les fichiers parents : 
   ```python
   # Avant
   from .general_settings import GeneralSettings
   
   # Après
   from .general_settings import GeneralSettings  # (identique, grâce à __init__.py)
   ```

Voulez-vous que je génère le code complet des nouveaux modules ?