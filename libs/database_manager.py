import sqlite3
from datetime import datetime

class RunContext:
    def __init__(self, db_path, run_id):
        self.db_path = db_path
        self.run_id = run_id

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def update_statistics(self, end_time, books_detected):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE runs
            SET end_time = ?, books_detected = ?
            WHERE id = ?
            """,
            (end_time, books_detected, self.run_id),
        )
        conn.commit()
        conn.close()

    def update_paths(self, input_file=None, output_dir=None):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            UPDATE runs
            SET input_file = ?, output_dir = ?
            WHERE id = ?
            """,
            (input_file, output_dir, self.run_id),
        )
        conn.commit()
        conn.close()

    def log_bookspine(self):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bookspines (run_id)
            VALUES (?)
            """,
            (self.run_id,),
        )
        bookspine_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return bookspine_id

    def log_bookspine_variant(self, bookspine_id, image_path, best_title):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO bookspine_variants (bookspine_id, image_path, best_title)
            VALUES (?, ?, ?)
            """,
            (bookspine_id, image_path, best_title),
        )
        conn.commit()
        conn.close()

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._initialize_tables()  # Initialise tables right during startup.

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def _initialize_tables(self):
        """Initialize all necessary tables in the database."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                books_detected INTEGER DEFAULT 0,
                output_dir TEXT,
                input_file TEXT
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookspines (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS bookspine_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookspine_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                best_title TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bookspine_id) REFERENCES bookspines (id)
            )
        """)

        conn.commit()
        conn.close()

    def create_run(self, start_time, input_file=None, output_dir=None):
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO runs (start_time, input_file, output_dir)
            VALUES (?, ?, ?)
            """,
            (start_time, input_file, output_dir),
        )
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return RunContext(self.db_path, run_id)

    def log_run_start(self, start_time, input_file=None, output_dir=None):
        """
        Log the start of a run into the database and return the run ID.
        
        Args:
            start_time: ISO format datetime string
            input_file: Relative path to the input file
            output_dir: Relative path to the output directory
        """
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO runs (start_time, input_file, output_dir)
            VALUES (?, ?, ?)
        """, (start_time, input_file, output_dir))
        run_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return run_id

    def get_bookspines(self, run_id=None):
        """Retrieve bookspines from the database, optionally filtered by run_id."""
        conn = self._connect()
        cursor = conn.cursor()

        if run_id:
            cursor.execute("SELECT * FROM bookspines WHERE run_id = ?", (run_id,))
        else:
            cursor.execute("SELECT * FROM bookspines")

        rows = cursor.fetchall()
        conn.close()

        return [dict(id=row[0], run_id=row[1], data=row[2]) for row in rows]

    def get_all_runs(self):
        """Retrieve all runs from the database with their details."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, start_time, end_time, books_detected, output_dir, input_file
            FROM runs
            ORDER BY start_time DESC
        """)
        runs = cursor.fetchall()
        conn.close()
        
        return [{
            'run_id': row[0],
            'start_time': row[1],
            'end_time': row[2],
            'books_detected': row[3],
            'output_dir': row[4],
            'input_file': row[5]
        } for row in runs]
