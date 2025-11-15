# UV Migration Guide

This document explains the migration from traditional virtual environments to UV (Universal Virtualenv).

## What is UV?

UV is a modern, fast Python package manager and virtual environment manager. It replaces the traditional `venv` + `pip` workflow with a single, high-performance tool.

## Benefits of UV

- **Speed**: 10-100x faster than traditional pip installations
- **Single Tool**: Manages both virtual environments and dependencies
- **Modern Format**: Uses `pyproject.toml` instead of `requirements.txt`
- **Lock File**: Ensures reproducible builds with `uv.lock`
- **Cross-platform**: Works consistently across Windows, macOS, and Linux

## Migration Changes

### 1. Project Configuration
- **Before**: `requirements.txt` + traditional venv
- **After**: `pyproject.toml` + UV environment

### 2. File Structure
```
Windows_and_Linux/
├── pyproject.toml         # Modern project configuration
├── uv.lock               # Lock file for reproducible builds
├── .uv/                  # UV environment directory
├── scripts/
│   ├── update_deps_uv.py # New UV-based setup script
│   └── dev_script.py     # Updated to work with UV
└── requirements.txt      # Kept for backward compatibility
```

### 3. Development Workflow

#### Old Workflow
```bash
# Setup environment
cd Windows_and_Linux
python -m venv myvenv
myvenv\Scripts\activate
pip install -r requirements.txt

# Run application
python scripts/dev_script.py
```

#### New UV Workflow
```bash
# Setup environment (one command)
cd Windows_and_Linux
python scripts/update_deps_uv.py

# Run application
uv run python scripts/dev_script.py

# Or with activated environment
.venv\Scripts\activate  # UV creates .venv instead of myvenv
uv sync  # Ensure dependencies are up to date
python scripts/dev_script.py
```

## Commands Reference

### Basic UV Commands
```bash
# Initialize UV project (already done)
uv init --name writing-tools

# Sync dependencies from pyproject.toml
uv sync

# Add new dependency
uv add package_name

# Add development dependency
uv add --dev package_name

# Update dependencies
uv sync --upgrade

# Run script with UV environment
uv run python script.py

# Create shell with UV environment activated
uv run
```

### Migration Commands
```bash
# Setup everything from scratch
python scripts/update_deps_uv.py

# Manual setup (if needed)
cd Windows_and_Linux
uv sync

# Verify installation
uv run python -c "import sys; print(sys.version)"
```

## Configuration Files

### pyproject.toml
The new standard for Python project configuration. Contains:
- Project metadata
- Dependencies list
- Build system configuration
- Tool configurations (Ruff, etc.)

### .gitignore Updates
Added UV-specific entries:
```
.uv/          # UV environment directory
uv.lock       # Lock file (keep in git for reproducibility)
```

## Scripts Updated

### update_deps_uv.py
- Replaces traditional venv setup
- Checks for UV installation
- Initializes UV project
- Syncs dependencies
- Provides usage instructions

### dev_script.py
- No changes required - works with both systems
- Can be run with `uv run python scripts/dev_script.py`

## Rollback Plan

If UV migration needs to be rolled back:

1. **Keep original scripts**: `update_deps.py` still works
2. **Preserve old venv**: `Windows_and_Linux/myvenv/` directory remains
3. **No data loss**: All settings and data remain unchanged

## Troubleshooting

### UV Not Found
```bash
# Install UV via pip
pip install uv

# Or download from official site
# https://docs.astral.sh/uv/getting-started/installation/
```

### Sync Issues
```bash
# Force recreation of environment
uv sync --recreate

# Clean installation
rm -rf .uv
uv sync
```

### Dependency Conflicts
```bash
# Update all dependencies
uv sync --upgrade

# Check for outdated packages
uv pip list --outdated
```

## Performance Comparison

| Operation | Traditional pip | UV |
|-----------|----------------|-----|
| Install dependencies | 2-5 minutes | 10-30 seconds |
| Create environment | 30 seconds | 5-10 seconds |
| Update dependencies | 1-2 minutes | 5-15 seconds |

## Next Steps

1. **Test the new setup**: Run `python scripts/update_deps_uv.py`
2. **Verify functionality**: Test your application with `uv run python scripts/dev_script.py`
3. **Update documentation**: Update any internal docs that mention the old workflow
4. **Team adoption**: Share this guide with team members

## Support

For UV documentation and issues:
- Official docs: https://docs.astral.sh/uv/
- GitHub: https://github.com/astral-sh/uv
- Discord: https://discord.gg/astral-sh