# 🔄 **FLUX TEXTE SÉLECTIONNÉ + MODE CHAT - Documentation Interactive**

## **FLUX COMPLET - "Texte sélectionné avec mode chat forcé" :**

### **📋 Overview for LLM :**

```markdown
User Action → Hotkey Detection → UI Creation → Force Chat Mode → AI Response → Response Window → Chat Interface
```

---

## **1. 👤 Utilisateur presse Ctrl+Space (avec texte sélectionné)**

### **Action :** L'utilisateur déclenche le raccourci avec du texte sélectionné

### **Code :** [`on_hotkey_pressed()`](../WritingToolApp.py#L565)

### **What this function does :**

- Vérifie le spam de raccourcis (protection anti-abus)
- Ferme les fenêtres existantes (modal/popup)
- Annule la requête du provider actuel
- Vide la queue de sortie
- Déclenche `_show_popup()` via signal Qt

```python
# Vérification anti-spam
if self.check_trigger_spam():
    return

# Nettoyage des fenêtres existantes
if self.non_editable_modal is not None:
    self.non_editable_modal.close()

if self.popup_window is not None:
    self.popup_window.close()

# Ferme la fenêtre de réponse existante (fenêtre de chat) si ouverte
if self.current_response_window is not None:
    self.current_response_window.close()
    self.current_response_window = None

# Annule la requête actuelle
if self.current_provider:
    self.current_provider.cancel()
    self.output_queue = ""

# Déclenche la popup
QtCore.QMetaObject.invokeMethod(self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection)
```

---

## **2. → _show_popup()**

### **Action :** Affichage de la fenêtre popup

### **Code :** [`_show_popup()`](../WritingToolApp.py#L583)

### **What this function does :**

- Capture le texte sélectionné (si pas d'image présente) - **Dans ce cas: selected_text contient le texte sélectionné**
- Ferme les fenêtres existantes
- Crée et positionne CustomPopupWindow
- Gère le focus et l'activation

```python
# Capture le texte si pas d'image - retourne le texte sélectionné
if self.image is None:
    selected_text = self.get_selected_text(sleep_duration=0.2)  # Retourne "c'est"

# Ferme les fenêtres existantes
if self.non_editable_modal is not None:
    self.non_editable_modal.close()

if self.popup_window is not None:
    self.popup_window.close()

# Crée une nouvelle popup
self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self, selected_text, self.image)
```

---

## **3. CustomPopupWindow s'ouvre (Mode avec texte sélectionné)**

### **Action :** Interface utilisateur prête pour l'interaction avec texte sélectionné

### **Code :** [`CustomPopupWindow`](../ui/CustomPopupWindow.py)

### **What this class does :**

- **Configuration Interface** : Crée popup avec barre de glissement, champ de saisie, boutons d'action
- **Détection Mode** : [`process_option()`](../ui/CustomPopupWindow.py#L1247) détecte texte sélectionné → **Mode boutons d'action** activé
- **Affichage Options** : Montre les outils IA disponibles basés sur le contexte

### **Options disponibles en Mode Texte Sélectionné :**

#### **🎯 Boutons d'Action (Principaux)**

- **Boutons Rewrite/Summary/etc.** : Actions prédéfinies sur le texte sélectionné
- **Instruction Système** : Basée sur la configuration de chaque action
- **Sortie** : Peut être remplacement direct OU fenêtre ResponseWindow selon `open_in_window`
- **Cas d'usage** : Transformation rapide de texte, résumés, réécritures

#### **🛠️ Force Chat Toggle (Critique pour ce flux)**

- **Quand Disponible** : Toujours affiché quand du texte est sélectionné
- **Fonction** : Force `return_response=True` même avec texte sélectionné
- **Fonctionnalité Verrouillage** : Peut être verrouillé pour maintenir le paramètre entre utilisations
- **Visuel** : Commutateur personnalisé avec animation de glissement
- **🔥 POINT CRITIQUE** : Quand activé, doit créer `current_response_window`

#### **🔧 Mode Édition (Paramètres)**

- **Accès** : Clic sur l'icône crayon (en haut à gauche)
- **Fonctionnalités** : Ajouter, éditer, supprimer et réorganiser les outils IA
- **Glisser-Déposer** : Réorganiser les outils en glissant
- **Persistance** : Changements sauvegardés dans le système de paramètres unifié

### **Comportement Spécifique Mode Texte Sélectionné :**

**Localisation :** [`process_option()` dans CustomPopupWindow.py](../ui/CustomPopupWindow.py#L1247)

```python
# Condition clé pour le mode fenêtre de réponse avec texte sélectionné
if selected_text.strip() and (force_chat or action_config.get("open_in_window", False)):
    return_response = True      # → Ouvre ResponseWindow
    current_response_window = self.show_response_window()
else:
    return_response = False     # → Remplacement direct
```

### **Éléments d'Interface :**

- **Barre Supérieure** : Poignée de glissement + Bouton Édition + Bouton Fermer
- **Zone de Saisie** : Champ de texte + Bouton Envoyer avec icône
- **Boutons d'Action** : Boutons Rewrite/Summary/Custom/etc. basés sur la configuration
- **Zone Force Chat** : Commutateur + bouton de verrouillage (visible avec texte sélectionné)

---

## **4. 👤 Utilisateur active Force Chat et clique sur une option**

### **Action :** L'utilisateur active le toggle "Force Chat" et choisit une action (ex: "Custom", "Rewrite", etc.)

### **Exemple :** L'utilisateur active Force Chat et clique sur "Custom" avec le texte "traduis"

### **Code :** Interface CustomPopupWindow

---

## **5. CustomPopupWindow.process_option() - Mode Force Chat**

### **Action :** Traite l'option sélectionnée en mode force chat

### **Code :** [`process_option()`](../ui/CustomPopupWindow.py#L1247)

### **🔥 PROBLÈME IDENTIFIÉ :**

```python
# PROBLÈME: La logique de _should_display_in_response_window ne gère pas correctement le force_chat
should_setup_response_window = self._should_display_in_response_window(
    option, selected_text, self.app.settings_manager.actions  # ❌ Passe actions au lieu d'action_config
)

# PROBLÈME: _should_display_in_response_window ne reçoit pas le paramètre force_chat
def _should_display_in_response_window(
    self, option: str, selected_text: str | None, action_config: dict  # ❌ Reçoit actions au lieu d'action_config
) -> bool:
    # ❌ force_chat n'est pas pris en compte ici
    has_selected_text = bool(selected_text and selected_text.strip() != "")
    is_custom_option = option == "Custom"
    # ❌ force_chat = getattr(self, "_current_force_chat", False) n'est pas encore défini
    
    return (
        (is_custom_option and not has_selected_text)
        or (has_selected_text and action_config.get("open_in_window", False))
        or (force_chat and has_selected_text)  # ❌ Cette condition n'est jamais vraie
        or self.has_image
    )
```

### **What this function should do :**

- `should_setup_response_window = True` (mode force chat avec texte sélectionné)
- `current_response_window = self.show_response_window()` (crée la fenêtre de réponse)
- Lance le traitement dans un thread séparé

---

## **6. 🔥 POINT DE DÉFAILLANCE - _should_display_in_response_window()**

### **Action :** Détermine si la réponse doit être affichée dans une fenêtre

### **Code :** [`_should_display_in_response_window()`](../ui/CustomPopupWindow.py#L1434)

### **🚨 PROBLÈMES IDENTIFIÉS :**

1. **Paramètre incorrect** : Reçoit `self.app.settings_manager.actions` au lieu de l'`action_config` spécifique
2. **Force chat non pris en compte** : `_current_force_chat` n'est pas encore défini au moment de l'appel
3. **Ordre d'exécution** : `_current_force_chat` est défini APRÈS l'appel à `_should_display_in_response_window`

```python
# ❌ PROBLÈME: Ordre d'exécution incorrect
should_setup_response_window = self._should_display_in_response_window(
    option, selected_text, self.app.settings_manager.actions  # Appelé AVANT
)

if should_setup_response_window:
    self._setup_response_window(option, selected_text)
elif hasattr(self.app, "current_response_window"):
    delattr(self.app, "current_response_window")

# Store force_chat state for the thread
self._current_force_chat = force_chat  # Défini APRÈS ❌
```

---

## **7. ❌ ÉCHEC - show_response_window() n'est pas appelé**

### **Action :** La fenêtre de réponse devrait être créée mais ne l'est pas

### **Code :** [`show_response_window()`](../ui/CustomPopupWindow.py#L1380)

### **What should happen but doesn't :**

- Création d'une nouvelle instance ResponseWindow
- Configuration de l'interface de chat
- Retour de la référence de fenêtre pour la gestion des réponses

### **🚨 RÉSULTAT :**

- `self.app.current_response_window` reste `None` ou n'existe pas
- Le thread de traitement continue sans fenêtre de réponse
- L'IA génère une réponse mais ne peut pas l'afficher

---

## **8. get_response() appelé avec return_response=False**

### **Action :** Requête à l'IA en mode remplacement direct (incorrect)

### **Code :** [`get_response()`](../aiprovider.py#L500)

### **What this function does (incorrectly) :**

- Vérifie le mode de réponse :

  ```python
  # ❌ PROBLÈME: return_response=False car current_response_window n'existe pas
  if not return_response and not hasattr(self.app, "current_response_window"):
      # Mode remplacement direct (incorrect pour force chat)
      self.app.output_ready_signal.emit(response_text)
      return ""
  else:
      # Mode chat - retourne response_text directement (ne se produit pas)
      return response_text
  ```

---

## **9. ❌ ÉCHEC - Tentative de mise à jour de current_response_window**

### **Action :** Tentative de mise à jour d'une fenêtre qui n'existe pas

### **Code :** [`_update_response_window()`](../ui/CustomPopupWindow.py#L1421)

### **What happens :**

```python
def _update_response_window(self, response: str) -> None:
    """Update response window with AI response (thread-safe)."""
    if hasattr(self.app, "current_response_window") and self.app.current_response_window:
        # ✅ Cette condition devrait être vraie mais ne l'est pas
        QtCore.QMetaObject.invokeMethod(
            self.app.current_response_window,
            "set_text",
            QtCore.Qt.ConnectionType.QueuedConnection,
            QtCore.Q_ARG(str, response),
        )
        self._logger.debug("Invoked set_text on response window")
    else:
        # ❌ Cette branche s'exécute à la place
        self._logger.warning("current_response_window not available for update")
```

---

## **🔧 SOLUTION IDENTIFIÉE :**

### **Problème Principal :**

L'ordre d'exécution dans `process_option()` est incorrect. `_current_force_chat` est défini APRÈS l'appel à `_should_display_in_response_window()`, ce qui fait que le force chat n'est jamais pris en compte.

### **Corrections Nécessaires :**

1. **Corriger l'ordre d'exécution** :

```python
# Store force_chat state BEFORE checking
self._current_force_chat = force_chat

should_setup_response_window = self._should_display_in_response_window(
    option, selected_text, force_chat
)
```

2. **Corriger les paramètres de _should_display_in_response_window** :

```python
def _should_display_in_response_window(
    self, option: str, selected_text: str | None, force_chat: bool = False
) -> bool:
    """Determine if response should be displayed in a window."""
    has_selected_text = bool(selected_text and selected_text.strip() != "")
    is_custom_option = option == "Custom"
    
    # Get action config properly
    action_config = self.app.settings_manager.actions.get(option, {})
    
    return (
        (is_custom_option and not has_selected_text)
        or (has_selected_text and action_config.get("open_in_window", False))
        or (force_chat and has_selected_text)  # ✅ Maintenant fonctionne
        or self.has_image
    )
```

---

## **🔧 TROUBLESHOOTING - Points de Vérification :**

### **Si la fenêtre de chat ne s'ouvre pas :**

1. ✅ Vérifier que `force_chat` est `True`
2. ✅ Vérifier que `selected_text` n'est pas vide
3. ✅ Vérifier que `_should_display_in_response_window` retourne `True`
4. ✅ Vérifier que `current_response_window` est créé dans `_setup_response_window`
5. ✅ Vérifier l'ordre d'exécution dans `process_option`

### **Si l'IA ne répond pas dans le chat :**

1. ✅ Vérifier que `return_response=True` est passé au provider
2. ✅ Vérifier la configuration du provider IA
3. ✅ Vérifier la connectivité réseau
4. ✅ Vérifier les clés API/tokens

### **Si les questions de suivi ne fonctionnent pas :**

1. ✅ Vérifier que ResponseWindow maintient le contexte de conversation
2. ✅ Vérifier que chaque question déclenche une nouvelle requête IA
3. ✅ Vérifier que les réponses sont correctement ajoutées

### **Fichiers clés à surveiller :**

- [`WritingToolApp.py`](../WritingToolApp.py) - Logique principale et gestion popup
- [`CustomPopupWindow.py`](../ui/CustomPopupWindow.py) - Détection mode fenêtre de réponse et création ResponseWindow
- [`ResponseWindow.py`](../ui/ResponseWindow.py) - Interface de chat et gestion des suivis
