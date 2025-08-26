# 💬 **CHAT INTERACTION FLOW - Interactive Documentation**

## **COMPLETE FLOW - "Chat Mode" Case (Response Window) :**

### **📋 Overview for LLM :**

```markdown
User Action → Hotkey Detection → UI Creation → Chat Mode → AI Response → Response Window → Text Replacement
```

---

## **1. 👤 User presses Ctrl+Space (without text selection)**

### **Action :** User triggers the keyboard shortcut with no selection

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

- Captures selected text (if no image present) - **In this case: selected_text will be empty string**
- Closes existing windows
- Creates and positions CustomPopupWindow
- Handles focus and activation

```python
# Capture text if no image - returns empty string when no selection
if self.image is None:
    selected_text = self.get_selected_text(sleep_duration=0.2)  # Returns ""

# Close existing windows
if self.non_editable_modal is not None:
    self.non_editable_modal.close()

if self.popup_window is not None:
    self.popup_window.close()

# Create new popup
self.popup_window = ui.CustomPopupWindow.CustomPopupWindow(self, selected_text, self.image)
```

---

## **3. CustomPopupWindow opens (Chat Mode)**

### **Action :** User interface ready for chat interaction

### **Code :** [`CustomPopupWindow`](../ui/CustomPopupWindow.py)

### **What this class does :**

- Displays interface with options (Rewrite, Summary, Custom, etc.)
- Shows that no text is selected (chat mode)
- Captures custom instruction
- Waits for user action

---

## **4. 👤 User types prompt in input field + clicks option**

### **Action :** User defines instruction and chooses mode (e.g., "Custom", "Rewrite", etc.)

### **Example :** User types "Write a summary of my document" and clicks "Custom"

### **Code :** CustomPopupWindow user interface

---

## **5. CustomPopupWindow.process_option() - Chat Mode**

### **Action :** Process selected option in chat mode

### **Code :** [`process_option()`](../ui/CustomPopupWindow.py#LXXX)

### **What this function does :**

- `return_response = True` (chat window mode)
- `current_response_window = self.show_response_window()` (creates response window)
- Launches processing in separate thread

```python
# Configuration for chat mode (no selected text)
if option in ['Rewrite', 'Custom', 'Summary'] and not selected_text.strip():
    # Chat window mode
    return_response = True
    current_response_window = self.show_response_window()
else:
    # Direct replacement mode (with selected text)
    return_response = False
    current_response_window = None

# Launch processing
threading.Thread(target=self.process_option_thread, args=(option, selected_text, custom_change), daemon=True).start()
```

---

## **6. show_response_window() creates ResponseWindow**

### **Action :** Creates new chat/response window

### **Code :** [`show_response_window()`](../ui/CustomPopupWindow.py#LXXX)

### **What this function does :**

- Creates new ResponseWindow instance
- Sets up chat interface
- Returns window reference for response handling

---

## **7. get_response() called with return_response=True**

### **Action :** Request to AI in chat mode

### **Code :** [`get_response()`](../aiprovider.py#LXXX)

### **What this function does :**

- Checks response mode :

  ```python
  if not return_response and not hasattr(self.app, "current_response_window"):
      # Direct replacement mode
      self.app.output_ready_signal.emit(response_text)
      return ""
  else:
      # Chat mode - return response to window
      return response_text
  ```

---

## **8. Provider checks :**

### **Condition :**

```python
if not return_response and not hasattr(self.app, "current_response_window"):
   → ❌ FALSE : returns response_text directly
```

---

## **9. ResponseWindow displays AI response**

### **Action :** AI response shown in chat window

### **Code :** [`ResponseWindow`](../ui/ResponseWindow.py)

### **What this function does :**

- Displays the AI-generated response
- Provides options to copy, edit, or use the response
- Allows for follow-up questions

---

## **10. 👤 User can continue conversation**

### **Action :** User types additional questions in the chat

### **Example :** "Make it shorter" or "Add more details about..."

### **Code :** ResponseWindow chat interface

---

## **11. Follow-up questions processing**

### **Action :** Additional AI requests from chat window

### **Code :** ResponseWindow processing

### **What happens :**

- Each follow-up question creates new AI request
- Responses are appended to the chat
- Conversation context is maintained

---

## **12. 👤 User wants to replace text with result**

### **Action :** User copies result from chat to replace text

### **Methods :**

- **Click "Copy" button** in ResponseWindow
- **Select text and use normal copy (Ctrl+C)**
- **Use "Replace" functionality if available**

---

## **🔧 TROUBLESHOOTING - Checkpoints :**

### **If chat window doesn't open :**

1. ✅ Check that `selected_text` is empty string
2. ✅ Check that `return_response=True`
3. ✅ Check that `current_response_window` is created
4. ✅ Check that ResponseWindow is properly initialized

### **If AI doesn't respond in chat :**

1. ✅ Check that `return_response=True`
2. ✅ Check AI provider configuration
3. ✅ Check network connectivity
4. ✅ Check API keys/tokens

### **If follow-up questions don't work :**

1. ✅ Check that ResponseWindow maintains conversation context
2. ✅ Check that each question triggers new AI request
3. ✅ Check that responses are properly appended

### **Key files to monitor :**

- [`WritingToolApp.py`](../WritingToolApp.py) - Main logic and popup handling
- [`CustomPopupWindow.py`](../ui/CustomPopupWindow.py) - Chat mode detection and ResponseWindow creation
- [`ResponseWindow.py`](../ui/ResponseWindow.py) - Chat interface and follow-up handling
- [`aiprovider.py`](../aiprovider.py) - AI communication and response routing

---

## **📊 COMPARISON - Chat Mode vs Direct Replacement :**

| Aspect | Chat Mode (No Selection) | Direct Replacement (With Selection) |
|--------|--------------------------|------------------------------------|
| **Trigger** | Ctrl+Space without selection | Ctrl+Space with selection |
| **return_response** | `True` | `False` |
| **Response Window** | ✅ Created | ❌ None |
| **Output Method** | Display in chat window | Direct text replacement |
| **Follow-up** | ✅ Additional questions | ❌ Single action |
| **Use Case** | Research, brainstorming, chat | Quick text editing |

---

## **💡 PRO TIPS :**

- **Chat mode** is perfect for research, getting AI suggestions, or multi-step interactions
- **Direct replacement** is ideal for quick text transformations
- Use **follow-up questions** to refine AI responses before replacing text
- **Copy from chat** using buttons or keyboard shortcuts to replace text anywhere

---

*Automatically generated documentation - Interactive links to source code*
