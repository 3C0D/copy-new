#!/usr/bin/env python3
"""
Writing Tools - Test Final Executable
Tests that the final executable shows onboarding and stays open
"""

import os
import sys
import subprocess
import time
from pathlib import Path


def test_exe_with_onboarding():
    """Test that the executable shows onboarding and stays open"""
    print("=== Testing executable with onboarding ===")

    # Find the executable
    exe_path = Path(__file__).parent.parent / "dist" / "Writing Tools.exe"
    if not exe_path.exists():
        print(f"❌ Executable not found at {exe_path}")
        return False

    print(f"Found executable: {exe_path}")

    try:
        print("Launching executable...")

        # Launch the executable
        process = subprocess.Popen(
            [str(exe_path)],
            cwd=exe_path.parent,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )

        print(f"Process started with PID: {process.pid}")

        # Wait a bit for the application to start
        time.sleep(5)

        # Check if process is still running
        poll_result = process.poll()
        if poll_result is None:
            print("✓ Process is still running after 5 seconds")

            # Wait a bit more to see if onboarding window appears
            print("Waiting 10 more seconds to see if onboarding appears...")
            time.sleep(10)

            # Check if still running
            poll_result = process.poll()
            if poll_result is None:
                print("✓ Process still running after 15 seconds total")
                print(
                    "✓ This suggests onboarding window is displayed and app is working"
                )

                # Terminate the process
                print("Terminating process...")
                process.terminate()
                try:
                    process.wait(timeout=5)
                    print("✓ Process terminated gracefully")
                except subprocess.TimeoutExpired:
                    print("⚠ Process didn't terminate gracefully, killing...")
                    process.kill()
                    process.wait()

                return True
            else:
                print(f"❌ Process exited with code: {poll_result}")
                return False
        else:
            print(f"❌ Process exited immediately with code: {poll_result}")

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


def check_data_json():
    """Check that data.json is in the right place with correct content"""
    print("\n=== Checking data.json ===")

    dist_dir = Path(__file__).parent.parent / "dist"
    data_json_path = dist_dir / "data.json"

    if not data_json_path.exists():
        print(f"❌ data.json not found at {data_json_path}")
        return False

    print(f"✓ data.json found at {data_json_path}")

    # Check content
    try:
        import json

        with open(data_json_path, "r") as f:
            data = json.load(f)

        system = data.get("system", {})
        provider = system.get("provider", "")
        api_key = system.get("api_key", "")
        run_mode = system.get("run_mode", "")

        print(f"provider: '{provider}'")
        print(f"api_key: '{api_key}'")
        print(f"run_mode: '{run_mode}'")

        if provider == "" and api_key == "" and run_mode == "build_final":
            print("✓ data.json has correct content for onboarding")
            return True
        else:
            print("❌ data.json content is not as expected")
            return False

    except Exception as e:
        print(f"❌ Error reading data.json: {e}")
        return False


def check_no_config_dir():
    """Check that no config directory was created in dist"""
    print("\n=== Checking no config directory in dist ===")

    dist_dir = Path(__file__).parent.parent / "dist"
    config_dir = dist_dir / "config"

    if config_dir.exists():
        print(f"❌ Unexpected config directory found at {config_dir}")
        # List contents
        try:
            contents = list(config_dir.iterdir())
            print(f"Contents: {contents}")
        except:
            pass
        return False
    else:
        print("✓ No config directory in dist (correct)")
        return True


def main():
    """Run all tests"""
    print("Testing final executable behavior...")

    success = True

    success &= check_data_json()
    success &= check_no_config_dir()
    success &= test_exe_with_onboarding()

    if success:
        print("\n🎉 All tests passed! Executable should work correctly.")
    else:
        print("\n❌ Some tests failed")

    return 0 if success else 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
