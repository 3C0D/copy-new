dans settingsWindow.py Système de gestion du Focus avancé    
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        # Force focus to this window when shown (important for hotkey workflow)
        self.raise_()
        self.activateWindow()
        self.setFocus()