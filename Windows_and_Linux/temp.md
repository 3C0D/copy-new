

Continuer la refactorisation de custom pop-up window

---

refactoriser Response window.

styles pour response window dans get_styles...

----
show_message_signal, message_box error level pour log

---

language help window

---

inverser écritures dans debugs

---

meilleure gestion releases updates, par os

---

translations.py Continuez à vérifier Les translations pour l'ensemble de l'application

---
comprendre le focus dans settings window

---

provider_settings language change

---

mettre à jour updates

---

Opérations qui pourraient être bloquées avant response window dans validate_connection :

1. **Support vision** (déjà implémenté) : Vérifier si le modèle supporte les images quand image fournie

2. **Taille du texte** : Bloquer si le texte sélectionné dépasse les limites du modèle
   - Ex: GPT a une limite de tokens, vérifier avant d'envoyer

3. **Format d'image** : Valider que l'image est dans un format supporté (PNG, JPEG, etc.)
   - Vérifier les dimensions, taille de fichier

4. **Connexion réseau** : Test rapide de connectivité à l'API endpoint
   - Ping ou requête simple pour vérifier que l'API est accessible

5. **Quota/Rate limits** : Vérifier si on approche les limites d'utilisation
   - Pour les providers qui exposent ces infos via API

6. **Permissions** : Vérifier l'accès aux ressources nécessaires
   - Droits d'écriture pour sauvegarder, accès aux fichiers temporaires

7. **Configuration API spécifique** : Valider les paramètres avancés
   - Organization ID requis pour certains providers
   - Project ID pour OpenAI
   - Format de base URL valide

8. **Modèle disponible** : Pour les providers avec liste fixe, vérifier que le modèle existe encore
   - Les modèles peuvent être dépréciés

9. **Authentification** : Test rapide de validité de la clé API
   - Requête simple pour vérifier que la clé n'est pas expirée

10. **Ressources système** : Vérifier la disponibilité des ressources
    - Espace disque pour les réponses longues
    - Mémoire disponible pour le traitement d'images

---

About window refresh_language à revoir et réutiliser ?

---

mettre un timer de fin d'écoute quand une touche pressée. ou améliorer la logique. bug intermittents.

---