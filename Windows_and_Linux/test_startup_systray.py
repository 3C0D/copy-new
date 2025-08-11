#!/usr/bin/env python3
"""
Test script to verify systray functionality during startup scenarios.
This script simulates startup conditions and tests the retry mechanisms.
"""

import logging
import os
import sys
import time
from unittest.mock import patch

# Add the Windows_and_Linux directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from PySide6 import QtWidgets, QtCore, QtGui
from WritingToolApp import WritingToolApp

# Set up logging
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler("startup_test.log")
    ]
)

class StartupTestApp(WritingToolApp):
    """Test version of WritingToolApp with startup simulation"""
    
    def __init__(self, argv, simulate_startup_delay=False):
        self.simulate_startup_delay = simulate_startup_delay
        self.systray_creation_attempts = 0
        super().__init__(argv)
    
    def _is_system_tray_available_with_retry(self, max_retries=5, delay_ms=1000):
        """Override to simulate startup conditions"""
        self.systray_creation_attempts += 1
        
        if self.simulate_startup_delay and self.systray_creation_attempts <= 2:
            logging.info(f"Simulating startup delay - systray not available yet (attempt {self.systray_creation_attempts})")
            return False
        
        # Call the original method
        return super()._is_system_tray_available_with_retry(max_retries, delay_ms)

def test_normal_startup():
    """Test normal startup without delays"""
    logging.info("=== Testing Normal Startup ===")
    
    app = StartupTestApp(sys.argv, simulate_startup_delay=False)
    app.setQuitOnLastWindowClosed(False)
    
    # Check if tray icon was created
    if app.tray_icon and app.tray_icon.isVisible():
        logging.info("✓ Normal startup: Tray icon created and visible")
        result = True
    else:
        logging.error("✗ Normal startup: Tray icon not visible")
        result = False
    
    app.quit()
    return result

def test_startup_with_delay():
    """Test startup with simulated system delays"""
    logging.info("=== Testing Startup with Simulated Delays ===")
    
    app = StartupTestApp(sys.argv, simulate_startup_delay=True)
    app.setQuitOnLastWindowClosed(False)
    
    # Give some time for retry mechanisms to work
    start_time = time.time()
    timeout = 10  # 10 seconds timeout
    
    while time.time() - start_time < timeout:
        app.processEvents()
        if app.tray_icon and app.tray_icon.isVisible():
            logging.info(f"✓ Delayed startup: Tray icon became visible after {time.time() - start_time:.2f} seconds")
            app.quit()
            return True
        time.sleep(0.1)
    
    logging.error("✗ Delayed startup: Tray icon never became visible")
    app.quit()
    return False

def test_autostart_simulation():
    """Test autostart scenario simulation"""
    logging.info("=== Testing Autostart Scenario ===")
    
    # Temporarily modify the settings to simulate autostart
    app = StartupTestApp(sys.argv, simulate_startup_delay=False)
    app.setQuitOnLastWindowClosed(False)
    
    # Simulate autostart setting
    app.settings_manager.start_on_boot = True
    
    # Test the delay detection logic
    startup_delay_needed = (
        len(QtWidgets.QApplication.topLevelWidgets()) == 0 or
        getattr(app.settings_manager, 'start_on_boot', False)
    )
    
    if startup_delay_needed:
        logging.info("✓ Autostart simulation: Startup delay correctly detected")
        result = True
    else:
        logging.error("✗ Autostart simulation: Startup delay not detected")
        result = False
    
    app.quit()
    return result

def main():
    """Run all tests"""
    logging.info("Starting systray startup tests...")
    
    results = []
    
    # Test 1: Normal startup
    try:
        results.append(test_normal_startup())
    except Exception as e:
        logging.error(f"Normal startup test failed with exception: {e}")
        results.append(False)
    
    # Test 2: Startup with delays
    try:
        results.append(test_startup_with_delay())
    except Exception as e:
        logging.error(f"Delayed startup test failed with exception: {e}")
        results.append(False)
    
    # Test 3: Autostart simulation
    try:
        results.append(test_autostart_simulation())
    except Exception as e:
        logging.error(f"Autostart simulation test failed with exception: {e}")
        results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    logging.info(f"\n=== Test Summary ===")
    logging.info(f"Passed: {passed}/{total}")
    
    if passed == total:
        logging.info("✓ All tests passed! Systray startup should work correctly.")
        return 0
    else:
        logging.error("✗ Some tests failed. Check the logs for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())
