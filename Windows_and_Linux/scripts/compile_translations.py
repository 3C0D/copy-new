#!/usr/bin/env python3
"""
Translation compilation script
Usage: python compile_translations.py [language]
"""

import argparse
import os
import sys
from pathlib import Path


def compile_language(lang_code):
    """Compile translations for a given language"""
    po_file = Path(f"locales/{lang_code}/LC_MESSAGES/messages.po")
    mo_file = Path(f"locales/{lang_code}/LC_MESSAGES/messages.mo")

    if not po_file.exists():
        print(f"ERROR {lang_code}: File {po_file} not found")
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
    locales_dir = Path("locales")

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
