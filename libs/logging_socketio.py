import logging
import eventlet

from flask_socketio import SocketIO
from libs.socketio_log_handler import SocketIOLogHandler
from libs.log_context import LogFilter

class LoggingSocketIO:
    """
    A class for managing Socket.IO logging.
    """
    def __init__(self, app):
        """Initializes the Socket.IO instance with a Flask app and a default namespace."""
        self._socketio = SocketIO(app, async_mode='eventlet')
        self._handlers = {}
        self._default_namespace = '/default'

        # Prepate app-wide logging
        self._create_app_handler()
        
    def _create_app_handler(self):
        """Creates a handler for app-wide logs."""
        handler = SocketIOLogHandler(self._socketio, namespace=self._default_namespace)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.addFilter(LogFilter(is_run_specific=False))
        
        self._handlers[self._default_namespace] = handler
        logging.getLogger().addHandler(handler)
        
    def _create_run_handler(self, namespace):
        """Creates a handler for run-specific logs."""
        handler = SocketIOLogHandler(self._socketio, namespace=namespace)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.addFilter(LogFilter(is_run_specific=True))
        
        self._handlers[namespace] = handler
        logging.getLogger().addHandler(handler)
        
    def register_namespace(self, run_id):
        """Registriert einen LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        if namespace not in self._handlers:
            self._create_run_handler(namespace)

    def deregister_namespace(self, run_id):
        """Entfernt den LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        handler = self._handlers.pop(namespace, None)
        if handler:
            logging.getLogger().removeHandler(handler)
            
    def emit_detection(self, run, detection):
        """Logs a detection of a specific run."""
        run_namespace = f'/run_{run.run_id}'
        if run_namespace not in self._handlers:
            self._create_run_handler(run_namespace)
        self._socketio.emit('detection', detection, namespace=run_namespace)
        
    def teardown(self):
        """Cleans up resources, such as removing the log handler."""
        for handler in self._handlers.values():
            logging.getLogger().removeHandler(handler)
        self._handlers = {}
        self._socketio = None

    def run_server(self, app, host='0.0.0.0', port=5010):
        """Starts the Socket.IO server."""
        self._socketio.run(app, host=host, port=port)

