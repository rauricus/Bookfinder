"""
Manages the lifecycle of a book detection run, including logging and event handling.
"""

from typing import Optional
from libs.logging import RunHandlerFactory

class RunManager:
    """
    Manages book detection runs, including their logging and event handling.
    Acts as a facade for the underlying logging infrastructure.
    """
    
    def __init__(self, socket_manager):
        """Initialize the run manager with a socket manager."""
        self._handler_factory = RunHandlerFactory(socket_manager)
        
    def start_run(self, run_id: str, output_dir: Optional[str] = None) -> None:
        """
        Start a new run with the given ID and optional output directory.
        Creates and initializes all necessary handlers.
        
        Args:
            run_id: The ID of the run
            output_dir: Optional output directory for logs and results
        """
        self._handler_factory.get_handlers_for_run(run_id, output_dir)
        
    def stop_run(self, run_id: str) -> None:
        """
        Stop a run and clean up its resources.
        
        Args:
            run_id: The ID of the run to stop
        """
        self._handler_factory.cleanup_run(run_id)
        
    def cleanup(self) -> None:
        """Clean up all runs and their resources."""
        self._handler_factory.cleanup_all()
