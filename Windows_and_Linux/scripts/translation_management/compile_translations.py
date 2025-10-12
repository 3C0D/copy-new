#!/usr/bin/env python3
"""
Translation compilation script
Usage: python compile_translations.py [language]
"""

import argparse
import os
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


def compile_language(lang_code):
    """Compile translations for a given language"""
    # Use absolute paths from project root
    project_root = get_project_root()
    po_file = project_root / f"locales/{lang_code}/LC_MESSAGES/messages.po"
    mo_file = project_root / f"locales/{lang_code}/LC_MESSAGES/messages.mo"

    if not po_file.exists():
        print(f"ERROR {lang_code}: File {po_file.relative_to(project_root)} not found")
        return False

    try:
        import polib
    except ImportError:
        print("ERROR: Missing polib module. Install with: pip install polib")
        return False

    try:
        # Load the .po file
        po = polib.pofile(str(po_file))

        # Check if there are translations
        translated_entries = [entry for entry in po if entry.msgstr.strip()]
        if not translated_entries:
            print(f"WARNING {lang_code}: No translations found")
            return False

        # Compile
        po.save_as_mofile(str(mo_file))
        print(f"SUCCESS {lang_code}: {len(translated_entries)} translations compiled")
        return True

    except Exception as e:
        print(f"ERROR {lang_code}: Compilation failed - {e}")
        return False


def get_available_languages():
    """Get the list of available languages"""
    languages = []
    locales_dir = Path(__file__).parent.parent.parent / "locales"

    if not locales_dir.exists():
        return languages

    for lang_dir in locales_dir.iterdir():
        if lang_dir.is_dir() and (lang_dir / "LC_MESSAGES" / "messages.po").exists():
            languages.append(lang_dir.name)

    return sorted(languages)


def main():
    parser = argparse.ArgumentParser(description="Compile translations")
    parser.add_argument("language", nargs="?", help="Language code to compile (e.g., fr, en, it)")
    parser.add_argument("--list", "-l", action="store_true", help="List available languages")

    args = parser.parse_args()

    # Change to project root directory (parent of scripts/)
    os.chdir(Path(__file__).parent.parent)

    # List languages
    available_languages = get_available_languages()

    if args.list:
        print("Available languages:")
        for lang in available_languages:
            print(f"  - {lang}")
        return

    if not available_languages:
        print("ERROR: No languages found in locales/ directory")
        return

    # Compile specific language
    if args.language:
        if args.language not in available_languages:
            print(f"ERROR: Language '{args.language}' not found")
            print(f"Available languages: {', '.join(available_languages)}")
            return

        success = compile_language(args.language)
        sys.exit(0 if success else 1)

    # Compile all languages
    print("Compiling all languages...")
    compiled_count = 0

    for lang in available_languages:
        if compile_language(lang):
            compiled_count += 1

    print(f"Result: {compiled_count}/{len(available_languages)} language(s) compiled")


if __name__ == "__main__":
    main()
