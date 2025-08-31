#!/usr/bin/env python3
"""
Test script to verify the image conversion fix.
This script tests the QImage to base64 conversion functionality.
"""

import base64
import tempfile
import time
from pathlib import Path

from PySide6.QtCore import QBuffer, QIODevice
from PySide6.QtGui import QGuiApplication, QImage
from PySide6.QtWidgets import QApplication


def test_qimage_to_base64_fixed(image: QImage) -> str:
    """
    Test the fixed version of QImage to base64 conversion.
    This mimics the corrected implementation from WritingToolApp.py
    """
    try:
        # Create temporary file path
        temp_dir = Path(tempfile.gettempdir())
        temp_filename = f"test_clipboard_{int(time.time() * 1000)}.png"
        temp_path = temp_dir / temp_filename

        # Save QImage to temporary file (PNG format for compatibility)
        # FIXED: Use 'PNG' string instead of 'PNG'.encode()
        if not image.save(str(temp_path), 'PNG'):
            print("Failed to save QImage to temporary file")
            return ""

        # Read the temporary file and convert to base64
        try:
            with open(temp_path, "rb") as image_file:
                image_bytes = image_file.read()
                base64_string = base64.b64encode(image_bytes).decode('utf-8')

            print(f"Successfully converted image to base64: {len(base64_string)} characters")
            return base64_string

        finally:
            # Clean up temporary file
            try:
                temp_path.unlink(missing_ok=True)
            except Exception as cleanup_error:
                print(f"Failed to cleanup temporary file {temp_path}: {cleanup_error}")

    except Exception as e:
        print(f"Error converting QImage to base64: {e}")
        return ""


def test_qimage_to_base64_broken(image: QImage) -> str:
    """
    Test the broken version to demonstrate the error.
    This shows what was wrong in the original implementation.
    """
    try:
        temp_dir = Path(tempfile.gettempdir())
        temp_filename = f"test_clipboard_broken_{int(time.time() * 1000)}.png"
        temp_path = temp_dir / temp_filename

        # BROKEN: Using 'PNG'.encode() which creates bytes instead of string
        if not image.save(str(temp_path), 'PNG'.encode()):
            print("Failed to save QImage to temporary file (broken version)")
            return ""

        return "This shouldn't work"

    except Exception as e:
        print(f"Expected error in broken version: {e}")
        return ""


def main():
    """
    Main test function.
    """
    print("Testing QImage to base64 conversion fix...")
    
    # Create QApplication (required for QImage operations)
    app = QApplication([])
    
    # Create a simple test image (100x100 red square)
    test_image = QImage(100, 100, QImage.Format.Format_RGB32)
    test_image.fill(0xFF0000)  # Red color
    
    if test_image.isNull():
        print("Failed to create test image")
        return
    
    print(f"Created test image: {test_image.width()}x{test_image.height()}")
    
    # Test the broken version (should fail)
    print("\n=== Testing BROKEN version ===")
    result_broken = test_qimage_to_base64_broken(test_image)
    
    # Test the fixed version (should work)
    print("\n=== Testing FIXED version ===")
    result_fixed = test_qimage_to_base64_fixed(test_image)
    
    if result_fixed:
        print("✅ Fixed version works correctly!")
        print(f"Base64 preview: {result_fixed[:50]}...")
    else:
        print("❌ Fixed version still has issues")
    
    app.quit()


if __name__ == "__main__":
    main()