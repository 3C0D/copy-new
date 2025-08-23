#!/usr/bin/env python3
"""
Simple clipboard test script that doesn't require PySide6.
Tests Linux system tools for clipboard access.
"""

import subprocess
import platform
import sys

def test_system_tools():
    """Test Linux system tools for clipboard access."""
    if platform.system() != "Linux":
        print("System tools test only available on Linux")
        return
    
    print("=== Testing Linux System Tools ===")
    
    # Test xclip
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'TARGETS'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("✓ xclip is available")
            print(f"Available targets: {result.stdout.strip()}")
            
            # Try to get image data
            print("\nTrying to get image data with xclip...")
            for img_type in ['image/png', 'image/jpeg', 'image/bmp', 'image/gif']:
                try:
                    img_result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', img_type, '-o'], 
                                             capture_output=True, timeout=5)
                    if img_result.returncode == 0 and img_result.stdout:
                        print(f"✓ {img_type}: {len(img_result.stdout)} bytes")
                    else:
                        print(f"✗ {img_type}: No data")
                except Exception as e:
                    print(f"✗ {img_type}: Error - {e}")
        else:
            print("✗ xclip returned error")
    except FileNotFoundError:
        print("✗ xclip not found")
    except Exception as e:
        print(f"✗ xclip error: {e}")
    
    # Test xsel
    try:
        result = subprocess.run(['xsel', '--clipboard', '--type', 'TARGETS'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0:
            print("\n✓ xsel is available")
            print(f"Available targets: {result.stdout.strip()}")
            
            # Try to get image data
            print("\nTrying to get image data with xsel...")
            for img_type in ['image/png', 'image/jpeg', 'image/bmp', 'image/gif']:
                try:
                    img_result = subprocess.run(['xsel', '--clipboard', '--type', img_type, '--output'], 
                                             capture_output=True, timeout=5)
                    if img_result.returncode == 0 and img_result.stdout:
                        print(f"✓ {img_type}: {len(img_result.stdout)} bytes")
                    else:
                        print(f"✗ {img_type}: No data")
                except Exception as e:
                    print(f"✗ {img_type}: Error - {e}")
        else:
            print("✗ xsel returned error")
    except FileNotFoundError:
        print("✗ xsel not found")
    except Exception as e:
        print(f"✗ xsel error: {e}")

def test_clipboard_content():
    """Test what's currently in the clipboard."""
    print("\n=== Current Clipboard Content ===")
    
    # Try to get text content
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard', '-o'], 
                              capture_output=True, text=True, timeout=5)
        if result.returncode == 0 and result.stdout.strip():
            content = result.stdout.strip()
            if len(content) > 100:
                content = content[:100] + "..."
            print(f"Text content: {content}")
        else:
            print("Text content: Empty or not available")
    except Exception as e:
        print(f"Error getting text content: {e}")
    
    # Try to get raw data size
    try:
        result = subprocess.run(['xclip', '-selection', 'clipboard', '-t', 'image/png', '-o'], 
                              capture_output=True, timeout=5)
        if result.returncode == 0 and result.stdout:
            print(f"PNG data: {len(result.stdout)} bytes")
        else:
            print("PNG data: Not available")
    except Exception as e:
        print(f"Error getting PNG data: {e}")

def main():
    """Main test function."""
    print("Simple Clipboard Test")
    print("=" * 30)
    print("This script tests Linux clipboard tools without requiring PySide6.")
    print()
    
    test_system_tools()
    test_clipboard_content()
    
    print("\n=== Test Complete ===")
    print("If you see 'No data' for image formats, try copying an image to your clipboard.")
    print("You can do this by:")
    print("1. Right-clicking on an image and selecting 'Copy Image'")
    print("2. Taking a screenshot and copying it")
    print("3. Copying an image from an image editor")

if __name__ == "__main__":
    main()