#!/usr/bin/env python3
"""
Script to extract translatable strings from the codebase and create a .pot file.
"""

import re
import sys
from pathlib import Path

# Add parent directory to path to import utils
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Go up to Windows_and_Linux
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(script_dir.parent))  # Add scripts directory

from utils import get_project_root, get_python_executable  # noqa: E402


def verify_environment():
    """Verify that the virtual environment exists"""
    # This will change to project root and return the path
    project_root = get_project_root()

    # Check for venv
    python_cmd = get_python_executable("myvenv")
    if not python_cmd.exists():
        print("=" * 60)
        print("ERROR: Virtual environment not found!")
        print("=" * 60)
        print()
        print(f"Expected location: {project_root / 'myvenv'}")
        print()
        print("Please run one of these commands first:")
        print("  - python dev_script.py          (to setup and run)")
        print("  - python scripts/update_deps.py (to setup only)")
        print()
        return False

    return True


def extract_translatable_strings():
    """Extract all strings wrapped in _() from the codebase."""

    # Files to check - use absolute path from project root
    project_root = get_project_root()
    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        return []

    ui_files = list(src_dir.rglob("**/*.py"))

    if not ui_files:
        print(f"Warning: No Python files found in {src_dir}")
        return []

    strings = set()

    for file_path in ui_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            # Find all _() calls (with multiline support for strings with newlines)
            matches = re.finditer(r'_\((["\'])(.*?)\1\)', content, re.DOTALL)
            for match in matches:
                string_content = match.group(2)
                # Skip empty strings and variables
                if (
                    string_content
                    and not string_content.startswith("$")
                    and "self." not in string_content
                ):
                    strings.add(string_content)

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return sorted(strings)


def create_pot_file(strings, output_file):
    """Create a .pot file from the extracted strings."""

    pot_content = """# Translation template for Writing Tools
# Generated automatically - do not edit manually
#
msgid ""
msgstr ""
"Content-Type: text/plain; charset=UTF-8\\n"
"Language: \\n"
"Plural-Forms: nplurals=2; plural=(n != 1);\\n"

"""

    for string in strings:
        # Escape quotes and newlines
        escaped = string.replace('"', '\\"').replace("\n", "\\n")
        pot_content += f'\nmsgid "{escaped}"\nmsgstr ""\n'

    with open(output_file, "w", encoding="utf-8") as f:
        f.write(pot_content)

    print(
        f"Created {output_file.relative_to(output_file.parent.parent)} with {len(strings)} translatable strings"
    )


def main():
    """Main entry point"""
    print("=" * 60)
    print("Extracting translatable strings from codebase")
    print("=" * 60)
    print()

    # Verify environment first
    if not verify_environment():
        return 1

    print("Scanning source files...")
    print()

    strings = extract_translatable_strings()
    print(f"Found {len(strings)} unique translatable strings")

    # Create locales directory if it doesn't exist - use absolute path
    project_root = get_project_root()
    locales_dir = project_root / "locales"
    locales_dir.mkdir(exist_ok=True)

    # Create pot file
    pot_file = locales_dir / "messages.pot"
    create_pot_file(strings, pot_file)

    print()
    print("Done!")
    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
