import sys
from pathlib import Path
from typing import TYPE_CHECKING

from PySide6 import QtCore, QtGui
from PySide6.QtGui import QImage, QPixmap
from PySide6.QtWidgets import QApplication, QLayout, QMessageBox, QVBoxLayout, QWidget

if TYPE_CHECKING:
    from ..WritingToolApp import WritingToolApp


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

    @staticmethod
    def show_confirmation_dialog(title: str, message: str, parent=None) -> bool:
        """Show a confirmation dialog and return True if user confirms."""
        confirm = QMessageBox(parent)
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        confirm.setWindowTitle(title)
        confirm.setText(message)
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)

        return confirm.exec_() == QMessageBox.StandardButton.Yes

    @staticmethod
    def existing_window_on_top(window: "QWidget | None"):
        if window is None:
            return

        # window.setWindowState(QtCore.Qt.WindowState.WindowActive) redundant
        window.raise_()
        window.activateWindow()

    @staticmethod
    def get_icon_path(app: "WritingToolApp", icon_name: str, with_theme: bool = True) -> Path:
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
                base_dir = Path(sys.argv[0]).parent

        # Define possible extensions and filenames
        extensions = [".svg", ".png"]  # SVG takes precedence
        if with_theme:
            current_mode = app.settings_manager.color_mode
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
                base_dir / "src" / "config" / "icons",  # Src config next to exe
            ]
        else:
            # For dev mode
            base_paths = [
                base_dir / "icons",  # Build location (dist/dev/icons/)
                base_dir / "config" / "icons",  # Dev location
                base_dir / "src" / "config" / "icons",  # Src config location
                base_dir
                / "Windows_and_Linux"
                / "src"
                / "config"
                / "icons",  # Root project src location
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


class ThemedWidget(QWidget):
    def __init__(self, app: "WritingToolApp"):  # Type hint using forward reference
        super().__init__()
        self.app = app
        self.setup_window_and_layout()
        self._theme_aware = False
        self.min_width = 150
        self.min_height = 150

        # Theme management integration
        self._register_for_theme_changes()

    def _calculate_window_size(self) -> None:
        """
        Calculate and set window size based on min_width and min_height.
        Makes window resizable with minimum constraints.
        Height is limited to 85% of screen height if needed.
        """
        screen = QApplication.primaryScreen().geometry()
        max_height = int(screen.height() * 0.85)

        # Use the smaller of desired height or 85% of screen height
        final_height = min(self.min_height, max_height)

        self.setMinimumSize(self.min_width, final_height)

        # If window would be larger than screen, also set maximum size
        if self.min_height > max_height:
            self.setMaximumHeight(max_height)

    def setup_window_and_layout(self) -> None:
        # Configure window flags for standard minimize/close/title behavior
        self.setWindowFlags(
            self.windowFlags() & ~QtCore.Qt.WindowType.WindowSystemMenuHint
            | QtCore.Qt.WindowType.WindowCloseButtonHint
            | QtCore.Qt.WindowType.WindowMinimizeButtonHint
        )

        # Set window icon
        icon_path = ui_utils.get_icon_path(self.app, "app_icon", with_theme=False)
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(icon_path.as_posix()))

        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)

        # Get current theme from settings if available
        current_background_theme = self.get_current_background_theme()
        self.background = ThemeBackground(self.app, self, current_background_theme)
        main_layout.addWidget(self.background)

    def showEvent(self, event: QtGui.QShowEvent) -> None:
        """Handle window show event to ensure focus."""
        super().showEvent(event)
        ui_utils.existing_window_on_top(self)

    def resizeEvent(self, event: QtGui.QResizeEvent) -> None:
        """Handle window resize events to maintain minimum size."""
        if self.width() < self.min_width or self.height() < self.min_height:
            self.resize(max(self.width(), self.min_width), max(self.height(), self.min_height))

    def get_current_background_theme(self) -> str:
        """Get the current background theme from settings."""
        return self.app.settings_manager.background_theme or "gradient"

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

    def _register_for_theme_changes(self) -> None:
        """Register this widget for theme change notifications."""
        self.app.theme_manager.register_widget(self)
        self.app.theme_manager.color_mode_changed.connect(self._on_color_mode_changed)
        self.app.theme_manager.background_theme_changed.connect(self._on_background_theme_changed)

        # Register for language changes
        self.app.language_manager.register_widget(self)
        self.app.language_manager.language_changed.connect(self._on_language_changed)

    def _on_color_mode_changed(self) -> None:
        """Automatically called when the color mode changes."""
        self.refresh_theme()

    def _on_background_theme_changed(self, style: str) -> None:
        """Automatically called when the background style changes."""
        if self.background is not None:
            self.background.background_theme = style
            self.background.update()

        self.refresh_theme()

    def _on_language_changed(self, language: str) -> None:
        """Automatically called when the language changes."""
        self.refresh_language()

    def refresh_theme(self) -> None:
        """
        Called when theme changes. Override in child classes for specific refresh logic.
        Base implementation just updates background if needed.
        """
        if self.background:
            self.background.update()

    def refresh_language(self) -> None:
        """
        Called when language changes. Override in child classes for specific refresh logic.
        Base implementation does nothing.
        """
        pass

    # not used currently
    def get_theme_styles(self) -> dict[str, str]:
        """Get current theme styles as a shortcut."""
        return self.app.theme_manager.get_styles()

    def closeEvent(self, event: QtGui.QCloseEvent) -> None:
        """Handle window close event and unregister from theme manager."""
        self.app.theme_manager.unregister_widget(self)
        self.app.language_manager.unregister_widget(self)


class ThemeBackground(QWidget):
    """
    A custom widget that creates a background for the application based on the selected background theme.
    """

    def __init__(
        self,
        app: "WritingToolApp",
        parent=None,
        background_theme="gradient",
        is_popup=False,
        border_radius=0,
    ):
        self.app = app
        super().__init__(parent)
        self.setAttribute(QtCore.Qt.WidgetAttribute.WA_StyledBackground, True)
        self.background_theme = background_theme
        self.is_popup = is_popup
        self.border_radius = border_radius

    def paintEvent(self, event: QtGui.QPaintEvent) -> None:
        """
        Override the paint event to draw the background based on the selected background theme.
        """
        painter = QtGui.QPainter(self)
        painter.setRenderHint(QtGui.QPainter.RenderHint.Antialiasing, True)
        painter.setRenderHint(QtGui.QPainter.RenderHint.SmoothPixmapTransform, True)
        if self.background_theme == "gradient":
            # Determine background file paths (check multiple locations)
            if getattr(sys, "frozen", False):
                base_dir = Path(sys.executable).parent
            else:
                # Handle different script execution contexts
                if sys.argv[0] in ["-c", ""]:
                    # Running with python -c or similar, use current working directory
                    base_dir = Path.cwd()
                else:
                    base_dir = Path(sys.argv[0]).resolve().parent

            current_mode = self.app.settings_manager.color_mode

            # Determine background filename
            if self.is_popup:
                bg_file = (
                    "background_popup_dark.png"
                    if current_mode == "dark"
                    else "background_popup.png"
                )
            else:
                bg_file = "background_dark.png" if current_mode == "dark" else "background.png"

            # Define possible paths using Path objects
            possible_paths = [
                base_dir / bg_file,  # Build location (dist/dev or dist/production)
                base_dir / "config" / "backgrounds" / bg_file,  # Dev location
                base_dir / "src" / "config" / "backgrounds" / bg_file,  # Src config location
            ]

            background_image = None
            for path in possible_paths:
                if path.exists():
                    background_image = QtGui.QPixmap(str(path))
                    break

            # Fallback to solid color if no background found
            if background_image is None:
                background_image = QtGui.QPixmap(self.width(), self.height())
                fallback_color = (
                    QtGui.QColor(50, 50, 50)
                    if current_mode == "dark"
                    else QtGui.QColor(240, 240, 240)
                )
                background_image.fill(fallback_color)

            # Create rounded rectangle path for clipping
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
            # Solid color theme
            current_mode = self.app.settings_manager.color_mode
            color = (
                QtGui.QColor(35, 35, 35)
                if current_mode == "dark"  # Dark mode color
                else QtGui.QColor(
                    255, 255, 255
                )  # Light mode color - pure white for better contrast
            )

            brush = QtGui.QBrush(color)
            painter.setBrush(brush)

            # Transparent pen
            pen = QtGui.QPen(QtGui.QColor(0, 0, 0, 0))
            pen.setWidth(0)
            painter.setPen(pen)

            painter.drawRoundedRect(
                QtCore.QRect(0, 0, self.width(), self.height()),
                self.border_radius,
                self.border_radius,
            )
