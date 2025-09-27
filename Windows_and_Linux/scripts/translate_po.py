#!/usr/bin/env python3
"""
Script de traduction automatique pour les fichiers .po
Utilise Google Translate API pour traduire les chaînes vides
"""

import sys
from pathlib import Path

# Ajouter le répertoire parent au path pour importer depuis myvenv
sys.path.insert(0, str(Path(__file__).parent.parent / "myvenv" / "Lib" / "site-packages"))

try:
    import polib
    from deep_translator import GoogleTranslator
    from googletrans import Translator
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Installez les dépendances: pip install polib googletrans deep-translator")
    sys.exit(1)


def translate_text(text, src="en", dest="fr"):
    """Traduit un texte en utilisant Google Translate"""
    try:
        # Essayer deep-translator d'abord (plus fiable)
        translator = GoogleTranslator(source=src, target=dest)
        result = translator.translate(text)
        return result
    except Exception as e:
        print(f"Erreur avec deep-translator: {e}")
        try:
            # Fallback vers googletrans
            translator = Translator()
            result = translator.translate(text, src=src, dest=dest)
            return result.text
        except Exception as e2:
            print(f"Erreur avec googletrans: {e2}")
            return text  # Retourner le texte original si échec


def translate_po_file(po_file_path, src_lang="en", dest_lang="fr"):
    """Traduit toutes les entrées vides d'un fichier .po"""
    print(f"Chargement du fichier: {po_file_path}")

    # Charger le fichier .po
    po = polib.pofile(po_file_path)

    translated_count = 0
    total_entries = len([e for e in po if e.msgid and not e.msgstr])

    print(f"Entrées à traduire: {total_entries}")

    # Parcourir toutes les entrées
    for entry in po:
        if entry.msgid and not entry.msgstr:  # Seulement les entrées non traduites
            print(f"Traduction: {entry.msgid[:50]}...")
            translated = translate_text(entry.msgid, src_lang, dest_lang)
            entry.msgstr = translated
            translated_count += 1

            # Afficher la progression
            if translated_count % 10 == 0:
                print(f"Progression: {translated_count}/{total_entries}")

    # Sauvegarder le fichier
    po.save()
    print(f"Traduction terminée: {translated_count} entrées traduites")

    return translated_count


def compile_po_to_mo(po_file_path):
    """Compile un fichier .po en .mo"""
    mo_file_path = po_file_path.replace(".po", ".mo")
    po = polib.pofile(po_file_path)
    po.save_as_mofile(mo_file_path)
    print(f"Compilé: {mo_file_path}")


def main():
    """Fonction principale"""
    if len(sys.argv) < 2:
        print("Usage: python translate_po.py <po_file_path> [src_lang] [dest_lang]")
        print("Exemple: python translate_po.py locales/fr/LC_MESSAGES/messages.po en fr")
        sys.exit(1)

    po_file_path = sys.argv[1]
    src_lang = sys.argv[2] if len(sys.argv) > 2 else "en"
    dest_lang = sys.argv[3] if len(sys.argv) > 3 else "fr"

    if not Path(po_file_path).exists():
        print(f"Fichier non trouvé: {po_file_path}")
        sys.exit(1)

    print(f"Traduction {src_lang} -> {dest_lang}")
    print("=" * 50)

    # Traduire
    translated_count = translate_po_file(po_file_path, src_lang, dest_lang)

    if translated_count > 0:
        # Compiler
        print("\nCompilation...")
        compile_po_to_mo(po_file_path)
        print("Terminé !")
    else:
        print("Aucune traduction nécessaire.")


if __name__ == "__main__":
    main()
