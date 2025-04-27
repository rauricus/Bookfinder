import sqlite3
from datetime import datetime

class DatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path

    def _connect(self):
        return sqlite3.connect(self.db_path)

    def initialize_tables(self):
        """Initialize all necessary tables in the database."""
        conn = self._connect()
        cursor = conn.cursor()

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS runs (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                start_time DATETIME NOT NULL,
                end_time DATETIME,
                books_detected INTEGER DEFAULT 0
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

    def log_run_start(self, start_time):
        """Log the start of a run into the database and return the run ID."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO runs (start_time)
            VALUES (?)
        """, (start_time,))
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