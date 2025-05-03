import threading
import logging
from flask import Flask

from libs.book_finder import BookFinder
from libs.logging_socketio import LoggingSocketIO


class BookFinderThread(threading.Thread):
    """
    Ein Thread, der den BookFinder ausführt und das Logging über LoggingSocketIO handhabt.
    """
    
    def __init__(self, app: Flask, source: str = None, db_manager = None):
        """
        Initialisiert den BookFinderThread.
        
        Args:
            app (Flask): Die Flask-App
            source (str, optional): Der Pfad zum Bild oder Video
            db_manager (DatabaseManager, optional): Der DatabaseManager für die Datenbank-Operationen
        """
        super().__init__()
        self.source = source
        self.db_manager = db_manager
        
        # BookFinder mit dem SocketIO LogHandler und DatabaseManager initialisieren
        self.book_finder = BookFinder(
            debug=1, 
            log_handler=LoggingSocketIO.get_log_handler(), 
            db_manager=self.db_manager
        )

        # Callback für Detections registrieren
        self.book_finder.on_detection = self.emit_detection
        
    def emit_detection(self, detection_data):
        """
        Sendet Detection-Daten über WebSocket an den Client.
        """
        LoggingSocketIO.get_instance().emit('detection', detection_data)
        
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