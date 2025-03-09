import os
import sqlite3

HOME_DIR = os.getcwd()
DICT_DIR = os.path.join(HOME_DIR, "dictionaries")
DB_PATH = os.path.join(HOME_DIR, "books.db")

DEFAULT_FREQUENCY = 100000

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

def save_names_for_symspell(output_dir, frequency):
    """Fetch author names from the database and save in SymSpell-compatible format per language."""
    os.makedirs(output_dir, exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT DISTINCT language FROM books")
    languages = [row[0] for row in cursor.fetchall()]

    for lang in languages:
        cursor.execute("SELECT authors FROM books WHERE language = ?", (lang,))
        names = set()
        for row in cursor.fetchall():
            for author in row[0].split(","):
                for part in author.strip().split():
                    if (
                        len(part) > 2 and
                        not any(char in part for char in ".,()-\"") and
                        not any(char.isdigit() for char in part)
                    ):
                        names.add(part)

        if not names:
            continue

        output_file = os.path.join(output_dir, f"names.{lang}.txt")
        with open(output_file, "w", encoding="utf-8") as f:
            for name in sorted(names):
                f.write(f"{name}\t{frequency}\n")

        print(f"📂 Saved {len(names)} names glanced from author's names for '{lang}' to {output_file}")

    conn.close()

if __name__ == "__main__":
    save_titles_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)
    save_names_for_symspell(DICT_DIR, DEFAULT_FREQUENCY)
    print("✅ Finished generating dictionary files.")