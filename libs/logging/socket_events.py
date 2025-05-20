"""Definition of supported Socket.IO events."""

from enum import Enum, auto
from dataclasses import dataclass
from typing import Any, Dict, Optional

class EventType(Enum):
    """Supported event types."""
    LOG = "log_message"
    DETECTION = "detection"
    RUN_STATUS = "run_status"  # Für zukünftige Erweiterungen
    
@dataclass
class LogEvent:
    """Log message event data."""
    message: str
    level: str
    timestamp: str

@dataclass
class DetectionEvent:
    """Detection event data."""
    id: str
    image_path: str
    title: Optional[str]
    book_details: Optional[Dict[str, Any]]

@dataclass
class RunStatusEvent:
    """Run status event data."""
    status: str
    run_id: str = ""
    timestamp: str = ""
    message: Optional[str] = None