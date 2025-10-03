# 🔄 **IMAGE ACTIONS SEPARATION - Interactive Documentation**

## **📋 Overview for LLM :**

Major architectural change that separated text actions and image actions into independent systems for better maintainability and clearer logic.

**Before**: Mixed configuration with `image: true` flags
**After**: Separate `actions` and `image_actions` dictionaries

---

## **🎯 WHY THIS CHANGE**

### **Problems with the old system:**
- Actions were mixed in the same dictionary
- `image: true` flags caused confusion
- Logic had to check image flags everywhere
- Harder to maintain and extend

### **Benefits of the new system:**
- ✅ Clear separation of concerns
- ✅ Independent configuration management
- ✅ Simplified UI logic
- ✅ Easier to add new image actions
- ✅ Better type safety

---

## **🏗️ ARCHITECTURAL CHANGES**

### **1. Configuration Layer**

#### **Before:**
```python
_DEFAULT_ACTIONS_VALUES_RAW = {
    "Proofread": {...},
    "Rewrite": {...},
    "Img_txt→En": {
        "prefix": "...",
        "instruction": "...",
        "icon": "...",
        "open_in_window": True,
        "image": True,  # ← Mixed flag
    },
}
```

#### **After:**
```python
# Text actions only
_DEFAULT_ACTIONS_VALUES_RAW = {
    "Proofread": {...},
    "Rewrite": {...},
}

# Image actions only
_DEFAULT_IMAGE_ACTIONS_VALUES_RAW = {
    "Img_txt→En": {
        "prefix": "...",
        "instruction": "...",
        "icon": "...",
        # No more open_in_window or image flags needed
    },
}
```

### **2. Settings Structure**

#### **Before:**
```python
class UnifiedSettings:
    system: SystemConfig
    actions: dict[str, ActionConfig]  # Mixed text + image
    custom_data: CustomDataStructure
```

#### **After:**
```python
class UnifiedSettings:
    system: SystemConfig
    actions: dict[str, ActionConfig]        # Text actions only
    image_actions: dict[str, ActionConfig]  # Image actions only
    custom_data: CustomDataStructure
```

### **3. UI Logic**

#### **Before:**
```python
def get_actions(self) -> dict[str, ActionConfig]:
    # Had to filter based on image presence
    if self.has_image:
        return {k: v for k, v in self.actions.items() if v.get("image", False)}
    else:
        return {k: v for k, v in self.actions.items() if not v.get("image", False)}
```

#### **After:**
```python
def get_actions(self) -> dict[str, ActionConfig]:
    # Direct access based on context
    if self.has_image:
        return self.app.settings_manager.image_actions
    else:
        return self.app.settings_manager.actions
```

---

## **🔄 PROCESSING LOGIC CHANGES**

### **1. Action Selection**

#### **Before:**
```python
# Had to check image flag in action config
action_config = self.actions.get(option, {})
if action_config.get("image", False):
    # Image processing logic
else:
    # Text processing logic
```

#### **After:**
```python
# Direct selection based on context
if has_image and option in self.image_actions:
    action_config = self.image_actions.get(option, {})
else:
    action_config = self.actions.get(option, {})
```

### **2. Response Window Logic**

#### **Before:**
```python
should_setup_response_window = (
    (is_custom_option and not has_selected_text)
    or (is_custom_option and has_image)
    or action_config.get("open_in_window", False)
    or (force_chat and has_selected_text)
    or (has_image and not is_custom_option)  # Complex condition
)
```

#### **After:**
```python
should_setup_response_window = (
    has_image                                    # 1. Image → always window
    or force_chat                               # 2. Force chat → always window
    or (is_custom_option and not has_selected_text)  # 3. Custom without text → window
    or action_config.get("open_in_window", False)    # 4. Action with flag → window
)
```

---

## **📁 FILES MODIFIED**

### **Core Configuration:**
- [`constants.py`](../src/config/constants.py) - Separated action dictionaries
- [`interfaces.py`](../src/config/interfaces.py) - Added image_actions to UnifiedSettings
- [`data_operations.py`](../src/config/data_operations.py) - Added image action handling

### **UI Logic:**
- [`CustomPopupWindow.py`](../src/ui/custom_popup/custom_popup_window.py) - Context-aware action selection

### **Processing Logic:**
- [`ai_processor.py`](../src/core/ai_processor.py) - Simplified response window logic

### **Settings Management:**
- [`settings.py`](../src/config/settings.py) - Added image action CRUD methods

---

## **🔧 TROUBLESHOOTING - Checkpoints :**

### **If image actions don't appear:**
1. ✅ Check `self.has_image` is correctly set in CustomPopupWindow
2. ✅ Verify `image_actions` exists in settings manager
3. ✅ Check `get_actions()` returns correct dictionary

### **If response windows don't open for images:**
1. ✅ Verify `has_image` is True in `should_setup_response_window`
2. ✅ Check simplified logic doesn't have conflicting conditions
3. ✅ Confirm image actions don't have conflicting `open_in_window` flags

### **If custom image actions fail:**
1. ✅ Check `update_image_action()` is called instead of `update_action()`
2. ✅ Verify `image_actions` dictionary is properly saved
3. ✅ Confirm UI uses correct removal method (`remove_image_action()`)

---

## **💡 PRO TIPS :**

- **Always use context**: Check `self.has_image` before accessing action dictionaries
- **Separate CRUD operations**: Use `update_image_action()` / `remove_image_action()` for image actions
- **Simplified logic**: Image presence now directly determines window behavior
- **Type safety**: Separate dictionaries prevent mixing text and image configurations

---

## **🔮 FUTURE EXTENSIONS**

This architecture makes it easy to add:
- New image action types (OCR, object detection, etc.)
- Different processing logic per action type
- Independent configuration management
- Better testing isolation

---

*This separation significantly improves code maintainability and prepares the codebase for future image processing features.*