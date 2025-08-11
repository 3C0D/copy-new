#!/usr/bin/env python3
"""
Script d'installation pour configurer le debug de démarrage de Writing Tools.
Ce script configure les entrées de registre pour lancer le debug au démarrage de Windows.
"""

import os
import sys
import winreg
import logging
from pathlib import Path

def setup_logging():
    """Configure le logging pour l'installation"""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.StreamHandler(),
            logging.FileHandler("install_debug.log")
        ]
    )

def get_script_directory():
    """Obtient le répertoire du script"""
    if getattr(sys, 'frozen', False):
        return os.path.dirname(sys.executable)
    else:
        return os.path.dirname(os.path.abspath(__file__))

def install_startup_debug():
    """Installe le script de debug dans le démarrage de Windows"""
    logger = logging.getLogger(__name__)
    
    try:
        script_dir = get_script_directory()
        logger.info(f"Script directory: {script_dir}")
        
        # Chemins des scripts
        python_script = os.path.join(script_dir, "startup_debug.py")
        batch_script = os.path.join(script_dir, "startup_debug.bat")
        ps_script = os.path.join(script_dir, "startup_debug.ps1")
        
        # Vérifier que les scripts existent
        if not os.path.exists(python_script):
            logger.error(f"Python script not found: {python_script}")
            return False
        
        if not os.path.exists(batch_script):
            logger.error(f"Batch script not found: {batch_script}")
            return False
        
        # Ouvrir la clé de registre pour le démarrage
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            
            # Ajouter l'entrée pour le debug de démarrage
            debug_entry_name = "WritingToolsStartupDebug"
            debug_command = f'"{batch_script}"'
            
            winreg.SetValueEx(key, debug_entry_name, 0, winreg.REG_SZ, debug_command)
            winreg.CloseKey(key)
            
            logger.info(f"Successfully installed startup debug entry: {debug_entry_name}")
            logger.info(f"Command: {debug_command}")
            
            return True
            
        except Exception as e:
            logger.error(f"Error accessing registry: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error installing startup debug: {e}")
        return False

def uninstall_startup_debug():
    """Désinstalle le script de debug du démarrage de Windows"""
    logger = logging.getLogger(__name__)
    
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        debug_entry_name = "WritingToolsStartupDebug"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
            
            try:
                winreg.DeleteValue(key, debug_entry_name)
                logger.info(f"Successfully removed startup debug entry: {debug_entry_name}")
            except OSError:
                logger.info("Startup debug entry was not found (already removed)")
            
            winreg.CloseKey(key)
            return True
            
        except Exception as e:
            logger.error(f"Error accessing registry: {e}")
            return False
            
    except Exception as e:
        logger.error(f"Error uninstalling startup debug: {e}")
        return False

def check_startup_debug_status():
    """Vérifie si le debug de démarrage est installé"""
    logger = logging.getLogger(__name__)
    
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        debug_entry_name = "WritingToolsStartupDebug"
        
        try:
            key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
            value, _ = winreg.QueryValueEx(key, debug_entry_name)
            winreg.CloseKey(key)
            
            logger.info(f"Startup debug is INSTALLED: {value}")
            return True, value
            
        except OSError:
            logger.info("Startup debug is NOT installed")
            return False, None
            
    except Exception as e:
        logger.error(f"Error checking startup debug status: {e}")
        return False, None

def main():
    """Fonction principale"""
    setup_logging()
    logger = logging.getLogger(__name__)
    
    logger.info("Writing Tools - Startup Debug Installer")
    logger.info("=" * 50)
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python install_startup_debug.py install   - Install startup debug")
        print("  python install_startup_debug.py uninstall - Remove startup debug")
        print("  python install_startup_debug.py status    - Check current status")
        return 1
    
    command = sys.argv[1].lower()
    
    if command == "install":
        logger.info("Installing startup debug...")
        if install_startup_debug():
            print("✓ Startup debug installed successfully!")
            print("The debug script will run at next Windows startup.")
            print("Check the 'startup_logs' folder for debug information.")
        else:
            print("✗ Failed to install startup debug.")
            return 1
            
    elif command == "uninstall":
        logger.info("Uninstalling startup debug...")
        if uninstall_startup_debug():
            print("✓ Startup debug uninstalled successfully!")
        else:
            print("✗ Failed to uninstall startup debug.")
            return 1
            
    elif command == "status":
        logger.info("Checking startup debug status...")
        is_installed, command_value = check_startup_debug_status()
        if is_installed:
            print("✓ Startup debug is INSTALLED")
            print(f"Command: {command_value}")
        else:
            print("✗ Startup debug is NOT installed")
            
    else:
        print(f"Unknown command: {command}")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
