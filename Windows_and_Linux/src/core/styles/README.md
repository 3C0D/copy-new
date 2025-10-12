# Architecture modulaire des styles - Writing Tools

## Vue d'ensemble

Cette architecture modulaire remplace l'ancien système monolithique de gestion des styles CSS/QSS. Elle offre une meilleure organisation, maintenabilité et évolutivité pour les thèmes de l'application.

## Structure des dossiers

```
Windows_and_Linux/src/core/styles/
├── README.md              # Cette documentation
├── __init__.py           # Exports principaux
├── colors.py             # Palettes de couleurs dark/light
├── containers.py         # Dialogs, containers, backgrounds
├── controls.py           # Boutons, inputs, dropdowns
├── feedback.py           # Progress bars, tooltips
├── navigation.py         # Scrollbars, menus
├── specialized.py        # Composants spécifiques (chat, markdown)
└── ../theme_manager.py   # Point d'entrée refactorisé
```

## Architecture des couleurs

### ColorPalette (dataclass)

```python
@dataclass
class ColorPalette:
    # Arrière-plans
    bg_primary: str
    bg_secondary: str
    bg_control: str

    # Textes
    fg_primary: str
    fg_secondary: str
    fg_control: str
    fg_control_text: str

    # Bordures et accents
    border: str
    border_checkbox: str
    selection: str

    # Boutons
    primary_default: str
    primary_hover: str
    primary_pressed: str
    # ... autres couleurs
```

### Palettes prédéfinies

- `DARK_PALETTE` : Thème sombre
- `LIGHT_PALETTE` : Thème clair

## Architecture modulaire par composants

Chaque module exporte des fonctions qui prennent une `ColorPalette` et retournent du CSS :

```python
# controls.py
def primary_button(palette: ColorPalette) -> str:
    return f"""
        QPushButton {{
            background-color: {palette.primary_default};
            color: white;
            padding: 10px;
            border-radius: 5px;
        }}
        QPushButton:hover {{
            background-color: {palette.primary_hover};
        }}
    """
```

## Utilisation

### Dans ThemeManager

```python
def get_styles(self) -> dict[str, str]:
    palette = self._current_palette
    return {
        "primary_button": primary_button(palette),
        "dialog": dialog(palette),
        "label": label(palette),
        # ... tous les autres styles
    }
```

### Dans les composants UI

```python
# Avant (monolithique)
self.setStyleSheet(self.app.styles["primary_button"])

# Après (modulaire)
# Le style est généré dynamiquement à partir des modules
self.setStyleSheet(self.app.styles["primary_button"])
```

## Avantages de cette architecture

### ✅ **Modularité**
- Chaque composant dans son propre fichier
- Responsabilités clairement séparées
- Facilite la navigation et la maintenance

### ✅ **Réutilisabilité**
- Les palettes sont partagées entre composants
- Fonctions réutilisables pour des variations
- Évite la duplication de code

### ✅ **Maintenabilité**
- Changements locaux aux composants
- Tests unitaires possibles par fonction
- Debugging facilité

### ✅ **Évolutivité**
- Ajout facile de nouveaux thèmes
- Extension simple des composants existants
- Migration progressive possible

### ✅ **Performance**
- Génération à la demande
- Cache possible au niveau ThemeManager
- Imports optimisés

## Migration depuis l'ancienne architecture

### Compatibilité ascendante
- Tous les anciens noms de styles sont préservés
- Les mappings temporaires assurent la compatibilité
- Aucune modification requise dans le code client

### Migration progressive
1. ✅ **Phase 1** : Création de l'architecture modulaire
2. ✅ **Phase 2** : Migration des styles de base
3. 🔄 **Phase 3** : Migration des styles spécialisés
4. 🔄 **Phase 4** : Nettoyage des mappings temporaires

## Développement

### Ajouter un nouveau style

1. **Identifier le module approprié** (controls, containers, etc.)
2. **Ajouter la fonction dans le module** :
```python
def new_component(palette: ColorPalette) -> str:
    return f"""
        QNewComponent {{
            background-color: {palette.bg_primary};
            color: {palette.fg_primary};
        }}
    """
```
3. **Exporter dans `__init__.py`**
4. **Ajouter au dictionnaire dans `ThemeManager.get_styles()`**

### Ajouter une nouvelle palette

1. **Créer une nouvelle ColorPalette** dans `colors.py`
2. **L'exporter dans `__init__.py`**
3. **Mettre à jour ThemeManager** pour supporter la nouvelle palette

## Tests

```bash
# Tester les imports
cd Windows_and_Linux
python -c "from src.core.styles import DARK_PALETTE, primary_button; print(primary_button(DARK_PALETTE)[:50])"

# Tester ThemeManager
python -c "
from unittest.mock import Mock
from src.core.theme_manager import ThemeManager
app = Mock(); app.settings_manager = Mock(); app.settings_manager.color_mode = 'dark'
tm = ThemeManager(app)
styles = tm.get_styles()
print(f'Styles générés: {len(styles)}')
"
```

## Métriques

- **Fichiers** : 8 modules spécialisés
- **Styles** : ~50 styles générés
- **Lignes de code** : ~800 lignes (vs 774 dans l'ancien système)
- **Complexité cyclomatique** : Réduite grâce à la modularité
- **Testabilité** : Chaque fonction testable indépendamment

## Évolution future

- **Variables CSS custom** pour les thèmes dynamiques
- **Système de tokens de design** plus avancé
- **Thèmes utilisateur personnalisables**
- **Optimisations de performance** (lazy loading, cache)

---

*Cette architecture respecte les principes SOLID et offre une base solide pour l'évolution future des styles de Writing Tools.*