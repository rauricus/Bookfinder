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

OUTPUT_FILE = os.path.join(DICT_DIR, "book_titles.txt")



def fetch_titles_from_openlibrary(subject, languages, book_limit):
    """Fetch book titles from OpenLibrary API based on subject and languages"""
    titles = []
    for lang in languages:
        url = f"https://openlibrary.org/subjects/{subject}.json?limit={book_limit}&lang={lang}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            books = data.get("works", [])
            titles.extend(book["title"] for book in books if "title" in book)
        else:
            print(f"⚠️ Failed to fetch data for subject '{subject}' in language '{lang}'")

    return titles

def save_titles_for_symspell(titles, output_file, frequency):
    """Save titles in SymSpell-compatible format"""
    with open(output_file, "w", encoding="utf-8") as f:
        for title in sorted(set(titles)):  # Remove duplicates
            f.write(f"{title}\t{frequency}\n")

def main():
    # Argument parser for CLI options
    parser = argparse.ArgumentParser(description="Fetch book titles from OpenLibrary and convert to SymSpell format.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="List of languages (ISO 639-1 codes, e.g., 'de', 'en', 'fr')")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS, help="List of subjects to fetch")
    parser.add_argument("--limit", type=int, default=DEFAULT_BOOK_LIMIT, help="Number of books to fetch per subject")
    
    args = parser.parse_args()

    all_titles = []
    for subject in args.subjects:
        print(f"📚 Fetching books for subject '{subject}' in languages: {args.languages}...")
        titles = fetch_titles_from_openlibrary(subject, args.languages, args.limit)
        all_titles.extend(titles)

    print(f"✅ Fetched {len(all_titles)} unique book titles.")

    save_titles_for_symspell(all_titles, OUTPUT_FILE, DEFAULT_FREQUENCY)
    print(f"📂 Saved {len(all_titles)} book titles to {OUTPUT_FILE} in SymSpell format.")

if __name__ == "__main__":
    main()