1. **Réutilisation de la logique existante** : Le cas `image != None` et `selected_text = None` tombe naturellement dans `is_custom_option and not has_selected_text`

2. **Suppression des conditions redondantes** : Plus de vérification `has_image` dans `_should_display_in_window` car c'est déjà géré par la condition existante

3. **Transmission simple des données d'image** : Via `image_data` dans les prompts sans créer de nouvelles branches logiques

4. **Préservation de l'architecture** : Aucun changement dans `_setup_response_window` car la logique originale fonctionne parfaitement

votre approche: quand il y a une image, on simule le comportement "Custom sans texte" qui ouvre automatiquement la fenêtre avec uniquement l'input de prompt manuel.

# Améliorer le nettoyage des ressources
def closeEvent(self, event) -> None:
    """Handle cleanup when window is closed."""
    # Clean up image resources
    if hasattr(self, 'image') and self.image:
        self.image = None
        
    # Clear any stored image data
    self.has_image = False
    
    super().closeEvent(event)