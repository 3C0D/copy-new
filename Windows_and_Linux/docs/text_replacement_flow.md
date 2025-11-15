# 🔄 **TEXT REPLACEMENT FLOW - Interactive Documentation**

## **COMPLETE FLOW - "Rewrite" Case (Direct Replacement) :**

### **📋 Overview for LLM :**

```
User Action → Hotkey Detection → UI Creation → Option Processing → AI Response → Text Replacement
```

---

## **1. 👤 User presses configured shortcut (default: ctrl space)**

### **Action :** User triggers the keyboard shortcut

### **Code :** [`on_hotkey_pressed()`](../WritingToolApp.py#L565)

### **What this function does :**

- Checks for shortcut spam (anti-abuse protection)
- Closes existing windows (modal/popup)
- Cancels current provider request
- Clears output queue
- Triggers `_show_popup()` via Qt signal

```python
# Anti-spam check
if self.check_trigger_spam():
    return

# Clean existing windows
if self.non_editable_modal is not None:
    self.non_editable_modal.close()

if self.popup_window is not None:
    self.popup_window.close()

# Close existing response window (chat window) if open
if self.current_response_window is not None:
    self.current_response_window.close()
    self.current_response_window = None

# Cancel current request
if self.current_provider:
    self.current_provider.cancel()
    self.output_queue = ""

# Trigger popup
QtCore.QMetaObject.invokeMethod(self, "_show_popup", QtCore.Qt.ConnectionType.QueuedConnection)
```

---

## **2. → _show_popup()**

### **Action :** Popup window display

### **Code :** [`_show_popup()`](../WritingToolApp.py#L583)

### **What this function does :**

- Captures selected text (if no image present)
- Closes existing windows
- Creates and positions CustomPopupWindow
- Handles focus and activation

```python
# Capture text if no image
if self.image is None:
    selected_text = self.get_selected_text(sleep_duration=0.2)

# Close existing windows
if self.non_editable_modal is not None:
    self.non_editable_modal.close()

if self.popup_window is not None:
    self.popup_window.close()

# Create new popup
self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self, selected_text, self.image)
```

---

## **3. CustomPopupWindow opens**

### **Action :** User interface ready

### **Code :** [`CustomPopupWindow`](../ui/CustomPopupWindow.py)

### **What this class does :**

- Displays interface with options (Rewrite, Summary, etc.)
- Captures custom instruction
- Waits for user action

---

## **4. 👤 User types "fix this code" + clicks "Rewrite"**

### **Action :** User defines instruction and chooses mode

### **Code :** CustomPopupWindow user interface

---

## **5. CustomPopupWindow.process_option()**

### **Action :** Process selected option

### **Code :** [`process_option()`](../ui/CustomPopupWindow.py#LXXX)

### **What this function does :**

- `return_response = False` (direct replacement mode)
- `current_response_window = None` (no response window)
- Launches processing in separate thread

```python
# Configuration for replacement mode
if option in ['Rewrite', 'Custom'] and not selected_text.strip():
    # Chat window mode
    return_response = True
    current_response_window = self.show_response_window()
else:
    # Direct replacement mode
    return_response = False
    current_response_window = None

# Launch processing
threading.Thread(target=self.process_option_thread, args=(option, selected_text, custom_change), daemon=True).start()
```

---

## **6. get_response() called with return_response=False**

### **Action :** Request to AI

### **Code :** [`get_response()`](../aiprovider.py#LXXX)

### **What this function does :**

- Checks response mode :

  ```python
  if not return_response and not hasattr(self.app, "current_response_window"):
      # Direct replacement mode
      self.app.output_ready_signal.emit(response_text)
      return ""
  ```

---

## **7. Provider checks :**

### **Condition :**

```python
if not return_response and not hasattr(self.app, "current_response_window"):
   → ✅ TRUE : emits output_ready_signal + returns ""
```

---

## **8. Signal output_ready_signal.emit(response_text)**

### **Action :** Signal emission with response

### **Code :** Connected to [`replace_text()`](../WritingToolApp.py#LXXX)

### **What this signal does :**

- Transports generated text to replacement function
- Ensures execution in main thread

---

## **9. replace_text() processes response_text**

### **Action :** Final text replacement

### **Code :** [`replace_text()`](../WritingToolApp.py#LXXX)

### **What this function does :**

- Copies to clipboard
- Simulates Ctrl+V to paste
- Handles errors (non-editable windows)

```python
def _handle_clipboard_paste(self) -> None:
    """Handle clipboard-based text replacement"""
    try:
        import pyperclip

        # Backup → Copy → Paste → Restore
        clipboard_backup = pyperclip.paste()
        cleaned_text = self.output_queue.rstrip('\n')
        pyperclip.copy(cleaned_text)

        # Simulate Ctrl+V
        kbrd = keyboard.Controller()
        kbrd.press(keyboard.Key.ctrl)
        kbrd.press('v')
        kbrd.release('v')
        kbrd.release(keyboard.Key.ctrl)

        # Restore clipboard
        pyperclip.copy(clipboard_backup)

    except Exception as e:
        # Fallback to modal window
        self._show_non_editable_modal(cleaned_text)
```

---

## **🔧 TROUBLESHOOTING - Checkpoints :**

### **If text is not replaced :**

1. ✅ Check that `return_response=False`
2. ✅ Check that `current_response_window=None`
3. ✅ Check that `output_ready_signal` is emitted
4. ✅ Check that `replace_text()` is called
5. ✅ Check that `pyperclip` works correctly

### **Key files to monitor :**

- [`WritingToolApp.py`](../WritingToolApp.py) - Main logic
- [`CustomPopupWindow.py`](../ui/CustomPopupWindow.py) - User interface
- [`aiprovider.py`](../aiprovider.py) - AI communication

---

## **📊 VARIANT - "Summary" Case (Response Window) :**

```
1-4. Same process
5. process_option() → return_response = True
   → current_response_window = new window
6. get_response() → return_response=True → returns response_text
7. Display in ResponseWindow (no signal)
```

---

*Automatically generated documentation - Interactive links to source code*
