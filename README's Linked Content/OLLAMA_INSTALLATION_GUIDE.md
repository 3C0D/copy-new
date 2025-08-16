# Guide d'installation automatique d'Ollama

## Nouvelle fonctionnalité : Installation automatique d'Ollama

Cette fonctionnalité permet d'installer Ollama automatiquement depuis l'interface de WritingTools, sans avoir besoin de suivre des instructions manuelles complexes.

## Comment ça fonctionne

### Détection automatique

- L'application détecte automatiquement si Ollama est installé sur votre système
- Si Ollama n'est pas détecté, un bouton "Installer Ollama automatiquement" apparaît
- Si Ollama est installé, le bouton affiche "Instructions d'installation" (pour les modèles)

### Processus d'installation

1. **Cliquez sur "Installer Ollama automatiquement"**
2. **Fenêtre de progression** : Une fenêtre avec des points animés s'affiche
3. **Téléchargement** : L'application télécharge automatiquement l'installateur officiel d'Ollama (~700 MB)
4. **Installation** : L'installateur se lance automatiquement
5. **Suivi des instructions** : Suivez les instructions à l'écran de l'installateur Ollama
6. **Finalisation** : Une fois l'installation terminée, l'interface se met à jour automatiquement

### Interface utilisateur améliorée

- **Fenêtre de progression** : Affichage d'une fenêtre avec animation de points pendant l'installation
- **Bouton d'actualisation** : Un bouton "🔄 Actualiser" permet de mettre à jour l'interface manuellement
- **Détection automatique** : L'interface se met à jour automatiquement après une installation réussie
- **Support multi-plateforme** : Fonctionne sur Windows et Linux

### Messages d'état

- **"Téléchargement d'Ollama en cours..."** : Le fichier d'installation est en cours de téléchargement
- **"Installation d'Ollama en cours..."** : L'installateur est en cours d'exécution
- **"Finalisation de l'installation..."** : Dernières étapes de l'installation
- **"Ollama a été installé avec succès !"** : Installation réussie
- **"L'installation d'Ollama a été annulée ou a échoué"** : Problème lors de l'installation

## Avantages

✅ **Simplicité** : Plus besoin de naviguer sur le site d'Ollama et de télécharger manuellement
✅ **Sécurité** : Téléchargement direct depuis le site officiel d'Ollama
✅ **Intégration** : L'interface se met à jour automatiquement après l'installation
✅ **Fiabilité** : Gestion des erreurs et messages informatifs
✅ **Multi-plateforme** : Support automatique pour Windows et Linux
✅ **Interface intuitive** : Fenêtre de progression avec animation et bouton d'actualisation

## Prérequis

### Windows

- Connexion Internet pour télécharger l'installateur
- Droits d'administrateur pour installer Ollama
- Environ 1 GB d'espace disque libre (installateur + Ollama)

### Linux

- Connexion Internet pour télécharger le script d'installation
- Droits sudo pour installer Ollama
- `curl` installé sur le système
- Environ 1 GB d'espace disque libre

## Après l'installation

Une fois Ollama installé :

1. **Interface mise à jour** : Le bouton change pour "Instructions d'installation"
2. **Détection automatique** : Les modèles installés apparaissent automatiquement dans la liste déroulante
3. **Actualisation dynamique** : Ouvrir la liste déroulante rafraîchit automatiquement les modèles disponibles

### Utilisation d'Ollama avec WritingTools

#### Installation et gestion des modèles

**Installation de modèles** :

- Utilisez la ligne de commande : `ollama pull llama2` (par exemple)
- Modèles populaires : `llama2`, `mistral`, `codellama`, `phi`, `gemma`
- Les nouveaux modèles apparaissent automatiquement dans WritingTools

**Chat intégré** :

- Une fois un modèle sélectionné, vous pouvez utiliser WritingTools normalement
- Le chat fonctionne comme avec les autres providers (Gemini, OpenAI, etc.)
- Toutes les fonctionnalités sont disponibles : résumé, réécriture, traduction, etc.

#### Comportement intelligent des modèles

**Chargement automatique** :

- Si le modèle est déjà en mémoire → Réponse immédiate
- Si le modèle n'est pas chargé → Chargement automatique (quelques secondes)
- Si le modèle n'est pas installé → Installation automatique puis utilisation

**Gestion de la mémoire** :

- Les modèles restent en mémoire selon le paramètre "keep_alive" (défaut : 5 minutes)
- Ollama gère automatiquement la mémoire et décharge les modèles inutilisés
- Plusieurs modèles peuvent coexister selon la RAM disponible

#### Avantages d'Ollama

✅ **Confidentialité** : Tout fonctionne localement, aucune donnée envoyée sur Internet
✅ **Rapidité** : Pas de latence réseau, réponses instantanées
✅ **Économique** : Pas de coûts d'API, utilisation illimitée
✅ **Hors ligne** : Fonctionne sans connexion Internet
✅ **Personnalisable** : Choix parmi de nombreux modèles open-source

## Dépannage

### "La bibliothèque 'requests' n'est pas disponible"

- Cette erreur indique un problème avec l'environnement Python
- Solution : Installation manuelle depuis <https://ollama.com>

### "Erreur lors de l'installation d'Ollama"

- Vérifiez votre connexion Internet
- Assurez-vous d'avoir les droits d'administrateur
- Essayez l'installation manuelle si le problème persiste

### L'interface ne se met pas à jour

- Cliquez sur le bouton "🔄 Actualiser" à côté du bouton principal
- Fermez et rouvrez les paramètres
- Redémarrez l'application si nécessaire

### Problème de détection dans l'environnement virtuel

- **"Ollama not available"** alors qu'Ollama est installé : Ce problème survient quand Ollama est installé globalement mais que WritingTools fonctionne dans un environnement virtuel Python
- **Solution automatique** : WritingTools cherche maintenant Ollama dans les emplacements standards :
  - Windows : `%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe`
  - Linux : `/usr/local/bin/ollama`, `/usr/bin/ollama`
- **Vérification manuelle** : Ouvrez un terminal et tapez `ollama --version` pour confirmer l'installation

### Problèmes spécifiques à Linux

- **"curl: command not found"** : Installez curl avec `sudo apt install curl` (Ubuntu/Debian) ou `sudo yum install curl` (CentOS/RHEL)
- **Permissions insuffisantes** : Assurez-vous d'avoir les droits sudo

## Code technique

La fonctionnalité utilise :

- `is_ollama_installed()` : Détection d'Ollama via `ollama --version`
- `install_ollama_auto()` : Détection automatique de la plateforme
- `install_ollama_windows()` : Téléchargement et installation automatique pour Windows
- `install_ollama_linux()` : Installation via script officiel pour Linux
- `OllamaInstallProgressWindow` : Fenêtre de progression avec animation
- Interface dynamique qui s'adapte selon l'état d'installation
- Bouton d'actualisation pour mise à jour manuelle

## Sécurité

### Windows

- Téléchargement uniquement depuis <https://ollama.com/download/OllamaSetup.exe>
- Vérification de l'intégrité du téléchargement
- Nettoyage automatique des fichiers temporaires

### Linux

- Utilisation du script officiel d'installation : <https://ollama.com/install.sh>
- Exécution sécurisée via curl avec vérification SSL

## Améliorations apportées

### Correction du bug de démarrage

- **Problème 1** : L'onboarding ne se déclenchait pas quand `api_model` était vide pour Ollama
- **Solution 1** : Modification de `has_providers_configured()` pour vérifier aussi la présence d'un modèle valide

- **Problème 2** : L'onboarding ne se déclenchait pas si Ollama était configuré mais désinstallé
- **Solution 2** : Vérification que Ollama est réellement installé et fonctionnel, pas seulement configuré

### Correction du bug de détection PATH

- **Problème** : Ollama installé globalement n'était pas détecté depuis l'environnement virtuel Python
- **Solution** : Nouvelle fonction `find_ollama_executable()` qui cherche dans les emplacements standards
- **Emplacements vérifiés** :
  - Windows : `%USERPROFILE%\AppData\Local\Programs\Ollama\ollama.exe`
  - Linux : `/usr/local/bin/ollama`, `/usr/bin/ollama`, `~/.local/bin/ollama`
- **Fallback** : Utilise `shutil.which()` pour chercher dans le PATH système

### Interface utilisateur améliorée

- **Fenêtre de progression** : Animation avec points pour indiquer l'activité
- **Bouton d'actualisation** : Permet de mettre à jour l'interface manuellement
- **Support multi-boutons** : Architecture étendue pour supporter plusieurs boutons par provider

### Compatibilité multi-plateforme

- **Détection automatique** : La fonction `install_ollama_auto()` détecte Windows/Linux automatiquement
- **Installation adaptée** : Utilise l'installateur Windows ou le script Linux selon la plateforme
- **Interface unifiée** : Même expérience utilisateur sur toutes les plateformes
- **Fonctionnalités identiques** : Toutes les fonctionnalités (détection, installation, rafraîchissement) fonctionnent sur Linux et Windows

#### Spécificités Linux

**Installation** :

- Utilise le script officiel d'Ollama : `curl -fsSL https://ollama.com/install.sh | sh`
- Installation automatique des dépendances
- Configuration automatique du service systemd

**Utilisation** :

- Démarrage automatique d'Ollama en arrière-plan
- Même interface et fonctionnalités que sur Windows
- Détection automatique des modèles installés
- Support complet du rafraîchissement dynamique
