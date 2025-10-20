"""
Provider Settings Module
------------------------

This module contains all setting classes for AI providers.
Settings are UI components that allow users to configure API keys, models, etc.
"""

# Disable Pylance reportPrivateImportUsage for google.generativeai
# pyright: reportPrivateImportUsage=false

# Standard library imports
import logging
from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import TYPE_CHECKING

# Third-party imports (with fallbacks for optional dependencies)
# PySide6 imports
from PySide6 import QtCore
from PySide6.QtWidgets import (
    QCheckBox,
    QComboBox,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QVBoxLayout,
)

# Type checking imports
if TYPE_CHECKING:
    from ..ui.custom_widgets.searchable_combobox import SearchableComboBox
    from ..writing_tools_app import WritingToolsApp


class AIProviderSetting(ABC):
    """
    Abstract base class for a provider setting (e.g., API key, model selection).

    Each setting has a name, display name, default value and description.
    Subclasses must implement UI rendering and value management.

    Attributes:
        name: Internal identifier for the setting
        display_name: Human-readable name shown in UI
        default_value: Default value if none is set
        description: Optional description text
        auto_save_callback: Optional callback for value changes
    """

    def __init__(
        self,
        name: str,
        display_name: str | None = None,
        default_value: str | bool | None = None,
        description: str | None = None,
    ):
        self.name: str = name
        self._logger = logging.getLogger(__name__)
        self.display_name: str = display_name or name
        self.default_value: str | bool = default_value or ""
        self.description: str = description or ""
        # Callback function (no args, no return) or None
        self.auto_save_callback: Callable[[], None] | None = None

    @abstractmethod
    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Render the setting widget(s) into the provided layout."""

    @abstractmethod
    def set_value(self, value: str | bool) -> None:
        """Set the internal value from configuration."""

    @abstractmethod
    def get_value(self) -> str | bool:
        """Return the current value from the widget."""

    def refresh_styles(self) -> None:
        """Optional: reapply the styles if the widget exists."""
        pass

    def set_auto_save_callback(self, callback: Callable) -> None:
        """Set callback function for auto-saving when value changes."""
        self.auto_save_callback = callback


class TextSetting(AIProviderSetting):
    """
    A text-based setting (for API keys, URLs, etc.).

    Uses a QLineEdit to allow free text input, and its label shown before.
    Value is stored internally until widget rendering.
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        name: str,
        display_name: str | None = None,
        default_value: str | None = None,
        description: str | None = None,
    ):
        super().__init__(name, display_name, default_value, description)
        self.app = app
        self.internal_value: str | None = default_value
        self.input: QLineEdit | None = None
        self.label: QLabel | None = None

    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Create and add the QLineEdit with its label to the layout."""
        row_layout = QHBoxLayout()
        self.label = QLabel(self.display_name)
        self.label.setStyleSheet(self.app.styles["label"])
        row_layout.addWidget(self.label)
        self.input = QLineEdit(self.internal_value)
        self.input.setStyleSheet(self.app.styles["input"])
        self.input.setPlaceholderText(self.description)
        # Connect auto-save if callback is set
        if self.auto_save_callback:
            self.input.editingFinished.connect(self.auto_save_callback)
        row_layout.addWidget(self.input)
        layout.addLayout(row_layout)

    def refresh_styles(self) -> None:
        """Refresh the styles for the input and label widgets."""
        # Update input style
        if self.input:
            self.input.setStyleSheet(self.app.styles["input"])

        # Update label style
        if self.label:
            self.label.setStyleSheet(self.app.styles["label"])

    def set_value(self, value: str | bool) -> None:
        """Store value internally and update widget if it exists."""
        self.internal_value = str(value) if isinstance(value, bool) else value
        if self.input is not None:
            try:
                # Only update if the value has actually changed to avoid triggering textChanged
                current_text = self.input.text()
                if str(value) != current_text:
                    self.input.setText(str(value))
            except RuntimeError:
                # Widget has been deleted, just store the value
                pass

    def get_value(self) -> str:
        """Return widget value or empty string if not yet rendered."""
        if self.input is not None:
            try:
                return self.input.text()
            except RuntimeError:
                # Widget has been deleted, return stored value or empty string
                return getattr(self, "internal_value", "")
        return getattr(self, "internal_value", "")


class CheckboxSetting(AIProviderSetting):
    """
    A checkbox setting for boolean values.

    Uses a QCheckBox to allow toggling boolean values.
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        name: str,
        display_name: str | None = None,
        default_value: bool | None = None,
        description: str | None = None,
        read_only: bool = False,
    ):
        super().__init__(name, display_name, default_value or False, description)
        self.app = app
        self.internal_value: bool = bool(default_value)
        self.checkbox: QCheckBox | None = None
        self.label: QLabel | None = None
        self.read_only: bool = read_only

    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Create and add the QCheckBox with its label to the layout."""
        from PySide6.QtWidgets import QCheckBox

        row_layout = QHBoxLayout()
        self.checkbox = QCheckBox(self.display_name)
        self.checkbox.setStyleSheet(self.app.styles["checkbox"])
        self.checkbox.setChecked(self.internal_value)

        # Make read-only if specified
        if self.read_only:
            self.checkbox.setEnabled(False)

        # Connect auto-save if callback is set and not read-only
        if self.auto_save_callback and not self.read_only:
            self.checkbox.stateChanged.connect(self.auto_save_callback)

        row_layout.addWidget(self.checkbox)
        layout.addLayout(row_layout)

    def refresh_styles(self) -> None:
        """Refresh the styles for the checkbox widget."""
        if self.checkbox:
            self.checkbox.setStyleSheet(self.app.styles["checkbox"])

    def set_value(self, value: bool | str) -> None:
        """Store value internally and update widget if it exists."""
        self.internal_value = bool(value)
        if self.checkbox is not None:
            try:
                self.checkbox.setChecked(self.internal_value)
            except RuntimeError:
                # Widget has been deleted, just store the value
                pass

    def set_read_only(self, read_only: bool) -> None:
        """Dynamically change the read-only state of the checkbox."""
        self.read_only = read_only
        if self.checkbox is not None:
            try:
                self.checkbox.setEnabled(not read_only)
            except RuntimeError:
                pass

    def get_value(self) -> bool:
        """Return checkbox value or stored value if not yet rendered."""
        if self.checkbox is not None:
            try:
                return self.checkbox.isChecked()
            except RuntimeError:
                # Widget has been deleted, return stored value
                return self.internal_value
        return self.internal_value


class DropdownSetting(AIProviderSetting):
    """
    A dropdown setting (e.g., for selecting a model).

    Uses a non-editable QComboBox or SearchableComboBox if searchable=True.
    Options are stored as tuples (display_name, value).
    """

    def __init__(
        self,
        app: "WritingToolsApp",
        name: str,
        display_name: str | None = None,
        default_value: str | None = None,
        description: str | None = None,
        options: list | None = None,
        refresh_callback: Callable | None = None,
        searchable: bool = False,
        search_placeholder: str = "Search models...",
    ):
        super().__init__(name, display_name, default_value, description)
        self.app = app
        self.options = options or []
        self.internal_value = default_value
        self.dropdown: QComboBox | SearchableComboBox | None = None
        self.label: QLabel | None = None
        self.refresh_callback = refresh_callback
        self.searchable = searchable
        self.search_placeholder = search_placeholder

    def render_to_layout(self, layout: QVBoxLayout) -> None:
        """Create and configure the QComboBox with available options."""
        row_layout = QHBoxLayout()
        self.label = QLabel(self.display_name)
        self.label.setStyleSheet(self.app.styles["label"])
        row_layout.addWidget(self.label)

        # Create searchable or regular combobox
        if self.searchable:
            from ..ui.custom_widgets.searchable_combobox import SearchableComboBox

            self.dropdown = SearchableComboBox(search_placeholder=self.search_placeholder)
        else:
            self.dropdown = QComboBox()

        # Ensure dropdown can receive focus and clicks properly
        self.dropdown.setFocusPolicy(QtCore.Qt.FocusPolicy.StrongFocus)
        self.dropdown.setStyleSheet(self.app.styles["dropdown"])

        # DISABLE WHEEL SCROLL
        if isinstance(self.dropdown, QComboBox):
            self.dropdown.wheelEvent = lambda e: e.ignore()
        else:
            # For SearchableComboBox, disable wheel events on the internal QComboBox
            if hasattr(self.dropdown, '_combo'):
                self.dropdown._combo.wheelEvent = lambda e: e.ignore()

        for option_tuple in self.options:
            if len(option_tuple) == 2:
                option, value = option_tuple
                self.dropdown.addItem(option, value)
            elif len(option_tuple) == 3:
                option, value, metadata = option_tuple
                # Add asterisk for vision support
                if metadata.get("vision", False):
                    display_option = f"* {option}"
                else:
                    display_option = option
                self.dropdown.addItem(display_option, value)
                # Store metadata (vision support) if necessary
            else:
                self._logger.warning(f"Unexpected option format: {option_tuple}")

        # Set current value
        if self.dropdown is not None:
            index = self.dropdown.findData(self.internal_value)
            if index != -1:
                self.dropdown.setCurrentIndex(index)

        # Connect auto-save if callback is set
        if self.auto_save_callback:
            self.dropdown.currentIndexChanged.connect(self.auto_save_callback)

        # Connect refresh callback when dropdown is about to be shown
        if self.refresh_callback and isinstance(self.dropdown, QComboBox):
            # Override showPopup to call refresh before showing
            # QComboBox doesn't have aboutToShow signal, so we override showPopup
            # Save original showPopup
            original_show_popup = self.dropdown.showPopup

            def show_popup_with_refresh():
                if callable(self.refresh_callback):
                    self.refresh_callback()
                original_show_popup()

            # Override
            self.dropdown.showPopup = show_popup_with_refresh

        row_layout.addWidget(self.dropdown)
        layout.addLayout(row_layout)

    def set_value(self, value: str | bool) -> None:
        """Store value for selection during rendering and update widget if it exists."""
        self.internal_value = str(value) if isinstance(value, bool) else value
        if self.dropdown is not None:
            try:
                # Check if the value is already selected to avoid triggering currentIndexChanged
                current_data = self.dropdown.currentData()
                if current_data != value:
                    # Find and select the matching option
                    for i in range(self.dropdown.count()):
                        if self.dropdown.itemData(i) == value:
                            self.dropdown.setCurrentIndex(i)
                            return
            except RuntimeError:
                # Widget has been deleted, just store the value
                pass

    def refresh_styles(self) -> None:
        """Refresh the styles for the dropdown and label widgets."""
        # Update dropdown style
        if self.dropdown:
            self.dropdown.setStyleSheet(self.app.styles["dropdown"])

        # Update label style
        if self.label:
            self.label.setStyleSheet(self.app.styles["label"])

    def get_value(self) -> str:
        """Return selected value from the dropdown."""
        if self.dropdown is None:
            return getattr(self, "internal_value", "")

        try:
            return self.dropdown.currentData()
        except RuntimeError:
            # Widget has been deleted, return stored value or empty string
            return getattr(self, "internal_value", "")

    def refresh_options(self, new_options: list) -> None:
        """Refresh the dropdown options dynamically."""
        if self.dropdown is None:
            self.options = new_options
            return

        try:
            # Save current selection
            current_value = self.get_value()
            initial_index = self.dropdown.currentIndex()

            # Block signals during refresh to prevent unwanted auto-save triggers
            self.dropdown.blockSignals(True)

            # Clear and repopulate dropdown
            self.dropdown.clear()
            self.options = new_options

            for option_tuple in self.options:
                if len(option_tuple) == 2:
                    option, value = option_tuple
                    self.dropdown.addItem(option, value)
                elif len(option_tuple) == 3:
                    option, value, metadata = option_tuple
                    # Add asterisk for vision support
                    if metadata.get("vision", False):
                        display_option = f"* {option}"
                    else:
                        display_option = option
                    self.dropdown.addItem(display_option, value)
                    # Store metadata (vision support) if necessary
                else:
                    self._logger.warning(f"Unexpected option format: {option_tuple}")

            # Restore selection if possible
            final_index = initial_index
            if current_value:
                index = self.dropdown.findData(current_value)
                if index != -1:
                    self.dropdown.setCurrentIndex(index)
                    final_index = index

            # Unblock signals
            self.dropdown.blockSignals(False)

            # Only trigger auto-save if the effective selection actually changed
            if final_index != initial_index and self.auto_save_callback:
                self.auto_save_callback()

        except RuntimeError:
            # Widget has been deleted, just update the options
            self.options = new_options
