#!/usr/bin/env python3
"""
Test script to quickly build and test console mode for dev_build
"""

import os
import sys
import subprocess
from pathlib import Path

def main():
    """Test console build functionality"""
    print("===== Testing Console Build =====")
    print()
    
    # Change to Windows_and_Linux directory if needed
    script_dir = Path(__file__).parent
    windows_linux_dir = script_dir.parent
    
    if os.getcwd() != str(windows_linux_dir):
        os.chdir(windows_linux_dir)
        print(f"Changed to directory: {windows_linux_dir}")
    
    # Test console build
    print("Building with console mode...")
    try:
        result = subprocess.run([
            sys.executable, "scripts/dev_build.py", "--console"
        ], check=True, capture_output=False)
        
        print("\n✅ Console build completed successfully!")
        print("The executable should now show console output when run.")
        
        # Check if exe exists
        exe_path = Path("dist/dev/Writing Tools.exe")
        if exe_path.exists():
            print(f"✅ Executable found at: {exe_path}")
            print("\nTo test console output, run:")
            print(f'  "{exe_path.absolute()}"')
            print("\nYou should see logs directly in the console window.")
        else:
            print("❌ Executable not found")
            
    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ Build cancelled by user")
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
