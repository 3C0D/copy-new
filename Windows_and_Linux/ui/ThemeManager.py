"""
Gestionnaire centralisé des thèmes pour toute l'application.
Remplace les méthodes get_*_style() éparpillées par un système unifié.
"""

from PySide6 import QtCore
from ui.ui_utils import colorMode, set_color_mode, get_effective_color_mode


class ThemeManager(QtCore.QObject):
    """Gestionnaire centralisé des thèmes avec signaux pour notifier les changements."""

    # Signal émis quand le thème change
    theme_changed = QtCore.Signal(str)  # Émet le nouveau mode (dark/light)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, '_initialized'):
            return
        super().__init__()
        self._initialized = True
        self._registered_widgets = []

    def register_widget(self, widget):
        """Enregistre un widget pour recevoir les mises à jour de thème."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget):
        """Désenregistre un widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def change_theme(self, new_mode):
        """Change le thème et notifie tous les widgets enregistrés."""
        set_color_mode(new_mode)
        current_mode = get_effective_color_mode()
        self.theme_changed.emit(current_mode)

        # Rafraîchir tous les widgets enregistrés
        for widget in self._registered_widgets[:]:  # Copie pour éviter les modifications pendant l'itération
            if hasattr(widget, 'refresh_theme'):
                try:
                    widget.refresh_theme()
                except RuntimeError:
                    # Widget détruit, le retirer de la liste
                    self._registered_widgets.remove(widget)

    @staticmethod
    def get_styles():
        """Retourne tous les styles standardisés basés sur le thème actuel."""
        current_mode = get_effective_color_mode()
        is_dark = current_mode == 'dark'

        return {
            'label': f"font-size: 16px; color: {'#ffffff' if is_dark else '#333333'};",
            'title': f"font-size: 24px; font-weight: bold; color: {'#ffffff' if is_dark else '#000000'};",
            'provider_title': f"font-size: 18px; font-weight: bold; color: {'#ffffff' if is_dark else '#000000'};",
            'input': f"""
                font-size: 16px;
                padding: 5px;
                background-color: {'#444' if is_dark else 'white'};
                color: {'#ffffff' if is_dark else '#000000'};
                border: 1px solid {'#666' if is_dark else '#ccc'};
            """,
            'dropdown': f"""
                font-size: 16px;
                padding: 5px;
                background-color: {'#444' if is_dark else 'white'};
                color: {'#ffffff' if is_dark else '#000000'};
                border: 1px solid {'#666' if is_dark else '#ccc'};
            """,
            'radio': f"color: {'#ffffff' if is_dark else '#333333'};",
            'button': f"""
                QPushButton {{
                    background-color: {'#444' if is_dark else '#f0f0f0'};
                    color: {'#ffffff' if is_dark else '#000000'};
                    border: 1px solid {'#666' if is_dark else '#ccc'};
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {'#555' if is_dark else '#e0e0e0'};
                }}
            """,
            'action_button': """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                    font-size: 16px;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """,
        }


class ThemeAwareMixin:
    """Mixin pour rendre un widget conscient des changements de thème."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        theme_manager.register_widget(self)
        # Connecter le signal de changement de thème
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self, new_mode):
        """Appelé automatiquement quand le thème change."""
        if hasattr(self, 'refresh_theme'):
            self.refresh_theme()

    def get_styles(self):
        """Raccourci pour obtenir les styles actuels."""
        return ThemeManager.get_styles()

    def closeEvent(self, event):
        """Désenregistrer le widget quand il se ferme."""
        theme_manager.unregister_widget(self)
        if hasattr(super(), 'closeEvent'):
            super().closeEvent(event)


# Instance globale
theme_manager = ThemeManager()
