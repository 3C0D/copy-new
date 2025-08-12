#!/usr/bin/env python3
"""
Writing Tools - Test Executable
Tests the built executable to see if it starts correctly
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def test_exe_launch():
    """Test launching the executable"""
    print("=== Testing executable launch ===")
    
    # Find the executable
    exe_path = Path(__file__).parent.parent / "dist" / "Writing Tools.exe"
    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    print(f"Found executable: {exe_path}")
    
    # Try to launch it
    try:
        print("Launching executable...")
        
        # Launch with subprocess to capture output
        process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=exe_path.parent
        )
        
        # Wait a bit to see if it starts
        time.sleep(3)
        
        # Check if process is still running
        poll_result = process.poll()
        if poll_result is None:
            print("✓ Process is running")
            
            # Terminate it
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            
            return True
        else:
            print(f"❌ Process exited with code: {poll_result}")
            
            # Get output
            stdout, stderr = process.communicate()
            if stdout:
                print(f"STDOUT:\n{stdout}")
            if stderr:
                print(f"STDERR:\n{stderr}")
            
            return False
            
    except Exception as e:
        print(f"❌ Error launching executable: {e}")
        return False


def test_with_debug():
    """Test with debug logging enabled"""
    print("\n=== Testing with debug logging ===")
    
    exe_path = Path(__file__).parent.parent / "dist" / "Writing Tools.exe"
    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return False
    
    try:
        # Set environment variable for debug logging
        env = os.environ.copy()
        env['PYTHONPATH'] = str(exe_path.parent)
        
        print("Launching with debug environment...")
        
        process = subprocess.Popen(
            [str(exe_path)],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            cwd=exe_path.parent,
            env=env
        )
        
        # Wait a bit
        time.sleep(5)
        
        # Check if still running
        poll_result = process.poll()
        if poll_result is None:
            print("✓ Process running with debug")
            process.terminate()
            try:
                process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                process.kill()
                process.wait()
            return True
        else:
            print(f"❌ Process exited with code: {poll_result}")
            stdout, stderr = process.communicate()
            if stdout:
                print(f"STDOUT:\n{stdout}")
            if stderr:
                print(f"STDERR:\n{stderr}")
            return False
            
    except Exception as e:
        print(f"❌ Error: {e}")
        return False


def check_dependencies():
    """Check if all required files are present"""
    print("\n=== Checking dependencies ===")
    
    dist_dir = Path(__file__).parent.parent / "dist"
    required_files = [
        "Writing Tools.exe",
        "data.json",
        "background.png",
        "background_dark.png",
        "background_popup.png",
        "background_popup_dark.png",
        "icons"
    ]
    
    missing = []
    for file in required_files:
        file_path = dist_dir / file
        if not file_path.exists():
            missing.append(file)
        else:
            print(f"✓ {file}")
    
    if missing:
        print(f"❌ Missing files: {missing}")
        return False
    else:
        print("✓ All required files present")
        return True


def main():
    """Run all tests"""
    print("Testing WritingTools executable...")
    
    success = True
    
    success &= check_dependencies()
    success &= test_exe_launch()
    success &= test_with_debug()
    
    if success:
        print("\n🎉 Executable tests completed!")
    else:
        print("\n❌ Some tests failed")
    
    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
