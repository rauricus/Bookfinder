"""Factory for creating run-specific handlers."""

import os
from typing import Tuple
from .run_log_handler import RunLogHandler
from .run_event_handler import RunEventHandler

class RunHandlerFactory:
    """Factory class for creating run-specific handlers."""
    
    def __init__(self, socket_manager):
        """Initialize the factory."""
        self.socket_manager = socket_manager
        self._log_handlers = {}
        self._event_handlers = {}
    
    def get_handlers_for_run(self, run_id: str, output_dir: str = None) -> Tuple[RunLogHandler, RunEventHandler]:
        """Get or create handlers for a specific run."""
        if run_id not in self._log_handlers:
            # Create output directory if needed
            if output_dir is None:
                output_dir = os.path.join('output', 'predict', str(run_id))
            os.makedirs(output_dir, exist_ok=True)
            
            # Create handlers
            log_handler = RunLogHandler(self.socket_manager, run_id, output_dir)
            event_handler = RunEventHandler(self.socket_manager, run_id)
            
            # Register handlers
            self.socket_manager.register_namespace(log_handler.namespace, log_handler)
            self.socket_manager.register_namespace(event_handler.namespace, event_handler)
            
            # Store handlers
            self._log_handlers[run_id] = log_handler
            self._event_handlers[run_id] = event_handler
            
        return self._log_handlers[run_id], self._event_handlers[run_id]
        
    def cleanup_run(self, run_id: str) -> None:
        """Clean up handlers for a specific run."""
        if run_id in self._log_handlers:
            log_handler = self._log_handlers.pop(run_id)
            self.socket_manager.deregister_namespace(log_handler.namespace)
            
        if run_id in self._event_handlers:
            event_handler = self._event_handlers.pop(run_id)
            self.socket_manager.deregister_namespace(event_handler.namespace)
            
    def cleanup_all(self) -> None:
        """Clean up all handlers."""
        for run_id in list(self._log_handlers.keys()):
            self.cleanup_run(run_id)