import os
import argparse

import requests
import json

HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")


# Default parameters
DEFAULT_LANGUAGES = ["de"]  # German by default
DEFAULT_SUBJECTS = ["science", "history", "fiction", "technology", "fantasy", "philosophy"]
DEFAULT_BOOK_LIMIT = 1000
DEFAULT_FREQUENCY = 100000

 



def fetch_titles_from_openlibrary(subject, languages, book_limit):
    """Fetch book titles from OpenLibrary API based on subject and languages"""
    titles_by_language = {lang: [] for lang in languages}
    for lang in languages:
        url = f"https://openlibrary.org/subjects/{subject}.json?limit={book_limit}&lang={lang}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            books = data.get("works", [])
            titles_by_language[lang].extend(book["title"] for book in books if "title" in book)
        else:
            print(f"⚠️ Failed to fetch data for subject '{subject}' in language '{lang}'")

    return titles_by_language

def save_titles_for_symspell(titles, output_file, frequency):
    """Save titles in SymSpell-compatible format, separated by language"""
    for lang, titles in titles.items():
        if not titles:
            continue
        output_file = os.path.join(DICT_DIR, f"book_titles_{lang}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for title in sorted(set(titles)):  # Remove duplicates
                f.write(f"{title}\t{frequency}\n")
        print(f"📂 Saved {len(set(titles))} book titles for '{lang}' to {output_file}")

def main():
    # Argument parser for CLI options
    parser = argparse.ArgumentParser(description="Fetch book titles from OpenLibrary and convert to SymSpell format.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="List of languages (ISO 639-1 codes, e.g., 'de', 'en', 'fr')")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS, help="List of subjects to fetch")
    parser.add_argument("--limit", type=int, default=DEFAULT_BOOK_LIMIT, help="Number of books to fetch per subject")
    
    args = parser.parse_args()

    all_titles_by_language = {lang: [] for lang in args.languages}
    for subject in args.subjects:
        print(f"📚 Fetching books for subject '{subject}' in languages: {args.languages}...")
        titles_by_language = fetch_titles_from_openlibrary(subject, args.languages, args.limit)
        for lang in args.languages:
            all_titles_by_language[lang].extend(titles_by_language.get(lang, []))

    total_titles = {lang: len(set(titles)) for lang, titles in all_titles_by_language.items()}
    for lang, count in total_titles.items():
        print(f"✅ Fetched {count} unique book titles for language '{lang}'.")

    save_titles_for_symspell(all_titles_by_language, DICT_DIR, DEFAULT_FREQUENCY)
    print("✅ Finished fetching and saving book titles.")

if __name__ == "__main__":
    main()