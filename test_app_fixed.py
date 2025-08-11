#!/usr/bin/env python3
"""
Test script to verify the fixed WritingToolApp works correctly.
"""

import sys
import os
import logging

# Add Windows_and_Linux to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "Windows_and_Linux"))

from WritingToolApp import WritingToolApp

def main():
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s"
    )
    
    logger = logging.getLogger(__name__)
    logger.info("Starting WritingToolApp test...")
    
    try:
        # Create the application
        app = WritingToolApp([])
        app.setQuitOnLastWindowClosed(False)
        
        # Check tray icon status
        logger.info(f"App created successfully")
        logger.info(f"Tray icon exists: {app.tray_icon is not None}")
        
        if app.tray_icon:
            logger.info(f"Tray icon visible: {app.tray_icon.isVisible()}")
            logger.info(f"Tray icon tooltip: {app.tray_icon.toolTip()}")
        
        logger.info("Application is running. Check your system tray!")
        logger.info("Press Ctrl+C to exit...")
        
        # Run the application
        return app.exec()
        
    except Exception as e:
        logger.error(f"Error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1

if __name__ == "__main__":
    sys.exit(main())
