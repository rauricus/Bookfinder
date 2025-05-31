import threading
from flask import Flask
from datetime import datetime

from libs.book_finder import BookFinder
from libs.logging import (
    get_logger, RunLogContext, 
    EventType, DetectionEvent, RunStatusEvent
)

# Module-specific logger
logger = get_logger(__name__)

class BookFinderThread(threading.Thread):
    """
    A thread that runs the BookFinder and handles logging through the new event system.
    """
    
    def __init__(self, app: Flask, source: str = None, output_dir: str = None, run_context=None, debug: int = 0):
        """
        Initializes the BookFinderThread.
        
        Args:
            app (Flask): The Flask app
            source (str, optional): The path to the image or video
            run_context (RunContext): The RunContext with run_id and output_dir
            debug (int, optional): The debug level
        """
        super().__init__()
        self.source = source
        self.output_dir = output_dir
        self.run_context = run_context
        self.debug = debug
        self.socket_manager = app.socket_manager

        # Initialize BookFinder with the RunContext and debug level
        self.book_finder = BookFinder(
            run=self.run_context,
            output_dir=self.output_dir,
            debug=self.debug
        )
        
        # Callback for detections with the new event system
        self.book_finder.on_detection = self._handle_detection

    def _handle_detection(self, bookspine_data):
        """
        Processes a new detection with the typed event system.
        """
        event = DetectionEvent(
            id=bookspine_data.get('id'),
            image_path=bookspine_data.get('image_path'),
            title=bookspine_data.get('title'),
            book_details=bookspine_data.get('book_details')
        )
        self.socket_manager.emit_event(
            event_type=EventType.DETECTION,
            event_data=event,
            namespace=f'/run_{self.run_context.run_id}'
        )

    def run(self):
        """
        Runs the BookFinder in a separate thread.
        """
        # Use the RunLogContext for all logging calls in this thread
        with RunLogContext(self.run_context.run_id):
            try:
                # Send start status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="starting"),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
                self.book_finder.findBooks(self.source)
                
                # Send success status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="completed"),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
            except Exception as e:
                # Send error status
                self.socket_manager.emit_event(
                    event_type=EventType.RUN_STATUS,
                    event_data=RunStatusEvent(status="error", message=str(e)),
                    namespace=f'/run_{self.run_context.run_id}'
                )
                
                logger.error(f"❌ Error during book detection: {str(e)}")
                raise