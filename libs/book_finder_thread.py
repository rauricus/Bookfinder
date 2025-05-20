import threading
from flask import Flask
from datetime import datetime

from libs.book_finder import BookFinder
from libs.logging import (
    get_logger, RunLogContext, 
    EventType, DetectionEvent, RunStatusEvent
)

# Modul-spezifischer Logger
logger = get_logger(__name__)

class BookFinderThread(threading.Thread):
    """
    Ein Thread, der den BookFinder ausführt und das Logging über das neue Event-System handhabt.
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
        self.socket_manager = app.socket_manager

        # BookFinder mit dem RunContext und Debug-Level initialisieren
        self.book_finder = BookFinder(
            run=self.run_context,
            output_dir=self.output_dir,
            debug=self.debug
        )
        
        # Callback für Detections mit dem neuen Event-System
        self.book_finder.on_detection = self._handle_detection

    def _handle_detection(self, detection_data):
        """
        Verarbeitet eine neue Detection mit dem typisierten Event-System.
        """
        event = DetectionEvent(
            id=detection_data.get('id'),
            image_path=detection_data.get('image_path'),
            title=detection_data.get('title'),
            book_details=detection_data.get('book_details')
        )
        self.socket_manager.emit_event(
            event_type=EventType.DETECTION,
            event_data=event,
            namespace=f'/run_{self.run_context.run_id}'
        )

    def run(self):
        """
        Führt den BookFinder in einem separaten Thread aus.
        """
        # Verwende den RunLogContext für alle Logging-Aufrufe in diesem Thread
        with RunLogContext(self.run_context.run_id):
            try:
                # Sende Start-Status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="starting"),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
                self.book_finder.findBooks(self.source)
                
                # Sende Erfolgs-Status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="completed"),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
            except Exception as e:
                # Sende Fehler-Status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="error", message=str(e)),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
                logger.error(f"❌ Fehler bei der Bucherkennung: {str(e)}")
                raise