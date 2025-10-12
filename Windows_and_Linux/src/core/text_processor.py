"""
Text Processing Manager - Handles text replacement, clipboard operations and output display.

This module manages all text processing operations including:
- Text replacement through clipboard operations
- Response window output handling
- Non-editable modal display
- Output queue management
"""

import logging
import time
from typing import Optional

import pyperclip
from PySide6.QtCore import Q_ARG, QMetaObject, QObject, Qt, Signal, Slot

from ..ui.non_editable_modal import NonEditableModal


class TextProcessor(QObject):
    """
    Handles text processing operations including clipboard management and output display.
    """

    output_ready_signal = Signal(str)

    def __init__(self, app):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.output_ready_signal.connect(self.replace_text)
        self.non_editable_modal: Optional[NonEditableModal] = None

    @Slot(str)
    def replace_text(self, new_text: str) -> None:
        """
        Replaces the text by pasting in the LLM generated text. With actions,
        invokes a window with the output instead.
        If pasting fails (non-editable page), shows the text in a modal window.
        """
        self._logger.debug(
            f"replace_text called with text length: {len(new_text) if new_text else 0}"
        )

        # Early return if no valid text
        if not new_text or not isinstance(new_text, str):
            self._logger.debug("No new text to process")
            return

        error_message = "ERROR_TEXT_INCOMPATIBLE_WITH_REQUEST"
        self.app.ai_processor.output_queue += new_text
        current_output = self.app.ai_processor.output_queue

        # Handle error message
        if current_output.strip() == error_message:
            self.app.ui_manager.show_message_signal.emit(
                "Error", "The text is incompatible with the requested change."
            )
            return

        # Check if we're building up to the error message (to prevent partial pasting)
        if len(current_output.strip()) <= len(error_message):
            clean_current = "".join(current_output.split())
            clean_error = "".join(error_message.split())
            if clean_current == clean_error[: len(clean_current)]:
                return

        self._logger.debug("Processing output text")

        try:
            # Handle Summary and Key Points - show in response window
            if self.app.current_response_window:
                self._handle_response_window_output(new_text)
            else:
                # Handle other options - try clipboard-based replacement with fallback
                self._handle_replacement()

                # Check if selection changed (indicating successful paste)
                new_selection = self.app.input_manager.get_selected_text(sleep_duration=0.1)

                # If selection is the same, paste failed (non-editable page)
                if (
                    self.app.popup_manager.original_selection == new_selection
                    and self.app.popup_manager.original_selection
                    and self.app.popup_manager.original_selection.strip()
                ):
                    # Fallback to modal window for non-editable pages
                    cleaned_text = self.app.ai_processor.output_queue.rstrip("\n")
                    QMetaObject.invokeMethod(
                        self,
                        "_show_non_editable_modal",
                        Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, cleaned_text),
                    )
                self.app.popup_manager.original_selection = None
                self.app.ai_processor.output_queue = ""

        except Exception as e:
            self._logger.exception(f"Error processing output: {e}")

    def _handle_response_window_output(self, new_text: str) -> None:
        """Handle output for response window (Summary/Key Points)"""
        # Check if current_response_window exists and is not None
        current_window = getattr(self.app, "current_response_window", None)
        if not current_window:
            self._logger.warning("No current_response_window to handle output")
            return

        # Check if chat_area exists and is not None
        chat_area = getattr(current_window, "chat_area", None)
        if chat_area:
            chat_area.add_message(new_text)
        else:
            self._logger.warning("No chat_area found in current_response_window")
            return

        # If this is the initial response, add it to chat history
        if len(current_window.chat_history) == 1:  # Only original text exists
            current_window.chat_history.append(
                {
                    "role": "assistant",
                    "content": self.app.ai_processor.output_queue.rstrip("\n"),
                }
            )

    def _handle_replacement(self) -> None:
        """Handle clipboard-based text replacement with simple pyperclip approach"""
        try:
            clipboard_backup = pyperclip.paste()
            cleaned_text = self.app.ai_processor.output_queue.rstrip("\n")
            pyperclip.copy(cleaned_text)

            self.app.input_manager.simulate_ctrl_key("v")
            time.sleep(0.2)
            pyperclip.copy(clipboard_backup)

        except Exception as e:
            self._logger.error(f"Error in clipboard paste: {e}")
            # Fallback to modal window for non-editable pages
            cleaned_text = self.app.ai_processor.output_queue.rstrip("\n")
            QMetaObject.invokeMethod(
                self,
                "_show_non_editable_modal",
                Qt.ConnectionType.QueuedConnection,
                Q_ARG(str, cleaned_text),
            )

    @Slot(str)
    def _show_non_editable_modal(self, transformed_text: str) -> None:
        """
        Show a modal window with the transformed text when pasting fails (non-editable page).
        """
        self._logger.debug("Showing non-editable modal window")
        try:
            # Close existing modal if any
            if self.non_editable_modal is not None:
                self.non_editable_modal.close()
                self.non_editable_modal = None

            # Create and show the modal window
            self.non_editable_modal = NonEditableModal(self.app, transformed_text)
            self.non_editable_modal.close_signal.connect(self._on_non_editable_modal_closed)
            self.non_editable_modal.show()

        except Exception as e:
            self._logger.error(f"Error showing non-editable modal: {e}", exc_info=True)

    @Slot()
    def _on_non_editable_modal_closed(self) -> None:
        """Clean up modal reference when it's closed"""
        self.non_editable_modal = None

    def clear_output_queue(self) -> None:
        """Clear the output queue"""
        self.app.ai_processor.output_queue = ""
