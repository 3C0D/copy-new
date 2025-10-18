"""
Searchable ComboBox Widget
--------------------------

A QComboBox with integrated fuzzy search functionality.
Search field appears above the combobox.
"""

from PySide6.QtCore import Qt, Signal
from PySide6.QtGui import QStandardItem, QStandardItemModel
from PySide6.QtWidgets import (
    QComboBox,
    QLineEdit,
    QListView,
    QVBoxLayout,
    QWidget,
)


class SearchableComboBox(QWidget):
    """
    A widget combining a search field and a QComboBox with fuzzy search.

    Features:
    - Search field always visible above the combobox
    - Fuzzy matching filters items as you type
    - Preserves original order when search is cleared
    - Customizable placeholder text
    """

    # Signal emitted when selection changes
    currentIndexChanged = Signal(int)
    currentTextChanged = Signal(str)

    def __init__(self, parent=None, search_placeholder: str = "Search...", app=None):
        super().__init__(parent)

        self.search_placeholder = search_placeholder
        self.app = app  # Store app reference for style access
        self._all_items = []  # Store all original items with their data

        # Create layout
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

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

        # Create combobox
        self._combo = QComboBox()
        self._combo.setModel(QStandardItemModel())
        list_view = QListView()
        self._combo.setView(list_view)
        list_view.setUniformItemSizes(True)

        # Forward combobox signals
        self._combo.currentIndexChanged.connect(self.currentIndexChanged.emit)
        self._combo.currentTextChanged.connect(self.currentTextChanged.emit)

        # Add widgets to layout
        layout.addWidget(self._search_field)
        layout.addWidget(self._combo)

        # Apply combobox style
        if self.app and "dropdown" in self.app.styles:
            self._combo.setStyleSheet(self.app.styles["dropdown"])

    def addItem(self, text: str, userData=None):
        """Add an item to the combobox and store it internally."""
        self._combo.addItem(text, userData)
        self._all_items.append((text, userData))

    def addItems(self, texts: list):
        """Add multiple items to the combobox."""
        for text in texts:
            self.addItem(text)

    def clear(self):
        """Clear all items from the combobox."""
        self._combo.clear()
        self._all_items.clear()

    def currentData(self, role=Qt.ItemDataRole.UserRole):
        """Get the data of the currently selected item."""
        return self._combo.currentData(role)

    def currentIndex(self) -> int:
        """Get the index of the currently selected item."""
        return self._combo.currentIndex()

    def currentText(self) -> str:
        """Get the text of the currently selected item."""
        return self._combo.currentText()

    def setCurrentIndex(self, index: int):
        """Set the current item by index."""
        self._combo.setCurrentIndex(index)

    def setCurrentText(self, text: str):
        """Set the current item by text."""
        self._combo.setCurrentText(text)

    def findData(self, data, role=Qt.ItemDataRole.UserRole):
        """Find an item by its data."""
        return self._combo.findData(data, role)

    def findText(self, text: str):
        """Find an item by its text."""
        return self._combo.findText(text)

    def count(self) -> int:
        """Get the number of items."""
        return self._combo.count()

    def itemData(self, index: int, role=Qt.ItemDataRole.UserRole):
        """Get the data of an item at the given index."""
        return self._combo.itemData(index, role)

    def itemText(self, index: int) -> str:
        """Get the text of an item at the given index."""
        return self._combo.itemText(index)

    def model(self):
        """Get the underlying model."""
        return self._combo.model()

    def setModel(self, model):
        """Set the underlying model."""
        self._combo.setModel(model)

    def blockSignals(self, b: bool) -> bool:
        """Block or unblock signals."""
        return self._combo.blockSignals(b)

    def setStyleSheet(self, styleSheet: str):
        """Set stylesheet for the combobox."""
        self._combo.setStyleSheet(styleSheet)

    def wheelEvent(self, event):
        """Disable wheel events on the combobox."""
        event.ignore()

    def _filter_items(self, search_text: str):
        """Filter items based on fuzzy search."""
        search_text = search_text.lower().strip()

        # Block signals to prevent triggering currentIndexChanged
        self._combo.blockSignals(True)

        # Store current selection
        current_data = self._combo.currentData()

        # Clear model
        model = self._combo.model()
        if not isinstance(model, QStandardItemModel):
            self._combo.blockSignals(False)
            return

        model.removeRows(0, model.rowCount())

        if not search_text:
            # Show all items if search is empty
            for text, data in self._all_items:
                item = QStandardItem(text)
                item.setData(data, Qt.ItemDataRole.UserRole)
                model.appendRow(item)
        else:
            # Split search by spaces to support multi-word search
            search_words = search_text.split()

            # Fuzzy search: match items that contain all search words/patterns
            matched_items = []
            for text, data in self._all_items:
                text_lower = text.lower()

                # Check if all search words match
                if all(self._fuzzy_match(word, text_lower) for word in search_words):
                    matched_items.append((text, data))

            # Add matched items to model
            for text, data in matched_items:
                item = QStandardItem(text)
                item.setData(data, Qt.ItemDataRole.UserRole)
                model.appendRow(item)

        # Restore selection if possible
        if current_data is not None:
            index = self._combo.findData(current_data)
            if index >= 0:
                self._combo.setCurrentIndex(index)

        self._combo.blockSignals(False)

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
