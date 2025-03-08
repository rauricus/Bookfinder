import os
import argparse
import sqlite3
import json
import gzip
import requests

HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
DB_PATH = os.path.join(HOME_DIR, "books.db")

# Default parameters
DEFAULT_LANGUAGES = ["de"]
DEFAULT_SUBJECTS = ["science", "history", "fiction", "technology", "fantasy", "philosophy"]
DEFAULT_BOOK_LIMIT = 1000
DEFAULT_FREQUENCY = 100000

def initialize_database():
    """Create the SQLite database and books table if they don't exist."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS books (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            authors TEXT,
            year TEXT,
            isbn TEXT,
            language TEXT NOT NULL,
            UNIQUE(title, language)
        )
    """)
    conn.commit()
    conn.close()

def purge_database():
    """Deletes all data from the books database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM books")
    conn.commit()
    conn.close()
    print("🗑️ Database purged successfully.")

def fetch_books_from_openlibrary(languages, queries, max_books_per_query=1000):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    lang_map = {'en': 'eng', 'de': 'ger', 'fr': 'fre', 'it': 'ita'}

    for lang in languages:
        lang_code = lang_map.get(lang, 'eng')
        for query in queries.get(lang, []):
            url = f"https://openlibrary.org/search.json?q={query}&language={lang_code}&limit={max_books_per_query}&sort=editions"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                books = data.get("docs", [])
                for book in books:
                    if 'language' in book and lang_code not in book['language']:
                        continue  # Skip if language does not match exactly

                    title = book.get('title', '').strip()
                    if not title:
                        continue

                    authors = ", ".join(book.get('author_name', [])) if 'author_name' in book else "Unknown"
                    year = str(book.get('first_publish_year', 'Unknown'))
                    isbn = book.get('isbn', ['Unknown'])[0]

                    try:
                        cursor.execute("""
                            INSERT INTO books (title, authors, year, isbn, language)
                            VALUES (?, ?, ?, ?, ?)
                        """, (title, authors, year, isbn, lang))
                    except sqlite3.IntegrityError:
                        continue  # Duplicate entry
            else:
                print(f"⚠️ Failed to fetch books for query '{query}' in language '{lang}'.")

    conn.commit()
    conn.close()

def save_titles_for_symspell(output_dir, frequency):
    """Fetch book titles from the database and save in SymSpell-compatible format per language."""
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT language FROM books")
    languages = [row[0] for row in cursor.fetchall()]

    for lang in languages:
        cursor.execute("SELECT title FROM books WHERE language = ?", (lang,))
        titles = [row[0] for row in cursor.fetchall()]

        if not titles:
            continue

        output_file = os.path.join(output_dir, f"book_titles.{lang}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for title in sorted(set(titles)):
                f.write(f"{title}\t{frequency}\n")

        print(f"📂 Saved {len(titles)} book titles for '{lang}' to {output_file}")

    conn.close()

def main():
    parser = argparse.ArgumentParser(description="Fetch book titles using pragmatic OpenLibrary queries and store in the local database.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="Languages (ISO 639-1 codes)")
    parser.add_argument("--limit", type=int, default=1000, help="Max number of books per query per language")
    parser.add_argument("--purge", action="store_true", help="Clear database before fetching new books")

    args = parser.parse_args()

    queries_by_language = {
        'de': ['der', 'die', 'das', 'und', 'ein', 'eine'],
        'en': ['the', 'and', 'of', 'in', 'to', 'a'],
        'fr': ['le', 'la', 'et', 'les', 'un', 'une'],
        'it': ['il', 'la', 'di', 'e', 'un', 'una']
    }

    initialize_database()

    if args.purge:
        purge_database()

    fetch_books_from_openlibrary(args.languages, queries_by_language, args.limit)

    save_titles_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)

    print("✅ Finished fetching and storing book data using pragmatic queries.")

if __name__ == "__main__":
    main()