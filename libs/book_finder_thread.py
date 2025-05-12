import threading
import logging
from flask import Flask
from datetime import datetime

from libs.book_finder import BookFinder


class BookFinderThread(threading.Thread):
    """
    Ein Thread, der den BookFinder ausführt und das Logging über LoggingSocketIO handhabt.
    """
    
    def __init__(self, app: Flask, source: str = None, db_manager=None, debug: int = 0):
        """
        Initialisiert den BookFinderThread.
        
        Args:
            app (Flask): Die Flask-App
            source (str, optional): Der Pfad zum Bild oder Video
            db_manager (DatabaseManager, optional): Der DatabaseManager für die Datenbank-Operationen
            debug (int, optional): Der Debug-Level
        """
        super().__init__()
        self.source = source
        self.debug = debug

        # Erzeuge einen neuen RunContext über den DatabaseManager
        self.run_context = db_manager.create_run(start_time=datetime.now().isoformat())

        # BookFinder mit dem RunContext und Debug-Level initialisieren
        self.book_finder = BookFinder(
            current_run=self.run_context,
            debug=self.debug
        )

        # Callback für Detections registrieren
        # Pass the emit method from LoggingSocketIO to BookFinder for detections
        self.book_finder.on_detection = lambda detection_data: app.logging_socketio.emit('detection', detection_data)

    def run(self):
        """
        Führt den BookFinder in einem separaten Thread aus.
        """
        try:
            logging.info("🔍 Starte Bucherkennung...")
            self.book_finder.findBooks(self.source)
            logging.info("✅ Bucherkennung abgeschlossen")
        except Exception as e:
            logging.error(f"❌ Fehler bei der Bucherkennung: {str(e)}")
            raise