"""
Window Sizing Manager - Manages window size calculations and adjustments.
"""

import logging
from typing import TYPE_CHECKING

from PySide6.QtWidgets import QApplication

if TYPE_CHECKING:
    from .response_window import ResponseWindow


def _(x):
    return x


class WindowSizingManager:
    """Manages window sizing calculations and adjustments"""

    def __init__(self):
        self._logger = logging.getLogger(__name__)

    def calculate_and_apply_size(
        self,
        window: "ResponseWindow",
        chat_area,
        input_height: int,
    ) -> None:
        """Calculate and set the ideal window height"""
        # Skip adjustment if window already has a size
        if hasattr(window, "_size_initialized"):
            return

        try:
            # Get content widget height
            if (
                not chat_area
                or not hasattr(chat_area, "content_widget")
                or not chat_area.content_widget
            ):
                return

            content_height = chat_area.content_widget.sizeHint().height()

            # Calculate other UI elements height
            ui_elements_height = (
                window.layout().contentsMargins().top()
                + window.layout().contentsMargins().bottom()
                + input_height
                + window.layout().spacing() * 5
                + 200  # Increased from 185 for taller default height
            )

            # Get screen constraints
            screen = QApplication.screenAt(window.pos())
            if not screen:
                screen = QApplication.primaryScreen()

            # Calculate maximum available height (85% of screen)
            max_height = int(screen.geometry().height() * 0.85)

            # Calculate desired height to show more content initially
            desired_content_height = int(content_height * 0.85)  # Show 85% of content
            desired_total_height = min(
                desired_content_height + ui_elements_height,
                max_height,
            )

            # Set reasonable minimum height - increased by 10%
            final_height = max(600, desired_total_height)  # Increased from 540

            # Set width to 600px
            final_width = 600

            # Update both width and height
            window.resize(final_width, final_height)

            # Center on screen
            frame_geometry = window.frameGeometry()
            screen_center = screen.geometry().center()
            frame_geometry.moveCenter(screen_center)
            window.move(frame_geometry.topLeft())

            # Mark size as initialized
            setattr(window, "_size_initialized", True)

        except Exception as e:
            self._logger.exception(f"Error adjusting window height: {e}")
            window.resize(600, 600)  # Updated fallback size
            setattr(window, "_size_initialized", True)
