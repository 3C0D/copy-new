# 🐛 Debug Console Mode - Complete Guide

## Overview

The Debug Console Mode is a specialized build option that creates an executable with a visible console window, allowing real-time monitoring of application logs and immediate diagnosis of startup issues.

## When to Use Console Mode

### ✅ **Recommended for:**
- Application launches but systray icon doesn't appear
- Silent startup failures
- Provider configuration issues
- Hotkey registration problems
- File permission or path issues
- Any unexplained application behavior

### ❌ **Not needed for:**
- Normal development (use regular dev mode)
- Production builds
- When application works correctly

## How to Use

### 1. **Build with Console Mode**
```bash
cd Windows_and_Linux
python scripts/dev_build.py --console
```

### 2. **Launch and Monitor**
- The executable will be created in `dist/dev/`
- Double-click the exe or run from command line
- Console window will appear showing real-time logs
- Keep console open to see all application activity

### 3. **Analyze Output**
Look for patterns like:
```
=== Writing Tools - Console Mode ===
Logs will appear in this console window.
Press Ctrl+C to exit.
=====================================
2025-08-11 10:10:58,779 - WritingToolApp - DEBUG - Initializing WritingToolApp
2025-08-11 10:10:58,784 - config.settings - DEBUG - SettingsManager initialized
[... more logs ...]
```

## Troubleshooting Common Issues

### **Systray Icon Not Appearing**
**Symptoms:** Application runs but no systray icon
**Diagnosis:** Look for logs about systray creation
**Common causes:**
- System tray not available
- Icon file missing
- Permissions issues

### **Application Crashes on Startup**
**Symptoms:** Console shows error then closes
**Diagnosis:** Look for exception traces
**Common causes:**
- Missing dependencies
- Configuration file corruption
- Provider initialization failures

### **Hotkey Not Working**
**Symptoms:** Application starts but hotkey doesn't respond
**Diagnosis:** Look for hotkey registration logs
**Common causes:**
- Hotkey already in use
- Insufficient permissions
- Invalid hotkey combination

## Technical Details

### **What Console Mode Changes:**
1. **PyInstaller Configuration:** Uses `--console` instead of `--windowed`
2. **Logging Setup:** Enables both console and file logging
3. **Error Handling:** Enhanced exception reporting
4. **Startup Detection:** Automatic console mode detection

### **Files Created:**
- `dist/dev/Writing Tools.exe` - Console-enabled executable
- `dist/dev/build_dev_debug.log` - File-based logs
- Console output - Real-time logs

### **Automatic Cleanup:**
- Removes existing `.spec` file to force regeneration
- Ensures correct console configuration
- Maintains all other build settings

## Best Practices

1. **Always test console mode** when reporting bugs
2. **Copy relevant log sections** when asking for help
3. **Note the exact step** where issues occur
4. **Test both console and normal modes** to compare behavior
5. **Use console mode only for debugging** - not for daily use

## Integration with Development Workflow

```bash
# Normal development
python scripts/dev_build.py

# When issues arise
python scripts/dev_build.py --console

# Back to normal after fixing
python scripts/dev_build.py
```

This approach ensures efficient debugging while maintaining clean production builds.
