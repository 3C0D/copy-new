"""
Searchable ComboBox Widget
--------------------------

A QComboBox with integrated fuzzy search functionality.
When opened, displays a search field above the dropdown list.
"""

from PySide6.QtCore import Qt
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QListView,
    QVBoxLayout,
    QWidget,
)


class SearchableComboBox(QComboBox):
    """
    A QComboBox with fuzzy search capability.

    Features:
    - Search field appears when dropdown is opened
    - Fuzzy matching filters items as you type
    - Preserves original order when search is cleared
    - Customizable placeholder text
    """

    def __init__(self, parent=None, search_placeholder: str = "Search...", app=None):
        super().__init__(parent)

        self.search_placeholder = search_placeholder
        self.app = app  # Store app reference for style access
        self._all_items = []  # Store all original items with their data
        self._search_field = None
        self._popup_widget = None

        # Set up the model
        self.setModel(QStandardItemModel())

        # Configure list view
        list_view = QListView()
        self.setView(list_view)
        list_view.setUniformItemSizes(True)

    def addItem(self, text: str, userData=None):  # type: ignore[override]
        """Add an item to the combobox and store it internally."""
        super().addItem(text, userData)
        self._all_items.append((text, userData))

    def addItems(self, texts):
        """Add multiple items to the combobox."""
        for text in texts:
            self.addItem(text)

    def clear(self):
        """Clear all items from the combobox."""
        super().clear()
        self._all_items.clear()

    def showPopup(self):
        """Override to show popup with search field."""
        if not self._popup_widget:
            self._setup_popup()

        # Reset search when opening
        if self._search_field:
            self._search_field.clear()
            self._filter_items("")

        super().showPopup()

        # Focus search field after popup is shown
        if self._search_field:
            self._search_field.setFocus()

    def _setup_popup(self):
        """Set up the popup widget with search field."""
        popup = self.view().parent()
        if not popup or not isinstance(popup, QWidget):
            return

        # Create search field
        self._search_field = QLineEdit()
        self._search_field.setPlaceholderText(self.search_placeholder)
        self._search_field.textChanged.connect(self._filter_items)

        # Apply styles if app is available
        if self.app:
            if "search_field" in self.app.styles:
                self._search_field.setStyleSheet(self.app.styles["search_field"])
            elif "input" in self.app.styles:
                self._search_field.setStyleSheet(self.app.styles["input"])

        # Cast to QWidget for proper type checking
        popup_widget: QWidget = popup  # type: ignore[assignment]

        # Insert search field at the top of popup
        popup_layout = popup_widget.layout()
        if popup_layout is None:
            popup_layout = QVBoxLayout(popup_widget)
            popup_layout.setContentsMargins(0, 0, 0, 0)

        # Cast to QVBoxLayout for proper type checking
        if isinstance(popup_layout, QVBoxLayout):
            popup_layout.insertWidget(0, self._search_field)

        self._popup_widget = popup_widget

        self._popup_widget = popup

    def _filter_items(self, search_text: str):
        """Filter items based on fuzzy search."""
        search_text = search_text.lower().strip()

        # Block signals to prevent triggering currentIndexChanged
        self.blockSignals(True)

        # Store current selection
        current_data = self.currentData()

        # Clear model
        model = self.model()
        if not isinstance(model, QStandardItemModel):
            self.blockSignals(False)
            return

        model.removeRows(0, model.rowCount())

        if not search_text:
            # Show all items if search is empty
            for text, data in self._all_items:
                item = QStandardItem(text)
                item.setData(data, Qt.ItemDataRole.UserRole)
                model.appendRow(item)
        else:
            # Fuzzy search: match items that contain all characters in order
            matched_items = []
            for text, data in self._all_items:
                if self._fuzzy_match(search_text, text.lower()):
                    matched_items.append((text, data))

            # Add matched items to model
            for text, data in matched_items:
                item = QStandardItem(text)
                item.setData(data, Qt.ItemDataRole.UserRole)
                model.appendRow(item)

        # Restore selection if possible
        if current_data is not None:
            index = self.findData(current_data)
            if index >= 0:
                self.setCurrentIndex(index)

        self.blockSignals(False)

    def _fuzzy_match(self, search: str, text: str) -> bool:
        """
        Check if search matches text in a fuzzy way.

        All characters from search must appear in text in the same order,
        but not necessarily consecutive.

        Example: "gpt4" matches "gpt-4-turbo"
        """
        search_idx = 0

        for char in text:
            if search_idx < len(search) and char == search[search_idx]:
                search_idx += 1

        return search_idx == len(search)

    def set_search_placeholder(self, placeholder: str):
        """Set the placeholder text for the search field."""
        self.search_placeholder = placeholder
        if self._search_field:
            self._search_field.setPlaceholderText(placeholder)
