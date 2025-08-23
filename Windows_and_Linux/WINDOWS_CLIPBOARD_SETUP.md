# Windows Clipboard Setup Guide

## 🎯 Objectif
Permettre à l'application de détecter les images du clipboard sur Windows **exactement comme Claude le fait**.

## 🚀 Installation sur Windows

### 1. **Installer pywin32**
```bash
# Dans votre environnement virtuel
pip install pywin32
```

### 2. **Vérifier l'installation**
```bash
python -c "import win32clipboard; print('✅ pywin32 installé avec succès')"
```

## 🔧 Comment ça marche

### **Méthode Qt (ancienne) :**
- Utilise `QApplication.clipboard()`
- **Problème** : Windows limite l'accès Qt au clipboard système
- **Résultat** : `hasImage(): False` même avec une image présente

### **Méthode Windows Native (nouvelle) :**
- Utilise directement l'API Windows : `win32clipboard`
- **Avantage** : Accès direct au clipboard système (comme Claude)
- **Formats supportés** :
  - `CF_BITMAP` - Bitmap Windows natif
  - `CF_DIB` - Device Independent Bitmap
  - `CF_DIBV5` - DIB version 5
  - `PNG` - Format PNG

## 📋 Ordre des méthodes

L'application essaie maintenant **8 méthodes** dans cet ordre :

1. **Qt hasImage()** - Méthode standard Qt
2. **Formats MIME spécifiques** - PNG, JPEG, BMP, etc.
3. **Tous les formats disponibles** - Recherche automatique
4. **Formats Linux spécifiques** - Sur Linux uniquement
5. **Accès direct imageData()** - Méthode Qt alternative
6. **Méthodes alternatives Linux** - Sur Linux uniquement
7. **Outils système Linux** - Désactivé (xclip, xsel)
8. **🆕 API Windows Native** - **NOUVELLE MÉTHODE** (comme Claude !)

## 🧪 Test

### **Sur Windows :**
1. Faites un **Print Screen** (ou `Alt + PrtScn`)
2. Lancez l'application
3. Vérifiez les logs : `Method 8: Trying Windows native clipboard API`
4. L'image devrait être détectée !

### **Sur Linux :**
- Les méthodes 1-6 continuent de fonctionner
- La méthode 8 est automatiquement désactivée

## 🔍 Debug

### **Logs à surveiller :**
```
Method 8: Trying Windows native clipboard API
Windows native: CF_BITMAP format found
Windows native: Image converted from CF_BITMAP: 1920x1080
```

### **Si ça ne marche pas :**
1. Vérifiez que `pywin32` est installé
2. Vérifiez que vous êtes sur Windows
3. Vérifiez les logs d'erreur

## 🎉 Résultat attendu

**Avant** : `No image found in clipboard using any method`
**Après** : `Image found via Windows native API: 1920x1080`

**Maintenant votre app peut faire comme Claude !** 🚀