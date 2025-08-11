#!/usr/bin/env python3
"""
Script to install/test autostart functionality for Writing Tools final build.
This script configures the final build to start automatically at Windows boot.
"""

import os
import sys
import winreg
import logging
from datetime import datetime

def setup_logging():
    """Setup logging"""
    log_dir = "startup_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"autostart_test_{timestamp}.log")
    
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__), log_file

def find_final_build_exe():
    """Find the final build executable"""
    possible_paths = [
        "Windows_and_Linux/dist/production/Writing Tools.exe",
        "Windows_and_Linux/dist/final/Writing Tools.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

def install_autostart(exe_path):
    """Install autostart entry for Writing Tools"""
    logger = logging.getLogger(__name__)
    
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        entry_name = "WritingTools"
        
        # Open registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        
        # Set the autostart entry
        winreg.SetValueEx(key, entry_name, 0, winreg.REG_SZ, f'"{exe_path}"')
        winreg.CloseKey(key)
        
        logger.info(f"✓ Autostart installed: {entry_name}")
        logger.info(f"  Command: \"{exe_path}\"")
        
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to install autostart: {e}")
        return False

def uninstall_autostart():
    """Remove autostart entry for Writing Tools"""
    logger = logging.getLogger(__name__)
    
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        entry_name = "WritingTools"
        
        # Open registry key
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_WRITE)
        
        try:
            winreg.DeleteValue(key, entry_name)
            logger.info(f"✓ Autostart removed: {entry_name}")
        except OSError:
            logger.info("Autostart entry was not found (already removed)")
        
        winreg.CloseKey(key)
        return True
        
    except Exception as e:
        logger.error(f"✗ Failed to remove autostart: {e}")
        return False

def check_autostart_status():
    """Check if autostart is currently installed"""
    logger = logging.getLogger(__name__)
    
    try:
        key_path = r"Software\Microsoft\Windows\CurrentVersion\Run"
        entry_name = "WritingTools"
        
        key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, key_path, 0, winreg.KEY_READ)
        value, _ = winreg.QueryValueEx(key, entry_name)
        winreg.CloseKey(key)
        
        logger.info(f"✓ Autostart is INSTALLED")
        logger.info(f"  Command: {value}")
        return True, value
        
    except OSError:
        logger.info("Autostart is NOT installed")
        return False, None

def main():
    """Main function"""
    logger, log_file = setup_logging()
    
    logger.info("=== WRITING TOOLS AUTOSTART MANAGER ===")
    
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python install_autostart_test.py install   - Install autostart")
        print("  python install_autostart_test.py uninstall - Remove autostart")
        print("  python install_autostart_test.py status    - Check status")
        print("  python install_autostart_test.py test      - Test current setup")
        return 1
    
    command = sys.argv[1].lower()
    
    try:
        if command == "install":
            logger.info("Installing autostart for Writing Tools...")
            
            # Find executable
            exe_path = find_final_build_exe()
            if not exe_path:
                logger.error("Final build executable not found!")
                return 1
            
            logger.info(f"Found executable: {exe_path}")
            
            # Install autostart
            if install_autostart(exe_path):
                print("✓ Autostart installed successfully!")
                print("Writing Tools will start automatically at next Windows boot.")
                print("Use 'python install_autostart_test.py uninstall' to remove.")
            else:
                print("✗ Failed to install autostart.")
                return 1
                
        elif command == "uninstall":
            logger.info("Removing autostart for Writing Tools...")
            
            if uninstall_autostart():
                print("✓ Autostart removed successfully!")
            else:
                print("✗ Failed to remove autostart.")
                return 1
                
        elif command == "status":
            logger.info("Checking autostart status...")
            
            is_installed, command_value = check_autostart_status()
            if is_installed:
                print("✓ Autostart is INSTALLED")
                print(f"Command: {command_value}")
            else:
                print("✗ Autostart is NOT installed")
                
        elif command == "test":
            logger.info("Testing current autostart setup...")
            
            # Check status
            is_installed, command_value = check_autostart_status()
            
            if not is_installed:
                print("✗ Autostart is not installed. Use 'install' command first.")
                return 1
            
            # Check if executable exists
            if command_value:
                exe_path = command_value.strip('"')
                if os.path.exists(exe_path):
                    logger.info(f"✓ Executable exists: {exe_path}")
                    print("✓ Autostart setup is valid!")
                    print("The application should start automatically at next Windows boot.")
                    print("Check the system tray after restart.")
                else:
                    logger.error(f"✗ Executable not found: {exe_path}")
                    print("✗ Autostart setup is invalid (executable not found).")
                    return 1
            
        else:
            print(f"Unknown command: {command}")
            return 1
        
        logger.info(f"Full log saved to: {log_file}")
        return 0
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
