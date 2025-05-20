"""Handler for run-specific logging."""

import os
import logging
from datetime import datetime
from .socket_events import EventType, LogEvent
from .log_context import LogFilter

class RunLogHandler(logging.Handler):
    """Handles logging for a specific run."""
    
    def __init__(self, socket_manager, run_id, output_dir):
        """Initialize the run-specific handler."""
        super().__init__()
        self.socket_manager = socket_manager
        self.namespace = f'/run_{run_id}'
        self.log_buffer = []  # Buffer für Logs
        
        self.run_id = run_id
        self.output_dir = output_dir
        
        # Create log handlers
        self._setup_handlers()
        
    def _setup_handlers(self):
        """Set up both socket and file handlers."""
        # File handler for persistent logging
        log_file = os.path.join(self.output_dir, f'run_{self.run_id}.log')
        self.file_handler = logging.FileHandler(log_file)
        self.file_handler.setLevel(logging.INFO)
        self.file_handler.setFormatter(
            logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        )
        self.file_handler.addFilter(LogFilter(is_run_specific=True))

        # Configure self as logging handler
        self.setLevel(logging.INFO)
        self.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        self.addFilter(LogFilter(is_run_specific=True))
        
        # Add handlers to root logger
        logging.getLogger().addHandler(self.file_handler)
        logging.getLogger().addHandler(self)
    
    def flush_buffer(self):
        """Flush buffered logs to the socket."""
        if self.log_buffer:
            for event in self.log_buffer:
                self.socket_manager.emit_event(EventType.LOG, event, self.namespace)
            self.log_buffer.clear()
        
    def emit(self, record):
        """Emit a log record both to file and socket."""
        # File logging is handled by the FileHandler
        
        # Create log event
        event = LogEvent(
            message=self.file_handler.formatter.format(record),
            level=record.levelname,
            timestamp=datetime.now().isoformat()
        )
        
        # Either emit directly or buffer
        if self.socket_manager._socketio.server.eio.sockets:
            self.socket_manager.emit_event(EventType.LOG, event, self.namespace)
        else:
            self.log_buffer.append(event)
        
    def cleanup(self):
        """Clean up the handlers when namespace is deregistered."""
        # Remove and close file handler
        if hasattr(self, 'file_handler'):
            self.file_handler.close()
            logging.getLogger().removeHandler(self.file_handler)
            
        # Remove self as handler
        logging.getLogger().removeHandler(self)