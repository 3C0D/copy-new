# Processus de lancement et construction de l'application

## Mode développement (dev_script.py)

Le mode développement exécute directement le script Python principal (main.py) via UV sans étape de compilation, permettant un développement rapide avec rechargement automatique. Les logs apparaissent dans la console pour faciliter le débogage (configuration déterminée dans main.py selon le mode console détecté).

### Étapes clés

1. Nettoyage de la console
2. Configuration du projet racine
3. Terminaison des processus existants (exe et script)
4. Vérification et configuration des données de développement
5. Lancement direct du script Python avec UV

### Commande principale

```bash
uv run main.py
```

### Citation du code

```python
cmd = ["uv", "run", str(script_path)]
if extra_args:
    cmd.extend(extra_args)

result = subprocess.run(cmd, check=True)
```

## Mode build développement (build_dev.py)

Ce mode utilise PyInstaller pour créer un exécutable de développement dans un dossier unique, avec options de mode console ou fenêtré. Les logs sont redirigés vers un fichier (build_dev_debug.log) en mode fenêtré, ou visibles en console avec le paramètre --console.

### Étapes clés

1. Nettoyage automatique du cache PyInstaller (si nécessaire après opérations Git)
2. Copie des fichiers requis vers `dist/dev/`
3. Terminaison des processus existants
4. Configuration des données de développement
5. Construction avec PyInstaller en mode dossier
6. Déplacement des fichiers construits vers `dist/dev/`
7. Lancement automatique de l'exécutable

### Paramètres PyInstaller essentiels

- `--onedir` : Mode dossier (plus rapide pour développement)
- `--console` ou `--windowed` : Console visible pour debug ou cachée pour production-like
- `--icon=src/config/icons/app_icon.ico`
- `--name=Writing Tools`
- `--distpath=dist/dev`
- `--exclude-module` pour exclusions définies dans `PYINSTALLER_EXCLUSIONS`

### Citation du code

```python
pyinstaller_command = [
    "uv",
    "run",
    "-m",
    "PyInstaller",
    "--onedir",
    "--console" if console_mode else "--windowed",
    f"--icon={icon_path}",
    "--name=Writing Tools",
    "--distpath=dist/dev",
    "--noconfirm" if not (clean_build or auto_clean) else "--clean",
]

# Add exclusions
for module in PYINSTALLER_EXCLUSIONS:
    pyinstaller_command.extend(["--exclude-module", module])

# Add main script
pyinstaller_command.append(f"{DEFAULT_SCRIPT_NAME}")

subprocess.run(pyinstaller_command, check=True)
```

## Mode build final (build_final.py)

Ce mode crée un exécutable de production unique optimisé pour la distribution. La console est toujours cachée (--windowed), les logs ne sont pas visibles ni sauvegardés pour une expérience utilisateur propre.

### Étapes clés

1. Nettoyage complet des répertoires de build (préserve `dist/dev/`)
2. Copie des fichiers requis vers `dist/production/`
3. Terminaison des processus existants
4. Configuration des données de production
5. Construction avec PyInstaller en mode fichier unique
6. Sortie finale dans `dist/production/`

### Paramètres PyInstaller essentiels

- `--onefile` : Mode fichier unique (optimisé pour distribution)
- `--windowed` : Console toujours cachée (mode production)
- `--icon=src/config/icons/app_icon.ico`
- `--name=Writing Tools`
- `--distpath=dist/production`
- `--clean` : Build propre pour release
- `--exclude-module` pour exclusions définies dans `PYINSTALLER_EXCLUSIONS`

### Citation du code

```python
pyinstaller_command = [
    "uv", "run", "-m", "PyInstaller",
    "--onefile",
    "--windowed",
    f"--icon={icon_path}",
    "--name=Writing Tools",
    "--distpath=dist/production",
    "--clean",
    "--noconfirm",
]

# Add exclusions
for module in PYINSTALLER_EXCLUSIONS:
    pyinstaller_command.extend(["--exclude-module", module])

# Add main script
pyinstaller_command.append(f"{DEFAULT_SCRIPT_NAME}")

subprocess.run(pyinstaller_command, check=True)
```

## Différences entre les modes

| Aspect | Développement | Build développement | Build final |
|--------|---------------|---------------------|-------------|
| **Type** | Exécution directe | Build dossier | Build fichier unique |
| **Console** | Visible | Configurable (--console/--windowed) | Toujours cachée (--windowed) |
| **Vitesse** | Instantané | Moyen (build + lancement) | Lent (optimisation complète) |
| **Usage** | Développement actif | Test/debug en conditions proches production | Distribution/release |
| **Sortie** | - | `dist/dev/` (dossier) | `dist/production/` (fichier unique) |
| **Nettoyage** | Aucun | Automatique si Git détecté | Complet systématique |
| **Paramètre clé** | `uv run main.py` | `--onedir` | `--onefile` |

## Chargement du main

Le processus de lancement de l'application commence par l'exécution de main.py :

1. **Exécution de main.py** : Le script principal est lancé, créant l'instance de l'application Qt.

2. **Initialisation de l'application** : Configuration des composants principaux (gestionnaires, paramètres, interface).

3. **Configuration du systray** : L'icône système est créée et affichée dans la barre des tâches.

4. **Boucle d'événements** : L'application entre dans sa boucle principale, rendant toutes les fonctionnalités disponibles.

## Note sur la compilation PyInstaller

Lors de la compilation avec PyInstaller, le script `main.py` est intégré tel quel dans l'exécutable généré. Quand l'utilisateur lance l'exécutable, il exécute exactement le même code que `main.py` en mode développement, mais de manière autonome sans nécessiter Python installé sur la machine. Aucune modification du code n'est nécessaire - seule la méthode d'exécution change (interprétation directe vs exécutable empaqueté).
