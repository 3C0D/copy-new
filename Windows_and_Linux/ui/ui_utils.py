import os
import sys
from pathlib import Path

import darkdetect
from PySide6 import QtCore, QtGui
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLayout, QVBoxLayout, QWidget

colorMode = "dark" if darkdetect.isDark() else "light"


def get_effective_color_mode() -> str:
    """
    Get the effective color mode based on current settings.
    This function provides the same logic as _get_effective_mode() in windows.
    """
    # Check if colorMode has been overridden by theme_override first
    global colorMode

    # Simple fallback to global colorMode to avoid creating multiple SettingsManager instances
    # The global colorMode is set by the main app and should be sufficient for UI styling
    return colorMode


def set_color_mode(theme: str) -> None:
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


def get_icon_path(icon_name: str, with_theme: bool = True) -> Path:
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
        base_dir = Path(sys.executable).parent
    else:
        # Handle different script execution contexts
        if sys.argv[0] in ["-c", ""]:
            # Running with python -c or similar, use current working directory
            base_dir = Path.cwd()
        else:
            # base_dir = Path(sys.argv[0]).parent.resolve()
            base_dir = Path(sys.argv[0]).parent
        # # If we're in the Windows_and_Linux subdirectory, go up one level
        # if base_dir.name == "Windows_and_Linux":
        #     base_dir = base_dir.parent

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
    if getattr(sys, "frozen", False):
        # For frozen builds
        base_paths = [
            base_dir / "icons",  # Next to exe
            base_dir / "config" / "icons",  # Config next to exe
        ]
    else:
        # For dev mode
        base_paths = [
            base_dir / "icons",  # Build location (dist/dev/icons/)
            base_dir / "config" / "icons",  # Dev location
            base_dir / "Windows_and_Linux" / "config" / "icons",  # Root project location
            base_dir / "Windows_and_Linux" / "dist" / "dev" / "icons",  # Dev build location
        ]

    # Check all combinations of paths and filenames
    for base_path in base_paths:
        for filename in filenames:
            full_path = base_path / filename
            if full_path.exists():
                return full_path

    return Path()


class ui_utils:
    @classmethod
    def clear_layout(cls, layout: QLayout) -> None:
        """
        Clear the layout of all widgets.
        """
        while (child := layout.takeAt(0)) is not None:
            # If the child is a layout, delete it
            if child.layout():
                cls.clear_layout(child.layout())
                child.layout().deleteLater()
            else:
                child.widget().deleteLater()

    @classmethod
    def resize_and_round_image(
        cls, image: QImage, image_size: int = 100, rounding_amount: int = 50
    ) -> QPixmap:
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
        self._theme_aware = False

        # Theme management integration
        self._register_for_theme_changes()

    def setup_window_and_layout(self) -> None:
        # Configure window flags for standard minimize/close/title behavior
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowType.WindowSystemMenuHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
            | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )

        # Set window icon
        icon_path = get_icon_path("app_icon", with_theme=False)
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(icon_path.as_posix()))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        self.background = ThemeBackground(self, "gradient")
        main_layout.addWidget(self.background)

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:  # pyright: ignore[reportIncompatibleMethodOverride]
        """Handle key press events with common shortcuts for all windows."""
        if event.key() == QtCore.Qt.Key.Key_Escape:
            self.close()
        else:
            super().keyPressEvent(event)

    def clean_TitleBar(self) -> None:
        """Clean title bar. Hide title and set transparent icon."""
        self.setWindowTitle(" ")  # Hidden title "python"
        self.set_transparent_icon()

    def set_transparent_icon(self) -> None:
        """Set a transparent window icon."""
        pixmap = QtGui.QPixmap(32, 32)
        pixmap.fill(QtCore.Qt.GlobalColor.transparent)
        self.setWindowIcon(QtGui.QIcon(pixmap))

    def center_on_screen(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        self.move(x, y)

    def get_dropdown_style(self) -> str:
        """Get standardized dropdown styling based on current theme."""
        current_mode = get_effective_color_mode()
        if current_mode == "dark":
            return """
                QComboBox {
                    background-color: #444;
                    color: #ffffff;
                    border: 1px solid #666;
                    padding: 5px;
                    font-size: 16px;
                }
                QComboBox QAbstractItemView {
                    background-color: #444;
                    color: #ffffff;
                    selection-background-color: #666;
                }
            """
        else:
            return """
                QComboBox {
                    background-color: white;
                    color: #000000;
                    border: 1px solid #ccc;
                    padding: 5px;
                    font-size: 16px;
                }
                QComboBox QAbstractItemView {
                    background-color: white;
                    color: #000000;
                    selection-background-color: #e0e0e0;
                }
            """

    def get_input_style(self) -> str:
        """Get standardized input field styling based on current theme."""
        current_mode = get_effective_color_mode()
        return f"""
            font-size: 16px;
            padding: 5px;
            background-color: {"#444" if current_mode == "dark" else "white"};
            color: {"#ffffff" if current_mode == "dark" else "#000000"};
            border: 1px solid {"#666" if current_mode == "dark" else "#ccc"};
        """

    def get_radio_style(self) -> str:
        """Get standardized radio button styling based on current theme."""
        current_mode = get_effective_color_mode()
        return f"color: {'#ffffff' if current_mode == 'dark' else '#333333'}; font-size: 16px;"

    def get_label_style(self) -> str:
        """Get standardized label styling based on current theme."""
        current_mode = get_effective_color_mode()
        color = "#ffffff" if current_mode == "dark" else "#333333"
        style = f"font-size: 16px; color: {color};"
        return style

    def get_checkbox_style(self) -> str:
        """Get standardized checkbox styling based on current theme."""
        current_mode = get_effective_color_mode()
        if current_mode == "dark":
            # En mode dark, garder le style original (juste le texte)
            return "color: #ffffff; font-size: 16px;"
        else:
            # En mode light, améliorer la visibilité des indicateurs
            return """
                QCheckBox {
                    color: #333333;
                    font-size: 16px;
                    spacing: 8px;
                }
                QCheckBox::indicator {
                    width: 13px;
                    height: 13px;
                    border-radius: 2px;
                }
                QCheckBox::indicator:unchecked {
                    border: 2px solid #666666;
                    background-color: white;
                }
                QCheckBox::indicator:checked {
                    border: 2px solid #666666;
                    background-color: #666666;
                    image: url(data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iOSIgaGVpZ2h0PSI5IiB2aWV3Qm94PSIwIDAgOSA5IiBmaWxsPSJub25lIiB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciPgo8cGF0aCBkPSJNNy41IDIuNUwzLjc1IDYuMjVMMi41IDUiIHN0cm9rZT0id2hpdGUiIHN0cm9rZS13aWR0aD0iMS4yIiBzdHJva2UtbGluZWNhcD0icm91bmQiIHN0cm9rZS1saW5lam9pbj0icm91bmQiLz4KPC9zdmc+Cg==);
                }
            """

    def _register_for_theme_changes(self) -> None:
        """Register this widget for theme change notifications."""
        try:
            from ui.ThemeManager import theme_manager

            theme_manager.register_widget(self)
            theme_manager.theme_changed.connect(self._on_theme_changed)
        except ImportError:
            # ThemeManager not available, skip registration
            pass

    def _on_theme_changed(self) -> None:
        """Automatically called when the theme changes."""
        refresh_theme_method = getattr(self, "refresh_theme", None)
        if refresh_theme_method and callable(refresh_theme_method):
            refresh_theme_method()

    def get_theme_styles(self) -> dict[str, str]:
        """Get current theme styles as a shortcut."""
        try:
            from ui.ThemeManager import theme_manager

            return theme_manager.get_styles()
        except ImportError:
            return {}

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event and unregister from theme manager."""
        try:
            from ui.ThemeManager import theme_manager

            theme_manager.unregister_widget(self)
        except ImportError:
            pass
        super().closeEvent(event)


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

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
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
                # Handle different script execution contexts
                if sys.argv[0] in ["-c", ""]:
                    # Running with python -c or similar, use current working directory
                    base_dir = os.getcwd()
                else:
                    base_dir = os.path.dirname(os.path.abspath(sys.argv[0]))

                # If we're in the Windows_and_Linux subdirectory, go up one level
                if os.path.basename(base_dir) == "Windows_and_Linux":
                    base_dir = os.path.dirname(base_dir)

            current_mode = get_effective_color_mode()
            if self.is_popup:
                bg_file = (
                    "background_popup_dark.png"
                    if current_mode == "dark"
                    else "background_popup.png"
                )
            else:
                bg_file = "background_dark.png" if current_mode == "dark" else "background.png"

            # Try multiple locations for background files
            possible_paths = [
                os.path.join(base_dir, bg_file),  # Build location (dist/)
                os.path.join(base_dir, "config", "backgrounds", bg_file),  # Dev location
                os.path.join(
                    base_dir, "Windows_and_Linux", "config", "backgrounds", bg_file
                ),  # Root project location
                os.path.join(
                    base_dir, "Windows_and_Linux", "dist", "dev", bg_file
                ),  # Dev build location
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
                    QtGui.QColor(50, 50, 50)
                    if current_mode == "dark"
                    else QtGui.QColor(240, 240, 240),
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
                color = QtGui.QColor(
                    255, 255, 255
                )  # Light mode color - pure white for better contrast
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
