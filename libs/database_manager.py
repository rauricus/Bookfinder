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
        variant_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return variant_id
        
    def log_book_lookup(self, bookspine_variant_id, source, book_details, raw_response=None):
        """
        Log the results of a book lookup to the database.
        
        Args:
            bookspine_variant_id: ID of the bookspine variant that triggered the lookup
            source: Source of the lookup (e.g., 'DNB', 'OpenLibrary', 'lobid_GND')
            book_details: Dictionary containing book details
            raw_response: Optional raw response data as string (e.g., JSON)
        
        Returns:
            ID of the created book lookup record
        """
        if not book_details:
            return None
            
        conn = self._connect()
        cursor = conn.cursor()
        
        # Extract fields from book_details based on the source
        # Use None (NULL in SQLite) for missing values instead of 'Unbekannt'
        title = book_details.get('title')
        authors = book_details.get('authors', book_details.get('author'))
        year = book_details.get('year')
        isbn = book_details.get('isbn')
        gnd_identifier = book_details.get('gndIdentifier')
        wikidata_link = book_details.get('wikidata')
        lobid_id = book_details.get('id')
        
        # Convert raw_response to string if it's a dictionary
        if isinstance(raw_response, dict):
            import json
            raw_response = json.dumps(raw_response)
        
        cursor.execute(
            """
            INSERT INTO book_lookups (
                bookspine_variant_id, source, title, authors, year, isbn,
                gnd_identifier, wikidata_link, lobid_id, raw_response
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                bookspine_variant_id, source, title, authors, year, isbn,
                gnd_identifier, wikidata_link, lobid_id, raw_response
            ),
        )
        
        lookup_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return lookup_id

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
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS book_lookups (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                bookspine_variant_id INTEGER NOT NULL,
                source TEXT NOT NULL,
                title TEXT,
                authors TEXT,
                year TEXT,
                isbn TEXT,
                gnd_identifier TEXT,
                wikidata_link TEXT,
                lobid_id TEXT,
                raw_response TEXT,
                created TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (bookspine_variant_id) REFERENCES bookspine_variants (id)
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
        
    def get_bookspines_for_run(self, run_id):
        """Retrieve all bookspines with their variants and book lookups for a specific run."""
        conn = self._connect()
        cursor = conn.cursor()
        
        # Get all bookspines for this run
        cursor.execute("""
            SELECT id, run_id, created, updated
            FROM bookspines
            WHERE run_id = ?
        """, (run_id,))
        
        bookspines = []
        for bookspine_row in cursor.fetchall():
            bookspine_id = bookspine_row[0]
            
            # Get all variants for this bookspine
            cursor.execute("""
                SELECT id, image_path, best_title, created, updated
                FROM bookspine_variants
                WHERE bookspine_id = ?
            """, (bookspine_id,))
            
            variants = []
            for variant_row in cursor.fetchall():
                variant_id = variant_row[0]
                
                # Get all book lookups for this variant
                cursor.execute("""
                    SELECT id, source, title, authors, year, isbn, 
                           gnd_identifier, wikidata_link, lobid_id, created
                    FROM book_lookups
                    WHERE bookspine_variant_id = ?
                """, (variant_id,))
                
                lookups = []
                for lookup_row in cursor.fetchall():
                    lookups.append({
                        'id': lookup_row[0],
                        'source': lookup_row[1],
                        'title': lookup_row[2],
                        'authors': lookup_row[3],
                        'year': lookup_row[4],
                        'isbn': lookup_row[5],
                        'gnd_identifier': lookup_row[6],
                        'wikidata_link': lookup_row[7],
                        'lobid_id': lookup_row[8],
                        'created': lookup_row[9]
                    })
                
                variants.append({
                    'id': variant_id,
                    'image_path': variant_row[1],
                    'title': variant_row[2],
                    'created': variant_row[3],
                    'updated': variant_row[4],
                    'lookups': lookups
                })
            
            # Add bookspine with its variants to the result
            bookspines.append({
                'id': bookspine_id,
                'run_id': bookspine_row[1],
                'created': bookspine_row[2],
                'updated': bookspine_row[3],
                'variants': variants
            })
        
        conn.close()
        return bookspines
        
    def get_book_lookups_for_variant(self, variant_id):
        """Retrieve all book lookups for a specific bookspine variant."""
        conn = self._connect()
        cursor = conn.cursor()
        
        cursor.execute("""
            SELECT id, source, title, authors, year, isbn, 
                   gnd_identifier, wikidata_link, lobid_id, raw_response, created
            FROM book_lookups
            WHERE bookspine_variant_id = ?
        """, (variant_id,))
        
        lookups = []
        for row in cursor.fetchall():
            lookups.append({
                'id': row[0],
                'source': row[1],
                'title': row[2],
                'authors': row[3],
                'year': row[4],
                'isbn': row[5],
                'gnd_identifier': row[6],
                'wikidata_link': row[7],
                'lobid_id': row[8],
                'raw_response': row[9],
                'created': row[10]
            })
        
        conn.close()
        return lookups

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
        
    def get_run_details(self, run_id):
        """Retrieve details for a specific run."""
        conn = self._connect()
        cursor = conn.cursor()
        cursor.execute("""
            SELECT id, start_time, end_time, books_detected, output_dir, input_file
            FROM runs
            WHERE id = ?
        """, (run_id,))
        
        row = cursor.fetchone()
        conn.close()
        
        if not row:
            return None
            
        return {
            'run_id': row[0],
            'start_time': row[1],
            'end_time': row[2],
            'books_detected': row[3],
            'output_dir': row[4],
            'input_file': row[5]
        }
