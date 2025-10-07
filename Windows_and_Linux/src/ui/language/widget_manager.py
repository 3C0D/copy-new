"""
Widget management for language updates.
"""

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


class WidgetManager:
    """Manages registered widgets for language updates."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app
        self._registered_widgets = []

    def register_widget(self, widget: Any) -> None:
        """Register a widget to receive language updates."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget: Any) -> None:
        """Unregister a widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def refresh_registered_widgets(self) -> None:
        """Refresh all registered widgets."""
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_language"):
                try:
                    widget.refresh_language()
                except RuntimeError:
                    # Widget destroyed, remove it from the list
                    self._registered_widgets.remove(widget)
