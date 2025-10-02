En regardant le code actuel, je vois encore plusieurs opportunités de refactorisation logiques :

## 1. **Text Processing & Clipboard Manager** (priorité élevée)

Créer `core/text_processor.py` pour extraire :
- `replace_text()`
- `_handle_response_window_output()`
- `_handle_clipboard_paste()`
- `_show_non_editable_modal()`
- `_on_non_editable_modal_closed()`
- `output_queue` (attribut)

Ces méthodes forment un ensemble cohérent pour le traitement et remplacement de texte.

## 2. **UI Manager** (priorité moyenne)

Créer `core/ui_manager.py` pour :
- `show_settings()`
- `show_response_window()`
- `show_message_box()`
- Gestion des références aux fenêtres (`settings_window`, etc.)

## 3. **Configuration Manager** (priorité moyenne)

Créer `core/config_manager.py` pour :
- `_detect_running_mode()`
- `setup_translations()`
- `_update_translation_functions()`
- `retranslate_ui()`
- `change_language()`
- `load_settings()`
- Gestion des traductions et langues

## 4. **Provider Manager** (priorité faible)

Créer `core/provider_manager.py` pour :
- `_setup_ai_providers()`
- `get_current_model()`
- Gestion de la liste `providers`

**Je recommande de commencer par le TextProcessor** car :
- Il a des responsabilités bien définies (traitement de texte/clipboard)
- Il simplifiera significativement la classe principale  
- Il a peu de dépendances complexes
- Les méthodes `replace_text()` et `_handle_clipboard_paste()` sont volumineuses

Veux-tu que je crée le module `TextProcessor` ?

//////////////////////////////////////

Application pour texte processeur

Je vais créer le module `TextProcessor` et indiquer les modifications nécessaires dans les autres modules.## Modifications à apporter dans WritingToolApp.py

### 1. Imports à ajouter (en haut du fichier) :
```python
from .core.text_processor import TextProcessor
```

### 2. Dans `_setup_core_attributes()` :
```python
def _setup_core_attributes(self) -> None:
    """Initialize core application attributes."""
    self.current_response_window: ResponseWindow | None = None
    self.current_provider: AIProvider | None = None
    # Remplacer output_queue par :
    self.text_processor = TextProcessor(self)
    self.ai_processor = AIProcessor(self)
    self.hotkey_manager = HotkeyManager(self)
    self.systray_manager = SystrayManager(self)
    self.image_processor = ImageProcessor(self._logger)
    self.popup_manager = PopupManager(self, self._logger)
```

### 3. Dans `_setup_signals()` :
```python
def _setup_signals(self) -> None:
    """Connect application signals to their handlers."""
    # Remplacer par :
    self.output_ready_signal.connect(self.text_processor.replace_text)
    self.show_message_signal.connect(self.show_message_box)
    self.hotkey_triggered_signal.connect(self.hotkey_manager.on_hotkey_pressed)
    # Connecter les signaux du text_processor
    self.text_processor.show_message_signal.connect(self.show_message_box)
```

### 4. Supprimer ces méthodes de WritingToolApp.py (elles sont maintenant dans TextProcessor) :
- `replace_text()`
- `_handle_response_window_output()`
- `_handle_clipboard_paste()`
- `_show_non_editable_modal()`
- `_on_non_editable_modal_closed()`

### 5. Supprimer cet attribut de `_setup_core_attributes()` :
```python
# Supprimer cette ligne :
self.output_queue = ""
# Et supprimer la référence à non_editable_modal (maintenant dans TextProcessor)
self.non_editable_modal = None
```

## Modifications à apporter dans AIProcessor

### Dans `__init__()` :
```python
def __init__(self, app):
    super().__init__()
    self.app = app
    self._logger = logging.getLogger(__name__)
    self.current_provider: AIProvider | None = None
    # Supprimer cette ligne car output_queue est maintenant dans TextProcessor :
    # self.output_queue = ""

    # Connect signals - modifier pour utiliser text_processor :
    self.output_ready_signal.connect(self.app.text_processor.replace_text)
```

### Dans toute référence à `self.app.output_queue` :
Remplacer par `self.app.text_processor.output_queue`

Ces modifications déplacent toute la logique de traitement de texte et de gestion du clipboard vers le nouveau module `TextProcessor`, simplifiant ainsi la classe principale `WritingToolApp`.

"""
Text Processing Manager - Handles text replacement, clipboard operations and output display.

This module manages all text processing operations including:
- Text replacement through clipboard operations
- Response window output handling
- Non-editable modal display
- Output queue management
"""

import time
import logging
from typing import Optional

from pynput import keyboard
from PySide6 import QtCore, QtGui
from PySide6.QtCore import QObject, Signal, Slot, Q_ARG
from PySide6.QtWidgets import QApplication

from ..ui.NonEditableModal import NonEditableModal
from ..ui.ResponseWindow import ResponseWindow


class TextProcessor(QObject):
    """
    Handles text processing operations including clipboard management and output display.
    """
    
    show_message_signal = Signal(str, str)
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self._logger = logging.getLogger(__name__)
        self.output_queue = ""
        self.non_editable_modal: Optional[NonEditableModal] = None
    
    @Slot(str)
    def replace_text(self, new_text: str) -> None:
        """
        Replaces the text by pasting in the LLM generated text. With "Key Points" and "Summary", 
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
        self.output_queue += new_text
        current_output = self.output_queue

        # Handle error message
        if current_output.strip() == error_message:
            self.show_message_signal.emit(
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
            if hasattr(self.app, "current_response_window") and self.app.current_response_window:
                self._handle_response_window_output(new_text)
            else:
                # Handle other options - try clipboard-based replacement with fallback
                self._handle_clipboard_paste()

                # Check if selection changed (indicating successful paste)
                new_selection = self.app.popup_manager.get_selected_text(sleep_duration=0.1)

                # If selection is the same, paste failed (non-editable page)
                if (
                    self.app.popup_manager.original_selection == new_selection
                    and self.app.popup_manager.original_selection
                    and self.app.popup_manager.original_selection.strip()
                ):
                    # Fallback to modal window for non-editable pages
                    cleaned_text = self.output_queue.rstrip("\n")
                    QtCore.QMetaObject.invokeMethod(
                        self,
                        "_show_non_editable_modal",
                        QtCore.Qt.ConnectionType.QueuedConnection,
                        Q_ARG(str, cleaned_text),
                    )
                self.app.popup_manager.original_selection = None
                self.output_queue = ""

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
                    "content": self.output_queue.rstrip("\n"),
                }
            )

    def _handle_clipboard_paste(self) -> None:
        """Handle clipboard-based text replacement with simple pyperclip approach"""
        try:
            import pyperclip

            clipboard_backup = pyperclip.paste()
            cleaned_text = self.output_queue.rstrip("\n")
            pyperclip.copy(cleaned_text)

            kbrd = keyboard.Controller()

            def press_ctrl_v():
                with kbrd.pressed(keyboard.Key.ctrl):
                    kbrd.press("v")
                    kbrd.release("v")

            press_ctrl_v()
            time.sleep(0.2)
            pyperclip.copy(clipboard_backup)

        except Exception as e:
            self._logger.error(f"Error in clipboard paste: {e}")
            # Fallback to modal window for non-editable pages
            cleaned_text = self.output_queue.rstrip("\n")
            QtCore.QMetaObject.invokeMethod(
                self,
                "_show_non_editable_modal",
                QtCore.Qt.ConnectionType.QueuedConnection,
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
        self.output_queue = ""