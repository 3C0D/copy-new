"""
refresh_manager.py

Unified refresh logic for theme and language updates.
"""

from collections.abc import Callable

from PySide6.QtWidgets import QWidget


class RefreshManager:
    """Manages refresh operations for UI components."""

    @staticmethod
    def refresh_theme(widgets_dict: dict[str, list[QWidget]], app_styles: dict[str, str]) -> None:
        """
        Apply stylesheets to widgets when theme changes.

        Args:
            widgets_dict: Widgets grouped by style type.
                         Example: {'label': [label1, label2], 'dropdown': [dropdown1]}
            app_styles: Stylesheet dictionary from theme_manager.
                       Example: {'label': 'QLabel { color: white; }', ...}
        """
        for style_key, widgets in widgets_dict.items():
            for widget in widgets:
                if widget:
                    widget.setStyleSheet(app_styles[style_key])

    @staticmethod
    def refresh_language(
        components: list[tuple],
        color_mode_dropdown,
        color_mode: str,
        translator_func: Callable[[str], str],
    ) -> None:
        """
        Update UI text when language changes.

        Args:
            components: List of (widget, text_getter) pairs.
                       text_getter can be a callable or a string key.
            color_mode_dropdown: Color mode QComboBox to repopulate.
            color_mode: Current mode ('auto'/'light'/'dark') to restore selection.
            translator_func: Translation function (typically _()).
        """
        # Block signals during refresh
        if color_mode_dropdown:
            color_mode_dropdown.blockSignals(True)

        try:
            # Update component texts
            for widget, text_getter in components:
                if widget:
                    if callable(text_getter):
                        widget.setText(text_getter())
                    else:
                        widget.setText(translator_func(text_getter))

            # Update color mode dropdown
            if color_mode_dropdown:
                color_mode_dropdown.clear()
                color_mode_dropdown.addItems(
                    [translator_func("Auto"), translator_func("Light"), translator_func("Dark")]
                )
                # Restore current selection
                mode_index = {"auto": 0, "light": 1, "dark": 2}.get(color_mode, 0)
                color_mode_dropdown.setCurrentIndex(mode_index)

        finally:
            # Always restore signals
            if color_mode_dropdown:
                color_mode_dropdown.blockSignals(False)
