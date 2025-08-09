#!/usr/bin/env python3
"""
Simple test to verify provider imports work
"""

import sys
import os

# Add the Windows_and_Linux directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Windows_and_Linux'))

try:
    from config.constants import PROVIDER_DISPLAY_NAMES, DEFAULT_MODELS
    print("✓ Successfully imported constants")
    print(f"PROVIDER_DISPLAY_NAMES: {PROVIDER_DISPLAY_NAMES}")
    print(f"DEFAULT_MODELS: {DEFAULT_MODELS}")
except Exception as e:
    print(f"✗ Error importing constants: {e}")

try:
    from config.data_operations import get_provider_display_name, get_provider_internal_name
    print("✓ Successfully imported data_operations")
    
    # Test the functions
    display_name = get_provider_display_name("gemini")
    internal_name = get_provider_internal_name("Gemini (Recommended)")
    print(f"get_provider_display_name('gemini') = '{display_name}'")
    print(f"get_provider_internal_name('Gemini (Recommended)') = '{internal_name}'")
except Exception as e:
    print(f"✗ Error importing data_operations: {e}")

try:
    from aiprovider import GeminiProvider, OpenAICompatibleProvider, OllamaProvider, AnthropicProvider, MistralProvider
    print("✓ Successfully imported all providers")
    
    # Test that providers have internal_name attribute
    class MockApp:
        pass
    
    app = MockApp()
    gemini = GeminiProvider(app)
    print(f"GeminiProvider internal_name: '{gemini.internal_name}'")
    print(f"GeminiProvider provider_name: '{gemini.provider_name}'")
    
except Exception as e:
    print(f"✗ Error importing providers: {e}")
    import traceback
    traceback.print_exc()
