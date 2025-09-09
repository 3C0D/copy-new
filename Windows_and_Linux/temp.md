ICI → response_window L970

voir commit récent aiprovider load_config

gemini n'a pas détecté une clé api invalide

dans data model → default_model. et default provider? en cours...

Voir focus
revoir previous_window

ajout d'un, bouton sur l'image pour la supprimer. effacement image après fermeture response window

debug files 3? rotation? 1 seule?
log date namefile... partout

vsc setttings searchexclude marche qu'à la racine. revoir settings

Raccourci 3 touches.

def _get_base_directory(self) -> Path:
    """Get the base directory based on execution context."""
    if getattr(sys, "frozen", False):
        return Path(sys.executable).parent
    return Path(sys.argv[0]).parent

thread, threadpoolexecutor → asyncio?

terminate_existing_processes marche pas??

Is the current mode useful again?

Appel des fenêtres, fermeture, voire dans le module principal...

Mise à jour download sur github.

Des signaux de changement de thème sur toutes les fenêtres?

👉 Le plus léger que tu pourrais utiliser en local avec vision est typiquement :

Qwen2.5-VL-3B | `ollama run qwen2.5vl:3b` ou 7b

<!-- MiniCPM-V 2.6 (≈ 2B–4B de paramètres, conçu pour tourner sur machines modestes).

Sinon BakLLaVA 7B (basé sur LLaMA + CLIP, plus lourd mais encore raisonnable). -->


Vérifier le focus
dans settingsWindow.py Système de gestion du Focus avancé    
    
    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        # Force focus to this window when shown (important for hotkey workflow)
        self.raise_()
        self.activateWindow()
        self.setFocus()


parent dir executable
    script_dir = Path(__file__).parent  # scripts/
    windows_linux_dir = script_dir.parent  # Windows_and_Linux/