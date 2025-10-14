"vision" openAI compatible

## Implémentation du support vision pour OpenAI-compatible

### Problématique

- OpenAI-compatible : modèles saisis manuellement (pas de liste prédéfinie comme Ollama)
- Besoin de marquer dynamiquement quels modèles supportent la vision
- Interface utilisateur pour indiquer le support vision

### Solution proposée

#### 1. Modification du stockage des données

Ajouter une propriété `has_vision` dans la config :

```json
{
  "openai-compatible": {
    "api_key": "...",
    "api_base": "https://openrouter.ai/api/v1",
    "api_model": "google/gemini-2.0-flash-exp:free",
    "has_vision": true
  }
}
```

#### 2. Extension du système de settings

- Ajouter un `BooleanSetting` ou `CheckboxSetting` dans `settings.py`
- Pour OpenAI-compatible : case à cocher "Supporte la vision"

#### 3. Logique de détection

Dans le provider OpenAI-compatible, détecter automatiquement :

```python
# Dans _get_response_impl
model_name = self.api_model
has_vision = getattr(self, 'has_vision', False)

if has_vision and image_data:
    # Traiter l'image
    pass
```

#### 4. Interface utilisateur

- Ajouter une case à cocher dans les settings du provider
- Texte d'aide : "Cochez si ce modèle supporte les images/vision"
- Sauvegarde automatique dans la config

#### 5. Alternative : Détection par préfixe

Si tu préfères l'approche "*model_name" :

```python
# Dans load_config ou set_value
if self.api_model.startswith('*'):
    self.api_model = self.api_model[1:]  # Enlever l'astérisque
    self.has_vision = True
else:
    self.has_vision = False
```

### Avantages de l'approche case à cocher

- Plus explicite pour l'utilisateur
- Pas de modification du nom du modèle
- Compatible avec tous les providers
- Plus maintenable

### Étapes d'implémentation

1. Créer `BooleanSetting` dans `settings.py`
2. Ajouter le setting dans `OpenAICompatibleProvider.__init__`
3. Modifier `load_config`/`save_config` pour gérer `has_vision`
4. Utiliser `self.has_vision` dans `_get_response_impl`

---

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
 ajouter la detection de la version avant de download et d'intaller ollama

---

mettre un timer de fin d'écoute quand une touche pressée. ou améliorer la logique. bug intermittents.

---