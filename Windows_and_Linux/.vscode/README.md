# VSCode Configuration

This directory contains VSCode configuration files for the Writing Tools project.

## Files

- `settings.json` - Default settings for Windows
- `settings.linux.json` - Settings for Linux users
- `PythonImportHelper-v2-Completion.json` - Auto-generated Python import completions

## Setup

### Windows Users
The default `settings.json` is already configured for Windows with the correct Python path:
```
./Windows_and_Linux/myvenv/Scripts/python.exe
```

### Linux Users
1. Backup the current `settings.json`:
   ```bash
   mv .vscode/settings.json .vscode/settings.windows.json
   ```

2. Copy the Linux configuration:
   ```bash
   cp .vscode/settings.linux.json .vscode/settings.json
   ```

This will set the Python path to:
```
./Windows_and_Linux/myvenv/bin/python
```

## Features

The configuration includes:
- ✅ Relative Python interpreter path (compatible with project structure)
- ✅ Automatic virtual environment activation
- ✅ Python analysis paths for proper imports
- ✅ File associations for Python files
- ✅ Environment file support

## Notes

- The virtual environment (`myvenv`) is created automatically by the build scripts
- All paths are relative to the workspace root for portability
- The configuration assumes the standard project structure with `Windows_and_Linux/` directory
