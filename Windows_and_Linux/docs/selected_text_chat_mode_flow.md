# 🔄 **FLUX TEXTE SÉLECTIONNÉ + MODE CHAT - Documentation Interactive**

## **COMPLETE FLOW - "Texte sélectionné avec Force Chat ou bouton Chat" :**

### **📋 Overview for LLM :**

```markdown
User Action → Hotkey avec texte → Popup s'ouvre → Force Chat activé OU bouton avec open_in_window=True → ResponseWindow devrait s'ouvrir → ❌ PROBLÈME : current_response_window not available
```

---

## **1. 👤 Utilisateur presse le raccourci configuré (par défaut: ctrl space) (avec texte sélectionné)**

### **Action :** Utilisateur déclenche le raccourci avec du texte sélectionné

### **Code :** [`on_hotkey_pressed()`](../WritingToolApp.py#L565)

### **What this function does :**

- Vérifie le spam de raccourcis
- Ferme les fenêtres existantes
- Annule la requête du provider actuel
- Déclenche `_show_popup()` via signal Qt

```python
# Dans les logs fournis :
2025-08-27 20:43:47,066 - DEBUG - Hotkey pressed ==============================
2025-08-27 20:43:47,067 - DEBUG - Cancelling current provider's request
2025-08-27 20:43:47,071 - DEBUG - Showing popup window
```

---

## **2. → _show_popup()**

### **Action :** Affichage de la fenêtre popup

### **Code :** [`_show_popup()`](../WritingToolApp.py#L583)

### **What this function does :**

- Capture le texte sélectionné - **Dans ce cas: selected_text = "c'est"**
- Ferme les fenêtres existantes
- Crée et positionne CustomPopupWindow

```python
# Dans les logs :
2025-08-27 20:43:47,143 - DEBUG - Getting selected text
2025-08-27 20:43:47,400 - DEBUG - Text retrieved and cleaned: 5 characters
2025-08-27 20:43:47,406 - DEBUG - Selected text: "c'est"
2025-08-27 20:43:47,407 - DEBUG - Creating new popup window ============
```

---

## **3. CustomPopupWindow s'ouvre (Mode avec texte sélectionné)**

### **Action :** Interface utilisateur prête avec texte sélectionné

### **Code :** [`CustomPopupWindow`](../ui/CustomPopupWindow.py)

### **What this class does :**

- **Interface Setup** : Crée popup avec barre de titre, champ input, boutons d'action
- **Mode Detection** : `has_sel_text = True` car texte sélectionné
- **Options Display** : Affiche les boutons d'action + toggle Force Chat

### **Options disponibles avec texte sélectionné :**

#### **🎯 Boutons d'Action**

- **Boutons standards** : Rewrite, Summary, etc.
- **Indicateurs** : Ⓡ pour remplacement, Ⓒ pour chat
- **Configuration** : `open_in_window` détermine le comportement

#### **🔄 Force Chat Toggle**

- **Fonction** : Force `return_response=True` même avec texte sélectionné
- **État** : Peut être verrouillé pour maintenir le réglage
- **Visual** : Toggle switch avec animation

#### **📝 Custom Input**

- **Placeholder** : "Describe your change..."
- **Fonction** : Permet instructions personnalisées

---

## **4. 👤 Utilisateur active Force Chat OU clique bouton avec open_in_window=True**

### **Action :** Utilisateur choisit le mode chat

### **Exemples :**

- Active le toggle "Force Chat" puis clique "Custom"
- Clique un bouton configuré avec `open_in_window: true`

### **Code :** Interface CustomPopupWindow

---

## **5. ❌ PROBLÈME : CustomPopupWindow.process_option() - Logique défaillante**

### **Action :** Traitement de l'option sélectionnée

### **Code :** [`process_option()`](../ui/CustomPopupWindow.py#L1158)

### **🐛 PROBLÈME IDENTIFIÉ :**

```python
# ❌ LIGNE PROBLÉMATIQUE (ligne ~1158) :
action_config = self.app.settings_manager.actions  # Récupère TOUTES les actions

should_setup_response_window = (
    (is_custom_option and not has_selected_text)
    or action_config.get("open_in_window", False)  # ❌ TOUJOURS False car actions est un dict
    or (force_chat and has_selected_text)
)
```

### **🔍 ANALYSE DU PROBLÈME :**

1. **`action_config`** récupère **TOUTES** les actions au lieu de l'action spécifique
2. **`action_config.get("open_in_window", False)`** retourne toujours `False` car `actions` est un dictionnaire d'actions, pas une action spécifique
3. **La condition `force_chat and has_selected_text`** fonctionne, mais pas les boutons avec `open_in_window=True`

---

## **6. ✅ SOLUTION : Correction de la logique**

### **Code corrigé :**

```python
# ✅ CORRECTION :
action_config = self.app.settings_manager.actions.get(option, {})  # Action spécifique

should_setup_response_window = (
    (is_custom_option and not has_selected_text)
    or action_config.get("open_in_window", False)  # ✅ Maintenant correct
    or (force_chat and has_selected_text)
)
```

---

## **7. Flux correct après correction**

### **Action :** Traitement correct de l'option

### **Code :** [`process_option()`](../ui/CustomPopupWindow.py#L1158)

### **What should happen :**

```python
if should_setup_response_window:
    self._logger.debug("Setting up response window for output")
    self._setup_response_window(option, selected_text)  # ✅ Crée current_response_window
```

---

## **8. _setup_response_window() crée ResponseWindow**

### **Action :** Création de la fenêtre de chat

### **Code :** [`_setup_response_window()`](../ui/CustomPopupWindow.py#L1180)

### **What this function does :**

```python
window_title = "Chat" if not is_custom else option
self.app.current_response_window = self.show_response_window(window_title, selected_text)

# Initialise l'historique de chat
self.app.current_response_window.chat_history = [
    {"role": "user", "content": f"Original text to {option.lower()}:\n\n{selected_text}"}
]
```

---

## **9. get_response() appelé avec return_response=True**

### **Action :** Requête à l'IA en mode chat

### **Code :** [`get_response()`](../aiprovider.py)

### **What this function does :**

- Vérifie le mode de réponse :

  ```python
  if not return_response and not hasattr(self.app, "current_response_window"):
      # Mode remplacement direct
      self.app.output_ready_signal.emit(response_text)
  else:
      # Mode chat - retourne la réponse à la fenêtre
      return response_text
  ```

---

## **10. ✅ ResponseWindow affiche la réponse IA**

### **Action :** Réponse IA affichée dans la fenêtre de chat

### **Code :** [`ResponseWindow`](../ui/ResponseWindow.py)

### **What this function does :**

- Affiche la réponse générée par l'IA
- Fournit des options pour copier, éditer ou utiliser la réponse
- Permet les questions de suivi

---

## **🔧 TROUBLESHOOTING - Points de vérification :**

### **Si la fenêtre de chat ne s'ouvre pas :**

1. ✅ **Vérifier `action_config`** : Doit récupérer l'action spécifique, pas toutes les actions
2. ✅ **Vérifier `should_setup_response_window`** : Doit être `True` pour Force Chat ou boutons chat
3. ✅ **Vérifier `current_response_window`** : Doit être créé dans `_setup_response_window`
4. ✅ **Vérifier les logs** : "Setting up response window for output" doit apparaître

### **Logs de débogage attendus (après correction) :**

```
DEBUG - Processing option: Custom
DEBUG - should_setup_response_window: True
DEBUG - Setting up response window for output
DEBUG - Showing response window with text: c'est
DEBUG - Getting response for window display
DEBUG - Got response of length: X
DEBUG - Invoked set_text on response window
```

### **Au lieu de :**

```
DEBUG - Processing option: Custom
DEBUG - should_setup_response_window: False  # ❌ PROBLÈME
WARNING - current_response_window not available for update  # ❌ CONSÉQUENCE
```

---

## **📊 COMPARAISON - Avant vs Après correction :**

| Aspect | Avant (Bugué) | Après (Corrigé) |
|--------|---------------|-----------------|
| **action_config** | `self.app.settings_manager.actions` (dict complet) | `self.app.settings_manager.actions.get(option, {})` (action spécifique) |
| **open_in_window check** | Toujours `False` | Correct selon la configuration |
| **should_setup_response_window** | `False` pour boutons chat | `True` pour boutons chat et Force Chat |
| **current_response_window** | ❌ Non créé | ✅ Créé correctement |
| **Résultat** | Remplacement direct (incorrect) | Fenêtre de chat (correct) |

---

## **💡 POINTS CLÉS :**

- **Le problème principal** : Récupération incorrecte de la configuration d'action
- **Force Chat fonctionne** car il ne dépend pas de `action_config.get("open_in_window")`
- **Boutons avec open_in_window=True** ne fonctionnent pas à cause de cette erreur
- **La correction est simple** : une ligne à changer dans `process_option()`

---

*Documentation générée automatiquement - Liens interactifs vers le code source*
