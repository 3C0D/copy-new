import os
import sys

import darkdetect
from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtWidgets import QWidget
from PySide6.QtGui import QImage, QPixmap

colorMode = "dark" if darkdetect.isDark() else "light"


def get_effective_color_mode():
    """
    Get the effective color mode based on current settings.
    This function provides the same logic as _get_effective_mode() in windows.
    """
    # Check if colorMode has been overridden by theme_override first
    global colorMode

    # Simple fallback to global colorMode to avoid creating multiple SettingsManager instances
    # The global colorMode is set by the main app and should be sufficient for UI styling
    return colorMode


def set_color_mode(theme):
    """
    Set the color mode globally, overriding auto-detection.

    Args:
        theme: "light", "dark", or "auto"
    """
    global colorMode
    if theme == "auto":
        colorMode = "dark" if darkdetect.isDark() else "light"
    else:
        colorMode = theme


def get_icon_path(icon_name, with_theme=True) -> str:
    """
    Get the correct path for an icon, handling both dev and build modes.
    Supports both PNG and SVG formats, with SVG taking precedence.

    Args:
        icon_name: Name of the icon without extension (e.g., "send", "app_icon", "copy_md")
        with_theme: Whether to append theme suffix (_dark/_light)

    Returns:
        Path to the icon file
    """
    # Use sys.executable for frozen apps, sys.argv[0] for scripts
    if getattr(sys, "frozen", False):
        base_dir = os.path.dirname(sys.executable)
    else:
        base_dir = os.path.dirname(sys.argv[0])

    # Define possible extensions and filenames
    extensions = [".svg", ".png"]  # SVG takes precedence

    if with_theme:
        current_mode = get_effective_color_mode()
        theme_suffix = "_dark" if current_mode == "dark" else "_light"
        filenames = [f"{icon_name}{theme_suffix}{ext}" for ext in extensions]
        # Fallback to non-themed version if themed version doesn't exist
        filenames.extend([f"{icon_name}{ext}" for ext in extensions])
    else:
        filenames = [f"{icon_name}{ext}" for ext in extensions]

    # Try multiple locations
    base_paths = [
        os.path.join(base_dir, "icons"),  # Build location (dist/dev/icons/)
        os.path.join(base_dir, "config", "icons"),  # Dev location
    ]

    # Check all combinations of paths and filenames
    for base_path in base_paths:
        for filename in filenames:
            full_path = os.path.join(base_path, filename)
            if os.path.exists(full_path):
                return full_path

    return ""


class ui_utils:
    @classmethod
    def clear_layout(cls, layout):
        """
        Clear the layout of all widgets.
        """
        while (child := layout.takeAt(0)) != None:
            # If the child is a layout, delete it
            if child.layout():
                cls.clear_layout(child.layout())
                child.layout().deleteLater()
            else:
                child.widget().deleteLater()

    @classmethod
    def resize_and_round_image(cls, image, image_size=100, rounding_amount=50):
        image = image.scaledToWidth(image_size)
        clipPath = QtGui.QPainterPath()
        clipPath.addRoundedRect(
            0,
            0,
            image_size,
            image_size,
            rounding_amount,
            rounding_amount,
        )
        target = QImage(image_size, image_size, QImage.Format.Format_ARGB32)
        target.fill(QtCore.Qt.GlobalColor.transparent)
        painter = QtGui.QPainter(target)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing)
        painter.setClipPath(clipPath)
        painter.drawImage(0, 0, image)
        painter.end()
        targetPixmap = QPixmap.fromImage(target)
        return targetPixmap


class ThemedWidget(QWidget):
    def __init__(self):
        super().__init__()
        self.setup_window_and_layout()

    def setup_window_and_layout(self):
        # Set window icon
        icon_path = get_icon_path("app_icon", with_theme=False)
        if os.path.exists(icon_path):
            self.setWindowIcon(QtGui.QIcon(icon_path))

        main_layout = QtWidgets.QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background = ThemeBackground(self, "gradient")
        main_layout.addWidget(self.background)

    def add_minimize_button(self):
        """Add minimize button to the window."""
        self.setWindowFlags(self.windowFlags() | QtCore.Qt.WindowType.WindowMinimizeButtonHint)

    def get_dropdown_style(self):
        """Get standardized dropdown styling based on current theme."""
        current_mode = get_effective_color_mode()
        return f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if current_mode == 'dark' else 'white'};
            color: {'#ffffff' if current_mode == 'dark' else '#000000'};
            border: 1px solid {'#666' if current_mode == 'dark' else '#ccc'};
        """

    def get_input_style(self):
        """Get standardized input field styling based on current theme."""
        current_mode = get_effective_color_mode()
        return f"""
            font-size: 16px;
            padding: 5px;
            background-color: {'#444' if current_mode == 'dark' else 'white'};
            color: {'#ffffff' if current_mode == 'dark' else '#000000'};
            border: 1px solid {'#666' if current_mode == 'dark' else '#ccc'};
        """

    def get_radio_style(self):
        """Get standardized radio button styling based on current theme."""
        current_mode = get_effective_color_mode()
        return f"color: {'#ffffff' if current_mode == 'dark' else '#333333'};"

    def get_label_style(self):
        """Get standardized label styling based on current theme."""
        current_mode = get_effective_color_mode()
        color = '#ffffff' if current_mode == 'dark' else '#333333'
        style = f"font-size: 16px; color: {color};"
        return style


class ThemeBackground(QWidget):
    """
    A custom widget that creates a background for the application based on the selected theme.
    """

    def __init__(self, parent=None, theme="gradient", is_popup=False, border_radius=0):
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.theme = theme
        self.is_popup = is_popup
        self.border_radius = border_radius

    def paintEvent(self, event):
        """
        Override the paint event to draw the background based on the selected theme.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        if self.theme == "gradient":
            # Determine background file paths (check multiple locations)
            if getattr(sys, "frozen", False):
                base_dir = os.path.dirname(sys.executable)
            else:
                base_dir = os.path.dirname(sys.argv[0])

            current_mode = get_effective_color_mode()
            if self.is_popup:
                bg_file = "background_popup_dark.png" if current_mode == "dark" else "background_popup.png"
            else:
                bg_file = "background_dark.png" if current_mode == "dark" else "background.png"

            # Try multiple locations for background files
            possible_paths = [
                os.path.join(base_dir, bg_file),  # Build location (dist/)
                os.path.join(
                    base_dir,
                    "config",
                    "backgrounds",
                    bg_file,
                ),  # Dev location
                os.path.join("config", "backgrounds", bg_file),  # Relative dev location
            ]

            background_image = None
            for path in possible_paths:
                if os.path.exists(path):
                    background_image = QtGui.QPixmap(path)
                    break

            if background_image is None:
                # Fallback to a solid color if no background found
                background_image = QtGui.QPixmap(self.width(), self.height())
                current_mode = get_effective_color_mode()
                background_image.fill(
                    QtGui.QColor(50, 50, 50) if current_mode == "dark" else QtGui.QColor(240, 240, 240),
                )
            # Adds a path/border using which the border radius would be drawn
            path = QtGui.QPainterPath()
            path.addRoundedRect(
                0,
                0,
                self.width(),
                self.height(),
                self.border_radius,
                self.border_radius,
            )
            painter.setClipPath(path)

            painter.drawPixmap(self.rect(), background_image)
        else:
            current_mode = get_effective_color_mode()
            if current_mode == "dark":
                color = QtGui.QColor(35, 35, 35)  # Dark mode color
            else:
                color = QtGui.QColor(255, 255, 255)  # Light mode color - pure white for better contrast
            brush = QtGui.QBrush(color)
            painter.setBrush(brush)
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
            pen.setWidth(0)
            painter.setPen(pen)
            painter.drawRoundedRect(
                QtCore.QRect(0, 0, self.width(), self.height()),
                self.border_radius,
                self.border_radius,
            )
