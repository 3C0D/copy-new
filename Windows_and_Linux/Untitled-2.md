

module ThemeManager.py

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
        self._initialized: bool = True
        self._registered_widgets = []

    def register_widget(self, widget: Any) -> None:
        """Register a widget to receive theme updates."""
        if widget not in self._registered_widgets:
            self._registered_widgets.append(widget)

    def unregister_widget(self, widget: Any) -> None:
        """Unregister a widget."""
        if widget in self._registered_widgets:
            self._registered_widgets.remove(widget)

    def change_theme(self, new_mode: str) -> None:
        """Change the theme and notify all registered widgets."""
        set_color_mode(new_mode)
        current_mode = get_effective_color_mode()
        self.theme_changed.emit(current_mode)

        # Refresh all registered widgets
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            if hasattr(widget, "refresh_theme"):
                try:
                    widget.refresh_theme()
                except RuntimeError:
                    # Widget destroyed, remove it from the list
                    self._registered_widgets.remove(widget)

    @staticmethod
    def get_styles() -> dict[str, str]:
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


module SettingsWindow.py


class SettingsWindow(ThemedWidget):
    """
    The settings window for the application.
    Now with scrolling support for better usability on smaller screens.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolApp", providers_only: bool = False):
        super().__init__()
        self.app = app
        self.current_provider_layout = None
        # Special mode to show only provider settings (during first setup)
        self.providers_only = providers_only

        self.gradient_radio = None
        self.plain_radio = None
        self.color_mode_dropdown = None
        self.provider_dropdown = None
        self.provider_container = None
        self.autostart_checkbox = None
        self.shortcut_input = None
        # Reference to previous window to return to after closing
        self.previous_window = None

        # Store current theme as instance variable for use throughout the class
        self.current_theme = self.app.settings_manager.theme or "gradient"

        # Set the correct theme from saved settings
        if self.background is not None:
            self.background.theme = self.current_theme

        self.init_ui()
        self.retranslate_ui()

    def _get_effective_mode(self) -> str:
        """Get the effective color mode based on user settings."""
        user_mode = self.app.settings_manager.color_mode or "auto"
        if user_mode == "auto":
            import darkdetect

            return "dark" if darkdetect.isDark() else "light"
        return user_mode

    def init_ui(self) -> None:
        """
        Initialize the user interface for the settings window.
        Now includes a scroll area for better handling of content on smaller screens.
        """
        self.setWindowTitle(_("Settings"))
        # Fixed width to maintain consistent layout and provide space for dropdowns
        self.setMinimumWidth(700)
        self.setFixedWidth(700)

        # Show on top initially but allow user to move to background
        self.setWindowState(QtCore.Qt.WindowState.WindowActive)
        self.raise_()  # Bring window to the front
        self.activateWindow()  # Give focus to the window to make it active

        main_layout = QVBoxLayout(self.background)  # Set icon, margin, and spacing in ThemedWidget

        # Create scroll area
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setHorizontalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )
        scroll_area.setVerticalScrollBarPolicy(
            QtCore.Qt.ScrollBarPolicy.ScrollBarAsNeeded,
        )

        # Custom styling for transparent and aesthetic scroll bars
        scroll_area.setStyleSheet(
            """
            QScrollArea {
                background: transparent;
                border: none;
            }
            QScrollArea > QWidget > QWidget {
                background: transparent;
            }
            QScrollBar:vertical {
                background-color: rgba(0, 0, 0, 0.1);
                width: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:vertical {
                background-color: rgba(128, 128, 128, 0.6);
                min-height: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:vertical:hover {
                background-color: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:vertical:pressed {
                background-color: rgba(128, 128, 128, 1.0);
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                height: 0px;
            }
            QScrollBar:horizontal {
                background-color: rgba(0, 0, 0, 0.1);
                height: 12px;
                margin: 0px;
                border-radius: 6px;
            }
            QScrollBar::handle:horizontal {
                background-color: rgba(128, 128, 128, 0.6);
                min-width: 20px;
                border-radius: 6px;
                margin: 2px;
            }
            QScrollBar::handle:horizontal:hover {
                background-color: rgba(128, 128, 128, 0.8);
            }
            QScrollBar::handle:horizontal:pressed {
                background-color: rgba(128, 128, 128, 1.0);
            }
            QScrollBar::add-line:horizontal, QScrollBar::sub-line:horizontal {
                width: 0px;
                background: transparent;
            }
            QScrollBar::add-page:vertical, QScrollBar::sub-page:vertical {
                background: transparent;
            }
        """,
        )

        # Create scrollable content widget with transparent background
        scroll_content = QWidget()
        scroll_content.setStyleSheet("background: transparent;")
        content_layout = QVBoxLayout(scroll_content)
        content_layout.setContentsMargins(30, 30, 30, 30)
        content_layout.setSpacing(20)

        # Full settings window (not provider-only mode)
        if not self.providers_only:
            title_label = QLabel(_("Settings"))
            title_label.setObjectName("title_label")  # For specific styling in refresh
            title_label.setStyleSheet(
                f"font-size: 24px; font-weight: bold; {self.get_label_style()}"
            )
            content_layout.addWidget(
                title_label,
                alignment=QtCore.Qt.AlignmentFlag.AlignCenter,
            )

            # Autostart functionality only for Windows compiled version
            if AutostartManager.get_startup_path():
                self.autostart_checkbox = QCheckBox(_("Start on Boot"))
                self.autostart_checkbox.setStyleSheet(self.get_checkbox_style())

                # Synchronize settings with registry state on startup
                AutostartManager.sync_with_settings(self.app.settings_manager)

                # Set checkbox state from settings (now synchronized)
                self.autostart_checkbox.setChecked(
                    getattr(self.app.settings_manager, "start_on_boot", False)
                )
                self.autostart_checkbox.stateChanged.connect(self.toggle_autostart)
                content_layout.addWidget(self.autostart_checkbox)

            # Global hotkey configuration
            shortcut_label = QLabel(_("Shortcut Key:"))
            shortcut_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(shortcut_label)

            self.shortcut_input = QLineEdit(self.app.settings_manager.hotkey or "ctrl+space")
            self.shortcut_input.setStyleSheet(self.get_input_style())
            # Auto-save when shortcut changes
            self.shortcut_input.textChanged.connect(self.auto_save_shortcut)
            content_layout.addWidget(self.shortcut_input)

            # Background theme selection
            theme_label = QLabel(_("Background Theme:"))
            theme_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(theme_label)

            theme_layout = QHBoxLayout()
            self.gradient_radio = QRadioButton(_("Blurry Gradient"))
            self.plain_radio = QRadioButton(_("Plain"))
            self.gradient_radio.setStyleSheet(self.get_radio_style())
            self.plain_radio.setStyleSheet(self.get_radio_style())
            # Use the instance variable instead of re-reading from settings
            self.gradient_radio.setChecked(self.current_theme == "gradient")
            self.plain_radio.setChecked(self.current_theme == "plain")
            # Auto-save theme changes for immediate visual feedback
            self.gradient_radio.toggled.connect(self.auto_save_theme)
            self.plain_radio.toggled.connect(self.auto_save_theme)
            theme_layout.addWidget(self.gradient_radio)
            theme_layout.addWidget(self.plain_radio)
            content_layout.addLayout(theme_layout)

            # Color mode selection
            color_mode_label = QLabel(_("Color Mode:"))
            color_mode_label.setStyleSheet(self.get_label_style())
            content_layout.addWidget(color_mode_label)

            self.color_mode_dropdown = QComboBox()
            self.color_mode_dropdown.addItems([_("Auto"), _("Light"), _("Dark")])

            # Set current selection based on saved setting
            current_mode = self.app.settings_manager.color_mode or "auto"
            mode_index = {"auto": 0, "light": 1, "dark": 2}.get(current_mode, 0)
            self.color_mode_dropdown.setCurrentIndex(mode_index)

            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

            # Auto-save color mode changes for immediate visual feedback
            self.color_mode_dropdown.currentTextChanged.connect(self.auto_save_color_mode)

            # Prevent wheel scroll from interfering with main scroll area
            self.color_mode_dropdown.wheelEvent = lambda e: e.ignore()

            content_layout.addWidget(self.color_mode_dropdown)


    def auto_save_theme(self) -> None:
        """
        Auto-save theme when it changes for immediate visual feedback.
        """
        if self.gradient_radio is not None and not self.providers_only:
            theme = "gradient" if self.gradient_radio.isChecked() else "plain"
            self.app.settings_manager.theme = theme
            self.app.settings_manager.save()  # Save automatically to disk

            # Apply theme change immediately to the background for live preview
            if self.background is not None:
                self.background.theme = theme
                self.background.update()

    def auto_save_color_mode(self) -> None:
        """
        Auto-save color mode when it changes for immediate visual feedback.
        """
        if self.color_mode_dropdown is not None and not self.providers_only:
            # Get the selected text and convert to internal format
            selected_text = self.color_mode_dropdown.currentText()
            mode_mapping = {_("Auto"): "auto", _("Light"): "light", _("Dark"): "dark"}
            color_mode = mode_mapping.get(selected_text, "auto")

            self.app.settings_manager.color_mode = color_mode
            self.app.settings_manager.save()  # Auto-save to disk

            # Update global colorMode variable
            set_color_mode(color_mode)

            # Apply color mode change immediately via centralized theme manager
            theme_manager.change_theme(color_mode)

            # Refresh UI styles with updated colorMode
            self._refresh_ui_styles()

    def _refresh_ui_styles(self) -> None:
        """Refresh all UI element styles to reflect the current color mode."""
        # Update color mode dropdown style
        if self.color_mode_dropdown:
            self.color_mode_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update provider dropdown style
        if self.provider_dropdown:
            self.provider_dropdown.setStyleSheet(self.get_dropdown_style())

        # Update specific labels with their individual styles
        # Title label
        title_labels = self.findChildren(QLabel)
        for widget in title_labels:
            if widget.text() == _("Settings"):
                widget.setStyleSheet(
                    f"font-size: 24px; font-weight: bold; {self.get_label_style()}"
                )
            elif widget.text() in [
                _("Shortcut Key:"),
                _("Background Theme:"),
                _("Color Mode:"),
                _("Choose AI Provider:"),
            ]:
                widget.setStyleSheet(self.get_label_style())

        # Update provider-specific labels by checking all labels
        for widget in title_labels:
            # Check if this is a provider name (contains provider name text)
            if (
                hasattr(widget, "text")
                and widget.text()
                and any(
                    provider in widget.text()
                    for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"]
                )
            ):
                # Provider title needs high contrast - force pure white/black
                # Use effective mode based on user settings
                current_mode = self._get_effective_mode()
                provider_color = "#ffffff" if current_mode == "dark" else "#000000"
                widget.setStyleSheet(
                    f"font-size: 18px; font-weight: bold; color: {provider_color};"
                )
            # Check if this is a description (longer text, not a simple label)
            elif hasattr(widget, "text") and widget.text() and len(widget.text()) > 50:
                widget.setStyleSheet(f"{self.get_label_style()} text-align: center;")
            # Update all other labels (field labels like "API Base URL", "API Model", etc.)
            elif (
                hasattr(widget, "text")
                and widget.text()
                and widget.text()
                not in [
                    _("Settings"),
                    _("Shortcut Key:"),
                    _("Background Theme:"),
                    _("Color Mode:"),
                    _("Choose AI Provider:"),
                ]
                and len(widget.text()) <= 50
                and not any(
                    provider in widget.text()
                    for provider in ["Ollama", "OpenAI", "Anthropic", "Groq"]
                )
            ):
                # Apply standard label style for field labels
                current_mode = self._get_effective_mode()
                label_color = "#ffffff" if current_mode == "dark" else "#333333"
                widget.setStyleSheet(f"font-size: 16px; color: {label_color};")


        # Update radio buttons if they exist
        if self.gradient_radio:
            radio_style = self.get_radio_style()
            self.gradient_radio.setStyleSheet(radio_style)
            if self.plain_radio:
                self.plain_radio.setStyleSheet(radio_style)

        # Force background update
        if self.background:
            self.background.update()

    def refresh_theme(self) -> None:
        """Automatically called when theme changes via ThemeManager."""
        # Use the old method for now, will be refactored later
        self._refresh_ui_styles()

dans ui.utils.py

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
