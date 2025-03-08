import os
import argparse
import requests
import sqlite3
import xml.etree.ElementTree as ET
import json
import gzip

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

def fetch_books_from_openlibrary_dump(dump_file, languages, max_books_per_lang=50000):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    lang_counts = {lang: 0 for lang in languages}
    lang_map = {'en': 'eng', 'de': 'ger', 'fr': 'fre', 'it': 'ita'}

    with gzip.open(dump_file, 'rt', encoding='utf-8') as f:
        for line in f:
            try:
                book = json.loads(line)
                title = book.get("title", "").strip()
                book_languages = [lang['key'].split('/')[-1] for lang in book.get('languages', []) if 'key' in lang]

                for lang in languages:
                    lang_code = lang_map.get(lang, lang)
                    if lang_code in book_languages and lang_counts[lang] < max_books_per_lang:
                        try:
                            cursor.execute("""
                                INSERT INTO books (title, authors, year, isbn, language)
                                VALUES (?, ?, ?, ?, ?)
                            """, (title, "Unknown", "Unknown", "Unknown", lang))
                            lang_counts[lang] += 1
                        except sqlite3.IntegrityError:
                            pass  # Duplicate entry
            except json.JSONDecodeError:
                continue

            if all(count >= max_books_per_lang for count in lang_counts.values()):
                break

    conn.commit()
    conn.close()


API_URL = "https://swisscovery.slsp.ch/view/sru/41SLSP_NETWORK"
ns = {'marc': 'http://www.loc.gov/MARC21/slim'}

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
    parser = argparse.ArgumentParser(description="Fetch book titles from OpenLibrary dump and store in the local database.")
    parser.add_argument("--languages", nargs="+", default=DEFAULT_LANGUAGES, help="List of languages (ISO 639-1 codes)")
    parser.add_argument("--dump_file", type=str, default="ol_dump_editions_latest.txt.gz", help="Path to OpenLibrary dump file")
    parser.add_argument("--limit", type=int, default=50000, help="Max number of books per language")
    parser.add_argument("--purge", action="store_true", help="Clear database before fetching new books")
    
    args = parser.parse_args()

    initialize_database()

    if args.purge:
        purge_database()

    print(f"📚 Fetching books from OpenLibrary dump for languages: {args.languages}...")
    fetch_books_from_openlibrary_dump(args.dump_file, args.languages, args.limit)

    save_titles_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)

    print("✅ Finished fetching and storing book data from OpenLibrary dump.")

if __name__ == "__main__":
    main()