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
- **Image Support** - Can process images from clipboard with dedicated image actions
- **Separated Action Types** - Text actions and image actions handled separately
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

### **Image Actions Separation (Major Architecture Change)**
- **Feature**: Complete separation of text actions and image actions
- **Issue Addressed**: Mixed configuration causing confusion between text and image processing
- **Solution**: Created separate `image_actions` configuration alongside existing `actions`
- **Implementation**:
  - New `_DEFAULT_IMAGE_ACTIONS_VALUES_RAW` for image-specific actions
  - Updated `UnifiedSettings` to include `image_actions` field
  - Modified UI logic to use appropriate action dictionaries based on context
  - Simplified response window logic: images always open windows
- **Location**: `constants.py`, `interfaces.py`, `data_operations.py`, `CustomPopupWindow.py`, `ai_processor.py`
- **Benefit**: Cleaner architecture, better maintainability, clearer separation of concerns

### **Chat Window Toggle Feature (Added)**
- **Feature**: Ctrl+Space now closes existing chat windows and returns to main popup
- **Issue Fixed**: Inconsistency in variable names (`response_window` vs `current_response_window`)
- **Solution**: Corrected variable reference in `on_hotkey_pressed()` method
- **Location**: `WritingToolApp.py:on_hotkey_pressed()`
- **Benefit**: Users can now seamlessly switch between chat and main interface

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
- ✅ Image actions separated from text actions
- ✅ Interactive documentation created
- ✅ Code cleaned and organized
- ✅ Major architecture improvements completed

### **Architecture Principles:**
- Separation of UI and business logic
- Signal/slot pattern for thread communication
- Provider abstraction for extensibility
- Clipboard-based text operations for reliability
- **Separated action types**: Text actions and image actions handled independently
- **Context-aware processing**: Different logic based on content type (text vs image)

---

*This memory file should be updated whenever significant changes are made to the codebase or architecture.*
