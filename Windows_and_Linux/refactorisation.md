Oui, ce code peut être significativement factorisé. Voici les principales opportunités de refactoring que j'identifie :

## Problèmes principaux

1. **Méthodes trop longues** : `init_ui()`, `enter_edit_mode()`, `exit_edit_mode()` font trop de choses
2. **Duplication de logique** : Gestion répétée des widgets (show/hide)
3. **Responsabilités mélangées** : UI, logique métier, et gestion d'état dans la même classe
4. **Dépendances circulaires** : Beaucoup de vérifications `if widget is not None`

## Suggestions de refactoring

### 1. Extraire la gestion de visibilité des widgets

```python
class WidgetVisibilityManager:
    """Gère la visibilité des widgets selon le mode."""
    
    def __init__(self, window: 'CustomPopupWindow'):
        self.window = window
    
    def set_edit_mode(self, enabled: bool) -> None:
        """Configure tous les widgets pour le mode édition."""
        visibility_map = {
            'edit_button': not enabled,
            'close_button': not enabled,
            'reset_button': enabled,
            'edit_close_button': enabled,
            'drag_label': enabled,
            'input_area': not enabled,
            'force_chat_area': not enabled and self.window.has_sel_text,
            'update_label': not enabled,
            'image_preview_container': not enabled and self.window.has_image,
        }
        
        for widget_name, should_show in visibility_map.items():
            widget = getattr(self.window, widget_name, None)
            if widget:
                widget.setVisible(should_show)
```

### 2. Extraire la création des boutons de la top bar

```python
class TopBarBuilder:
    """Construit la barre supérieure avec ses composants."""
    
    def __init__(self, app, parent: 'CustomPopupWindow'):
        self.app = app
        self.parent = parent
    
    def build(self, layout: QHBoxLayout) -> dict[str, QPushButton]:
        """Construit tous les boutons et retourne un dictionnaire."""
        buttons = {}
        
        if self.parent.has_sel_text or self.parent.has_image:
            buttons['reset'] = self._create_reset_button()
            buttons['edit'] = self._create_edit_button()
            buttons['edit_close'] = self._create_edit_close_button()
            
            layout.addWidget(buttons['reset'], 0, Qt.AlignmentFlag.AlignLeft)
            # ... etc
        
        buttons['close'] = self._create_close_button()
        layout.addWidget(buttons['close'], 0, Qt.AlignmentFlag.AlignRight)
        
        return buttons
    
    def _create_reset_button(self) -> QPushButton:
        btn = QPushButton()
        # Configuration...
        return btn
```

### 3. Séparer la logique de validation

```python
class VisionSupportValidator:
    """Valide le support vision des modèles."""
    
    VISION_MODELS = {
        "gemini": GEMINI_MODELS,
        "openai": OPENAI_MODELS,
        "anthropic": ANTHROPIC_MODELS,
        "mistral": MISTRAL_MODELS,
    }
    
    OLLAMA_VISION_INDICATORS = ["llava", "bakllava", "moondream", "minicpm-v", "qwen2.5vl"]
    
    @classmethod
    def has_vision_support(cls, provider_name: str, api_model: str) -> bool:
        """Vérifie si le modèle supporte la vision."""
        if not provider_name or not api_model:
            return False
        
        if provider_name in cls.VISION_MODELS:
            return cls._check_standard_provider(provider_name, api_model)
        
        if provider_name == "ollama":
            return cls._check_ollama_model(api_model)
        
        return False
    
    @classmethod
    def _check_standard_provider(cls, provider: str, model: str) -> bool:
        return any(
            m[1] == model and m[2].get("vision", False)
            for m in cls.VISION_MODELS[provider]
        )
    
    @classmethod
    def _check_ollama_model(cls, model: str) -> bool:
        return any(ind in model.lower() for ind in cls.OLLAMA_VISION_INDICATORS)
```

### 4. Simplifier la gestion de l'état d'édition

```python
class EditModeController:
    """Contrôle le mode édition."""
    
    def __init__(self, window: 'CustomPopupWindow'):
        self.window = window
        self.visibility_manager = WidgetVisibilityManager(window)
    
    def enter_edit_mode(self) -> None:
        self.window.edit_mode = True
        self.visibility_manager.set_edit_mode(True)
        self.window.rebuild_grid_layout(force_edit_mode=True)
        self.window.add_edit_overlays_to_buttons()
        
        if self.window.has_image:
            self.window.resize(self.window.width(), 420)
    
    def exit_edit_mode(self) -> None:
        self.window.edit_mode = False
        self.window.reload_window()
```

### 5. Usage dans CustomPopupWindow simplifié

```python
class CustomPopupWindow(QWidget):
    def __init__(self, app, selected_text=None, image=None):
        super().__init__()
        self.app = app
        self.selected_text = selected_text
        self.image = image
        
        # Managers/Controllers
        self.visibility_manager = WidgetVisibilityManager(self)
        self.edit_controller = EditModeController(self)
        self.vision_validator = VisionSupportValidator()
        
        # État
        self.edit_mode = False
        self.has_sel_text = bool(selected_text and selected_text.strip())
        self.has_image = bool(image)
        
        self._init_ui_components()
        self.init_ui()
    
    def enter_edit_mode(self) -> None:
        self.edit_controller.enter_edit_mode()
    
    def exit_edit_mode(self) -> None:
        self.edit_controller.exit_edit_mode()
    
    def _check_vision_support(self) -> bool:
        provider = self.app.settings_manager.provider
        model = self.app.ai_processor.get_current_model(provider)
        return self.vision_validator.has_vision_support(provider, model)
```

Ces refactorings rendraient le code plus maintenable, testable, et respecteraient mieux le principe de responsabilité unique (SRP).