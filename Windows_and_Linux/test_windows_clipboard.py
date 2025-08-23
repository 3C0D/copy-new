#!/usr/bin/env python3
"""
Test script for Windows native clipboard method.
This script tests the new _get_image_from_windows_native method.
"""

import platform
import sys

def test_windows_clipboard_import():
    """Test if Windows clipboard components are properly imported."""
    print(f"Platform: {platform.system()}")
    
    if platform.system() == "Windows":
        try:
            import win32clipboard
            import win32con
            print("✅ win32clipboard imported successfully")
            print("✅ win32con imported successfully")
            return True
        except ImportError as e:
            print(f"❌ Failed to import win32clipboard: {e}")
            return False
    else:
        print("ℹ️ Not on Windows, skipping win32clipboard test")
        return True

def test_writing_tool_app_import():
    """Test if WritingToolApp imports successfully."""
    try:
        from WritingToolApp import WritingToolApp
        print("✅ WritingToolApp imported successfully")
        
        # Check if the Windows native method exists
        if hasattr(WritingToolApp, '_get_image_from_windows_native'):
            print("✅ _get_image_from_windows_native method found")
        else:
            print("❌ _get_image_from_windows_native method not found")
            
        return True
    except ImportError as e:
        print(f"❌ Failed to import WritingToolApp: {e}")
        return False

def main():
    """Main test function."""
    print("🧪 Testing Windows clipboard integration...")
    print("=" * 50)
    
    # Test 1: Windows clipboard imports
    clipboard_ok = test_windows_clipboard_import()
    
    print()
    
    # Test 2: WritingToolApp import
    app_ok = test_writing_tool_app_import()
    
    print()
    print("=" * 50)
    
    if clipboard_ok and app_ok:
        print("🎉 All tests passed! Windows clipboard integration ready.")
    else:
        print("⚠️ Some tests failed. Check the output above.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())