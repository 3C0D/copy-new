#!/usr/bin/env python3
"""
Script de debug pour le démarrage de Writing Tools.
Ce script capture tous les logs détaillés du processus de démarrage
pour diagnostiquer les problèmes de systray au boot.
"""

import logging
import os
import sys
import time
import traceback
from datetime import datetime


# Configuration du logging très détaillé
def setup_detailed_logging():
    """Configure un logging très détaillé pour le debug de démarrage"""

    # Créer le dossier de logs s'il n'existe pas
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_logs")
    os.makedirs(log_dir, exist_ok=True)

    # Nom du fichier de log avec timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"startup_debug_{timestamp}.log")

    # Configuration du logging
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(name)s - %(funcName)s:%(lineno)d - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)],
    )

    # Log des informations système au démarrage
    logger = logging.getLogger("STARTUP_DEBUG")
    logger.info("=" * 80)
    logger.info("WRITING TOOLS - STARTUP DEBUG SESSION")
    logger.info("=" * 80)
    logger.info(f"Log file: {log_file}")
    logger.info(f"Python version: {sys.version}")
    logger.info(f"Python executable: {sys.executable}")
    logger.info(f"Script path: {sys.argv[0]}")
    logger.info(f"Working directory: {os.getcwd()}")
    logger.info(f"Frozen: {getattr(sys, 'frozen', False)}")

    if getattr(sys, 'frozen', False):
        logger.info(f"Executable path: {sys.executable}")
        logger.info(f"Base directory: {os.path.dirname(sys.executable)}")

    # Informations sur l'environnement Windows
    try:
        import platform

        logger.info(f"Platform: {platform.platform()}")
        logger.info(f"Machine: {platform.machine()}")
        logger.info(f"Processor: {platform.processor()}")
    except Exception as e:
        logger.error(f"Error getting platform info: {e}")

    # Variables d'environnement importantes
    env_vars = ['PATH', 'USERPROFILE', 'APPDATA', 'LOCALAPPDATA', 'TEMP']
    for var in env_vars:
        value = os.environ.get(var, 'NOT_SET')
        logger.info(f"ENV {var}: {value}")

    return logger, log_file


def log_systray_environment():
    """Log l'état de l'environnement systray"""
    logger = logging.getLogger("SYSTRAY_ENV")

    try:
        # Importer PySide6 et vérifier la disponibilité
        logger.info("Importing PySide6...")
        from PySide6 import QtWidgets, QtCore, QtGui

        logger.info("PySide6 imported successfully")

        # Créer une application temporaire pour tester le systray
        logger.info("Creating temporary QApplication...")
        app = QtWidgets.QApplication.instance()
        if app is None:
            app = QtWidgets.QApplication([])
            logger.info("New QApplication created")
        else:
            logger.info("Using existing QApplication instance")

        # Tester la disponibilité du systray
        logger.info("Testing system tray availability...")
        systray_available = QtWidgets.QSystemTrayIcon.isSystemTrayAvailable()
        logger.info(f"System tray available: {systray_available}")

        # Informations sur les écrans
        logger.info("Screen information:")
        screens = app.screens()
        logger.info(f"Number of screens: {len(screens)}")
        for i, screen in enumerate(screens):
            logger.info(f"Screen {i}: {screen.name()} - {screen.geometry()}")

        # Test de création d'icône systray
        if systray_available:
            logger.info("Attempting to create test system tray icon...")
            try:
                test_icon = QtWidgets.QSystemTrayIcon()
                test_icon.setToolTip("Writing Tools Debug Test")
                test_icon.show()

                # Vérifier si elle est visible
                time.sleep(0.5)  # Petit délai
                is_visible = test_icon.isVisible()
                logger.info(f"Test tray icon visible: {is_visible}")

                test_icon.hide()
                logger.info("Test tray icon cleaned up")

            except Exception as e:
                logger.error(f"Error creating test tray icon: {e}")
                logger.error(traceback.format_exc())

        return True

    except Exception as e:
        logger.error(f"Error in systray environment check: {e}")
        logger.error(traceback.format_exc())
        return False


def find_project_python():
    """Trouve le bon exécutable Python pour le projet"""
    logger = logging.getLogger("PYTHON_FINDER")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemins possibles pour l'environnement virtuel
    possible_venv_paths = [
        os.path.join(script_dir, "Windows_and_Linux", "myvenv", "Scripts", "python.exe"),
        os.path.join(script_dir, "Windows_and_Linux", "venv", "Scripts", "python.exe"),
        os.path.join(script_dir, "Windows_and_Linux", ".venv", "Scripts", "python.exe"),
        os.path.join(script_dir, "myvenv", "Scripts", "python.exe"),
        os.path.join(script_dir, "venv", "Scripts", "python.exe"),
        os.path.join(script_dir, ".venv", "Scripts", "python.exe"),
    ]

    # Tester chaque chemin
    for venv_path in possible_venv_paths:
        if os.path.exists(venv_path):
            logger.info(f"Found virtual environment Python: {venv_path}")
            return venv_path

    # Fallback vers Python système
    logger.warning("No virtual environment found, using system Python")
    return sys.executable


def main():
    """Fonction principale du script de debug"""

    # Setup du logging détaillé
    logger, log_file = setup_detailed_logging()

    try:
        logger.info("Starting Writing Tools startup debug...")

        # Trouver le bon Python
        project_python = find_project_python()
        logger.info(f"Using Python: {project_python}")

        # Si on n'utilise pas le bon Python, relancer avec le bon
        if project_python != sys.executable and os.path.exists(project_python):
            logger.info("Relaunching with project Python environment...")
            import subprocess

            script_path = os.path.abspath(__file__)
            result = subprocess.run([project_python, script_path], capture_output=True, text=True)

            logger.info(f"Subprocess exit code: {result.returncode}")
            if result.stdout:
                logger.info(f"Subprocess stdout:\n{result.stdout}")
            if result.stderr:
                logger.error(f"Subprocess stderr:\n{result.stderr}")

            return result.returncode

        # Log de l'environnement systray
        logger.info("Checking systray environment...")
        systray_ok = log_systray_environment()

        if not systray_ok:
            logger.error("Systray environment check failed!")
            return 1

        # Maintenant lancer l'application principale
        logger.info("Launching main Writing Tools application...")

        # Ajouter le répertoire Windows_and_Linux au path
        script_dir = os.path.dirname(os.path.abspath(__file__))
        windows_linux_dir = os.path.join(script_dir, "Windows_and_Linux")
        if os.path.exists(windows_linux_dir):
            sys.path.insert(0, windows_linux_dir)
            logger.info(f"Added to path: {windows_linux_dir}")

        # Nettoyer l'application temporaire avant de créer WritingToolApp
        logger.info("Cleaning up temporary QApplication...")
        from PySide6 import QtWidgets

        temp_app = QtWidgets.QApplication.instance()
        if temp_app:
            temp_app.quit()
            temp_app = None

        # Importer et lancer l'application
        from WritingToolApp import WritingToolApp

        logger.info("Creating WritingToolApp instance...")
        app = WritingToolApp(sys.argv)
        app.setQuitOnLastWindowClosed(False)

        # Log de l'état de l'application après création
        logger.info(f"App created. Tray icon exists: {app.tray_icon is not None}")
        if app.tray_icon:
            logger.info(f"Tray icon visible: {app.tray_icon.isVisible()}")

        # Attendre un peu pour voir si le systray apparaît
        logger.info("Waiting 10 seconds to monitor tray icon status...")
        for i in range(10):
            time.sleep(1)
            if app.tray_icon:
                visible = app.tray_icon.isVisible()
                logger.info(f"Second {i+1}: Tray icon visible = {visible}")

                # Log des détails de l'icône
                if hasattr(app.tray_icon, 'icon') and not app.tray_icon.icon().isNull():
                    logger.info(f"Second {i+1}: Icon is set and valid")
                else:
                    logger.warning(f"Second {i+1}: Icon is null or not set")
            else:
                logger.info(f"Second {i+1}: No tray icon object")

        logger.info("Debug session completed successfully")
        logger.info(f"Full log saved to: {log_file}")

        # Garder l'application ouverte pour observation
        logger.info("Application will remain running for observation...")
        return app.exec()

    except Exception as e:
        logger.error(f"Critical error in startup debug: {e}")
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
