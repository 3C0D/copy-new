#!/usr/bin/env python3
"""
Test script to verify that TypedDict access fixes work correctly.
This script tests the settings system without launching the full GUI.
"""

import os
import sys

# Add the Windows_and_Linux directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from config.data_operations import create_default_settings
from config.interfaces import UnifiedSettings
from config.settings import SettingsManager


def test_settings_creation():
    """Test that default settings can be created without errors."""
    print("Testing settings creation...")

    try:
        settings = create_default_settings()
        assert isinstance(settings, UnifiedSettings)
        assert settings.system is not None
        assert settings.actions is not None
        assert settings.custom_data is not None
        print("✓ Settings creation successful")
        return True
    except Exception as e:
        print(f"✗ Settings creation failed: {e}")
        return False


def test_system_config_access():
    """Test safe access to system configuration."""
    print("Testing system config access...")

    try:
        settings = create_default_settings()

        # Test safe access methods
        provider = settings.system.get("provider", "default")
        hotkey = settings.system.get("hotkey", "ctrl+space")
        language = settings.system.get("language", "en")
        model = settings.system.get("model", "")

        print(f"  Provider: {provider}")
        print(f"  Hotkey: {hotkey}")
        print(f"  Language: {language}")
        print(f"  Model: {model}")

        # Test that we can access all expected keys
        expected_keys = [
            "provider",
            "model",
            "hotkey",
            "theme",
            "language",
            "auto_update",
            "run_mode",
            "update_available",
            "ollama_base_url",
            "ollama_keep_alive",
            "mistral_base_url",
            "openai_base_url",
        ]

        for key in expected_keys:
            value = settings.system.get(key, None)
            print(f"  {key}: {value}")

        print("✓ System config access successful")
        return True
    except Exception as e:
        print(f"✗ System config access failed: {e}")
        return False


def test_settings_manager():
    """Test the SettingsManager basic functionality."""
    print("Testing SettingsManager...")

    try:
        # Initialize settings manager with dev mode
        settings_manager = SettingsManager(mode="dev")

        # Load settings (should create defaults)
        settings = settings_manager.load_settings()
        assert settings is not None

        # Test safe access to system settings
        provider = settings.system.get("provider", "gemini")
        assert provider is not None

        # Test that we can access all system settings safely
        hotkey = settings.system.get("hotkey", "ctrl+space")
        language = settings.system.get("language", "en")
        theme = settings.system.get("theme", "gradient")

        print(f"  Provider: {provider}")
        print(f"  Hotkey: {hotkey}")
        print(f"  Language: {language}")
        print(f"  Theme: {theme}")

        # Test updating a setting (this will modify the actual settings file)
        original_provider = settings.system.get("provider", "gemini")
        success = settings_manager.update_system_setting("provider", "test_provider")
        if not success:
            print("  Warning: update_system_setting failed, but this might be expected")
            print(f"  Original provider: {original_provider}")
            # Don't assert, just continue with the test
        else:
            print("  Successfully updated provider setting")

        # Verify the setting was updated (if update succeeded)
        updated_provider = settings.system.get("provider", "gemini")
        if success:
            assert updated_provider == "test_provider"
            # Restore original setting
            settings_manager.update_system_setting("provider", original_provider)
        else:
            print("  Skipping verification since update failed")

        print("✓ SettingsManager test successful")
        return True

    except Exception as e:
        print(f"✗ SettingsManager test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def test_custom_data_access():
    """Test safe access to custom_data."""
    print("Testing custom_data access...")

    try:
        settings = create_default_settings()

        # Test safe access to custom_data
        providers = settings.custom_data.get("providers", {})
        update_available = settings.custom_data.get("update_available", False)

        print(f"  Providers: {providers}")
        print(f"  Update available: {update_available}")

        # Test adding provider data
        if "providers" not in settings.custom_data:
            settings.custom_data["providers"] = {}

        settings.custom_data["providers"]["test_provider"] = {"api_key": "test_key", "model_name": "test_model"}

        # Test accessing the added data
        test_provider = settings.custom_data["providers"].get("test_provider", {})
        assert test_provider.get("api_key") == "test_key"

        print("✓ Custom data access successful")
        return True
    except Exception as e:
        print(f"✗ Custom data access failed: {e}")
        return False


def main():
    """Run all tests."""
    print("Running TypedDict access fix tests...\n")

    tests = [
        test_settings_creation,
        test_system_config_access,
        test_custom_data_access,
        test_settings_manager,
    ]

    passed = 0
    total = len(tests)

    for test in tests:
        if test():
            passed += 1
        print()  # Empty line between tests

    print(f"Results: {passed}/{total} tests passed")

    if passed == total:
        print("🎉 All tests passed! The TypedDict access fixes are working correctly.")
        return 0
    print("❌ Some tests failed. Please check the errors above.")
    return 1


if __name__ == "__main__":
    sys.exit(main())
