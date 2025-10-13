#!/usr/bin/env python3
"""
Script to update .po files from the .pot template
Adds new strings, keeps existing translations, marks obsolete entries
"""

import sys
from pathlib import Path

# Add parent directory to path to import utils
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Go up to Windows_and_Linux
sys.path.insert(0, str(project_root))

from scripts.utils import get_project_root, get_python_executable  # noqa: E402


def verify_environment():
    """Verify that the virtual environment exists and has required packages"""
    project_root = get_project_root()
    python_cmd = get_python_executable("myvenv")

    if not python_cmd.exists():
        print("=" * 60)
        print("ERROR: Virtual environment not found!")
        print("=" * 60)
        print()
        print(f"Expected location: {project_root / 'myvenv'}")
        print()
        print("Please run one of these commands first:")
        print("  - python dev_script.py")
        print("  - python scripts/update_deps.py")
        print()
        return False

    try:
        import polib  # noqa: F401

        return True
    except ImportError:
        print("=" * 60)
        print("ERROR: Missing polib dependency!")
        print("=" * 60)
        print()
        print("Install with:")
        print(f"  {python_cmd} -m pip install polib")
        print()
        return False


def update_po_from_pot(pot_file, po_file):
    """Update a .po file from a .pot template"""
    import polib

    # Load files
    pot = polib.pofile(str(pot_file))

    if po_file.exists():
        po = polib.pofile(str(po_file))
        print(f"Updating existing file: {po_file.name}")
    else:
        # Create new .po from .pot
        po = polib.POFile()
        po.metadata = pot.metadata.copy()
        print(f"Creating new file: {po_file.name}")

    # Build dict of existing translations
    existing_translations = {entry.msgid: entry.msgstr for entry in po if entry.msgstr}

    # Clear current entries
    po.clear()

    # Copy metadata from pot
    po.metadata = pot.metadata.copy()

    # Add all entries from pot
    added_count = 0
    updated_count = 0
    kept_count = 0

    for pot_entry in pot:
        # Create new entry
        entry = polib.POEntry(
            msgid=pot_entry.msgid,
            msgstr=existing_translations.get(pot_entry.msgid, ""),
            occurrences=pot_entry.occurrences,
        )

        if pot_entry.msgid in existing_translations:
            if existing_translations[pot_entry.msgid]:
                kept_count += 1
            else:
                updated_count += 1
        else:
            added_count += 1

        po.append(entry)

    # Save updated .po file
    po.save(str(po_file))

    # Print stats
    print(f"  - Kept {kept_count} existing translations")
    print(f"  - Added {added_count} new strings (untranslated)")
    if updated_count > 0:
        print(f"  - Updated {updated_count} entries")

    obsolete_count = len(existing_translations) - kept_count
    if obsolete_count > 0:
        print(f"  - Removed {obsolete_count} obsolete translations")

    return added_count


def main():
    """Main entry point"""
    print("=" * 60)
    print("Update PO files from POT template")
    print("=" * 60)
    print()

    # Verify environment
    if not verify_environment():
        return 1

    project_root = get_project_root()

    # Check if pot file exists
    pot_file = project_root / "locales" / "messages.pot"
    if not pot_file.exists():
        print(f"ERROR: Template file not found: {pot_file}")
        print()
        print("Run this first:")
        print("  python scripts/translation_management/extract_translations.py")
        return 1

    print(f"Using template: {pot_file.name}")
    print()

    # Find all language directories
    locales_dir = project_root / "locales"
    lang_dirs = [d for d in locales_dir.iterdir() if d.is_dir() and d.name != "__pycache__"]

    if not lang_dirs:
        print("No language directories found in locales/")
        print()
        print("Create a language directory first, example:")
        print("  mkdir -p locales/fr/LC_MESSAGES")
        return 1

    # Update each language
    total_new_strings = 0
    updated_languages = []

    for lang_dir in sorted(lang_dirs):
        lc_messages = lang_dir / "LC_MESSAGES"
        lc_messages.mkdir(parents=True, exist_ok=True)

        po_file = lc_messages / "messages.po"

        print(f"Language: {lang_dir.name}")
        new_strings = update_po_from_pot(pot_file, po_file)
        total_new_strings += new_strings
        updated_languages.append(lang_dir.name)
        print()

    # Summary
    print("=" * 60)
    print(f"Updated {len(updated_languages)} language(s): {', '.join(updated_languages)}")

    if total_new_strings > 0:
        print()
        print(f"Total new untranslated strings: {total_new_strings}")
        print()
        print("Next steps:")
        print("  1. Translate manually or run:")
        print(
            "     python scripts/translation_management/translate_po.py locales/fr/LC_MESSAGES/messages.po"
        )
        print("  2. Compile with:")
        print("     python scripts/translation_management/compile_translations.py")
    else:
        print("All translations are up to date!")

    return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.")
        sys.exit(130)
    except Exception:
        print("\nUnexpected error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)
