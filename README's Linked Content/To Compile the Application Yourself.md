# 👨‍💻 To compile the application yourself:

### Windows and Linux Version build instructions:

Writing Tools now includes automated build scripts that handle everything for you!

## 🚀 Quick Build (Recommended)

**1. Download the Code**

- Click the green `<> Code ▼` button toward the very top of this page, and click `Download ZIP`.

**2. Build with Automated Scripts**
Navigate to the `Windows_and_Linux` directory and use the build scripts:

- **Development Build (Fast):**

  ```bash
  # Windows
  .\run.bat build-dev

  # Linux
  ./run.sh build-dev
  ```

- **Development Build with Console (For Debugging):**

  ```bash
  # Direct script execution with console visible
  python Windows_and_Linux/scripts/dev_build.py --console
  ```

  This creates a build where the console window remains visible, allowing you to see logs in real-time instead of only in log files.

- **Final Release Build (Clean):**

  ```bash
  # Windows
  .\run.bat build-final

  # Linux
  ./run.sh build-final
  ```

## 🔧 Build Mode Information

**Settings Storage:**

- **build-dev**: Settings stored in `dist/dev/data_dev.json` + debug logs in `dist/dev/debug.log`
- **build-final**: Settings stored in `dist/production/data.json` (same directory as executable)

**Debug Features:**

- **build-dev**: Includes debug file logging to `dist/dev/debug.log` for development analysis
- **build-dev --console**: Same as build-dev but with console visible for real-time log viewing
- **build-final**: Production build with minimal logging

## 🐛 **Debug Mode with Console**

For troubleshooting startup issues and seeing real-time logs:

```bash
# Build with visible console for debugging
python Windows_and_Linux/scripts/dev_build.py --console
```

**What this mode provides:**

- ✅ Console window stays open during execution
- ✅ Real-time log output visible immediately
- ✅ Helps diagnose startup crashes and systray issues
- ✅ Shows exactly where the application fails

**When to use:**

- Application launches but doesn't appear in system tray
- Startup crashes or silent failures
- Need to see initialization steps in real-time
- Debugging provider configuration issues

**Troubleshooting methodology:**

1. Build with `--console` flag
2. Launch the executable and watch console output
3. Note the last successful step before any crash
4. Use the detailed logs to identify the exact problem
5. Fix the issue and rebuild in normal mode

The scripts will automatically:

- ✅ Create a virtual environment (`myvenv/`)
- ✅ Install all required dependencies
- ✅ Build the executable with PyInstaller
- ✅ Copy all necessary assets and configurations
- ✅ Launch the built application (dev-build only)

**Build Output:**

- **build-dev**: Executable and assets in `dist/dev/`
- **build-final**: Executable and assets in `dist/production/`

- Executable: `dist/Writing Tools.exe` (Windows) or `dist/Writing Tools` (Linux)
- Assets: Icons, backgrounds, and configuration files in `dist/`

## 🔧 Manual Build (Advanced Users)

If you prefer manual setup:

1. **Create and activate a virtual environment:**

```bash
# Install virtualenv if you haven't already
pip install virtualenv

# Create a new virtual environment
virtualenv myvenv

# Activate it
# On Windows:
myvenv\Scripts\activate
# On Linux:
source myvenv/bin/activate
```

2. **Install required packages:**

```bash
pip install -r requirements.txt
```

3. **Build Writing Tools:**

```bash
python pyinstaller-build-script.py
```

### macOS Version (by [Aryamirsepasi](https://github.com/Aryamirsepasi)) build instructions:

1. **Install Xcode**

   - Download and install Xcode from the App Store
   - Launch Xcode once installed and complete any additional component installations

2. **Clone the Repository**

   - Open Terminal and navigate to the directory where you want to store the project:

   ```bash
   git clone https://github.com/theJayTea/WritingTools.git
   ```

3. **Open in Xcode**

   - Open Xcode
   - Select "Open an existing project..." from the options.
   - Navigate to the macOS folder within the WritingTools directory that you cloned previously, and select "writing-tools.xcodeproj"

4. **Configure Project Settings**

   - In Xcode, select the project in the Navigator pane.
   - Under "Targets", select "writing-tools"
   - Set the following:
     - Deployment Target: macOS 14.0
     - Signing & Capabilities: Add your development team

5. **Build and Run**
   - In Xcode, select "My Mac" as the run destination
   - Click the Play button or press ⌘R to build and run

## 🛠️ For Developers

If you're planning to contribute or modify the code, check out our comprehensive development guide:

**[📖 Development Strategy and Setup](./Development%20Strategy%20and%20Setup.md)**

### [**◀️ Back to main page**](https://github.com/theJayTea/WritingTools)
