#!/usr/bin/env python3
"""
Script to find untranslated strings in the codebase.
Looks for setText(), setWindowTitle(), setText() calls that don't use _()
"""

import re
import sys
from pathlib import Path

# Add parent directory to path to import utils
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Go up to Windows_and_Linux
sys.path.insert(0, str(project_root))

# Import after path setup
from scripts.utils import get_project_root, get_python_executable  # noqa: E402


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


def find_untranslated_strings():
    """Find strings that should be translated but aren't wrapped in _()"""

    # Patterns for untranslated strings
    patterns = [
        r'setText\("([^"]+)"\)',  # setText("string")
        r"setText\(\'([^\']+)\'\)",  # setText('string')
        r'setWindowTitle\("([^"]+)"\)',  # setWindowTitle("string")
        r"setWindowTitle\(\'([^\']+)\'\)",  # setWindowTitle('string')
        r'setTitle\("([^"]+)"\)',  # setTitle("string")
        r"setTitle\(\'([^\']+)\'\)",  # setTitle('string')
        r'setPlaceholderText\("([^"]+)"\)',  # setPlaceholderText("string")
        r"setPlaceholderText\(\'([^\']+)\'\)",  # setPlaceholderText('string')
    ]

    # Files to check - use absolute path from project root
    project_root = get_project_root()
    src_dir = project_root / "src"

    if not src_dir.exists():
        print(f"Error: Source directory not found at {src_dir}")
        return []

    ui_files = list(src_dir.rglob("ui/**/*.py"))

    if not ui_files:
        print(f"Warning: No UI files found in {src_dir / 'ui'}")
        return []

    untranslated = []

    for file_path in ui_files:
        try:
            with open(file_path, encoding="utf-8") as f:
                content = f.read()

            lines = content.split("\n")
            for line_num, line in enumerate(lines, 1):
                for pattern in patterns:
                    matches = re.finditer(pattern, line)
                    for match in matches:
                        string_content = match.group(1)
                        # Skip if it's a variable or already translated
                        if not (
                            string_content.startswith("$")
                            or "self." in string_content
                            or "config" in string_content.lower()
                            or "button_text" in string_content
                            or string_content.strip() == ""
                            or len(string_content) < 3
                        ):  # Skip very short strings
                            untranslated.append(
                                {
                                    "file": str(file_path.relative_to(src_dir)),
                                    "line": line_num,
                                    "string": string_content,
                                    "context": line.strip(),
                                }
                            )

        except Exception as e:
            print(f"Error reading {file_path}: {e}")

    return untranslated


def print_results(untranslated):
    """Print the results in a formatted way"""
    if not untranslated:
        print("No untranslated strings found!")
        return

    print(f"Found {len(untranslated)} untranslated strings:")
    print()

    # Group by file
    by_file = {}
    for item in untranslated:
        file_name = item["file"]
        if file_name not in by_file:
            by_file[file_name] = []
        by_file[file_name].append(item)

    for file_name, items in sorted(by_file.items()):
        print(f"File: {file_name}:")
        for item in items:
            string_preview = item["string"][:50]
            if len(item["string"]) > 50:
                string_preview += "..."
            print(f"  Line {item['line']:4d}: {string_preview}")
            print(f"             Context: {item['context'][:80]}")
        print()

    print("=" * 60)
    print(f"Total: {len(untranslated)} strings need translation")
    print()
    print("To fix, wrap strings with _() like: _('Your string here')")


def main():
    """Main entry point"""
    print("=" * 60)
    print("Finding untranslated strings in UI modules")
    print("=" * 60)
    print()

    # Verify environment first
    if not verify_environment():
        return 1

    print("Scanning source files...")
    print()

    # Find untranslated strings
    untranslated = find_untranslated_strings()

    # Print results
    print_results(untranslated)

    return 0 if not untranslated else 1


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
