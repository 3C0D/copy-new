#!/usr/bin/env python3
"""
Test script to verify provider configuration is working correctly
"""

import sys
import os

# Add the Windows_and_Linux directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Windows_and_Linux'))

from config.constants import PROVIDER_DISPLAY_NAMES, DEFAULT_MODELS
from config.data_operations import get_provider_display_name, get_provider_internal_name

def test_provider_display_names():
    """Test that PROVIDER_DISPLAY_NAMES is correctly structured"""
    print("Testing PROVIDER_DISPLAY_NAMES...")
    
    expected_providers = ["gemini", "openai", "anthropic", "mistral", "ollama"]
    
    for provider in expected_providers:
        if provider in PROVIDER_DISPLAY_NAMES:
            display_name = PROVIDER_DISPLAY_NAMES[provider]
            print(f"✓ {provider} -> {display_name}")
        else:
            print(f"✗ Missing provider: {provider}")
    
    print()

def test_data_operations():
    """Test the data operations functions"""
    print("Testing data operations functions...")
    
    # Test get_provider_display_name
    for internal_name, expected_display in PROVIDER_DISPLAY_NAMES.items():
        actual_display = get_provider_display_name(internal_name)
        if actual_display == expected_display:
            print(f"✓ get_provider_display_name('{internal_name}') = '{actual_display}'")
        else:
            print(f"✗ get_provider_display_name('{internal_name}') = '{actual_display}', expected '{expected_display}'")
    
    # Test get_provider_internal_name
    for expected_internal, display_name in PROVIDER_DISPLAY_NAMES.items():
        actual_internal = get_provider_internal_name(display_name)
        if actual_internal == expected_internal:
            print(f"✓ get_provider_internal_name('{display_name}') = '{actual_internal}'")
        else:
            print(f"✗ get_provider_internal_name('{display_name}') = '{actual_internal}', expected '{expected_internal}'")
    
    print()

def test_default_models():
    """Test that DEFAULT_MODELS has entries for all providers"""
    print("Testing DEFAULT_MODELS...")
    
    for provider in PROVIDER_DISPLAY_NAMES.keys():
        if provider in DEFAULT_MODELS:
            model = DEFAULT_MODELS[provider]
            print(f"✓ {provider} -> {model}")
        else:
            print(f"✗ Missing default model for provider: {provider}")
    
    print()

if __name__ == "__main__":
    print("Provider Configuration Test")
    print("=" * 40)
    
    test_provider_display_names()
    test_data_operations()
    test_default_models()
    
    print("Test completed!")
