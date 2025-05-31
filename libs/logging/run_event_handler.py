"""Handler for run-specific events."""

from datetime import datetime
from .socket_events import EventType, DetectionEvent, RunStatusEvent

class RunEventHandler:
    """Handles events for a specific run."""
    
    def __init__(self, socket_manager, run_id):
        """Initialize the run-specific event handler."""
        self.socket_manager = socket_manager
        self.namespace = f'/run_{run_id}'
        self.run_id = run_id
        
    def emit_detection(self, bookspine_data: dict):
        """
        Emit a bookspine event.
        
        Args:
            bookspine_data: Dictionary containing bookspine information with keys:
                - id: Detection ID
                - image_path: Path to the detected book image
                - title: Optional book title
                - book_details: Optional dictionary with book details
        """
        event = DetectionEvent(
            id=bookspine_data['id'],
            image_path=bookspine_data['image_path'],
            title=bookspine_data.get('title'),
            book_details=bookspine_data.get('book_details')
        )
        self.socket_manager.emit_event(EventType.DETECTION, event, self.namespace)
        
    def emit_status(self, status: str):
        """
        Emit the current status of the run.
        
        Args:
            status: Current status message
        """
        event = RunStatusEvent(
            status=status,
            run_id=self.run_id,
            timestamp=datetime.now().isoformat()
        )
        self.socket_manager.emit_event(EventType.RUN_STATUS, event, self.namespace)