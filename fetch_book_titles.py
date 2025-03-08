import os

import requests
import json


HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")

# List of subjects to fetch book titles from
SUBJECTS = ["science", "history", "fiction", "technology", "fantasy", "philosophy"]

# Number of books per subject
BOOK_LIMIT = 100

# Output file for SymSpell
OUTPUT_FILE = os.path.join(DICT_DIR, "book_titles.txt")

# Default frequency (adjustable)
DEFAULT_FREQUENCY = 100000

def fetch_titles_from_openlibrary(subject):
    """Fetch book titles from OpenLibrary API based on a subject"""
    url = f"https://openlibrary.org/subjects/{subject}.json?limit={BOOK_LIMIT}"
    response = requests.get(url)

    if response.status_code == 200:
        data = response.json()
        books = data.get("works", [])
        return [book["title"] for book in books if "title" in book]
    else:
        print(f"Failed to fetch data for subject: {subject}")
        return []

def save_titles_for_symspell(titles, output_file, frequency):
    """Save titles in SymSpell-compatible format"""
    with open(output_file, "w", encoding="utf-8") as f:
        for title in sorted(set(titles)):  # Remove duplicates
            f.write(f"{title}\t{frequency}\n")

def main():
    all_titles = []

    for subject in SUBJECTS:
        print(f"Fetching books for subject: {subject}...")
        titles = fetch_titles_from_openlibrary(subject)
        all_titles.extend(titles)

    print(f"Fetched {len(all_titles)} unique book titles.")

    save_titles_for_symspell(all_titles, OUTPUT_FILE, DEFAULT_FREQUENCY)
    print(f"Saved {len(all_titles)} book titles to {OUTPUT_FILE} in SymSpell format.")

if __name__ == "__main__":
    main()