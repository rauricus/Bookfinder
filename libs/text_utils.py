import re
import os
import unicodedata

from symspellpy import SymSpell, Verbosity


HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")

# Unicode-Zeichenbereiche für verschiedene Sprachen
LANGUAGE_RANGES = {
    "de": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß",
    "fr": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÂÇÉÈÊËÎÏÔÙÛÜŸàâçéèêëîïôùûüÿ"
}

# Load word spelling dictionaries
def load_symspell(dictionary_path, max_edit_distance=2, separator=" "):
    """Lädt Dictionaires für Text Autokorrektur."""
    sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=7)

    if not sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1, separator=separator):
        print(f"❌ Failed to load dictionary: {dictionary_path}")
        return None
    
    return sym_spell


word_dict_paths = {
    "en": os.path.join(DICT_DIR, "frequency_en.txt"),
    "de": os.path.join(DICT_DIR, "frequency_de.txt"),
    "fr": os.path.join(DICT_DIR, "frequency_fr.txt"),
    "it": os.path.join(DICT_DIR, "frequency_it.txt")
}
WORD_DICTS = {lang: load_symspell(path) for lang, path in word_dict_paths.items()}

for lang, sym_spell in WORD_DICTS.items():
    if sym_spell:
        print(f"✅ Loaded {len(sym_spell.words)} words for '{lang}'")
    else:
        print(f"❌ Failed to load words dictionary for '{lang}'")

# Load author name dictionaries
name_dict_paths = {
    "de": os.path.join(DICT_DIR, "names.de.txt")
}
NAME_DICTS = {lang: load_symspell(path, separator="\t") for lang, path in name_dict_paths.items()}

for lang, sym_spell in NAME_DICTS.items():
    if sym_spell:
        print(f"✅ Loaded {len(sym_spell.words)} names for '{lang}'")
    else:
        print(f"❌ Failed to load name dictionary for '{lang}'")


# Load book title dictionaries
booktitle_dict_paths = {
    "de": os.path.join(DICT_DIR, "book_titles.de.txt")
}
BOOKTITLE_DICTS = {lang: load_symspell(path, separator="\t") for lang, path in booktitle_dict_paths.items()}

for lang, sym_spell in BOOKTITLE_DICTS.items():
    if sym_spell:
        print(f"✅ Loaded {len(sym_spell.words)} book titles for '{lang}'")
        print("Total book titles loaded:", len(sym_spell.words))
        print("Sample words:", list(sym_spell.words.keys())[:20])  # Print first 20 entries
    else:
        print(f"❌ Failed to load book title dictionary for '{lang}'")


def get_language_charset(languages):
    """Erstellt eine Zeichenmenge mit allen Buchstaben der gewünschten Sprachen."""
    allowed_chars = set()
    for lang in languages:
        if lang in LANGUAGE_RANGES:
            allowed_chars.update(LANGUAGE_RANGES[lang])
        else:
            print(f"⚠ Sprache {lang} nicht bekannt, wird ignoriert.")
    return "".join(allowed_chars)


def clean_ocr_text(text, languages=("de", "fr")):
    """Bereinigt OCR-Text basierend auf erlaubten Zeichen für bestimmte Sprachen."""
    allowed_chars = get_language_charset(languages)

    # Unicode-Normalisierung, um inkonsistente Zeichen darzustellen
    text = unicodedata.normalize("NFKC", text)

    # Entfernt alle Zeichen, die nicht in der erlaubten Zeichengruppe sind
    text = "".join(char for char in text if char in allowed_chars or char.isspace())

    # Mehrfache Leerzeichen entfernen und Text in Kleinbuchstaben umwandeln
    text = re.sub(r"\s+", " ", text).strip().lower()
    
    return text


def detect_names(word, lang="de"):
    """Überprüft, ob ein Wort ein bekannter Name ist, indem es mit der Autorenliste abgeglichen wird."""
    if lang not in NAME_DICTS or not NAME_DICTS[lang]:
        return False  # Falls keine Namen bekannt, nicht als Name erkennen
    
    suggestions = NAME_DICTS[lang].lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    return bool(suggestions)  # True, falls Wort ein bekannter Name ist


def match_to_words(text, lang="de"):
    """Korrigiert OCR-Text mittels Autokorrektur für verschiedene Sprachen, 
    aber belässt erkannte Namen unverändert."""

    # Jedes Wort einzeln korrigieren
    corrected_words = []

    if lang in WORD_DICTS and WORD_DICTS[lang]:
        for word in text.split():
            # Namenserkennung: Falls das Wort ein Name ist, nicht korrigieren
            if detect_names(word, lang):
                corrected_words.append(word)
                continue

            # Falls kein Name, normal mit Autokorrektur korrigieren
            suggestions = WORD_DICTS[lang].lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            if suggestions:
                corrected_words.append(suggestions[0].term)  # Beste Korrektur nehmen
            else:
                corrected_words.append(word)  # Falls keine Korrektur möglich ist, das Original behalten

        # Ergebnis ausgeben
        corrected_text = " ".join(corrected_words)

    return corrected_text


def match_to_titles(text, lang="de"):
    """Korrigiert text speziell gegen eine Buchtitelliste."""
    if lang not in BOOKTITLE_DICTS or not BOOKTITLE_DICTS[lang]:
        print(f"⚠ Kein SymSpell-Wörterbuch für Sprache '{lang}' gefunden.")
        return text  # Ohne Korrektur zurückgeben, wenn kein Wörterbuch verfügbar ist

    suggestions = BOOKTITLE_DICTS[lang].lookup_compound(text, max_edit_distance=2)

    if suggestions:
        corrected_text = suggestions[0].term
        print(f"📖 OCR-Korrektur: '{text}' → '{corrected_text}'")
        return corrected_text
    else:
        print(f"⚠ Keine Korrektur für: '{text}' gefunden.")
        return text  # Keine Korrektur gefunden