J'ai demandé à opus qui est actuellement le meilleur LLM D'adapter le code pour remonter à la logique concernant le changement de background Vers ThemedWidget. Tu vas appliquer la logique préconisée par opus.



Je comprends votre besoin. Vous voulez remonter la logique de changement de thème de background (gradient/plain) dans la classe mère ThemedWidget, similaire à ce qui est déjà fait pour le color mode. Voici comment refactoriser le code :

# ui/utils.py - Refactored ThemedWidget

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

        # Get current theme from settings if available
        current_theme = self._get_current_background_theme()
        self.background = ThemeBackground(self, current_theme)
        main_layout.addWidget(self.background)

    def _get_current_background_theme(self) -> str:
        """Get the current background theme from settings."""
        # Try to get from app settings manager if available
        try:
            if hasattr(self, 'app') and hasattr(self.app, 'settings_manager'):
                return self.app.settings_manager.theme or "gradient"
        except:
            pass
        return "gradient"  # Default

    def change_background_theme(self, theme: str) -> None:
        """
        Change the background theme (gradient/plain).
        This method can be called by child classes or externally.
        """
        if self.background is not None:
            self.background.theme = theme
            self.background.update()
    
    def auto_save_theme(self, theme: str) -> None:
        """
        Auto-save and apply theme changes.
        This method should be overridden by child classes if they need custom save logic.
        """
        # Apply theme change immediately
        self.change_background_theme(theme)
        
        # Save to settings if available
        if hasattr(self, 'app') and hasattr(self.app, 'settings_manager'):
            self.app.settings_manager.theme = theme
            self.app.settings_manager.save()

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
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

    def refresh_theme(self) -> None:
        """
        Called when theme changes. Override in child classes for specific refresh logic.
        Base implementation just updates background if needed.
        """
        if self.background:
            self.background.update()

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


-----

SettingsWindow.py

# SettingsWindow.py - Simplified version using parent class methods

class SettingsWindow(ThemedWidget):
    """
    The settings window for the application.
    Now with scrolling support for better usability on smaller screens.
    """

    close_signal = QtCore.Signal()

    def __init__(self, app: "WritingToolApp", providers_only: bool = False):
        # Store app reference before calling parent init
        self.app = app
        super().__init__()  # This will call setup_window_and_layout which needs self.app
        
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
            
            # Get current theme from settings
            current_theme = self.app.settings_manager.theme or "gradient"
            self.gradient_radio.setChecked(current_theme == "gradient")
            self.plain_radio.setChecked(current_theme == "plain")
            
            # Connect to the simplified handler
            self.gradient_radio.toggled.connect(self._on_theme_radio_changed)
            self.plain_radio.toggled.connect(self._on_theme_radio_changed)
            
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

    def _on_theme_radio_changed(self) -> None:
        """Handle theme radio button changes."""
        if self.gradient_radio is not None and not self.providers_only:
            theme = "gradient" if self.gradient_radio.isChecked() else "plain"
            # Use parent class method for theme change
            self.auto_save_theme(theme)

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
        """Override parent refresh_theme to use our custom refresh logic."""
        self._refresh_ui_styles()


-------------


# ThemeManager.py - Enhanced version with background theme management

class ThemeManager(QtCore.QObject):
    """Centralized theme manager with signals to notify changes."""

    # Signal emitted when the color mode changes
    theme_changed = QtCore.Signal(str)  # Emits the new mode (dark/light)
    
    # Signal emitted when the background theme changes
    background_theme_changed = QtCore.Signal(str)  # Emits the new background theme (gradient/plain)

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
        """Change the color mode and notify all registered widgets."""
        set_color_mode(new_mode)
        current_mode = get_effective_color_mode()
        self.theme_changed.emit(current_mode)

        # Refresh all registered widgets
        self._refresh_all_widgets()
    
    def change_background_theme(self, new_theme: str) -> None:
        """Change the background theme (gradient/plain) and notify all registered widgets."""
        self.background_theme_changed.emit(new_theme)
        
        # Update background for all registered widgets
        for widget in self._registered_widgets[:]:  # Copy to avoid modifications during iteration
            try:
                if hasattr(widget, "change_background_theme"):
                    widget.change_background_theme(new_theme)
                elif hasattr(widget, "background") and widget.background:
                    # Direct update if widget has background but no method
                    widget.background.theme = new_theme
                    widget.background.update()
            except RuntimeError:
                # Widget destroyed, remove it from the list
                self._registered_widgets.remove(widget)
    
    def _refresh_all_widgets(self) -> None:
        """Refresh all registered widgets."""
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
            """,
            "radio": f"color: {'#ffffff' if is_dark else '#333333'}; font-size: 16px;",
            "checkbox_dark": "color: #ffffff; font-size: 16px;",
            "checkbox_light": """
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
            """,
        }

# Create a global instance
theme_manager = ThemeManager()


---

class HelpWindow(ThemedWidget):
    """
    The help window for the application.
    """

    min_width: int
    min_height: int
    content_layout: QVBoxLayout

    def __init__(self) -> None:
        super().__init__()
        self.min_width = 600
        self.min_height = 750
        self.init_ui()

    def init_ui(self) -> None:
        """Initialize the user interface for the help window."""
        self._setup_window()
        self._create_layout()
        self._load_content()

    def _setup_window(self) -> None:
        """Configure window properties and positioning."""
        self.setWindowTitle(" ")  # Hidden title for clean look
        self.setMinimumSize(self.min_width, self.min_height)

        # Center window on screen
        self._center_on_screen()

        # Note: Window flags are handled by ThemedWidget

        self.set_transparent_icon()

    def _center_on_screen(self) -> None:
        """Center the window on the primary screen."""
        screen = QApplication.primaryScreen().geometry()
        window_rect = self.geometry()
        x = (screen.width() - window_rect.width()) // 2
        y = (screen.height() - window_rect.height()) // 2
        self.move(x, y)

    def _create_layout(self) -> None:
        """Create the main layout structure."""
        self.content_layout = QVBoxLayout(self.background)
        self.content_layout.setContentsMargins(30, 30, 30, 30)
        self.content_layout.setSpacing(20)

    def _load_content(self) -> None:
        """Load and display the help content."""
        # Title
        self.title_label: QLabel = self._create_title_label()
        self.content_layout.addWidget(self.title_label, alignment=QtCore.Qt.AlignmentFlag.AlignCenter)

        # Scrollable main content
        help_content: str = self._get_help_content()
        self.scroll_area: QScrollArea = self._create_scrollable_content(help_content)
        self.content_layout.addWidget(self.scroll_area)

    def _create_title_label(self) -> QLabel:
        """Create the main title label."""
        title_label = QLabel(_("Writing Tools Help"))
        title_label.setStyleSheet(self._get_title_style())
        return title_label

    def _get_title_style(self) -> str:
        """Get the title styling based on current theme."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        color = "#ffffff" if current_mode == "dark" else "#333333"
        return f"font-size: 24px; font-weight: bold; color: {color};"

    def _get_help_content(self) -> str:
        """Get the formatted help content HTML."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        text_color = "#f0f0f0" if current_mode == "dark" else "#333333"
        bg_color = "transparent"
        highlight_bg = (
            "rgba(76, 175, 80, 0.2)" if current_mode == "dark" else "rgba(76, 175, 80, 0.1)"
        )
        border_color = "#555555" if current_mode == "dark" else "#dddddd"

        return f"""
        <div style='text-align: left; line-height: 1.6; color: {text_color}; background-color: {bg_color};'>
            <h2 style='color: {text_color};'>🎯 {_("How to Use Writing Tools")}</h2>

            <h3 style='color: {text_color};'> 🖼️\u00a0 {_("Image Processing Priority")}</h3>
            <p><strong>{_("Clipboard Images:")}</strong> {_("When an image is in your clipboard, it takes priority over selected text. Press Ctrl+Space to open a prompt window for image analysis (OCR, translation, description, etc.).")}</p>
            <p><strong>{_("Screenshot Workflow:")}</strong> {_("Take a screenshot (Ctrl+Shift+S or Print Screen) → Image copied to clipboard → Ctrl+Space → Enter prompt → Chat window opens with AI response → Continue discussion about the image.")}</p>
            <p><strong>{_("Clipboard Management:")}</strong> <b>{_("Once you validate the prompt and enter chat mode, the image is cleared from clipboard to prevent accidental reuse. If you cancel the prompt, the image remains in clipboard.")}</b></p>

            <h3 style='color: {text_color};'>📝 {_("Text Selection & Interaction Modes")}</h3>
            <p><strong>{_("When no image in clipboard:")}</strong> {_("With no image in clipboard, text selection works with two interaction paths:")}</p>

            <div style='margin-left: 20px; margin-bottom: 15px;'>
                <h4 style='color: {text_color};'>🎯 {_("Manual Prompt Input")}</h4>
                <p>{_("Type your custom prompt in the text area → Choose behavior:")}</p>
                <ul style='margin-left: 20px;'>
                    <li><strong>{_("Chat Mode:")}</strong> {_("Click Force Chat or use Ctrl+Enter to open chat window")}</li>
                    <li><strong>{_("Replace Text:")}</strong> {_("Press Enter to replace selected text (editable text only)")}</li>
                </ul>
            </div>

            <div style='margin-left: 20px; margin-bottom: 15px;'>
                <h4 style='color: {text_color};'>⚡ {_("Predefined Action Buttons")}</h4>
                <p>{_("Click action buttons with predefined prompts → Behavior indicated by icons:")}</p>
                <ul style='margin-left: 20px;'>
                    <li><strong>💬 C</strong> {_("(Chat icon) → Opens chat window regardless of text type")}</li>
                    <li><strong>🔄 R</strong> {_("(Replace icon) → Replaces editable text, opens modal for non-editable text")}</li>
                </ul>
                <p><em>{_("Icons show default behavior when Force Chat is not active")}</em></p>
            </div>

            <div style='margin-left: 20px;'>
                <h4 style='color: {text_color};'>📋 {_("Text Type Behavior")}</h4>
                <ul style='margin-left: 20px;'>
                    <li><strong>{_("Editable Text:")}</strong> {_("Can be replaced or opened in chat mode")}</li>
                    <li><strong>{_("Non-Editable Text:")}</strong> {_("Always opens in modal window without modifying original")}</li>
                    <li><strong>{_("No Selection:")}</strong> {_("Opens prompt that directly enters chat mode")}</li>
                </ul>
            </div>

            <h3 style='color: {text_color};'>💬 {_("Force Chat Mode")}</h3>
            <p><strong>{_("Force Chat Button:")}</strong> {_("Overrides default behavior to always open chat mode")}</p>
            <p><strong>{_("Lockable Mode:")}</strong> {_("Keep Force Chat permanently active for sensitive editable text")}</p>

            <h3 style='color: {text_color};'>⚙️ {_("Settings & Configuration")}</h3>
            <p><strong>{_("Interface Settings:")}</strong> {_("Customize appearance, themes, and window behavior")}</p>
            <p><strong>{_("Global Shortcut:")}</strong> {_("Set your preferred keyboard shortcut (default: Ctrl+Space)")}</p>
            <p><strong>{_("LLM Selection:")}</strong> {_("Choose from available AI models. Models marked with ⭐ support image processing across all providers")}</p>

            <h4 style='color: {text_color};'>🔧 {_("Ollama Integration")}</h4>
            <p><strong>{_("Installation:")}</strong> {_("Writing Tools can install Ollama automatically, opening chat interface immediately")}</p>
            <p><strong>{_("Model Testing:")}</strong> {_("Click models in chat interface to test and install directly")}</p>
            <p><strong>{_("Model Management:")}</strong> {_("Installed models appear immediately in settings dropdown")}</p>

            <h3 style='color: {text_color};'>🎛️ {_("Systray/Settings")}</h3>
            <p><strong>{_("System Tray Menu:")}</strong> {_("Right-click icon for quick access to settings, help, and mode toggles")}</p>

            <div style='margin-top: 30px; padding: 15px; background: {highlight_bg}; border: 1px solid {border_color}; border-radius: 8px;'>
                <strong style='color: {text_color};'>💡 {_("Quick Reference:")}</strong><br>
                <div style='display: flex; justify-content: space-between; margin-top: 10px; color: {text_color};'>
                    <div>
                        <strong>{_("Flow:")}</strong><br>
                         🖼️\u00a0 Image → Ctrl+Space → Prompt → Chat<br>
                        📝 Text → Ctrl+Space → Manual/Action → Chat/Replace<br>
                        ❌ Cancel → Clipboard preserved<br>
                        ✅ Validate → Clipboard cleared
                    </div>
                    <div>
                        <strong>{_("Icons:")}</strong><br>
                        💬 C = Chat mode<br>
                        🔄 R = Replace mode<br>
                        ⭐ = Image support
                    </div>
                </div>
            </div>
        </div>
        """

    def _get_scroll_style(self) -> str:
        """Get the scrollbar styling based on current theme."""
        from ui.ui_utils import get_effective_color_mode

        current_mode = get_effective_color_mode()
        if current_mode == "dark":
            handle_color = "rgba(255, 255, 255, 0.3)"
        else:
            handle_color = "rgba(0, 0, 0, 0.3)"

        return f"""
        QScrollArea {{
            background: transparent;
            border: none;
        }}
        QScrollBar:vertical {{
            background: transparent;
            width: 10px;
        }}
        QScrollBar::handle:vertical {{
            background: {handle_color};
            border-radius: 5px;
        }}
        """

    def _create_scrollable_content(self, content: str) -> QScrollArea:
        """Create a scrollable area for the content."""
        scroll_area = QScrollArea()
        scroll_area.setWidgetResizable(True)
        scroll_area.setFrameShape(QFrame.Shape.NoFrame)
        scroll_area.setStyleSheet(self._get_scroll_style())

        self.content_widget = QLabel(content)
        self.content_widget.setWordWrap(True)
        self.content_widget.setOpenExternalLinks(True)
        self.content_widget.setStyleSheet("""
            QLabel {
                background: transparent;
                padding: 10px;
                font-size: 14px;
            }
        """)

        scroll_area.setWidget(self.content_widget)
        return scroll_