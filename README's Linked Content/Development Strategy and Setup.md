# 🛠️ Development Strategy and Setup

This guide explains the development environment setup and best practices for contributing to Writing Tools.

## 🚀 Quick Development Setup

### 1. **Environment Setup**

The project uses automated scripts that handle virtual environment creation and dependency management:

```bash
# Windows
cd Windows_and_Linux
.\run.bat dev

# Linux
cd Windows_and_Linux
./run.sh dev
```

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
│   └── dev_script.py       # Development utilities
└── myvenv/                 # Virtual environment (auto-created)
```

## 🎯 Development Workflow

1. **Setup**: Run `.\run.bat dev` to initialize environment
2. **Code**: Use VSCode with the provided configuration
3. **Test**: Modify `constants.py` for first-window theme testing
4. **Format**: Black formatting is applied automatically
5. **Update**: Use `update_deps.py` when dependencies change

### [**◀️ Back to main page**](https://github.com/theJayTea/WritingTools)
