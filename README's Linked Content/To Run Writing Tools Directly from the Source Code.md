# 👨‍💻 To Run Writing Tools Directly from the Source Code

Writing Tools now includes automated scripts that handle environment setup and dependency management for you!

## 🚀 Quick Start (Recommended)

**1. Download the Code**

- Click the green `<> Code ▼` button toward the very top of this page, and click `Download ZIP`.

**2. Run with Automated Scripts**
After extracting the folder, navigate to the `Windows_and_Linux` directory and use the automated scripts:

- **Windows:**

  ```bash
  cd path\to\Windows_and_Linux
  run.bat dev
  ```

- **Linux:**
  ```bash
  cd /path/to/Windows_and_Linux
  ./run.sh dev
  ```

The scripts will automatically:

- ✅ Create a virtual environment (`myvenv/`)
- ✅ Install all required dependencies
- ✅ Launch the application in development mode

## 📋 Available Commands

- `.\run.bat dev` (Windows) / `./run.sh dev` (Linux) - Run in development mode
- `.\run.bat build-dev` / `./run.sh build-dev` - Create a development build
- `.\run.bat build-final` / `./run.sh build-final` - Create a final release build
- `.\run.bat` / `./run.sh` - Interactive menu

### 🔄 Updating Dependencies

To update or reinstall dependencies:

```bash
# Windows
python scripts\update_deps.py

# Linux
python3 scripts/update_deps.py
```

This script automatically updates the virtual environment and all dependencies.

> **ℹ️ Note:** The scripts automatically terminate any existing instances before starting, so manual cleanup is not required.

## 🔧 Development Mode Information

**Settings Storage:**

- **DEV mode** and **build-dev mode**: Settings are stored in `dist/dev/data_dev.json`
- **build-final mode**: Settings are stored in `dist/production/data.json` (same directory as executable)

**Debug Logging:**

- **build-dev mode**: Debug logs are automatically written to `dist/dev/debug.log` for development analysis
- **DEV mode**: Debug logs are automatically enabled and appear in console
- **build-final mode**: No debug file logging (console only)

## 🔧 Manual Setup (Advanced Users)

If you prefer manual setup, you can still run the program directly:

**1. Install Dependencies**

```bash
# Windows
cd path\to\Windows_and_Linux
python -m pip install -r requirements.txt

# Linux
cd /path/to/Windows_and_Linux
python3 -m pip install -r requirements.txt
```

**2. Run the Program**

```bash
# Windows
python main.py

# Linux
python3 main.py
```

> **ℹ️ Note:** Debug logging is automatically enabled when running from source code.

Of course, you'll need to have [Python installed](https://www.python.org/downloads/)!

## 🛠️ For Developers

If you're planning to contribute or modify the code, check out our comprehensive development guide:

**[📖 Development Strategy and Setup](./Development%20Strategy%20and%20Setup.md)**

### [**◀️ Back to main page**](https://github.com/theJayTea/WritingTools)
