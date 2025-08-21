# Guide d'Intégration des Images - Custom Pop-up Windows

## 🎉 Nouvelle Fonctionnalité : Support des Images

Votre Custom Pop-up Windows supporte maintenant les images ! Vous pouvez coller des images directement dans l'interface et les envoyer à l'IA pour analyse.

## 🚀 Comment Utiliser

### 1. Coller une Image

- Ouvrez le Custom Pop-up Windows (Ctrl+C deux fois ou hotkey)
- Dans le champ de texte, appuyez sur **Ctrl+V** avec une image dans le clipboard
- Un aperçu de l'image apparaîtra avec un bouton pour l'effacer (✕)

### 2. Envoyer à l'IA

- Tapez votre question ou instruction (optionnel)
- Cliquez sur le bouton d'envoi ou appuyez sur Entrée
- **Le mode chat sera automatiquement activé** quand une image est présente
- L'IA recevra votre texte ET l'image pour analyse

### 3. Chat avec Images

- La réponse s'ouvrira dans une fenêtre de chat
- L'historique montrera un indicateur 🖼️ pour les messages avec images
- Vous pouvez continuer la conversation normalement

## 🔧 Fonctionnalités Techniques

### Formats d'Images Supportés

- PNG, JPEG, JPG, GIF, BMP
- Images copiées depuis le clipboard
- Conversion automatique en JPEG pour l'envoi

### Providers IA Compatibles

- ✅ **Gemini** : Support complet des images
- ❌ OpenAI, Ollama, Anthropic, Mistral : Texte uniquement (l'image sera ignorée)

### Comportements Automatiques

- **Force Chat Mode** : Activé automatiquement quand une image est présente
- **Aperçu** : Miniature de 80x120 pixels maximum
- **Nettoyage** : Fichiers temporaires supprimés automatiquement

## 🎯 Cas d'Usage

### Analyse d'Images

```
Prompt: "Décris cette image en détail"
+ Image collée
→ L'IA analysera l'image et fournira une description
```

### Traduction de Texte dans Images

```
Prompt: "Traduis le texte dans cette image en français"
+ Image avec texte
→ L'IA lira et traduira le texte visible
```

### Questions sur le Contenu

```
Prompt: "Que vois-tu d'intéressant dans cette capture d'écran ?"
+ Capture d'écran
→ L'IA analysera et commentera le contenu
```

## 🔍 Interface Utilisateur

### Indicateurs Visuels

- **🖼️ Icône d'image** : Apparaît dans l'aperçu et l'historique du chat
- **Bouton ✕** : Pour effacer l'image sélectionnée
- **Force Chat activé** : Toggle automatiquement coché

### Workflow Complet

1. **Sélection de texte** (optionnel) → Custom Pop-up s'ouvre
2. **Ctrl+V avec image** → Aperçu apparaît + Force Chat activé
3. **Saisie du prompt** → Description de ce que vous voulez
4. **Envoi** → Mode chat avec image + texte envoyés à l'IA
5. **Réponse** → Chat window avec historique incluant l'image

## ⚙️ Configuration

### Prérequis

- Provider Gemini configuré avec clé API valide
- Image dans le clipboard (copiée depuis n'importe quelle source)

### Paramètres

- Aucune configuration supplémentaire requise
- Le mode chat se force automatiquement avec les images
- Les images sont temporairement sauvées puis supprimées

## 🐛 Dépannage

### L'image ne s'affiche pas

- Vérifiez qu'une image est bien dans le clipboard
- Essayez de copier l'image à nouveau
- Formats supportés : PNG, JPEG, GIF, BMP

### L'IA ne voit pas l'image

- Vérifiez que vous utilisez le provider Gemini
- Les autres providers ignorent les images (fonctionnalité normale)
- Assurez-vous que votre clé API Gemini est valide

### Erreurs de traitement

- Vérifiez votre connexion internet
- Essayez avec une image plus petite
- Redémarrez l'application si nécessaire

## 🎨 Personnalisation Future

Cette intégration est extensible pour :

- Support d'autres providers IA avec images
- Aperçus d'images plus détaillés
- Glisser-déposer d'images
- Sélection d'images depuis fichiers

## 📝 Notes Techniques

### Architecture

- `CustomPopupWindow` : Gestion du collage et aperçu
- `GeminiProvider` : Envoi des images en base64
- `ResponseWindow` : Affichage de l'historique avec images
- `WritingToolApp` : Coordination du workflow

### Sécurité

- Images converties en base64 pour transmission
- Fichiers temporaires nettoyés automatiquement
- Pas de stockage permanent des images

---

🎉 **Profitez de cette nouvelle fonctionnalité pour enrichir vos interactions avec l'IA !**
