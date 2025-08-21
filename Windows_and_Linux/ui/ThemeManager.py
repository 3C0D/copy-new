"""
Centralized theme manager for the entire application.
"""

from PySide6 import QtCore

from ui.ui_utils import get_effective_color_mode, set_color_mode


class ThemeManager(QtCore.QObject):
    """Centralized theme manager with signals to notify changes."""

    # Signal emitted when the theme changes
    theme_changed = QtCore.Signal(str)  # Emits the new mode (dark/light)

    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        super().__init__()
        self._initialized = True
        self._registered_widgets = []

    def register_widget(self, widget):
        """Register a widget to receive theme updates."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget):
        """Unregister a widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def change_theme(self, new_mode):
        """Change the theme and notify all registered widgets."""
        set_color_mode(new_mode)
        current_mode = get_effective_color_mode()
        self.theme_changed.emit(current_mode)

        # Refresh all registered widgets
        for widget in self._registered_widgets[
            :
        ]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_theme"):
                try:
                    widget.refresh_theme()
                except RuntimeError:
                    # Widget destroyed, remove it from the list
                    self._registered_widgets.remove(widget)

    @staticmethod
    def get_styles():
        """Return all standardized styles based on the current theme."""
        current_mode = get_effective_color_mode()
        is_dark = current_mode == "dark"

        return {
            "label": f"font-size: 16px; color: {'#ffffff' if is_dark else '#333333'};",
            "title": f"font-size: 24px; font-weight: bold; color: {'#ffffff' if is_dark else '#000000'};",
            "provider_title": f"font-size: 18px; font-weight: bold; color: {'#ffffff' if is_dark else '#000000'};",
            "input": f"""
                font-size: 16px;
                padding: 5px;
                background-color: {"#444" if is_dark else "white"};
                color: {"#ffffff" if is_dark else "#000000"};
                border: 1px solid {"#666" if is_dark else "#ccc"};
            """,
            "dropdown": f"""
                font-size: 16px;
                padding: 5px;
                background-color: {"#444" if is_dark else "white"};
                color: {"#ffffff" if is_dark else "#000000"};
                border: 1px solid {"#666" if is_dark else "#ccc"};
            """,
            "radio": f"color: {'#ffffff' if is_dark else '#333333'};",
            "button": f"""
                QPushButton {{
                    background-color: {"#444" if is_dark else "#f0f0f0"};
                    color: {"#ffffff" if is_dark else "#000000"};
                    border: 1px solid {"#666" if is_dark else "#ccc"};
                    border-radius: 5px;
                    padding: 8px;
                    font-size: 14px;
                }}
                QPushButton:hover {{
                    background-color: {"#555" if is_dark else "#e0e0e0"};
                }}
            """,
            "action_button": """
                QPushButton {
                    background-color: #4CAF50;
                    color: white;
                    padding: 10px;
                    font-size: 16px;
                    border: none;
                    border-radius: 5px;
                }
                QPushButton:hover {
                    background-color: #45a049;
                }
            """,
        }


class ThemeAwareMixin:
    """Mixin to make a widget theme change aware."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        theme_manager.register_widget(self)
        # Connect the theme change signal
        theme_manager.theme_changed.connect(self._on_theme_changed)

    def _on_theme_changed(self):
        """Automatically called when the theme changes."""
        # Call refresh_theme if the method exists in the derived class
        refresh_theme_method = getattr(self, "refresh_theme", None)
        if refresh_theme_method and callable(refresh_theme_method):
            refresh_theme_method()

    def get_styles(self):
        """Shortcut to get current styles."""
        return ThemeManager.get_styles()

    def closeEvent(self, event):
        """Unregister the widget when it closes."""
        theme_manager.unregister_widget(self)
        # Safely call parent's closeEvent if it exists
        parent_close = getattr(super(), "closeEvent", None)
        if parent_close:
            parent_close(event)
        else:
            event.accept()


# Global instance
theme_manager = ThemeManager()
