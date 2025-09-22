Faire une synthèse des aides plus tard Demandez à 1LLM...

# 🛠️ Development Strategy and Setup

This guide explains how to set up the development environment and best practices for contributing to writing tools.

## Tips

The best way is to use the VSC `Code Runner` extension to run the scripts. It's easy and fast. And there's a configuration directly integrated into the repository. No need to navigate through subfolders, just open the project. And run it. You can also use `exe Runner` to directly execute the build without having to go into the file's folder and click on it. (From VSC explorer).
Important note: When the Virtual Environment is not yet installed, if you press the Code Runner triangle button, you'll get an error that makes you think the script doesn't work. Actually, with the script open in the editor, there's a small dropdown arrow next to the Code Runner button to open additional options - select "Run Python File in Terminal". The difference is that in the first case, you're using the path to Python in the virtual environment (which doesn't exist yet), and in the second case, you're using the general Python installation. This will first install the virtual environment in your project, then install the dependencies from requirements.txt. Obviously, afterwards, you'll use the direct button instead.

## 🚀 Quick Development Setup

****

### 1. **Environment Setup**

The project uses automated scripts that handle virtual environment creation and dependency management:

```bash
# Windows
cd Windows_and_Linux
python scripts\build_dev.py # Run in development mode 
other modes see To Run Writing Tools Directly from the Source Code and To Compile the Application Yourself

# Linux
cd Windows_and_Linux
python3 scripts/build_dev.py
```

Once the virtual environment is created, so that the interpreter can properly read the scripts, enter the command console: interpreter and choose the Python interpreter. So that it indicates the exe in `Windows_and_Linux\myvenv\Scripts\python.exe` under Windows and `Windows_and_Linux\myvenv\bin\python` under Linux. This way, the scripts, type corrections, and a port will be OK. Otherwise, it will look for the general Python and will not be able to read the types and others correctly.

You can also run the `update_deps.py` script if you don't plan to do a direct build. See below

### 2. **Update Dependencies**

To update or reinstall dependencies, use the dedicated script:

```bash
# Windows
cd Windows_and_Linux
python scripts\update_deps.py

# Linux
cd Windows_and_Linux
python3 scripts/update_deps.py
```

This script will:

- ✅ Create/update the virtual environment (`myvenv/`)
- ✅ Install/update all dependencies from `requirements.txt`
- ✅ Handle both new installations and updates

## 🔧 VSCode Configuration

### **Recommended Settings**

The project includes a `.vscode/settings.json` file with optimal configuration:

```json
{
  "python.defaultInterpreterPath": "./myvenv/Scripts/python.exe",
  "python.terminal.activateEnvironment": true,
  "python.formatting.provider": "black",
  "python.analysis.typeCheckingMode": "basic"
}
```

**Key Benefits:**

- 🐍 **Auto Python Detection**: Uses the virtual environment Python automatically
- 🔄 **Auto Environment**: New terminals automatically activate the virtual environment
- 🎨 **Black Formatting**: Consistent code formatting (strongly recommended)
- 🔍 **Type Checking**: Basic level resolves Qt library access issues

### ⚠️ **CRITICAL: Python Interpreter Setup**

**You MUST manually select the Python interpreter** to avoid seeing 20+ import errors:

1. **Open VS Code** in the project directory
2. **Press `Ctrl+Shift+P`** (or `Cmd+Shift+P` on Mac)
3. **Type**: `Python: Select Interpreter`
4. **Choose**: `Windows_and_Linux/myvenv/Scripts/python.exe` (Windows) or `Windows_and_Linux/myvenv/bin/python` (Linux)

**Alternative method:**

- Click on the Python version in the bottom-left status bar
- Select the virtual environment interpreter

**Without this step**, VS Code will show numerous import errors even though the code runs correctly.

### **Important Notes**

- ⚠️ **Manual interpreter selection is REQUIRED** (settings.json alone is not sufficient)
- ✅ **Keep `.vscode/settings.json`** in version control (it's essential for proper setup)
- ✅ **Scripts work without manual venv activation** (handled automatically)
- ✅ **Black formatter is strongly recommended** for code consistency
- ✅ **Basic type checking** resolves many Qt attribute access issues

## 📦 Dependencies and Libraries

### **Core Dependencies**

- **PySide6**: Main Qt framework for UI
- **PySide6-stubs**: Type hints and IDE support for PySide6 (resolves Qt attribute issues)
- **darkdetect**: System theme detection
- **keyboard**: Global hotkey handling
- **requests**: HTTP requests for AI providers

### **Development Dependencies**

The `requirements.txt` includes all necessary development tools and type stubs for optimal IDE experience.

## 🔄 Autostart System (For Developers)

Writing Tools includes a smart autostart system with mutual exclusion to prevent conflicts.

### **Two Autostart Methods**

1. **Application Autostart** (For built executables)
   - Available in Settings → "Start on boot"
   - Creates registry key: `WritingTools`
   - Works with built executables only
   - Automatically disables dev autostart if active

2. **Development Autostart** (For debugging)
   - Run: `python scripts/setup_dev_autostart.py`
   - Creates registry key: `WritingToolsDevStartup`
   - Runs dev script with visible console for debugging
   - Automatically disables application autostart if active

### **How It Works**

- **Mutual Exclusion**: Only one autostart method can be active at a time
- **Automatic Cleanup**: Activating one method automatically disables the other
- **Conflict Prevention**: No duplicate processes at startup
- **Smart Detection**: System detects and manages existing configurations

### **Usage Examples**

```bash
# For development with console debugging
python scripts/setup_dev_autostart.py  # Toggle dev autostart

# For testing built application autostart
python scripts/build_dev.py  # Build first
# Then enable autostart in the app settings
```

## 🏗️ Project Structure

```
Windows_and_Linux/
├── main.py                 # Application entry point
├── WritingToolApp.py       # Main application class
├── config/                 # Configuration files
│   ├── constants.py        # Default values and settings
│   └── settings.py         # Settings management
├── ui/                     # User interface components
│   ├── OnboardingWindow.py # First-time setup window
│   ├── SettingsWindow.py   # Settings configuration
│   └── ui_utils.py         # UI utilities and theming
├── scripts/                # Development scripts
│   ├── update_deps.py      # Dependency management
│   ├── dev_script.py       # Development utilities
│   └── setup_dev_autostart.py # Development autostart setup
└── myvenv/                 # Virtual environment (auto-created)
```

## 🎯 Development Workflow

1. **Setup**: Run `.\run.bat dev` to initialize environment
2. **Code**: Use VSCode with the provided configuration
3. **Test**: Modify `constants.py` for first-window theme testing
4. **Format**: Black formatting is applied automatically
5. **Update**: Use `update_deps.py` when dependencies change

## ⚙️ Script Behavior & Build Modes

### **Common Script Features**

- **Automatic Instance Termination**: All scripts automatically close existing Writing Tools instances before starting
- **Build Timers**: Both `build_dev.py` and `build_final.py` measure and display compilation time
- **Environment Setup**: Scripts automatically create virtual environments and install dependencies

### **Build Mode Comparison**

| Feature | build_dev.py | build_final.py |
|---------|-------------|----------------|
| **PyInstaller Mode** | `--onedir` (folder) | `--onefile` (single exe) |
| **Output** | `dist/dev/` folder | `dist/production/` single file |
| **Compression** | Fast development | Maximum compression |
| **Auto-clean** | Detects Git changes (>10 min) | Always clean build |
| **Debug Support** | Console mode available | Production optimized |
| **File Transfer** | Direct folder transfer | Single file deployment |

#### **build_dev Optimizations**

- **Smart Caching**: Preserves build cache between compilations for faster rebuilds
- **Git-Aware Cleaning**: Automatically cleans cache when detecting commits older than 10 minutes
- **Manual Clean Option**: Use `--clean` flag for forced cache cleanup
- **Console Debug Mode**: `--console` flag enables visible console for debugging (works with autostart too)
- **Asset Transfer**: Directly transfers required files to build folder for immediate execution
- **Development Focus**: Optimized for rapid iteration during development

#### **build_final Optimizations**

- **Single File**: Creates standalone executable with maximum compression
- **Clean Build**: Always performs fresh build for consistency
- **Production Ready**: Optimized for distribution and deployment
- **Minimal Size**: Excludes unnecessary development files

### [**◀️ Back to main page**](https://github.com/theJayTea/WritingTools)
