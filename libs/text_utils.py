import re
import unicodedata

from symspellpy import SymSpell, Verbosity


# Unicode-Zeichenbereiche für verschiedene Sprachen
LANGUAGE_RANGES = {
    "de": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß",
    "fr": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÂÇÉÈÊËÎÏÔÙÛÜŸàâçéèêëîïôùûüÿ"
}

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

def autocorrect_ocr_text(text, symspell_dicts, lang="en"):
    """Korrigiert OCR-Text mittels Autokorrektur für verschiedene Sprachen."""

    # Jedes Wort einzeln korrigieren
    corrected_words = []

    if lang in symspell_dicts and symspell_dicts[lang]:
        for word in text.split():
            suggestions = symspell_dicts[lang].lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            if suggestions:
                corrected_words.append(suggestions[0].term)  # Beste Korrektur nehmen
            else:
                corrected_words.append(word)  # Falls keine Korrektur möglich ist, das Original behalten

        # Ergebnis ausgeben
        corrected_text = " ".join(corrected_words)

    return corrected_text
