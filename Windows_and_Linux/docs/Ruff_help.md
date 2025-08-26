# 🐍 Ruff Usage Guide

## 📋 Overview

Ruff is an extremely fast Python linter and code formatter written in Rust that replaces multiple tools:

- **Flake8** (linting)
- **Black** (formatting)
- **isort** (import organization)
- **pyupgrade** (code modernization)
- And many more...

## 🗂️ Project Configuration

### Configuration Files Structure

```shell
Windows_and_Linux/
├── pyproject.toml          # Main Ruff configuration
├── requirements.txt        # Dependencies (including ruff)
├── myvenv/                # Virtual environment
├── scripts/
│   ├── run_ruff.py        # Automated script
│   └── update_deps.py     # Dependency installation
└── .vscode/
    ├── settings.json      # VS Code config (Windows)
    └── settings.linux.json # VS Code config (Linux)
```

### Ruff Configuration (`pyproject.toml`)

```toml
[tool.ruff]
line-length = 120                    # Maximum line length

exclude = [                          # Ignored directories
    "build", "dist", "__pycache__",
    "myvenv", ".pytest_cache", ".mypy_cache"
]

[tool.ruff.format]
quote-style = "double"               # Double quotes
indent-style = "space"               # Space indentation
line-ending = "auto"                 # Automatic line endings

[tool.ruff.lint]
select = [
    "E",      # pycodestyle errors
    "W",      # pycodestyle warnings
    "F",      # pyflakes
    "I",      # isort (imports)
    "UP",     # pyupgrade
    "W291",   # trailing-whitespace
    "W292",   # no-newline-at-end-of-file
    "W293",   # blank-line-with-whitespace
]

ignore = [
    "E501",   # line-too-long (handled by formatter)
]
```

## 🚀 Usage

### 1. Via Automated Script (Recommended)

```bash
# From Windows_and_Linux/scripts/
python run_ruff.py
```

**What the script does:**

1. ✅ Checks if Ruff is installed
2. 🔧 Installs dependencies if needed (via `update_deps.py`)
3. 🔍 Runs linting with automatic fixes
4. 🎨 Runs code formatting
5. 📊 Provides final report of remaining issues

### 2. Via VS Code (with Ruff extension installed)

#### Real-time Auto-corrections

- ✅ Red/yellow error underlining
- ✅ Quick fixes on hover (💡)
- ✅ Automatic formatting on save
- ✅ Automatic import organization

#### Command Palette Commands (Ctrl+Shift+P)

- `Ruff: Fix all auto-fixable problems` - Fixes all auto-fixable issues
- `Ruff: Format Document` - Formats current document
- `Ruff: Format Imports` - Organizes imports
- `Ruff: Restart Server` - Restarts Ruff server
- `Ruff: Show client logs` - Shows client logs
- `Ruff: Show server logs` - Shows server logs

### 3. Manual Command Line

```bash
# From Windows_and_Linux/ (with virtual environment activated)

# Check only (no fixes)
ruff check .

# Check with automatic fixes
ruff check --fix .

# Code formatting
ruff format .

# Combined command (recommended)
ruff check --fix . && ruff format .

# Real-time monitoring
ruff check --watch .
```

## 🔧 VS Code Configuration

### Windows Settings (`settings.json`)

```json
{
    "python.defaultInterpreterPath": "./myvenv/Scripts/python.exe",
    "[python]": {
        "editor.defaultFormatter": "charliermarsh.ruff",
        "editor.formatOnSave": true,
        "editor.codeActionsOnSave": {
            "source.fixAll.ruff": "explicit",
            "source.organizeImports.ruff": "explicit"
        }
    },
    "ruff.configuration": "./pyproject.toml",
    "ruff.path": ["./myvenv/Scripts/ruff.exe"]
}
```

### Linux Settings (`settings.linux.json`)

```json
{
    "python.defaultInterpreterPath": "./Windows_and_Linux/myvenv/bin/python",
    "ruff.configuration": "./Windows_and_Linux/pyproject.toml",
    "ruff.path": ["./Windows_and_Linux/myvenv/bin/ruff"]
}
```

## 📦 Installation

### Automatic

Simply run `python scripts/run_ruff.py` - the script handles everything!

### Manual

```bash
# In virtual environment
pip install ruff

# Or via requirements.txt
pip install -r requirements.txt
```

## 🎯 What Ruff Does

### Automatic Fixes

- ✅ Removes unused imports
- ✅ Organizes and sorts imports
- ✅ Fixes indentation
- ✅ Removes trailing whitespace
- ✅ Adds missing newlines
- ✅ Modernizes Python syntax
- ✅ Applies PEP 8 conventions

### Code Formatting

- ✅ Consistent line length (120 characters)
- ✅ Consistent quote usage
- ✅ Spacing around operators
- ✅ Import organization by groups
- ✅ Consistent indentation

## 🚨 Troubleshooting

### Common Issues

1. **"ruff: command not found"**
   - ✅ Solution: Run `python scripts/run_ruff.py` which will install automatically

2. **VS Code extension not working**
   - ✅ Check that "Ruff" extension is installed
   - ✅ Verify path in `ruff.path` in settings.json
   - ✅ Restart VS Code

3. **Configuration not applied**
   - ✅ Check that `pyproject.toml` is at project root
   - ✅ Verify `ruff.configuration` in settings.json

### Logs and Debugging

```bash
# Show Ruff version
ruff --version

# Verbose mode
ruff check --verbose .

# Logs via VS Code
Ctrl+Shift+P > "Ruff: Show server logs"
```

## 📈 Benefits of This Configuration

- 🚀 **Performance**: 10-100x faster than Black + Flake8
- 🔄 **Automatic**: Complete script that handles everything
- 🌐 **Cross-platform**: Works on Windows and Linux
- 🎯 **Integrated**: Real-time corrections in VS Code
- 📋 **Consistent**: Same configuration everywhere
- 🛠️ **Simple**: One tool for everything

## 🎉 Recommended Workflow

1. **Development**: Use VS Code with extension for real-time corrections
2. **Before commit**: Run `python scripts/run_ruff.py` for complete check
3. **CI/CD**: Integrate script into automated pipelines

---

*This guide covers Ruff usage in the Windows_and_Linux project with optimized configuration for efficient development workflow.*
