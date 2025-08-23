#!/usr/bin/env python3
"""
Test script for clipboard image detection on Linux.
This script tests various methods to detect images in the clipboard.
"""

import sys
import os
import platform
from pathlib import Path

# Add the Windows_and_Linux directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "Windows_and_Linux"))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage
    from PySide6.QtCore import QByteArray
except ImportError as e:
    print(f"PySide6 not available: {e}")
    sys.exit(1)

def test_qt_clipboard():
    """Test basic Qt clipboard functionality."""
    print("=== Testing Qt Clipboard ===")
    
    app = QApplication([])
    clipboard = app.clipboard()
    mime_data = clipboard.mimeData()
    
    print(f"Platform: {platform.system()}")
    print(f"hasImage(): {mime_data.hasImage()}")
    print(f"hasText(): {mime_data.hasText()}")
    print(f"hasUrls(): {mime_data.hasUrls()}")
    
    # List all available formats
    formats = mime_data.formats()
    print(f"Available formats ({len(formats)}): {formats}")
    
    # Check specific image formats
    image_formats = [
        "image/png", "image/jpeg", "image/jpg", "image/bmp",
        "image/gif", "image/tiff", "image/dib", "CF_DIB",
        "CF_BITMAP", "application/x-qt-image"
    ]
    
    for fmt in image_formats:
        has_format = mime_data.hasFormat(fmt)
        if has_format:
            data_size = len(mime_data.data(fmt))
            print(f"Format '{fmt}': YES ({data_size} bytes)")
        else:
            print(f"Format '{fmt}': NO")
    
    # Linux-specific format checks
    if platform.system() == "Linux":
        print("--- Linux-specific format checks ---")
        linux_formats = [
            "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
            "application/x-qt-image", "application/x-qt-pixmap",
            "image/x-portable-pixmap", "image/x-portable-bitmap",
            "image/x-portable-graymap", "image/x-portable-anymap"
        ]
        
        for fmt in linux_formats:
            has_format = mime_data.hasFormat(fmt)
            if has_format:
                data_size = len(mime_data.data(fmt))
                print(f"Linux format '{fmt}': YES ({data_size} bytes)")
            else:
                print(f"Linux format '{fmt}': NO")
        
        # Check for any format containing image-related keywords
        print("--- Checking for image-related formats ---")
        for fmt in formats:
            if any(img_type in fmt.lower() for img_type in ['image', 'pixmap', 'bitmap', 'png', 'jpeg', 'jpg', 'gif', 'bmp', 'tiff']):
                has_format = mime_data.hasFormat(fmt)
                if has_format:
                    data_size = len(mime_data.data(fmt))
                    print(f"Image-related format '{fmt}': YES ({data_size} bytes)")
                else:
                    print(f"Image-related format '{fmt}': NO")
    
    # Try to get image data directly
    try:
        image_data = mime_data.imageData()
        if image_data is not None:
            print(f"imageData() returned: {type(image_data)}")
            if hasattr(image_data, 'width') and hasattr(image_data, 'height'):
                print(f"Image dimensions: {image_data.width()}x{image_data.height()}")
        else:
            print("imageData() returned None")
    except Exception as e:
        print(f"Error getting imageData(): {e}")
    
    app.quit()

def test_system_tools():
    """Test Linux system tools for clipboard access."""
    if platform.system() != "Linux":
        print("System tools test only available on Linux")
        return
    
    print("\n=== Testing Linux System Tools ===")
    
    import subprocess
    
    # Test xclip
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'TARGETS'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("xclip is available")
            print(f"Available targets: {result.stdout.strip()}")
        else:
            print("xclip returned error")
    except FileNotFoundError:
        print("xclip not found")
    except Exception as e:
        print(f"xclip error: {e}")
    
    # Test xsel
    try:
        result = subprocess.run(['xsel', '--clipboard', '--type', 'TARGETS'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("xsel is available")
            print(f"Available targets: {result.stdout.strip()}")
        else:
            print("xsel returned error")
    except FileNotFoundError:
        print("xsel not found")
    except Exception as e:
        print(f"xsel error: {e}")

def main():
    """Main test function."""
    print("Clipboard Image Detection Test")
    print("=" * 40)
    print("Please copy an image to your clipboard before running this test.")
    print("You can do this by:")
    print("1. Right-clicking on an image and selecting 'Copy Image'")
    print("2. Taking a screenshot and copying it")
    print("3. Copying an image from an image editor")
    print()
    
    input("Press Enter when you have an image in your clipboard...")
    
    test_qt_clipboard()
    test_system_tools()
    
    print("\n=== Test Complete ===")
    print("If no image was detected, the clipboard might be empty or contain data in an unsupported format.")

if __name__ == "__main__":
    main()