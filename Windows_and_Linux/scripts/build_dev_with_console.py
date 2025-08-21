#!/usr/bin/env python3
"""
Test script to quickly build and test console mode for build_dev
"""

import os
import subprocess
import sys
from pathlib import Path


def main():
    """Main function to run build_dev in console mode"""
    # Change to Windows_and_Linux directory
    script_dir = Path(__file__).parent
    windows_linux_dir = script_dir.parent

    if os.getcwd() != str(windows_linux_dir):
        os.chdir(windows_linux_dir)
        print(f"Changed to directory: {windows_linux_dir}")

    # Test console build
    print("Building with console mode...")
    try:
        subprocess.run(
            [sys.executable, "scripts/build_dev.py", "--console"],
            check=True,
            capture_output=False,
        )

    except subprocess.CalledProcessError as e:
        print(f"❌ Build failed: {e}")
        return 1
    except KeyboardInterrupt:
        print("\n⚠️ Build cancelled by user")
        return 1

    return 0


if __name__ == "__main__":
    sys.exit(main())
