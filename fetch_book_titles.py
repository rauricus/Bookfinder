import os
import argparse

import requests
import sqlite3

import xml.etree.ElementTree as ET


HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
DB_PATH = os.path.join(HOME_DIR, "books.db")

API_URL = "https://slsp-network.alma.exlibrisgroup.com/view/sru/41SLSP_NETWORK"
ns = {'marc': 'http://www.loc.gov/MARC21/slim'}

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


def fetch_books_from_swisscovery(subject, languages, book_limit):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    lang_map = {'en': 'eng', 'de': 'ger', 'fr': 'fre', 'it': 'ita'}

    for lang in languages:
        lang_code = lang_map.get(lang, "eng")

        response = requests.get(API_URL, params={
            "version": "1.2",
            "operation": "searchRetrieve",
            "query": f'alma.subjects="{subject}" AND alma.language="{lang_code}"',
            "maximumRecords": book_limit
        })

        if response.status_code == 200:
            root = ET.fromstring(response.text)
            records = root.findall(".//{http://www.loc.gov/MARC21/slim}record")

            for record in records:
                title_elem = record.find(".//{http://www.loc.gov/MARC21/slim}datafield[@tag='245']/{http://www.loc.gov/MARC21/slim}subfield[@code='a']")
                author_elem = record.find(".//{http://www.loc.gov/MARC21/slim}datafield[@tag='100']/{http://www.loc.gov/MARC21/slim}subfield[@code='a']")
                pub_year_elem = record.find(".//{http://www.loc.gov/MARC21/slim}datafield[@tag='260']/{http://www.loc.gov/MARC21/slim}subfield[@code='c']")

                title = title_elem.text.strip() if title_elem is not None else "Unknown"
                authors = author_elem.text.strip() if author_elem is not None else "Unknown"
                publication_year = pub_year_elem.text.strip() if pub_year_elem is not None else "Unknown"

                try:
                    cursor.execute("""
                        INSERT INTO books (title, authors, year, isbn, language)
                        VALUES (?, ?, ?, ?, ?)
                    """, (title, authors, publication_year, "Unknown", lang))
                except sqlite3.IntegrityError:
                    pass  # Duplicate entry
        else:
            print(f"⚠️ Failed to fetch books for subject '{subject}' in language '{lang}' from swisscovery.")

    conn.commit()
    conn.close()


def fetch_books_from_openlibrary(subject, languages, book_limit):
    """Fetch book titles and metadata from OpenLibrary API and store them in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    lang_map = {'en': 'eng', 'de': 'ger', 'fr': 'fre', 'it': 'ita'}

    for lang in languages:
        lang_code = lang_map.get(lang, "eng")
        # Correct API call for strict language filtering
        url = f"https://openlibrary.org/search.json?q=*&subject={subject}&language={lang_code}&limit={book_limit}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            books = data.get("docs", [])

            for book in books:
                title = book.get("title", "").strip()
                authors = ", ".join(book.get("author_name", [])) if "author_name" in book else "Unknown"
                publication_year = str(book.get("first_publish_year", "Unknown"))
                isbn = book.get("isbn", ["Unknown"])[0]

                try:
                    cursor.execute("""
                        INSERT INTO books (title, authors, year, isbn, language)
                        VALUES (?, ?, ?, ?, ?)
                    """, (title, authors, publication_year, isbn, lang))
                except sqlite3.IntegrityError:
                    pass  # Duplicate entry
        else:
            print(f"⚠️ Failed to fetch books for subject '{subject}' in language '{lang}'.")

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
    parser = argparse.ArgumentParser(description="Fetch book titles and metadata from OpenLibrary and store in a database.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="List of languages (ISO 639-1 codes)")
    parser.add_argument("--subjects", nargs="+", default=DEFAULT_SUBJECTS, help="List of subjects to fetch")
    parser.add_argument("--limit", type=int, default=DEFAULT_BOOK_LIMIT, help="Number of books to fetch per subject")
    
    args = parser.parse_args()

    initialize_database()

    for subject in args.subjects:
        print(f"📚 Fetching books for subject '{subject}' in languages: {args.languages}...")
        fetch_books_from_swisscovery(subject, args.languages, args.limit)

    save_titles_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)

    print("✅ Finished fetching and storing book data.")

if __name__ == "__main__":
    main()