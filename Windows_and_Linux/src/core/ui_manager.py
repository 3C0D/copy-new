"""
UI Manager - Gestion centralisée des fenêtres et modales de l'application.

Ce module fournit une classe UIManager qui centralise la gestion de toutes les
fenêtres et modales de l'application Writing Tools.
"""

import logging
from typing import TYPE_CHECKING, Optional

from PySide6.QtWidgets import QMessageBox

from ..ui.NonEditableModal import NonEditableModal
from ..ui.OnboardingWindow import OnboardingWindow
from ..ui.ResponseWindow import ResponseWindow
from ..ui.SettingsWindow import SettingsWindow

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


class UIManager:
    """
    Gestionnaire centralisé pour toutes les fenêtres et modales de l'application.

    Cette classe fournit des méthodes pour afficher et gérer les différentes
    fenêtres de l'interface utilisateur de manière centralisée.
    """

    def __init__(self, app: "WritingToolApp"):
        """
        Initialise le gestionnaire d'interface utilisateur.

        Args:
            app: Instance principale de l'application WritingToolApp
        """
        self.app = app
        self._logger = logging.getLogger(__name__)

        # Références aux fenêtres actives
        self.onboarding_window: Optional[OnboardingWindow] = None
        self.settings_window: Optional[SettingsWindow] = None
        self.response_window: Optional[ResponseWindow] = None
        self.non_editable_modal: Optional[NonEditableModal] = None

    def show_onboarding(self) -> None:
        """
        Affiche la fenêtre d'onboarding pour les nouveaux utilisateurs.

        Crée une instance d'OnboardingWindow et l'affiche, en connectant
        le signal de fermeture à la méthode de gestion appropriée.
        """
        self._logger.debug("Affichage de la fenêtre d'onboarding")

        if self.onboarding_window:
            self.onboarding_window.close()

        self.onboarding_window = OnboardingWindow(self.app)
        self.onboarding_window.close_signal.connect(self.on_onboarding_closed)
        self.onboarding_window.show()

    def on_onboarding_closed(self) -> None:
        """
        Gère la fermeture de la fenêtre d'onboarding.

        Cette méthode est appelée lorsque l'utilisateur ferme la fenêtre
        d'onboarding, permettant de continuer l'initialisation normale
        de l'application.
        """
        self._logger.debug("Fenêtre d'onboarding fermée, continuation de l'initialisation")
        self.onboarding_window = None

        # Déléguer la logique métier à l'application principale
        if hasattr(self.app, "on_onboarding_closed"):
            self.app.on_onboarding_closed()

    def show_settings(self, providers_only: bool = False, previous_window=None) -> None:
        """
        Show the settings window with debounce protection against rapid clicks.

        Args:
            providers_only: If True, show only the provider settings section
            previous_window: Previous window for navigation
        """
        import time

        current_time = time.time() * 1000  # Convert to milliseconds

        # Prevent rapid successive clicks that could accidentally open Settings
        # This fixes the bug where rapid right-clicks on tray icon open Settings accidentally
        if (
            hasattr(self.app.systray_manager, "last_tray_click_time")
            and (current_time - self.app.systray_manager.last_tray_click_time)
            < self.app.systray_manager.tray_click_debounce_ms
        ):
            self._logger.debug("Settings click ignored due to debounce protection")
            return

        self.app.systray_manager.last_tray_click_time = int(current_time)

        self._logger.debug("Showing settings window")

        if self.settings_window:
            self.settings_window.close()

        # Always create a new settings window to handle providers_only correctly
        self.settings_window = SettingsWindow(self.app, providers_only=providers_only)

        # Set reference to previous window for navigation
        if previous_window:
            self.settings_window.previous_window = previous_window

        self.settings_window.close_signal.connect(self.app.exit_app)
        self.settings_window.retranslate_ui()
        self.settings_window.show()

    def show_response_window(self, option: str, text: Optional[str] = None) -> ResponseWindow:
        """
        Affiche une fenêtre de réponse pour afficher les résultats de l'IA.

        Args:
            option: Option sélectionnée (ex: "Summary", "Rewrite", etc.)
            text: Texte sélectionné ou None pour le mode image

        Returns:
            ResponseWindow: Instance de la fenêtre créée
        """
        self._logger.debug(f"Affichage de la fenêtre de réponse pour l'option: {option}")

        response_window = ResponseWindow(self.app, f"{option} Result")

        # Configuration pour l'image si disponible
        if (
            hasattr(self.app.popup_manager, "has_image")
            and self.app.popup_manager.has_image
            and self.app.popup_manager.image
        ):
            response_window.image = self.app.popup_manager.image
            self._logger.debug("Image configurée dans la fenêtre de réponse")
            response_window.selected_text = None
        else:
            response_window.selected_text = text
            response_window.image = None

        response_window.show()
        self.response_window = response_window
        return response_window

    def show_message_box(self, title: str, message: str) -> None:
        """
        Affiche une boîte de message avec le titre et le message donnés.

        Pour les erreurs API, ajoute un bouton pour ouvrir les paramètres.

        Args:
            title: Titre de la boîte de message
            message: Message à afficher
        """
        self._logger.debug(f"Affichage d'une boîte de message: {title}")

        msg_box = QMessageBox(None)
        msg_box.setWindowFlags(msg_box.windowFlags() | self.app.Qt.WindowType.WindowStaysOnTopHint)  # type: ignore
        msg_box.setWindowTitle(title)
        msg_box.setText(message)

        # Ajouter le bouton OK standard
        msg_box.addButton(QMessageBox.StandardButton.Ok)

        # Pour les erreurs API, ajouter un bouton pour ouvrir les paramètres
        settings_button = None
        if any(
            keyword in title.lower()
            for keyword in [
                "api",
                "key",
                "quota",
                "rate limit",
                "connection",
                "authentication",
                "vision",
                "configuration",
            ]
        ):
            settings_button = msg_box.addButton("Open Settings", QMessageBox.ButtonRole.ActionRole)

        # Afficher la boîte de message
        msg_box.exec()

        # Si le bouton paramètres a été cliqué, ouvrir les paramètres
        if settings_button and msg_box.clickedButton() == settings_button:
            self.show_settings()

    def _show_non_editable_modal(self, transformed_text: Optional[str] = None) -> None:
        """
        Affiche une modale pour le texte non éditable.

        Utilisée lorsque le collage direct échoue et qu'il faut afficher
        le texte transformé dans une modale.

        Args:
            transformed_text: Texte transformé à afficher
        """
        self._logger.debug("Affichage de la modale non éditable")

        if self.non_editable_modal:
            self.non_editable_modal.close()

        self.non_editable_modal = NonEditableModal(self.app, transformed_text)
        self.non_editable_modal.show()

    # pas utilisé? !!!
    def close_all_windows(self) -> None:
        """
        Ferme toutes les fenêtres gérées par ce gestionnaire.
        """
        self._logger.debug("Fermeture de toutes les fenêtres")

        windows_to_close = [
            self.onboarding_window,
            self.settings_window,
            self.response_window,
            self.non_editable_modal,
        ]

        for window in windows_to_close:
            if window:
                window.close()

        # Réinitialiser les références
        self.onboarding_window = None
        self.settings_window = None
        self.response_window = None
        self.non_editable_modal = None
