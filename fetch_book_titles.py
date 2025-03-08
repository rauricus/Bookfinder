import os
import argparse
import requests
import sqlite3

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
            UNIQUE(title, language)  -- Prevent duplicate titles in the same language
        )
    """)
    conn.commit()
    conn.close()

def fetch_books_from_openlibrary(subject, languages, book_limit):
    """Fetch book titles and metadata from OpenLibrary API and store them in the database."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    for lang in languages:
        url = f"https://openlibrary.org/subjects/{subject}.json?limit={book_limit}&lang={lang}"
        response = requests.get(url)

        if response.status_code == 200:
            data = response.json()
            books = data.get("works", [])

            for book in books:
                title = book.get("title", "").strip()
                authors = ", ".join([author["name"] for author in book.get("authors", [])]) if "authors" in book else "Unknown"
                publication_year = str(book.get("first_publish_year", "Unknown"))
                isbn = book.get("cover_edition_key", "Unknown")

                try:
                    cursor.execute("""
                        INSERT INTO books (title, authors, year, isbn, language)
                        VALUES (?, ?, ?, ?, ?)
                    """, (title, authors, publication_year, isbn, lang))
                except sqlite3.IntegrityError:
                    pass  # Ignore duplicate entries

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

        output_file = os.path.join(output_dir, f"book_titles_{lang}.txt")
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
        fetch_books_from_openlibrary(subject, args.languages, args.limit)

    save_titles_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)

    print("✅ Finished fetching and storing book data.")

if __name__ == "__main__":
    main()