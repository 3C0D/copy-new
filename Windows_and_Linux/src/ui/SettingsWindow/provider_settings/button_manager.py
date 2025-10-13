"""
button_manager.py

Manages provider action buttons.
"""

from typing import TYPE_CHECKING, cast

from PySide6.QtWidgets import (
    QHBoxLayout,
    QLayout,
    QPushButton,
    QWidget,
)

if TYPE_CHECKING:
    from ....aiprovider.aiprovider import AIProvider
    from ....writing_tools_app import WritingToolsApp


class ProviderButtonManager:
    """Manages provider action buttons."""

    def __init__(self, app: "WritingToolsApp"):
        self.app = app

    def create_button_layout(self, provider: "AIProvider") -> QWidget | None:
        """Create button layout for provider."""
        if not provider.button_text and not (
            hasattr(provider, "additional_buttons") and provider.additional_buttons
        ):
            return None

        button_container = QHBoxLayout()
        button_container.setSpacing(10)

        # Main button
        if provider.button_text:
            main_button = QPushButton(provider.button_text)
            main_button.setStyleSheet(self.app.styles["primary_button"])
            main_button.clicked.connect(provider.button_action)
            button_container.addWidget(main_button)

        # Additional buttons
        if hasattr(provider, "additional_buttons"):
            for button_config in provider.additional_buttons:
                button = QPushButton(button_config["text"])
                style = (
                    self.app.styles["secondary_button"]
                    if button_config.get("style") == "secondary"
                    else self.app.styles["primary_button"]
                )
                button.setStyleSheet(style)
                button.clicked.connect(button_config["action"])
                button_container.addWidget(button)

        # Center button container
        button_widget = QWidget()
        button_widget.setLayout(button_container)
        return button_widget

    def update_button_styles(self, layout: QLayout) -> None:
        """Update button styles recursively."""
        for i in range(layout.count()):
            item = layout.itemAt(i)
            if item.widget() and isinstance(item.widget(), QPushButton):
                button = cast(QPushButton, item.widget())
                button_text = button.text().lower() if button.text() else ""

                secondary_keywords = ["cancel", "reset", "clear", "remove", "delete"]
                if any(kw in button_text for kw in secondary_keywords):
                    button.setStyleSheet(self.app.styles["secondary_button"])
                else:
                    button.setStyleSheet(self.app.styles["primary_button"])
            elif item.layout():
                self.update_button_styles(item.layout())
