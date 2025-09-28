#!/usr/bin/env python3
"""
Automatic translation script for .po files
Uses Google Translate API to translate empty strings
"""

import sys
from pathlib import Path

# Add parent directory to path to import from myvenv
sys.path.insert(0, str(Path(__file__).parent.parent / "myvenv" / "Lib" / "site-packages"))

try:
    import polib
    from deep_translator import GoogleTranslator
    from googletrans import Translator
except ImportError as e:
    print(f"Import error: {e}")
    print("Install dependencies: pip install polib googletrans deep-translator")
    sys.exit(1)


def translate_text(text, src="en", dest="fr"):
    """Translate text using Google Translate"""
    try:
        # Try deep-translator first (more reliable)
        translator = GoogleTranslator(source=src, target=dest)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Error with deep-translator: {e}")
        try:
            # Fallback to googletrans
            translator = Translator()
            result = translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e2:
            print(f"Error with googletrans: {e2}")
            return text  # Return original text if failure


def translate_po_file(po_file_path, src_lang="en", dest_lang="fr"):
    """Translate all empty entries in a .po file"""
    print(f"Loading file: {po_file_path}")

    # Load the .po file
    po = polib.pofile(po_file_path)

    translated_count = 0
    total_entries = len([e for e in po if e.msgid and not e.msgstr])

    print(f"Entries to translate: {total_entries}")

    # Go through all entries
    for entry in po:
        if entry.msgid and not entry.msgstr:  # Only untranslated entries
            print(f"Translating: {entry.msgid[:50]}...")
            translated = translate_text(entry.msgid, src_lang, dest_lang)
            entry.msgstr = translated
            translated_count += 1

            # Show progress
            if translated_count % 10 == 0:
                print(f"Progress: {translated_count}/{total_entries}")

    # Save the file
    po.save()
    print(f"Translation completed: {translated_count} entries translated")

    return translated_count


def compile_po_to_mo(po_file_path):
    """Compile a .po file to .mo"""
    mo_file_path = po_file_path.replace(".po", ".mo")
    po = polib.pofile(po_file_path)
    po.save_as_mofile(mo_file_path)
    print(f"Compiled: {mo_file_path}")


def main():
    """Main function"""
    if len(sys.argv) < 2:
        print("Usage: python translate_po.py <po_file_path> [src_lang] [dest_lang]")
        print("Example: python translate_po.py locales/fr/LC_MESSAGES/messages.po en fr")
        sys.exit(1)

    po_file_path = sys.argv[1]
    src_lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    dest_lang = sys.argv[3] if len(sys.argv) > 3 else "fr"

    if not Path(po_file_path).exists():
        print(f"File not found: {po_file_path}")
        sys.exit(1)

    print(f"Translating {src_lang} -> {dest_lang}")
    print("=" * 50)

    # Translate
    translated_count = translate_po_file(po_file_path, src_lang, dest_lang)

    if translated_count > 0:
        # Compile
        print("\nCompiling...")
        compile_po_to_mo(po_file_path)
        print("Done!")
    else:
        print("No translation needed.")


if __name__ == "__main__":
    main()
