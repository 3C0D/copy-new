#!/usr/bin/env python3
"""
Automatic translation script for .po files
Uses Google Translate API to translate empty strings
"""

import sys
from pathlib import Path

# Add parent directory to path to import utils
script_dir = Path(__file__).parent
project_root = script_dir.parent.parent  # Go up to Windows_and_Linux
sys.path.insert(0, str(project_root))

# Import after path setup
from scripts.utils import get_project_root, get_python_executable  # noqa: E402


def verify_environment():
    """Verify that the virtual environment exists and has required packages"""
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

    # Try to import required packages
    try:
        import polib  # noqa: F401
        from deep_translator import GoogleTranslator  # noqa: F401
        from googletrans import Translator  # noqa: F401
        return True
    except ImportError as e:
        print("=" * 60)
        print("ERROR: Missing dependencies!")
        print("=" * 60)
        print()
        print(f"Import error: {e}")
        print()
        print("Install translation dependencies:")
        print(f"  {python_cmd} -m pip install polib googletrans==4.0.0rc1 deep-translator")
        print()
        return False


def translate_text(text, src="en", dest="fr"):
    """Translate text using Google Translate"""
    from deep_translator import GoogleTranslator
    from googletrans import Translator

    try:
        # Try deep-translator first (more reliable)
        translator = GoogleTranslator(source=src, target=dest)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Warning: deep-translator failed: {e}")
        try:
            # Fallback to googletrans
            translator = Translator()
            result = translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e2:
            print(f"Error: googletrans also failed: {e2}")
            return text  # Return original text if failure


def translate_po_file(po_file_path, src_lang="en", dest_lang="fr", force=False):
    """Translate all empty entries in a .po file, or all entries if force=True"""
    import polib

    print(f"Loading file: {po_file_path}")

    # Load the .po file
    po = polib.pofile(str(po_file_path))

    if force:
        # Force translate all entries
        entries_to_translate = [e for e in po if e.msgid]
        print(f"Force mode: Translating all {len(entries_to_translate)} entries")
    else:
        # Only translate empty entries
        entries_to_translate = [e for e in po if e.msgid and not e.msgstr.strip()]
        print(f"Entries to translate: {len(entries_to_translate)}")

    if not entries_to_translate:
        print("No entries need translation!")
        return 0

    translated_count = 0
    total_entries = len(entries_to_translate)

    # Go through all entries to translate
    for entry in entries_to_translate:
        try:
            preview = entry.msgid[:50]
            if len(entry.msgid) > 50:
                preview += "..."
            print(f"[{translated_count + 1}/{total_entries}] {preview}")
        except UnicodeEncodeError:
            print(f"[{translated_count + 1}/{total_entries}] [Unicode - {len(entry.msgid)} chars]")

        translated = translate_text(entry.msgid, src_lang, dest_lang)
        entry.msgstr = translated
        translated_count += 1

    # Save the file
    po.save()
    print(f"\n* Translation completed: {translated_count} entries translated")

    return translated_count


def compile_po_to_mo(po_file_path):
    """Compile a .po file to .mo"""
    import polib

    mo_file_path = po_file_path.with_suffix('.mo')
    po = polib.pofile(str(po_file_path))
    po.save_as_mofile(str(mo_file_path))
    print(f"* Compiled: {mo_file_path}")


def main():
    """Main function"""
    print("=" * 60)
    print("PO File Translation Tool")
    print("=" * 60)
    print()

    if len(sys.argv) < 2:
        print("Usage: python translate_po.py <po_file_path> [src_lang] [dest_lang] [--force]")
        print()
        print("Examples:")
        print("  python translate_po.py locales/fr/LC_MESSAGES/messages.po")
        print("  python translate_po.py locales/fr/LC_MESSAGES/messages.po en fr")
        print("  python translate_po.py locales/fr/LC_MESSAGES/messages.po en fr --force")
        print()
        return 1

    # Verify environment first (BEFORE trying to import translation libs)
    if not verify_environment():
        return 1

    # Parse arguments
    po_file_path = Path(sys.argv[1])
    src_lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    dest_lang = sys.argv[3] if len(sys.argv) > 3 else "fr"
    force = "--force" in sys.argv

    # Make path absolute relative to project root
    if not po_file_path.is_absolute():
        project_root = get_project_root()
        po_file_path = project_root / po_file_path

    if not po_file_path.exists():
        print(f"ERROR: File not found: {po_file_path}")
        return 1

    print(f"File: {po_file_path.name}")
    print(f"Translation: {src_lang} -> {dest_lang}")
    if force:
        print("Mode: FORCE (retranslate all entries)")
    else:
        print("Mode: Normal (only empty entries)")
    print("-" * 60)
    print()

    # Translate
    translated_count = translate_po_file(po_file_path, src_lang, dest_lang, force)

    if translated_count > 0:
        # Compile
        print("\nCompiling to .mo file...")
        compile_po_to_mo(po_file_path)
        print("\n* All done!")
        return 0
    else:
        print("\n* No translation needed.")
        return 0


if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n\nWARNING: Operation cancelled by user.")
        sys.exit(130)
    except Exception as e:
        print(f"\nERROR: Unexpected error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)