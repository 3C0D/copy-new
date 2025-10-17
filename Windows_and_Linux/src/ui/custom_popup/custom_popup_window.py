"""
Writing Tools - CustomPopupWindow module
Used for displaying a custom popup window with various input fields and options.
"""

import logging
from typing import TYPE_CHECKING, Any

from PySide6 import QtCore, QtGui, QtWidgets
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (
    QFrame,
    QHBoxLayout,
    QLabel,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QVBoxLayout,
    QWidget,
)

from ...config.data_operations import (
    create_default_actions_config,
    create_default_image_actions_config,
)
from ...config.interfaces import ActionConfig
from ..custom_popup.button_edit_dialog import ButtonEditDialog
from ..custom_popup.components.button_manager import ButtonManager
from ..custom_popup.components.force_chat_widget import ForceChatWidget
from ..custom_popup.components.image_preview import ImagePreview
from ..custom_popup.components.input_area import InputArea
from ..custom_popup.components.update_notice import UpdateNotice
from ..custom_popup.edit_mode_controller import EditModeController
from ..custom_popup.top_bar_builder import TopBarBuilder
from ..custom_popup.vision_support_validator import VisionSupportValidator
from ..custom_popup.widget_visibility_manager import WidgetVisibilityManager
from ..ui_utils import ThemeBackground, ui_utils

if TYPE_CHECKING:
    from ...writing_tools_app import WritingToolsApp


def _(x):
    return x


class CustomPopupWindow(QWidget):
    def __init__(
        self,
        app: "WritingToolsApp",
        selected_text: str | None = None,
        image: QtGui.QImage | None = None,
    ):
        super().__init__()
        self._logger = logging.getLogger(__name__)
        self.app = app
        self.selected_text: str | None = selected_text
        self.image: QtGui.QImage | None = image
        self.edit_mode = False
        self.has_sel_text = bool(selected_text.strip() if selected_text else False)
        self.has_image = bool(image is not None)

        # Managers/Controllers
        self.visibility_manager = WidgetVisibilityManager(self)
        self.top_bar_builder = TopBarBuilder(self.app, self)
        self.vision_validator = VisionSupportValidator()
        self.edit_controller = EditModeController(self, self.visibility_manager)
        self.button_manager = ButtonManager(self.app, self)

        # UI Components - initialized to None
        self._init_ui_components()

        # Variables for dragging functionality
        self.is_dragging = False
        self.drag_start_position: QtCore.QPoint | None = None

        self.button_widgets: list[Any] = []
        self.input_area: InputArea | None = None
        self.image_preview: ImagePreview | None = None
        self.force_chat_widget: ForceChatWidget | None = None
        self.update_notice: UpdateNotice | None = None
        self.init_ui()

    def _init_ui_components(self) -> None:
        """Initialize all UI component references to None."""
        self.drag_label: QLabel | None = None
        self.edit_button: QPushButton | None = None
        self.reset_button: QPushButton | None = None
        self.edit_close_button: QPushButton | None = None
        self.close_button: QPushButton | None = None
        # Component references - now handled by component classes
        self.top_bar_widget: QWidget | None = None
        self.remove_image_button: QPushButton | None = None
        self.image_preview_container: QWidget | None = None
        self.add_new_button: QPushButton | None = None

    def init_ui(self):
        """Initialize the main UI structure."""
        self.edit_mode = False  # Ensure we start in normal mode
        self._setup_window_properties()
        main_layout = self._create_main_layout()
        content_layout = self._create_background_and_content_layout(main_layout)

        self._create_top_bar(content_layout)
        self._create_input_area(content_layout)
        if self.has_sel_text:
            self.force_chat_widget = ForceChatWidget(self.app)
            self.force_chat_widget.connect_signals(
                self.force_chat_widget.on_force_chat_toggled,
                self.force_chat_widget.on_force_chat_lock_toggled,
            )
            content_layout.addWidget(self.force_chat_widget)
            if self.edit_mode:
                self.force_chat_widget.hide()
        if self.has_sel_text or self.has_image:
            buttons_layout = self._create_buttons_scroll_layout(content_layout)
            self._setup_buttons_and_content(buttons_layout)
        self._create_image_preview_area(content_layout)
        self.update_notice = UpdateNotice(self.app)
        content_layout.addWidget(self.update_notice)
        if self.edit_mode:
            self.update_notice.hide()

        self._finalize_ui_setup()

    def _setup_window_properties(self) -> None:
        """Configure window flags and properties."""
        flags = Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        self.setWindowFlags(flags)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setWindowTitle("Writing Tools")
        self.min_width = 300  # be sure to see action buttons and scrollbar
        self.min_height = 150  # when no selected text or image
        self.setMinimumSize(self.min_width, self.min_height)
        self._set_window_icon()

    def _set_window_icon(self) -> None:
        """Set the window icon."""
        icon_path = ui_utils.get_icon_path(
            self.app,
            "app_icon",
            with_theme=False,
        )
        if icon_path.exists():
            self.setWindowIcon(QtGui.QIcon(icon_path.as_posix()))

    def _create_main_layout(self) -> QVBoxLayout:
        """Create and configure the main layout."""
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        return main_layout

    def _create_background_and_content_layout(self, main_layout: QVBoxLayout) -> QVBoxLayout:
        """Create background widget and content layout."""
        self.background = ThemeBackground(
            self.app,
            self,
            self.app.settings_manager.background_theme or "gradient",
            is_popup=True,
            border_radius=10,
        )
        main_layout.addWidget(self.background)

        content_layout = QVBoxLayout(self.background)
        content_layout.setContentsMargins(10, 4, 10, 10)
        content_layout.setSpacing(10)
        return content_layout

    def _create_top_bar(self, content_layout: QVBoxLayout) -> None:
        """Create the top bar with all its components."""
        self.top_bar_widget = QWidget()
        self.top_bar_widget.setFixedHeight(30)
        top_bar_layout = QHBoxLayout(self.top_bar_widget)
        top_bar_layout.setContentsMargins(0, 0, 0, 0)
        top_bar_layout.setSpacing(0)
        if self.has_sel_text or self.has_image:
            self._create_reset_button(top_bar_layout)
            self._create_drag_label(top_bar_layout)
            self._create_edit_buttons(top_bar_layout)
        self._create_close_button(top_bar_layout)
        # Configure mouse events for draggable top bar
        self.setup_draggable_top_bar()

        content_layout.addWidget(self.top_bar_widget)

    def _create_reset_button(self, layout: QHBoxLayout) -> None:
        """Create the reset button for edit mode."""
        self.reset_button = QPushButton()
        reset_icon_path = ui_utils.get_icon_path(self.app, "restore", with_theme=True)
        if reset_icon_path.exists():
            self.reset_button.setIcon(QtGui.QIcon(reset_icon_path.as_posix()))

        self.reset_button.setText("")
        self.reset_button.setFixedSize(24, 24)
        self.reset_button.setStyleSheet(self._get_icon_button_style())
        self.reset_button.clicked.connect(self.on_reset_clicked)
        self.reset_button.setToolTip(_("Reset to Default Buttons"))
        self.reset_button.installEventFilter(self)

        layout.addWidget(self.reset_button, 0, Qt.AlignmentFlag.AlignLeft)

    def _create_drag_label(self, layout: QHBoxLayout) -> None:
        """Create the drag instruction label for edit mode."""
        self.drag_label = QLabel(_("Drag to rearrange"))
        self.drag_label.setStyleSheet(self.app.styles["label"])
        self.drag_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.drag_label.hide()

        layout.addWidget(
            self.drag_label,
            1,
            Qt.AlignmentFlag.AlignVCenter | Qt.AlignmentFlag.AlignHCenter,
        )

    def _create_edit_buttons(self, layout: QHBoxLayout) -> None:
        """Create edit and edit close buttons."""
        # Edit close button (shown in edit mode)
        self.edit_close_button = QPushButton("×")
        self.edit_close_button.setFixedSize(24, 24)
        self.edit_close_button.setStyleSheet(self._get_close_button_style())
        self.edit_close_button.clicked.connect(self.exit_edit_mode)
        self.edit_close_button.setToolTip(_("Exit Edit Mode"))
        self.edit_close_button.hide()
        self.edit_close_button.installEventFilter(self)
        layout.addWidget(self.edit_close_button, 0, Qt.AlignmentFlag.AlignRight)

        # Edit button (shown in normal mode)
        self.edit_button = QPushButton()
        pencil_icon = ui_utils.get_icon_path(self.app, "pencil", with_theme=True)
        if pencil_icon.exists():
            self.edit_button.setIcon(QtGui.QIcon(pencil_icon.as_posix()))

        self.edit_button.setFixedSize(24, 24)
        self.edit_button.setStyleSheet(self._get_icon_button_style())
        self.edit_button.clicked.connect(self.enter_edit_mode)
        self.edit_button.setToolTip(_("Edit Tools Layout"))
        self.edit_button.installEventFilter(self)
        layout.addWidget(self.edit_button, 0, Qt.AlignmentFlag.AlignLeft)

    def _create_close_button(self, layout: QHBoxLayout) -> None:
        """Create the main close button."""
        self.close_button = QPushButton("×")
        self.close_button.setFixedSize(24, 24)
        self.close_button.setStyleSheet(self._get_close_button_style())
        self.close_button.clicked.connect(self.close)
        self.close_button.installEventFilter(self)
        layout.addWidget(self.close_button, 0, Qt.AlignmentFlag.AlignRight)

    def _get_icon_button_style(self) -> str:
        """Get stylesheet for icon buttons."""
        return self.app.styles["icon_small_button"]

    def _get_close_button_style(self) -> str:
        """Get stylesheet for close buttons."""
        return self.app.styles["close_small_button"]

    def _create_input_area(self, content_layout: QVBoxLayout) -> None:
        """Create the input area with text field and send button."""
        self.input_area = InputArea(self.app, self.has_sel_text, self.has_image)
        self.input_area.connect_send_signal(self.on_custom_change)
        content_layout.addWidget(self.input_area)

    def _create_image_preview_area(self, content_layout: QVBoxLayout) -> None:
        """Create the image preview area if there's an image."""
        if self.has_image:
            self.image_preview = ImagePreview(self.app, self.image)
            self.image_preview.connect_remove_signal(self._remove_image_from_clipboard)
            content_layout.addWidget(self.image_preview)

    def _remove_image_from_clipboard(self) -> None:
        """Remove image from clipboard and close application."""
        try:
            # Clear the clipboard
            clipboard = QtWidgets.QApplication.clipboard()
            clipboard.clear()

            # Show a brief message to the user
            self.app.ui_manager.show_message_signal.emit(
                "Image Removed",
                f"Image has been removed from clipboard.\n"
                f"Application will close.\n"
                f"Restart with {self.app.settings_manager.hotkey} to continue.",
            )

            #  Clean the image and close
            self.app.popup_manager.clean_image()
            self.close()

            # Schedule application quit after a brief delay to allow message to be shown
            # QtCore.QTimer.singleShot(2000, self.app.quit)

        except Exception:
            # In case of error, just close the popup
            self.close()

    def _get_input_style(self) -> str:
        """Get the styling for input elements."""
        return self.app.styles["input_full"]

    def _get_send_button_style(self) -> str:
        """Get stylesheet for send button."""
        return self.app.styles["send_button"]

    def _create_buttons_scroll_layout(self, parent_layout: QVBoxLayout) -> QVBoxLayout:
        """Create a scrollable layout specifically for buttons."""
        buttons_scroll = QScrollArea()
        buttons_scroll.setWidgetResizable(True)  # vertical scroll when more action buttons
        buttons_scroll.setFrameShape(QFrame.Shape.NoFrame)  # No border
        buttons_scroll.setMaximumHeight(250)
        buttons_scroll.setStyleSheet(self.app.styles["transparent_background"]("QScrollArea"))

        buttons_widget = QWidget()
        buttons_widget.setStyleSheet(self.app.styles["transparent_background"])
        buttons_layout = QVBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(5)

        buttons_scroll.setWidget(buttons_widget)
        parent_layout.addWidget(buttons_scroll)

        return buttons_layout

    def _setup_buttons_and_content(self, content_layout: QVBoxLayout) -> None:
        """Setup buttons and main content based on available input."""
        if self.has_sel_text or self.has_image:
            self.button_manager.build_buttons_list()
            self.button_manager.rebuild_grid_layout(content_layout)
            self.initialize_button_visibility()
        else:
            # Only custom instructions input if no selected text
            if self.input_area and self.input_area.custom_input is not None:
                self.input_area.custom_input.setMinimumWidth(400)

    def _finalize_ui_setup(self) -> None:
        """Finalize UI setup with event filters and focus."""
        self.installEventFilter(self)
        QtCore.QTimer.singleShot(
            250, lambda: self.input_area.set_focus() if self.input_area else None
        )

    def setup_draggable_top_bar(self) -> None:
        """Configure top bar to be draggable"""
        if self.top_bar_widget:
            # Install event filter on top bar
            self.top_bar_widget.installEventFilter(self)

            # Change cursor to indicate draggable area
            self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)

    def eventFilter(self, watched: QtCore.QObject, event: QtCore.QEvent) -> bool:
        """Event filter that handles cursor changes and dragging behavior for the top bar.

        This filter manages:
        - Setting appropriate cursors for buttons and top bar
        - Handling drag & drop functionality for window movement
        - Window deactivation behavior
        """
        # Handle buttons cursors first
        if watched in [
            self.close_button,
            self.edit_close_button,
            self.reset_button,
            self.edit_button,
        ]:
            if event.type() in [QtCore.QEvent.Type.Enter, QtCore.QEvent.Type.Leave]:
                if watched == self.close_button and self.close_button:
                    self.close_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.edit_close_button and self.edit_close_button:
                    self.edit_close_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.reset_button and self.reset_button:
                    self.reset_button.setCursor(Qt.CursorShape.ArrowCursor)
                elif watched == self.edit_button and self.edit_button:
                    self.edit_button.setCursor(Qt.CursorShape.ArrowCursor)
            return False

        # Handle dragging via top bar
        if watched == self.top_bar_widget and isinstance(event, QtGui.QMouseEvent):
            if event.type() == QtCore.QEvent.Type.MouseButtonPress:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.is_dragging = True
                    self.drag_start_position = event.globalPosition().toPoint() - self.pos()
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.ClosedHandCursor)
                    return True

            elif event.type() == QtCore.QEvent.Type.MouseMove:
                if self.is_dragging and event.buttons() == Qt.MouseButton.LeftButton:
                    if self.drag_start_position is not None:
                        new_position = event.globalPosition().toPoint() - self.drag_start_position
                        self.move(new_position)
                    return True

            elif event.type() == QtCore.QEvent.Type.MouseButtonRelease:
                if event.button() == Qt.MouseButton.LeftButton:
                    self.is_dragging = False
                    self.drag_start_position = None
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)
                    return True

            elif event.type() == QtCore.QEvent.Type.Enter:
                if not self.is_dragging:
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.OpenHandCursor)

            elif event.type() == QtCore.QEvent.Type.Leave:
                if not self.is_dragging:
                    if self.top_bar_widget:
                        self.top_bar_widget.setCursor(Qt.CursorShape.ArrowCursor)

        # The window will now stay open when clicking outside
        return super().eventFilter(watched, event)

    def is_force_chat_enabled(self) -> bool:
        """Check if Force Chat is currently enabled."""
        return bool(self.force_chat_widget and self.force_chat_widget.is_force_chat_enabled())

    def action_config_to_dict(self, action_config: ActionConfig) -> dict:
        """
        Convert ActionConfig to dict format for ButtonEditDialog compatibility.
        Only use when dict format is specifically needed.
        For image actions, open_in_window defaults to True since they need chat windows.
        """
        return {
            "prefix": action_config.get("prefix", ""),
            "instruction": action_config.get("instruction", ""),
            "icon": action_config.get("icon", ""),
            "open_in_window": action_config.get("open_in_window", True),
        }

    def enter_edit_mode(self) -> None:
        """Enter edit mode - called when user clicks the pencil icon."""
        self.edit_controller.enter_edit_mode()

    def exit_edit_mode(self) -> None:
        """Exit edit mode - called when user clicks the close button in edit mode."""
        self.edit_controller.exit_edit_mode()

    def initialize_button_visibility(self) -> None:
        """Initialize button visibility for normal (non-edit) mode."""
        self.edit_mode = False
        self._logger.debug("Initializing button visibility")
        self.visibility_manager.set_edit_mode(False)

    def on_reset_clicked(self) -> None:
        """
        Reset options to default actions and reload the interface.
        """
        confirm_box = QMessageBox()
        confirm_box.setWindowFlags(
            confirm_box.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint
        )
        confirm_box.setWindowTitle(_("Confirm Reset to Defaults?"))
        confirm_box.setText(
            "This will reset all buttons to their original configuration.\nYour custom buttons will be removed.\n\nAre you sure you want to continue?",
        )
        confirm_box.setStandardButtons(
            QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
        )
        confirm_box.setDefaultButton(QMessageBox.StandardButton.No)

        if confirm_box.exec_() == QMessageBox.StandardButton.Yes:
            try:
                self._logger.debug("Resetting to default actions")
                # Reset actions to defaults in unified settings
                if hasattr(self.app, "settings_manager") and self.app.settings_manager.settings:
                    if self.has_image:
                        # Reset image actions to defaults - completely replace the dict
                        self.app.settings_manager.settings.image_actions = (
                            create_default_image_actions_config()
                        )
                        self.app.settings_manager.image_actions = (
                            self.app.settings_manager.settings.image_actions
                        )
                    else:
                        # Reset text actions to defaults - completely replace the dict
                        self.app.settings_manager.settings.actions = create_default_actions_config()
                        self.app.settings_manager.actions = (
                            self.app.settings_manager.settings.actions
                        )
                else:
                    self._logger.error("Settings manager not available for reset")

                # Reload the interface immediately
                self.button_manager.build_buttons_list()
                self.button_manager.rebuild_grid_layout(force_edit_mode=self.edit_mode)
                if self.edit_mode:
                    self.button_manager.add_edit_overlays_to_buttons()

            except Exception as e:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", f"An error occurred while resetting: {e!s}"
                )

    def add_new_button_clicked(self) -> None:
        dialog = ButtonEditDialog(
            self.app, self, title="Add New Button", is_image_context=self.has_image
        )
        if dialog.exec_():
            bd = dialog.get_button_data()

            # Check if the name already exists
            if bd.get("name", "") in self.button_manager.get_actions():
                if not ui_utils.show_confirmation_dialog(
                    "Overwrite Existing Action",
                    f"An action named '{bd.get('name', '')}' already exists. Do you want to overwrite it?",
                ):
                    return  # The user canceled

            action_config = ActionConfig(
                prefix=bd.get("prefix", ""),
                instruction=bd.get("instruction", ""),
                icon=bd.get("icon", ""),
                open_in_window=bd.get("open_in_window", True),
            )

            # Use appropriate method based on context
            if self.has_image:
                success = self.app.settings_manager.update_image_action(
                    bd.get("name", ""), action_config
                )
            else:
                success = self.app.settings_manager.update_action(bd.get("name", ""), action_config)

            if success:
                # Stay in edit mode and refresh buttons
                self.button_manager.build_buttons_list()
                self.button_manager.rebuild_grid_layout(force_edit_mode=True)
                self.button_manager.add_edit_overlays_to_buttons()
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to save button changes. Please try again."
                )

    def edit_button_clicked(self, btn: QPushButton) -> None:
        """User clicked the small pencil icon over a button."""
        key = getattr(btn, "key", None)
        if key is None:
            self._logger.error("Button does not have a 'key' attribute.")
            return
        actions = self.button_manager.get_actions()
        if key not in actions:
            self._logger.error(f"Action not found: {key}")
            return

        action_config = actions[key]
        bd = self.action_config_to_dict(action_config)
        bd["name"] = key

        dialog = ButtonEditDialog(self.app, self, bd, is_image_context=self.has_image)
        if dialog.exec_():
            new_data = dialog.get_button_data()

            success = True

            # Remove old action if name changed
            if new_data.get("name", "") != key:
                if new_data.get("name", "") in self.button_manager.get_actions():
                    if not ui_utils.show_confirmation_dialog(
                        "Overwrite Existing Action",
                        f"An action named '{new_data.get('name', '')}' already exists. Do you want to overwrite it?",
                    ):
                        return  # The user cancelled

                # Delete the old action (use appropriate method based on context)
                if self.has_image:
                    success = self.app.settings_manager.remove_image_action(key)
                else:
                    success = self.app.settings_manager.remove_action(key)

            # Create and save new ActionConfig (only if previous operation succeeded)
            if success:
                action_config = ActionConfig(
                    prefix=new_data.get("prefix", ""),
                    instruction=new_data.get("instruction", ""),
                    icon=new_data.get("icon", ""),
                    open_in_window=new_data.get("open_in_window", True),
                )
                # Use appropriate method based on context
                if self.has_image:
                    success = self.app.settings_manager.update_image_action(
                        new_data.get("name", ""), action_config
                    )
                else:
                    success = self.app.settings_manager.update_action(
                        new_data.get("name", ""), action_config
                    )

            if success:
                # Stay in edit mode and refresh buttons
                self.button_manager.build_buttons_list()
                self.button_manager.rebuild_grid_layout(force_edit_mode=True)
                self.button_manager.add_edit_overlays_to_buttons()
                # Show success message after UI update
                QtCore.QTimer.singleShot(
                    100,
                    lambda: self.app.ui_manager.show_message_signal.emit(
                        "Button Updated", "Your button changes have been saved and are now active."
                    ),
                )
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to save button changes!! Please try again."
                )

    def delete_button_clicked(self, btn: QPushButton) -> None:
        """Handle deletion of a button."""
        key = getattr(btn, "key", None)
        if key is None:
            self._logger.error("Button does not have a 'key' attribute.")
            return

        confirm = QMessageBox()
        confirm.setWindowFlags(confirm.windowFlags() | QtCore.Qt.WindowType.WindowStaysOnTopHint)
        confirm.setWindowTitle(_("Confirm Delete?"))
        confirm.setText(_("Are you sure you want to continue?"))
        confirm.setStandardButtons(QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
        confirm.setDefaultButton(QMessageBox.StandardButton.No)

        if confirm.exec_() == QMessageBox.StandardButton.Yes:
            # Remove action using appropriate SettingsManager method
            if self.has_image:
                success = self.app.settings_manager.remove_image_action(key)
            else:
                success = self.app.settings_manager.remove_action(key)

            if success:
                # Clean up UI elements and refresh
                self.button_manager.remove_button_from_ui(key)

                # Stay in edit mode and refresh buttons
                self.button_manager.rebuild_grid_layout(force_edit_mode=True)
                self.button_manager.add_edit_overlays_to_buttons()
            else:
                self.app.ui_manager.show_message_signal.emit(
                    "Error", "Failed to delete the button. Please try again."
                )

    def reload_window(self) -> None:
        """
        Reload the window with updated button configuration.
        This recreates the popup window with the same selected text and image.
        """
        # Store current position, selected text, and image
        current_pos = self.pos()
        selected_text = self.selected_text
        image = self.image

        # Close current window
        self.close()

        # Create and show new popup window
        new_popup = CustomPopupWindow(self.app, selected_text, image)
        new_popup.move(current_pos)
        new_popup.show()

    def on_custom_change(self) -> None:
        """
        Prompt entered by user in the input field.
        """
        # Check if image is provided but model doesn't support vision
        if self.has_image and not self._check_vision_support():
            self.app.ui_manager.show_message_signal.emit(
                "Vision Not Supported",
                f"The current AI model {self.app.ai_processor.get_current_model(self.app.settings_manager.provider) or 'Unknown'} does not support image analysis. Please select a model that supports vision capabilities.",
            )
            return

        txt = self.input_area.get_input_text() if self.input_area else ""
        if txt.strip():
            self.app.ai_processor.process_option(
                "Custom", self.selected_text, self.is_force_chat_enabled(), txt, self.image
            )
            self.close()

    def on_generic_instruction(self, instruction: str) -> None:
        """
        User clicked a generic instruction button.
        """
        if not self.edit_mode and (self.selected_text is not None or self.has_image):
            self.app.ai_processor.process_option(
                instruction, self.selected_text, self.is_force_chat_enabled(), None, self.image
            )
            self.close()

    def _check_vision_support(self) -> bool:
        """
        Check if the current AI provider and model support vision/image analysis.

        Returns:
            bool: True if the current model supports vision, False otherwise
        """
        # Use the provider's validation method directly
        provider = self.app.ai_processor.current_provider
        if not provider:
            return False

        return provider._supports_vision()

    def refresh_language(self) -> None:
        """Refresh all text elements to reflect the current language."""
        try:
            # Update drag label
            if hasattr(self, "drag_label") and self.drag_label:
                self.drag_label.setText(_("Drag to rearrange"))

            # Update reset button tooltip
            if hasattr(self, "reset_button") and self.reset_button:
                self.reset_button.setToolTip(_("Reset to Default Buttons"))

            # Update edit button tooltip
            if hasattr(self, "edit_button") and self.edit_button:
                self.edit_button.setToolTip(_("Edit Tools Layout"))

            # Update close button tooltip
            if hasattr(self, "edit_close_button") and self.edit_close_button:
                self.edit_close_button.setToolTip(_("Exit Edit Mode"))

        except RuntimeError:
            # Widget might be destroyed, skip refresh
            pass

    def keyPressEvent(self, event: QtGui.QKeyEvent) -> None:
        if event.key() == QtCore.Qt.Key.Key_Escape:
            if self.edit_mode:
                # If in edit mode, exit edit mode (like clicking the close button)
                self.exit_edit_mode()
            else:
                # If not in edit mode, close the window
                self.close()
        else:
            super().keyPressEvent(event)
