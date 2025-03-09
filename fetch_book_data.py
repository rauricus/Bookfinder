import os
import argparse

import json
import gzip

import sqlite3
import requests

from langdetect import detect, LangDetectException


HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
DB_PATH = os.path.join(HOME_DIR, "books.db")

# Supported languages
SUPPORTED_LANGUAGES = ["de"]

# Default parameters
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

        lang_code = lang_map.get(lang)
        if not lang_code:
            print(f"❌ Language '{lang}' not supported. Skipping it.")
            continue

        print(f"📚 Starting fetch for language '{lang}'...")
        for query in queries.get(lang, []):

            print(f"    Query '{query}'...")

            url = f"https://openlibrary.org/search.json?q={query}&language={lang_code}&limit={max_books_per_query}&sort=editions"
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                books = data.get("docs", [])
 
                inserted_count = 0 # Count of inserted books, for showing a progress indicator

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
                        inserted_count += 1

                        if inserted_count % 100 == 0:
                            print(f"        📚 {inserted_count} books inserted...")
                            
                    except sqlite3.IntegrityError:
                        continue  # Duplicate entry

        print(f"📚 Finished fetching for language '{lang}'.")
    conn.commit()
    conn.close()

def is_correct_language(title, target_lang):
    try:
        detected_lang = langdetect.detect(title)
        return detected_lang == lang
    except:
        return False


def main():
    parser = argparse.ArgumentParser(description="Fetch book titles using pragmatic OpenLibrary queries and store in the local database.")
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

    fetch_books_from_openlibrary(SUPPORTED_LANGUAGES, queries_by_language, args.limit)

    print("✅ Finished fetching and storing book data. Run `generate_dictionaries.py` to create dictionary files.")

if __name__ == "__main__":
    main()