# 🛠️ Writing Tools - Scripts Documentation

This directory contains all the essential scripts for developing, building, and debugging Writing Tools. Each script is designed to work with VS Code's Code Runner extension for easy execution.

## 🚀 Main Development Scripts

### **`dev_script.py`** - Direct Source Execution
```bash
python scripts/dev_script.py
```
**Purpose**: Run Writing Tools directly from source code without building an executable.

**When to use**:
- Quick testing during development
- Immediate code changes verification
- Fastest iteration cycle
- When you don't need to test the executable behavior

**Features**:
- Automatic environment setup
- Dependency verification
- Process cleanup (kills existing instances)
- Real-time console output

---

### **`dev_build.py`** - Development Build
```bash
python scripts/dev_build.py                    # Standard windowed build
python scripts/dev_build.py --console          # Console mode (for debugging)
```
**Purpose**: Create a development executable with fast build times and debug capabilities.

**When to use**:
- Testing executable behavior
- Debugging systray issues
- Verifying build process
- Testing with real executable environment

**Features**:
- Fast build (no cleanup for speed)
- Console mode support (`--console` flag)
- Automatic asset copying
- Build-dev mode configuration
- Process management

**Console Mode Benefits**:
- Real-time log visibility
- Immediate error feedback
- Systray debugging
- Startup issue diagnosis

---

### **`final_build.py`** - Production Build
```bash
python scripts/final_build.py
```
**Purpose**: Create the final production executable with full optimization and cleanup.

**When to use**:
- Preparing for distribution
- Final testing before release
- Performance testing
- Creating clean, optimized builds

**Features**:
- Full PyInstaller cleanup
- Production configuration
- Optimized executable size
- Final asset management

---

## 🔧 Utility Scripts

### **`utils.py`** - Shared Utilities
**Purpose**: Common functions used by all build scripts.

**Contains**:
- Environment setup functions
- Process management utilities
- Path resolution helpers
- Cross-platform compatibility functions

---

### **`update_deps.py`** - Dependency Management
```bash
python scripts/update_deps.py
```
**Purpose**: Update and manage Python dependencies.

**When to use**:
- Updating requirements.txt
- Installing new dependencies
- Resolving dependency conflicts
- Environment maintenance

---

## 🐛 Debug Scripts

### **`startup_debug.py`** - Startup Diagnostics
```bash
python scripts/startup_debug.py
```
**Purpose**: Capture detailed startup logs to diagnose systray and boot issues.

**When to use**:
- Application starts but systray icon missing
- Silent startup failures
- Boot-time environment issues
- Need detailed startup diagnostics

**Features**:
- Comprehensive logging
- Systray monitoring
- Environment analysis
- Real-time status display
- Log file generation

---

### **`install_startup_debug.py`** - Auto-Debug Installer
```bash
python scripts/install_startup_debug.py
```
**Purpose**: Configure automatic startup debugging at Windows boot.

**When to use**:
- Issues only occur at Windows startup
- Need to debug boot-time behavior
- Application works manually but fails at boot
- Investigating startup environment differences

**Features**:
- Windows registry configuration
- Automatic debug activation
- Boot-time log capture
- Install/uninstall functionality

---

### **`test_console_build.py`** - Console Build Testing
```bash
python scripts/test_console_build.py
```
**Purpose**: Specialized testing for console mode builds.

**When to use**:
- Verifying console mode functionality
- Testing log output visibility
- Console-specific debugging
- Build verification

---

## 📋 Quick Reference

### **Common Development Workflow**
1. **Quick Test**: `python scripts/dev_script.py`
2. **Build Test**: `python scripts/dev_build.py`
3. **Debug Issues**: `python scripts/dev_build.py --console`
4. **Final Build**: `python scripts/final_build.py`

### **Debugging Workflow**
1. **Startup Issues**: `python scripts/startup_debug.py`
2. **Boot Problems**: `python scripts/install_startup_debug.py`
3. **Console Debugging**: `python scripts/dev_build.py --console`

### **VS Code Code Runner**
All scripts are optimized for Code Runner. Simply:
1. Open the script file
2. Press `Ctrl+F5` (or your Code Runner shortcut)
3. The script runs with proper working directory

### **Script Dependencies**
- All scripts automatically handle environment setup
- Virtual environment creation and activation
- Dependency installation and verification
- Process cleanup and management

## 🎯 Troubleshooting

### **Script Won't Run**
- Ensure you're in the project root directory
- Check Python installation and PATH
- Verify virtual environment setup

### **Build Fails**
- Run `python scripts/update_deps.py` first
- Check for missing dependencies
- Try console mode for detailed error output

### **Systray Issues**
- Use `python scripts/startup_debug.py`
- Try console mode: `python scripts/dev_build.py --console`
- Check Windows system tray settings

### **Performance Issues**
- Use `python scripts/final_build.py` for optimized builds
- Check for background processes
- Verify system resources

## 📚 Additional Resources

- **Architecture**: See `ARCHITECTURE_DOCUMENT.md` in project root
- **Changes**: See `README's Linked Content/Major Changes from Original Fork.md`
- **Development**: See `README's Linked Content/Development Strategy and Setup.md`
