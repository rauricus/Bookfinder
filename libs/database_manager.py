import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self._initialize_tables()  # Initialisiere Tabellen direkt beim Erstellen

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
            CREATE TABLE IF NOT EXISTS detections (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                run_id INTEGER NOT NULL,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (run_id) REFERENCES runs (id)
            )
        """)

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS detection_variants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                detection_id INTEGER NOT NULL,
                image_path TEXT NOT NULL,
                best_title TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (detection_id) REFERENCES detections (id)
            )
        """)

        conn.commit()
        conn.close()

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

    def update_run_statistics(self, run_id, end_time, books_detected):
        """Update the statistics of a run in the database."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runs
            SET end_time = ?, books_detected = ?
            WHERE id = ?
        """, (end_time, books_detected, run_id))
        conn.commit()
        conn.close()

    def update_run_paths(self, run_id, input_file=None, output_dir=None):
        """Update the input and output paths of a run in the database.
        
        Args:
            run_id: The ID of the run to update
            input_file: Relative path to the input file
            output_dir: Relative path to the output directory
        """
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE runs
            SET input_file = ?, output_dir = ?
            WHERE id = ?
        """, (input_file, output_dir, run_id))
        conn.commit()
        conn.close()

    def log_detection_entry(self, run_id):
        """Log a detected item into the detections table and return its ID."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO detections (run_id)
            VALUES (?)
        """, (run_id,))
        detection_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return detection_id

    def log_detection_variant(self, detection_id, image_path, best_title):
        """Log a variant of a detection into the detection_variants table."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO detection_variants (detection_id, image_path, best_title)
            VALUES (?, ?, ?)
        """, (detection_id, image_path, best_title))
        conn.commit()
        conn.close()

    def get_detections(self, run_id=None):
        """Retrieve detections from the database, optionally filtered by run_id."""
        conn = self._connect()
        cursor = conn.cursor()

        if run_id:
            cursor.execute("SELECT * FROM detections WHERE run_id = ?", (run_id,))
        else:
            cursor.execute("SELECT * FROM detections")

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
