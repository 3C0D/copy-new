#!/usr/bin/env python3
"""
Script de debug pour tester l'exécutable Writing Tools au démarrage.
Ce script lance l'exécutable et monitore son comportement.
"""

import logging
import os
import sys
import time
import subprocess
from datetime import datetime


def setup_logging():
    """Configure le logging pour le debug"""
    log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), "startup_logs")
    os.makedirs(log_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"exe_debug_{timestamp}.log")

    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s.%(msecs)03d - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        handlers=[logging.FileHandler(log_file, encoding='utf-8'), logging.StreamHandler(sys.stdout)],
    )

    logger = logging.getLogger("EXE_DEBUG")
    logger.info("=" * 80)
    logger.info("WRITING TOOLS - EXECUTABLE DEBUG SESSION")
    logger.info("=" * 80)
    logger.info(f"Log file: {log_file}")

    return logger, log_file


def find_writing_tools_exe():
    """Trouve l'exécutable Writing Tools"""
    logger = logging.getLogger("EXE_FINDER")

    script_dir = os.path.dirname(os.path.abspath(__file__))

    # Chemins possibles pour l'exécutable
    possible_exe_paths = [
        os.path.join(script_dir, "Windows_and_Linux", "dist", "dev", "Writing Tools.exe"),
        os.path.join(script_dir, "Windows_and_Linux", "dist", "final", "Writing Tools.exe"),
        os.path.join(script_dir, "dist", "dev", "Writing Tools.exe"),
        os.path.join(script_dir, "dist", "final", "Writing Tools.exe"),
        os.path.join(script_dir, "Writing Tools.exe"),
    ]

    for exe_path in possible_exe_paths:
        if os.path.exists(exe_path):
            logger.info(f"Found Writing Tools executable: {exe_path}")
            return exe_path

    logger.error("Writing Tools executable not found!")
    return None


def monitor_systray_icons():
    """Monitore les icônes du systray"""
    logger = logging.getLogger("SYSTRAY_MONITOR")

    try:
        # Utiliser PowerShell pour lister les icônes du systray
        ps_command = """
        Get-Process | Where-Object { $_.MainWindowTitle -ne "" -or $_.ProcessName -like "*Writing*" } | 
        Select-Object ProcessName, Id, MainWindowTitle, StartTime | 
        Format-Table -AutoSize
        """

        result = subprocess.run(["powershell", "-Command", ps_command], capture_output=True, text=True, timeout=10)

        if result.returncode == 0:
            logger.info("Current processes with windows:")
            logger.info(result.stdout)
        else:
            logger.warning(f"PowerShell command failed: {result.stderr}")

    except Exception as e:
        logger.error(f"Error monitoring systray: {e}")


def check_writing_tools_processes():
    """Vérifie les processus Writing Tools en cours"""
    logger = logging.getLogger("PROCESS_MONITOR")

    try:
        # Utiliser tasklist pour lister les processus
        result = subprocess.run(
            ["tasklist", "/FI", "IMAGENAME eq Writing Tools.exe", "/FO", "CSV"],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode == 0 and "Writing Tools.exe" in result.stdout:
            logger.info("Found Writing Tools processes:")
            logger.info(result.stdout)
            return True
        else:
            logger.info("No Writing Tools processes found")
            return False

    except Exception as e:
        logger.error(f"Error checking processes: {e}")
        return False


def main():
    """Fonction principale"""
    logger, log_file = setup_logging()

    try:
        logger.info("Starting Writing Tools executable debug...")

        # Trouver l'exécutable
        exe_path = find_writing_tools_exe()
        if not exe_path:
            logger.error("Cannot proceed without executable")
            return 1

        # Vérifier les processus existants
        logger.info("Checking for existing Writing Tools processes...")
        has_existing = check_writing_tools_processes()

        # Lancer l'exécutable
        logger.info(f"Launching executable: {exe_path}")

        # Changer vers le répertoire de l'exécutable
        exe_dir = os.path.dirname(exe_path)
        original_cwd = os.getcwd()
        os.chdir(exe_dir)
        logger.info(f"Changed working directory to: {exe_dir}")

        # Lancer le processus
        process = subprocess.Popen([exe_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

        logger.info(f"Process launched with PID: {process.pid}")

        # Monitorer pendant 30 secondes
        logger.info("Monitoring for 30 seconds...")

        for i in range(30):
            time.sleep(1)

            # Vérifier si le processus est toujours en vie
            if process.poll() is not None:
                logger.warning(f"Process terminated at second {i+1}")
                break

            # Log périodique
            if (i + 1) % 5 == 0:
                logger.info(f"Second {i+1}: Process still running")

                # Vérifier les processus Writing Tools
                has_processes = check_writing_tools_processes()

                # Monitorer le systray
                monitor_systray_icons()

        # Récupérer la sortie du processus
        try:
            stdout, stderr = process.communicate(timeout=5)

            if stdout:
                logger.info("Process stdout:")
                logger.info(stdout)

            if stderr:
                logger.error("Process stderr:")
                logger.error(stderr)

        except subprocess.TimeoutExpired:
            logger.warning("Process still running, terminating...")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()

        # Restaurer le répertoire de travail
        os.chdir(original_cwd)

        logger.info("Debug session completed")
        logger.info(f"Full log saved to: {log_file}")

        return 0

    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback

        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    sys.exit(main())
