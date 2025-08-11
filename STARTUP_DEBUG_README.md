# Writing Tools - Debug de Démarrage

Ce dossier contient des scripts pour diagnostiquer les problèmes de systray au démarrage de Windows.

## Problème

L'application Writing Tools ne s'affiche pas dans le systray quand elle démarre automatiquement au boot de Windows, même si elle est bien chargée en mémoire.

## Scripts de Debug

### 1. `startup_debug.py`
Script Python principal qui :
- Configure un logging très détaillé
- Teste l'environnement systray
- Lance l'application avec monitoring complet
- Capture tous les événements de démarrage

### 2. `startup_debug.bat`
Script batch Windows pour :
- Lancer le script Python de debug
- Capturer les erreurs de base
- Créer des logs même si Python échoue

### 3. `startup_debug.ps1`
Script PowerShell avancé qui :
- Capture des informations système détaillées
- Vérifie l'état de l'environnement Windows
- Peut être lancé avec délai pour le démarrage

### 4. `install_startup_debug.py`
Script d'installation qui :
- Configure le debug pour s'exécuter au démarrage
- Ajoute/supprime les entrées de registre
- Vérifie le statut d'installation

## Utilisation

### Installation du Debug de Démarrage

1. **Installer le debug au démarrage :**
   ```cmd
   python install_startup_debug.py install
   ```

2. **Redémarrer Windows**
   - Le script de debug se lancera automatiquement
   - Les logs seront créés dans le dossier `startup_logs/`

3. **Vérifier les logs :**
   - Ouvrir le dossier `startup_logs/`
   - Examiner les fichiers de log créés

### Désinstallation

```cmd
python install_startup_debug.py uninstall
```

### Vérifier le Statut

```cmd
python install_startup_debug.py status
```

### Test Manuel

Pour tester sans redémarrer :

```cmd
# Test simple
python startup_debug.py

# Test avec PowerShell
powershell -ExecutionPolicy Bypass -File startup_debug.ps1

# Test avec délai (simule le démarrage)
powershell -ExecutionPolicy Bypass -File startup_debug.ps1 -DelaySeconds 5
```

## Logs Générés

### `startup_logs/startup_debug_YYYYMMDD_HHMMSS.log`
Log principal Python avec :
- Informations système détaillées
- État de l'environnement PySide6/Qt
- Tests de création de systray
- Monitoring de l'application

### `startup_logs/powershell_debug_YYYYMMDD_HHMMSS.log`
Log PowerShell avec :
- Informations de session Windows
- État des processus
- Environnement système

### `startup_logs/batch_debug.log`
Log simple du script batch

## Analyse des Résultats

### Indicateurs à Vérifier

1. **System Tray Available** : Doit être `True`
2. **Test Tray Icon Visible** : Doit être `True`
3. **App Tray Icon Visible** : Doit devenir `True` après quelques secondes
4. **Timing** : Noter les délais entre les étapes

### Problèmes Courants

- **System tray not available** : Windows pas encore prêt
- **Icon created but not visible** : Problème de timing
- **Python/PySide6 errors** : Problème d'environnement

## Résolution

Basé sur les logs, les solutions possibles :

1. **Augmenter le délai de démarrage** dans `_create_tray_icon_with_startup_delay()`
2. **Améliorer les retry mechanisms** dans `_is_system_tray_available_with_retry()`
3. **Ajouter des vérifications d'environnement** avant création du systray

## Nettoyage

Après diagnostic, supprimer le debug de démarrage :

```cmd
python install_startup_debug.py uninstall
```

Et optionnellement supprimer les logs :

```cmd
rmdir /s startup_logs
```
