# 🤖 **GUIDE DE CRÉATION DE DOCUMENTS DE PARCOURS - Pour l'IA**

## **OBJECTIF**

Créer des documents de parcours utilisateur interactifs et complets pour chaque fonctionnalité de l'application Writing Tools.

---

## **STRUCTURE STANDARD À SUIVRE**

### **1. En-tête du document**

```markdown
# 🔄 **TITRE DU FLOW - Interactive Documentation**

## **COMPLETE FLOW - "Description du cas" :**
```

### **2. Vue d'ensemble pour l'IA**

```markdown
### **📋 Overview for LLM :**

User Action → Étape 1 → Étape 2 → Étape 3 → Résultat final
```

### **3. Étapes numérotées avec format standard**

````markdown
## **X. 👤 Action utilisateur**
### **Action :** Description claire de l'action
### **Code :** [`fonction()`](../fichier.py#Lligne)
### **What this function does :**
- Point 1
- Point 2
- Point 3

```python
# Code snippet pertinent
```
````

### **4. Section de dépannage**

```markdown
## **🔧 TROUBLESHOOTING - Checkpoints :**

### **Si problème spécifique :**
1. ✅ Vérification 1
2. ✅ Vérification 2
3. ✅ Vérification 3
```

### **5. Comparaisons et variantes**

```markdown
## **📊 COMPARISON - Cas A vs Cas B :**

| Aspect | Cas A | Cas B |
|--------|-------|-------|
| **Trigger** | Condition A | Condition B |
| **Résultat** | Output A | Output B |
```

### **6. Conseils pratiques**

```markdown
## **💡 PRO TIPS :**

- **Conseil 1** : Description
- **Conseil 2** : Description
```

---

## **RÈGLES DE CRÉATION**

### **📝 Règles générales**

1. **Toujours inclure les chemins de fichiers relatifs** : `../WritingToolApp.py`, `../ui/CustomPopupWindow.py`
2. **Ligne de code spécifique** : `#L565` pour pointer vers la ligne exacte
3. **Liens interactifs** : [`nom_fonction()`](../fichier.py#LXXX)
4. **Emojis cohérents** :
   - 👤 Actions utilisateur
   - → Transitions
   - ✅ Points de vérification
   - 🔄 Flows généraux
   - 💬 Chat/interaction
   - 🔧 Dépannage

### **🏗️ Structure logique**

1. **Déclenchement** : Comment l'utilisateur démarre le flow
2. **Capture** : Comment le système capture le contexte (texte, image, etc.)
3. **Interface** : Quelle fenêtre s'ouvre et pourquoi
4. **Configuration** : Paramètres clés (`return_response`, `current_response_window`, etc.)
5. **Traitement** : Comment la demande est envoyée à l'IA
6. **Réponse** : Comment la réponse est gérée et affichée
7. **Utilisation** : Comment l'utilisateur utilise le résultat

### **🔍 Points critiques à documenter**

- **Conditions de déclenchement** : Avec/sans sélection, avec/sans image
- **Variables d'état** : `return_response`, `selected_text`, `current_response_window`
- **Signaux Qt** : `output_ready_signal`, `invokeMethod`
- **Modes de traitement** : Threading, signaux, retours directs

---

## **EXEMPLES DE PROCHAINS DOCUMENTS À CRÉER**

### **1. "Pas de sélection + Mode chat forcé"**

**Titre suggéré :** `forced_chat_mode_flow.md`
**Cas :** Quand l'utilisateur force le mode chat même avec du texte sélectionné
**Étapes :**

- Hotkey avec sélection
- Popup s'ouvre
- Utilisateur choisit "Chat" explicitement
- Force `return_response = True`
- Ouvre ResponseWindow malgré la sélection

### **2. "Mode image + Description"**

**Titre suggéré :** `image_description_flow.md`
**Cas :** Quand l'utilisateur capture une image
**Étapes :**

- Capture d'écran ou image
- Analyse par IA
- Génération de description
- Options de traitement (résumé, description longue, etc.)

### **3. "Mode multi-sélection"**

**Titre suggéré :** `multi_selection_flow.md`
**Cas :** Sélection de plusieurs blocs de texte
**Étapes :**

- Détection de sélections multiples
- Consolidation ou traitement séparé
- Interface adaptée

### **4. "Mode correction automatique"**

**Titre suggéré :** `auto_correction_flow.md`
