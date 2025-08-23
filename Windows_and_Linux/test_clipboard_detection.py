#!/usr/bin/env python3
"""
Test script for clipboard image detection using the improved methods.
This script tests the enhanced image detection logic we added to WritingToolApp.py
"""

import sys
import os
from pathlib import Path

# Add current directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

try:
    from PySide6.QtWidgets import QApplication
    from PySide6.QtGui import QImage
    from PySide6.QtCore import QByteArray
    import platform
except ImportError as e:
    print(f"Import error: {e}")
    sys.exit(1)

def test_enhanced_clipboard_detection():
    """Test the enhanced clipboard detection methods."""
    print("=== Testing Enhanced Clipboard Detection ===")
    
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
    
    # Test the enhanced detection logic
    print("\n--- Testing Enhanced Detection Logic ---")
    
    # Method 1: Standard Qt image detection
    if mime_data.hasImage():
        print("✓ Method 1: hasImage() returned True")
        image = mime_data.imageData()
        if isinstance(image, QImage) and not image.isNull():
            print(f"  Image found: {image.width()}x{image.height()}")
        else:
            print("  hasImage() returned null or invalid QImage")
    else:
        print("✗ Method 1: hasImage() returned False")
    
    # Method 2: Format-specific detection
    found_image = False
    for fmt in image_formats:
        if mime_data.hasFormat(fmt):
            print(f"✓ Method 2: Found format '{fmt}'")
            try:
                data = mime_data.data(fmt)
                if data and not data.isEmpty():
                    image = QImage()
                    if image.loadFromData(data):
                        if not image.isNull():
                            print(f"  Image loaded from format '{fmt}': {image.width()}x{image.height()}")
                            found_image = True
                            break
            except Exception as e:
                print(f"  Error processing format '{fmt}': {e}")
    
    if not found_image:
        print("✗ Method 2: No image found via format-specific detection")
    
    # Method 3: Linux-specific formats
    if platform.system() == "Linux":
        found_linux_image = False
        linux_formats = [
            "image/x-qt-image", "image/x-qt-pixmap", "image/x-qt-pixmap",
            "application/x-qt-image", "application/x-qt-pixmap",
            "image/x-portable-pixmap", "image/x-portable-bitmap",
            "image/x-portable-graymap", "image/x-portable-anymap"
        ]
        
        for fmt in linux_formats:
            if mime_data.hasFormat(fmt):
                print(f"✓ Method 3: Found Linux format '{fmt}'")
                try:
                    data = mime_data.data(fmt)
                    if data and not data.isEmpty():
                        image = QImage()
                        if image.loadFromData(data):
                            if not image.isNull():
                                print(f"  Image loaded from Linux format '{fmt}': {image.width()}x{image.height()}")
                                found_linux_image = True
                                break
                except Exception as e:
                    print(f"  Error processing Linux format '{fmt}': {e}")
        
        if not found_linux_image:
            print("✗ Method 3: No image found via Linux-specific formats")
    
    app.quit()

def main():
    """Main test function."""
    print("Enhanced Clipboard Image Detection Test")
    print("=" * 50)
    print("This script tests the improved image detection methods we added.")
    print("Please copy an image to your clipboard before running this test.")
    print()
    
    input("Press Enter when you have an image in your clipboard...")
    
    test_enhanced_clipboard_detection()
    
    print("\n=== Test Complete ===")
    print("If an image was detected, the enhanced methods are working!")
    print("If no image was detected, check the clipboard content.")

if __name__ == "__main__":
    main()