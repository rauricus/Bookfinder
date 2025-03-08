import os
import argparse
import requests
import json

HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
METADATA_DIR = os.path.join(HOME_DIR, "metadata")

# Default parameters
DEFAULT_LANGUAGES = ["de"]
DEFAULT_SUBJECTS = ["science", "history", "fiction", "technology", "fantasy", "philosophy"]
DEFAULT_BOOK_LIMIT = 1000
DEFAULT_FREQUENCY = 100000

def fetch_books_from_openlibrary(subject, languages, book_limit):
    """Fetch book titles and metadata from OpenLibrary API."""
    books_by_language = {lang: [] for lang in languages}
    metadata_by_language = {lang: [] for lang in languages}

    for lang in languages:
        url = f"https://openlibrary.org/subjects/{subject}.json?limit={book_limit}&lang={lang}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            books = data.get("works", [])

            for book in books:
                title = book.get("title", "").strip()
                author_names = [author["name"] for author in book.get("authors", [])] if "authors" in book else []
                publication_year = book.get("first_publish_year", "Unknown")
                isbn = book.get("cover_edition_key", "Unknown")

                # Add to title list for SymSpell
                books_by_language[lang].append(title)

                # Store metadata
                metadata_by_language[lang].append({
                    "title": title,
                    "authors": author_names,
                    "year": publication_year,
                    "isbn": isbn
                })
        else:
            print(f"⚠️ Failed to fetch data for subject '{subject}' in language '{lang}'")

    return books_by_language, metadata_by_language

def save_titles_for_symspell(books_by_language, output_dir, frequency):
    """Save titles in SymSpell-compatible format per language."""
    os.makedirs(output_dir, exist_ok=True)

    for lang, titles in books_by_language.items():
        if not titles:
            continue

        output_file = os.path.join(output_dir, f"book_titles_{lang}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for title in sorted(set(titles)):  # Remove duplicates
                f.write(f"{title}\t{frequency}\n")

        print(f"📂 Saved {len(set(titles))} book titles for '{lang}' to {output_file}")

def save_metadata(metadata_by_language, output_dir):
    """Save metadata as JSON per language."""
    os.makedirs(output_dir, exist_ok=True)

    for lang, metadata in metadata_by_language.items():
        if not metadata:
            continue

        json_file = os.path.join(output_dir, f"book_metadata_{lang}.json")

        # Save as JSON
        with open(json_file, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=4, ensure_ascii=False)

        print(f"📂 Saved metadata for '{lang}' to {json_file}")

def main():
    parser = argparse.ArgumentParser(description="Fetch book titles and metadata from OpenLibrary.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="List of languages (ISO 639-1 codes)")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS, help="List of subjects to fetch")
    parser.add_argument("--limit", type=int, default=DEFAULT_BOOK_LIMIT, help="Number of books to fetch per subject")
    
    args = parser.parse_args()

    all_books_by_language = {lang: [] for lang in args.languages}
    all_metadata_by_language = {lang: [] for lang in args.languages}

    for subject in args.subjects:
        print(f"📚 Fetching books for subject '{subject}' in languages: {args.languages}...")
        books_by_language, metadata_by_language = fetch_books_from_openlibrary(subject, args.languages, args.limit)

        for lang in args.languages:
            all_books_by_language[lang].extend(books_by_language.get(lang, []))
            all_metadata_by_language[lang].extend(metadata_by_language.get(lang, []))

    save_titles_for_symspell(all_books_by_language, DICT_DIR, DEFAULT_FREQUENCY)
    save_metadata(all_metadata_by_language, METADATA_DIR)

    print("✅ Finished fetching and saving book titles + metadata.")

if __name__ == "__main__":
    main()