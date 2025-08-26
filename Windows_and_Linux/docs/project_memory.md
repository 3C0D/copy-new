# 🧠 **PROJECT MEMORY - Writing Tools Application**

## **📋 PROJECT OVERVIEW**
Writing Tools is a cross-platform desktop application that provides AI-powered text processing capabilities through a global keyboard shortcut (Ctrl+Space). The application captures selected text and offers various AI transformations like rewriting, summarizing, and custom prompts.

## **🏗️ ARCHITECTURE & STRUCTURE**

### **Core Components:**
- **WritingToolApp.py** - Main application class, handles hotkeys, UI coordination
- **aiprovider.py** - AI provider management (Gemini, OpenAI, Anthropic, etc.)
- **CustomPopupWindow.py** - Main user interface for option selection
- **ResponseWindow.py** - Window for displaying AI responses (Summary, Key Points)

### **Key Features:**
- **Direct Text Replacement** - AI response replaces selected text directly
- **Response Windows** - AI responses shown in separate windows (Summary, Key Points)
- **Multi-Provider Support** - Gemini, OpenAI, Anthropic, Mistral, Ollama
- **Image Support** - Can process images from clipboard
- **Cross-Platform** - Windows/Linux support

## **🔄 TEXT REPLACEMENT FLOW (Direct Mode)**

```
1. User presses Ctrl+Space
   ↓
2. on_hotkey_pressed() → _show_popup()
   ↓
3. CustomPopupWindow opens
   ↓
4. User selects "Rewrite" option
   ↓
5. process_option() called with return_response=False
   ↓
6. get_response() emits output_ready_signal (no window)
   ↓
7. replace_text() processes response
   ↓
8. Text replaced via clipboard operations
```

## **🪟 RESPONSE WINDOW FLOW (Summary/Key Points)**

```
1-4. Same as above
   ↓
5. process_option() called with return_response=True
   ↓
6. get_response() returns response_text
   ↓
7. ResponseWindow displays result
   ↓
8. User can ask follow-up questions
```

## **🔧 RECENT FIXES & IMPORTANT NOTES**

### **Text Replacement Bug (Fixed)**
- **Issue**: Complex clipboard operations caused replacement failures
- **Solution**: Simplified to use `pyperclip` with backup/restore pattern
- **Location**: `WritingToolApp.py:_handle_clipboard_paste()`

### **Key Functions to Monitor:**
- `on_hotkey_pressed()` - Hotkey detection and window management
- `_show_popup()` - UI creation and text capture
- `process_option()` - Option processing and mode selection
- `get_response()` - AI request handling
- `replace_text()` - Final text replacement

## **🐛 DEBUGGING CHECKPOINTS**

When text replacement fails:
1. ✅ Check `return_response=False` in direct mode
2. ✅ Check `current_response_window=None` in direct mode
3. ✅ Verify `output_ready_signal` is emitted
4. ✅ Confirm `replace_text()` is called
5. ✅ Test `pyperclip` clipboard operations

## **📁 IMPORTANT FILES**
- `WritingToolApp.py` - Main application logic
- `aiprovider.py` - AI provider implementations
- `ui/CustomPopupWindow.py` - Main user interface
- `ui/ResponseWindow.py` - Response display windows

## **🎯 DEVELOPMENT NOTES**

### **Current State:**
- ✅ Text replacement working correctly
- ✅ Multi-provider support functional
- ✅ Interactive documentation created
- ✅ Code cleaned and organized

### **Architecture Principles:**
- Separation of UI and business logic
- Signal/slot pattern for thread communication
- Provider abstraction for extensibility
- Clipboard-based text operations for reliability

---

*This memory file should be updated whenever significant changes are made to the codebase or architecture.*
