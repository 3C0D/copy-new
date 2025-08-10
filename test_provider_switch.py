#!/usr/bin/env python3
"""
Test script to verify that provider switching works correctly in the UI.
This script will test the provider dropdown functionality.
"""

import sys
import os
import time
from PySide6.QtCore import QTimer
from PySide6.QtWidgets import QApplication

# Add the Windows_and_Linux directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'Windows_and_Linux'))

from WritingToolApp import WritingToolApp
from ui.SettingsWindow import SettingsWindow


def test_provider_switching():
    """Test that provider switching updates the UI correctly."""
    print("Starting provider switching test...")

    # Create the main app (WritingToolApp is a QApplication)
    writing_app = WritingToolApp(sys.argv)

    # Create settings window in providers_only mode
    settings_window = SettingsWindow(writing_app, providers_only=True)
    settings_window.show()

    def test_switch():
        """Test switching between providers."""
        print("Testing provider switches...")

        # Get the dropdown
        dropdown = settings_window.provider_dropdown
        if not dropdown:
            print("ERROR: Provider dropdown not found!")
            return

        print(f"Available providers: {[dropdown.itemText(i) for i in range(dropdown.count())]}")

        # Test switching to each provider
        for i in range(dropdown.count()):
            provider_name = dropdown.itemText(i)
            print(f"Switching to provider: {provider_name}")

            # Change the dropdown selection
            dropdown.setCurrentIndex(i)

            # Give time for UI to update
            QApplication.processEvents()
            time.sleep(0.1)

            # Check if the provider UI was updated
            current_layout = settings_window.current_provider_layout
            if current_layout:
                widget_count = current_layout.count()
                print(f"  Provider UI has {widget_count} widgets")

                # Check if we have provider-specific widgets
                has_provider_widgets = False
                for j in range(widget_count):
                    item = current_layout.itemAt(j)
                    if item and item.widget():
                        widget = item.widget()
                        if hasattr(widget, 'text') and widget.text():
                            text = widget.text()
                            if any(keyword in text.lower() for keyword in ['api', 'key', 'url', 'model']):
                                has_provider_widgets = True
                                print(f"    Found provider widget: {text[:50]}...")
                                break

                if has_provider_widgets:
                    print(f"  ✓ Provider {provider_name} UI loaded correctly")
                else:
                    print(f"  ⚠ Provider {provider_name} UI may not have loaded correctly")
            else:
                print(f"  ✗ No provider layout found for {provider_name}")

        print("Provider switching test completed!")

        # Close the application
        QTimer.singleShot(1000, writing_app.quit)

    # Start the test after a short delay
    QTimer.singleShot(1000, test_switch)

    # Run the application
    return writing_app.exec()


if __name__ == "__main__":
    test_provider_switching()
