import re
import unicodedata

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