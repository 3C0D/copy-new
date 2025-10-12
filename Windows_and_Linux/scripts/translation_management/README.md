# Translation Management System

Ce dossier contient tous les outils nécessaires pour gérer les traductions de l'application Writing Tools.

## 📋 Vue d'ensemble

Le système de traduction utilise gettext et permet de supporter plusieurs langues. Les traductions sont extraites automatiquement du code Python, traduites, puis compilées.

## 🗂️ Fichiers

### Scripts principaux
- `extract_translations.py` - Extrait les chaînes traduisibles du code
- `translate_po.py` - Traduit automatiquement les fichiers .po
- `compile_translations.py` - Compile les .po en .mo
- `find_untranslated.py` - Trouve les chaînes non traduites

### Structure des fichiers de traduction
```
locales/
├── messages.pot          # Template de traduction
├── en/LC_MESSAGES/
│   └── messages.po/.mo   # Anglais (référence)
├── fr/LC_MESSAGES/
│   └── messages.po/.mo   # Français
└── zh/LC_MESSAGES/
    └── messages.po/.mo   # Chinois (exemple)
```

## 🚀 Workflow complet

### 1. Extraction des chaînes
```bash
python scripts/translation_management/extract_translations.py
```
Scanne tout le code `src/` et trouve les appels `_()`. Met à jour `locales/messages.pot`.

### 2. Ajout d'une nouvelle langue
```bash
# Créer le dossier
mkdir -p locales/zh/LC_MESSAGES

# Copier le template
cp locales/messages.pot locales/zh/LC_MESSAGES/messages.po
```

### 3. Traduction automatique
```bash
# Traduction normale (chaînes vides seulement)
python scripts/translation_management/translate_po.py locales/zh/LC_MESSAGES/messages.po en zh

# Forcer retraduction de tout
python scripts/translation_management/translate_po.py locales/zh/LC_MESSAGES/messages.po en zh --force
```

### 4. Compilation
```bash
python scripts/translation_management/compile_translations.py zh
```

### 5. Mise à jour après ajout de code
Quand vous ajoutez de nouvelles chaînes `_()` dans le code :

1. **Ré-extraire** : `extract_translations.py` met à jour le `.pot`
2. **Fusion intelligente** : Les outils fusionnent automatiquement :
   - ✅ Chaînes existantes gardent leurs traductions
   - ✅ Nouvelles chaînes ajoutées vides
   - ✅ Chaînes supprimées commentées

## 🔧 Scripts détaillés

### extract_translations.py
- **Rôle** : Scan automatique du code Python
- **Entrée** : Dossier `src/`
- **Sortie** : `locales/messages.pot`
- **Utilité** : Nécessaire sous Windows (remplace xgettext)

### translate_po.py
- **Rôle** : Traduction automatique via Google Translate
- **Options** :
  - `--force` : Retraduit toutes les chaînes (même existantes)
  - Sans `--force` : Traduit seulement les chaînes vides
- **Utilité** : Accélère la traduction initiale

### compile_translations.py
- **Rôle** : Compilation .po → .mo (format binaire)
- **Utilité** : Fichiers .mo utilisés par Python gettext

### find_untranslated.py
- **Rôle** : Détecte les chaînes non traduites
- **Utilité** : Vérification qualité

## 🎯 Rôles respectifs : Script vs LLM

### 🤖 Ce qui doit être fait par script :
- ✅ Extraction automatique des chaînes `_()`
- ✅ Traduction automatique (Google Translate)
- ✅ Compilation .po → .mo
- ✅ Détection des chaînes non traduites

### 🧠 Ce qui doit être fait par LLM (toi) :
- ✅ Vérification qualité des traductions automatiques
- ✅ Corrections contextuelles ("Start on boot" → "Démarrer au démarrage")
- ✅ Adaptation culturelle et terminologique
- ✅ Vérification de la longueur des chaînes UI
- ✅ Tests fonctionnels du changement de langue

## 📝 Exemple de corrections LLM

### Avant traduction automatique :
```
msgid "Start on boot"
msgstr "Commencer sur botte"  # ❌ Traduction littérale
```

### Après correction LLM :
```
msgid "Start on boot"
msgstr "Démarrer au démarrage"  # ✅ Terminologie correcte
```

## 🔄 Maintenance

### Ajout de nouvelles chaînes :
1. Ajouter `_()` dans le code
2. `extract_translations.py` → met à jour .pot
3. `translate_po.py --force` → retraduit tout
4. Vérifier/corriger avec LLM
5. `compile_translations.py`

### Nouvelle langue :
1. Créer dossier `locales/xx/LC_MESSAGES/`
2. Copier `messages.pot` → `messages.po`
3. `translate_po.py` → traduction automatique
4. Corrections LLM si nécessaire
5. `compile_translations.py`

## ⚠️ Points d'attention

- **Sauvegarde** : Toujours sauvegarder les traductions personnalisées avant `--force`
- **Contexte** : Les traductions automatiques peuvent manquer de contexte UI
- **Longueur** : Vérifier que les traductions ne dépassent pas l'espace UI
- **Terminologie** : Adapter aux conventions de chaque langue
- **Test** : Tester le changement de langue dans l'application