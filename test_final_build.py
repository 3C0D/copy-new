#!/usr/bin/env python3
"""
Test script to verify the final build works correctly with systray.
This script simulates the final build environment and tests startup timing.
"""

import os
import sys
import time
import subprocess
import logging
from datetime import datetime

def setup_logging():
    """Setup logging for the test"""
    log_dir = "startup_logs"
    os.makedirs(log_dir, exist_ok=True)
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    log_file = os.path.join(log_dir, f"final_build_test_{timestamp}.log")
    
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
        "dist/production/Writing Tools.exe",
        "dist/final/Writing Tools.exe",
    ]
    
    for path in possible_paths:
        if os.path.exists(path):
            return os.path.abspath(path)
    
    return None

def test_final_build_startup():
    """Test the final build startup timing"""
    logger, log_file = setup_logging()
    
    logger.info("=== FINAL BUILD STARTUP TEST ===")
    
    # Find the executable
    exe_path = find_final_build_exe()
    if not exe_path:
        logger.error("Final build executable not found!")
        logger.info("Available paths checked:")
        for path in ["Windows_and_Linux/dist/production/Writing Tools.exe",
                     "Windows_and_Linux/dist/final/Writing Tools.exe"]:
            logger.info(f"  {path} - {'EXISTS' if os.path.exists(path) else 'NOT FOUND'}")
        return False
    
    logger.info(f"Found executable: {exe_path}")
    
    # Test startup timing
    logger.info("Testing startup timing...")
    start_time = time.time()
    
    try:
        # Launch the executable
        process = subprocess.Popen(
            [exe_path],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )
        
        logger.info(f"Process launched with PID: {process.pid}")
        
        # Monitor for 15 seconds
        for i in range(15):
            time.sleep(1)
            
            # Check if process is still running
            if process.poll() is not None:
                logger.warning(f"Process terminated at second {i+1}")
                break
            
            if (i + 1) % 5 == 0:
                elapsed = time.time() - start_time
                logger.info(f"Second {i+1}: Process still running (elapsed: {elapsed:.1f}s)")
        
        # Check final status
        elapsed = time.time() - start_time
        if process.poll() is None:
            logger.info(f"✓ Process running successfully after {elapsed:.1f}s")
            logger.info("Check your system tray for the Writing Tools icon!")
            
            # Terminate the process
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
            
            return True
        else:
            logger.error(f"✗ Process terminated after {elapsed:.1f}s")
            
            # Get output
            stdout, stderr = process.communicate()
            if stdout:
                logger.info(f"STDOUT:\n{stdout}")
            if stderr:
                logger.error(f"STDERR:\n{stderr}")
            
            return False
            
    except Exception as e:
        logger.error(f"Error during test: {e}")
        return False

def test_icon_resolution():
    """Test icon path resolution in different contexts"""
    logger = logging.getLogger(__name__)
    
    logger.info("=== ICON RESOLUTION TEST ===")
    
    # Test icon paths that should exist
    icon_files = [
        "Windows_and_Linux/config/icons/app_icon.png",
        "Windows_and_Linux/config/icons/app_icon.ico",
    ]
    
    for icon_file in icon_files:
        exists = os.path.exists(icon_file)
        logger.info(f"Icon {icon_file}: {'✓ EXISTS' if exists else '✗ NOT FOUND'}")
    
    return True

def main():
    """Main test function"""
    logger, log_file = setup_logging()
    
    try:
        logger.info("Starting final build tests...")
        
        # Test 1: Icon resolution
        test_icon_resolution()
        
        # Test 2: Final build startup
        startup_ok = test_final_build_startup()
        
        # Summary
        logger.info("=== TEST SUMMARY ===")
        if startup_ok:
            logger.info("✓ Final build startup test PASSED")
            logger.info("The application should appear in the system tray")
        else:
            logger.error("✗ Final build startup test FAILED")
            logger.info("Check the logs for details")
        
        logger.info(f"Full log saved to: {log_file}")
        
        return 0 if startup_ok else 1
        
    except Exception as e:
        logger.error(f"Critical error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
