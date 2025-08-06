import re
import os
import unicodedata

from symspellpy import SymSpell, Verbosity
from Levenshtein import distance as levenshtein_distance

import config
from libs.logging import get_logger

# Module-specific logger that uses the module name as prefix for log messages
logger = get_logger(__name__)

# Unicode character ranges for different languages
LANGUAGE_RANGES = {
    "de": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÄÖÜäöüß",
    "fr": "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyzÀÂÇÉÈÊËÎÏÔÙÛÜŸàâçéèêëîïôùûüÿ"
}

# Load word spelling dictionaries
def load_symspell(dictionary_path, max_edit_distance=2, separator=" "):
    """Loads dictionaries for text autocorrection."""
    sym_spell = SymSpell(max_dictionary_edit_distance=max_edit_distance, prefix_length=7)

    if not sym_spell.load_dictionary(dictionary_path, term_index=0, count_index=1, separator=separator):
        logger.error(f"❌ Failed to load dictionary: {dictionary_path}")
        return None
    
    return sym_spell


def initialize():
    global WORD_DICTS, NAME_DICTS, BOOKTITLE_DICTS

    word_dict_paths = {
        "en": os.path.join(config.DICT_DIR, "frequency_en.txt"),
        "de": os.path.join(config.DICT_DIR, "frequency_de.txt"),
        "fr": os.path.join(config.DICT_DIR, "frequency_fr.txt"),
        "it": os.path.join(config.DICT_DIR, "frequency_it.txt")
    }
    WORD_DICTS = {lang: load_symspell(path) for lang, path in word_dict_paths.items()}

    for lang, sym_spell in WORD_DICTS.items():
        if sym_spell:
            logger.info(f"✅ Loaded {len(sym_spell.words)} words for '{lang}'")
        else:
            logger.error(f"❌ Failed to load words dictionary for '{lang}'")

    # Load author name dictionaries
    name_dict_paths = {
        "de": os.path.join(config.DICT_DIR, "names.de.txt")
    }
    NAME_DICTS = {lang: load_symspell(path, separator="\t") for lang, path in name_dict_paths.items()}

    for lang, sym_spell in NAME_DICTS.items():
        if sym_spell:
            logger.info(f"✅ Loaded {len(sym_spell.words)} names for '{lang}'")
        else:
            logger.error(f"❌ Failed to load name dictionary for '{lang}'")


    # Load book title dictionaries
    booktitle_dict_paths = {
        "de": os.path.join(config.DICT_DIR, "book_titles.de.txt")
    }
    BOOKTITLE_DICTS = {lang: load_symspell(path, separator="\t") for lang, path in booktitle_dict_paths.items()}

    for lang, sym_spell in BOOKTITLE_DICTS.items():
        if sym_spell:
            logger.info(f"✅ Loaded {len(sym_spell.words)} book titles for '{lang}'")
        else:
            logger.error(f"❌ Failed to load book title dictionary for '{lang}'")


def get_language_charset(languages):
    """Creates a character set with all letters of the desired languages."""
    allowed_chars = set()
    for lang in languages:
        if lang in LANGUAGE_RANGES:
            allowed_chars.update(LANGUAGE_RANGES[lang])
        else:
            logger.warning(f"⚠ Language {lang} not recognized, will be ignored.")
    return "".join(allowed_chars)


def clean_ocr_text(text, languages=("de", "fr")):
    """
    Cleans OCR text based on allowed characters for specific languages.
    
    Improvements:
    - Replaces unwanted characters with spaces instead of removing them
    - Preserves numbers when they are part of words or standalone
    - Preserves punctuation (. : / ; -) when part of words, removes when standalone
    - Removes special characters like trademark symbols
    - Normalizes multiple spaces to single spaces
    
    Args:
        text (str): The text to clean
        languages (tuple): Language codes for allowed character sets
        
    Returns:
        str: Cleaned text with proper spacing and case normalization
    """
    allowed_chars = get_language_charset(languages)
    # Define punctuation that should be preserved when part of words
    punctuation_to_preserve = ".:/;-"

    # First, remove known problematic symbols before Unicode normalization
    # to prevent them from being converted to valid characters
    problematic_symbols = "™®©"
    for symbol in problematic_symbols:
        text = text.replace(symbol, " ")

    # Unicode normalization to represent inconsistent characters
    text = unicodedata.normalize("NFKC", text)

    # Process character by character, with intelligent punctuation handling
    cleaned_chars = []
    for i, char in enumerate(text):
        if char in allowed_chars or char.isspace():
            # Keep allowed characters and existing spaces
            cleaned_chars.append(char)
        elif char.isdigit():
            # Keep digits (they can be part of titles like "2nd Edition" or years like "2022")
            cleaned_chars.append(char)
        elif char in punctuation_to_preserve:
            # Keep punctuation if:
            # 1. Between alphanumeric characters (e.g., "8/9", "2.5")
            # 2. Multiple punctuation together (e.g., "J.K.")
            # 3. At the end of a word followed by space (e.g., "Title: Subtitle")
            
            has_char_before = i > 0 and (text[i-1].isalnum() or text[i-1] in punctuation_to_preserve)
            has_char_after = i < len(text) - 1 and (text[i+1].isalnum() or text[i+1] in punctuation_to_preserve)
            has_space_after = i < len(text) - 1 and text[i+1].isspace()
            
            if has_char_before and (has_char_after or has_space_after):
                # Keep punctuation
                cleaned_chars.append(char)
            else:
                # Standalone punctuation, replace with space
                cleaned_chars.append(' ')
        else:
            # Replace unwanted characters with space
            cleaned_chars.append(' ')
    
    # Join characters and normalize spaces
    text = ''.join(cleaned_chars)
    
    # Remove multiple spaces and convert text to lowercase
    text = re.sub(r"\s+", " ", text).strip().lower()
    
    return text


def detect_names(word, lang="de"):
    """Checks if a word is a known name by matching it against the author list."""
    if lang not in NAME_DICTS or not NAME_DICTS[lang]:
        return False  # If no names are known, don't recognize as name
    
    suggestions = NAME_DICTS[lang].lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
    return bool(suggestions)  # True if word is a known name


def is_valid_word(word, lang="de"):
    """Checks if a word is a valid word in the word or name dictionary."""
    if lang in WORD_DICTS and WORD_DICTS[lang]:
        if word in WORD_DICTS[lang].words:
            return True

    if lang in NAME_DICTS and NAME_DICTS[lang]:
        if word in NAME_DICTS[lang].words:
            return True

    return False


def compute_validity_score(text, lang="de"):
    """Calculates the percentage of valid words in a text."""
    words = text.split()
    if not words:
        return 0.0  # Prevent division by zero

    valid_words = [word for word in words if is_valid_word(word, lang)]
    return len(valid_words) / len(words)


def match_to_words(text, lang="de"):
    """Corrects OCR text using autocorrection for different languages, 
    but leaves recognized names unchanged."""

    # Correct each word individually
    corrected_words = []

    if lang in WORD_DICTS and WORD_DICTS[lang]:
        for word in text.split():
            # Name detection: If the word is a name, don't correct it
            if detect_names(word, lang):
                corrected_words.append(word)
                continue

            # If not a name, correct normally with autocorrection
            suggestions = WORD_DICTS[lang].lookup(word, Verbosity.CLOSEST, max_edit_distance=2)
            if suggestions:
                corrected_words.append(suggestions[0].term)  # Take best correction
            else:
                corrected_words.append(word)  # If no correction possible, keep the original

        # Output result
        corrected_text = " ".join(corrected_words)

    return corrected_text


def match_to_titles(text, lang="de"):
    """Corrects text specifically against a book title list."""
    if lang not in BOOKTITLE_DICTS or not BOOKTITLE_DICTS[lang]:
        logger.warning(f"⚠ No SymSpell dictionary found for language '{lang}'.")
        return text  # Return without correction if no dictionary is available

    suggestions = BOOKTITLE_DICTS[lang].lookup_compound(text, max_edit_distance=2)

    if suggestions:
        corrected_text = suggestions[0].term
        return corrected_text
    else:
        logger.info(f"⚠ No correction found for: '{text}'.")
        return text  # No correction found
    

def is_match_better(corrected, matched, lev_threshold=0.4, jaccard_threshold=0.5):
    """
    Compares corrected and matched titles using Levenshtein distance and Jaccard similarity.
    Returns True if the matched title is a good replacement, otherwise False.
    """
    if not corrected or not matched:
        return False  # Avoid empty matches being considered better

    # Levenshtein Distance Score (normalized)
    lev_dist = levenshtein_distance(corrected, matched)
    max_len = max(len(corrected), len(matched))
    lev_similarity = 1 - (lev_dist / max_len) if max_len > 0 else 0
    
    # Jaccard Similarity (word overlap)
    set_corrected = set(corrected.lower().split())
    set_matched = set(matched.lower().split())
    intersection = len(set_corrected & set_matched)
    union = len(set_corrected | set_matched)
    jaccard_similarity = intersection / union if union != 0 else 0
    
    # The matched title is only accepted if it meets both criteria
    return lev_similarity >= lev_threshold and jaccard_similarity >= jaccard_threshold


def select_best_title(corrected_title, matched_title):
    """
    Determines the best title to use: either the corrected OCR title or the matched book title.
    """
    if is_match_better(corrected_title, matched_title):
        return matched_title
    return corrected_title
