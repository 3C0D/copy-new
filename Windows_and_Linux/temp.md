Is the current mode useful again?

Appel des fenêtres, fermeture, voire dans le module principal...

Mise à jour download sur github.

Des signaux de changement de thème sur toutes les fenêtres?


Vérifier le focus
dans settingsWindow.py Système de gestion du Focus avancé    
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        # Force focus to this window when shown (important for hotkey workflow)
        self.raise_()
        self.activateWindow()
        self.setFocus()


