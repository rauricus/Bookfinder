import threading
from flask import Flask
from datetime import datetime

from libs.book_finder import BookFinder
from libs.logging.log_context import RunLogContext, get_logger

# Modul-spezifischer Logger, der den Modulnamen als Präfix für Log-Nachrichten nutzt
logger = get_logger(__name__)

class BookFinderThread(threading.Thread):
    """
    Ein Thread, der den BookFinder ausführt und das Logging über LoggingSocketIO handhabt.
    """
    
    def __init__(self, app: Flask, source: str = None, output_dir: str = None, run_context=None, debug: int = 0):
        """
        Initialisiert den BookFinderThread.
        
        Args:
            app (Flask): Die Flask-App
            source (str, optional): Der Pfad zum Bild oder Video
            run_context (RunContext): Der RunContext mit run_id und output_dir
            debug (int, optional): Der Debug-Level
        """
        super().__init__()
        self.source = source
        self.output_dir = output_dir
        self.run_context = run_context
        self.debug = debug
        

        # BookFinder mit dem RunContext und Debug-Level initialisieren
        self.book_finder = BookFinder(
            run=self.run_context,
            output_dir=self.output_dir,
            debug=self.debug
        )

        # Register the run namespace with its output directory
        app.logging_socketio.register_namespace(self.run_context.run_id, self.output_dir)
        
        # Callback für Detections registrieren
        self.book_finder.on_detection = lambda detection_data: app.logging_socketio.emit_detection(self.run_context, detection_data)

    def run(self):
        """
        Führt den BookFinder in einem separaten Thread aus.
        """
        # Verwende den RunLogContext für alle Logging-Aufrufe in diesem Thread
        with RunLogContext(self.run_context.run_id):
            try:
                logger.info("🔍 Starte Bucherkennung...")
                self.book_finder.findBooks(self.source)
                logger.info("✅ Bucherkennung abgeschlossen")
            except Exception as e:
                logger.error(f"❌ Fehler bei der Bucherkennung: {str(e)}")
                raise