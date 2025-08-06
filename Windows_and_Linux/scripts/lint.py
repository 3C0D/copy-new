#!/usr/bin/env python3
"""
Script de nettoyage de code simplifié
Utilise seulement les outils essentiels : Ruff + Black + Mypy
"""

import subprocess
import sys
from pathlib import Path
import os

if os.name == 'nt':  # Windows
    from utils import get_python_executable # type: ignore
else:  # Linux/Unix
    from .utils import get_python_executable


def run_command(cmd, description, fix_mode=False):
    """Run a command and return success status"""
    print(f"\n{'='*50}")
    print(f"Running {description}...")
    print(f"{'='*50}")

    try:
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            cwd=Path(__file__).parent.parent,
        )

        if result.stdout:
            print(result.stdout)

        if result.stderr and result.returncode != 0:
            print("STDERR:")
            print(result.stderr)

        if result.returncode == 0:
            print(f"✅ {description} - OK")
            return True
        else:
            print(f"❌ {description} - Erreurs trouvées")
            return False

    except Exception as e:
        print(f"❌ {description} - Échec: {e}")
        return False


def main():
    """Nettoyage du code avec les outils essentiels"""
    print("🔍 Nettoyage du code Python...")

    # Get Python executable
    venv_path = "myvenv"
    python_cmd = str(get_python_executable(venv_path))

    if not Path(python_cmd).exists():
        print(f"❌ Python non trouvé: {python_cmd}")
        return 1

    # Mode choix
    fix_mode = "--fix" in sys.argv
    action = "correction" if fix_mode else "vérification"
    print(f"Mode: {action}")

    # Commandes essentielles
    commands = []
    
    # 1. Ruff : linting + import sorting + formatting léger
    ruff_cmd = [python_cmd, "-m", "ruff", "check", ".", "--exclude", "myvenv"]
    if fix_mode:
        ruff_cmd.append("--fix")
    commands.append((ruff_cmd, "Ruff (linting + imports)"))

    # 2. Black : formatage
    if fix_mode:
        black_cmd = [python_cmd, "-m", "black", ".", "--exclude", "myvenv"]
        commands.append((black_cmd, "Black (formatage)"))
    else:
        black_cmd = [python_cmd, "-m", "black", ".", "--check", "--exclude", "myvenv"]
        commands.append((black_cmd, "Black (vérification formatage)"))

    # 3. MyPy : types (seulement si demandé)
    if "--types" in sys.argv:
        mypy_cmd = [python_cmd, "-m", "mypy", ".", "--config-file", "pyproject.toml"]
        commands.append((mypy_cmd, "MyPy (types)"))

    # Exécution
    results = []
    for cmd, description in commands:
        success = run_command(cmd, description, fix_mode)
        results.append((description, success))

    # Résumé
    print(f"\n{'='*50}")
    print("RÉSUMÉ")
    print(f"{'='*50}")

    failed = [desc for desc, success in results if not success]
    
    if not failed:
        print("🎉 Tout est OK !")
        return 0
    else:
        print(f"⚠️  {len(failed)} problème(s) détecté(s)")
        for desc in failed:
            print(f"  - {desc}")
        return 1


if __name__ == "__main__":
    if len(sys.argv) == 1:
        print("Usage:")
        print("  python lint.py           # Vérification seulement")
        print("  python lint.py --fix     # Correction automatique")
        print("  python lint.py --fix --types  # + vérification types")
    
    sys.exit(main())