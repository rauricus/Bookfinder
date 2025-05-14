import logging
import eventlet

from flask_socketio import SocketIO
from libs.socketio_log_handler import SocketIOLogHandler

class LoggingSocketIO:
    """
    A class for managing Socket.IO logging.
    """
    def __init__(self, app):
        """Initializes the Socket.IO instance with a Flask app and a default namespace."""
        self._socketio = SocketIO(app, async_mode='eventlet')
        self._handlers = {}
        self._default_namespace = '/default'

        # Create a default handler for app logs
        self._ensure_handler_exists(self._default_namespace)
        
    def _ensure_handler_exists(self, namespace):
        """ Creates a SocketIOLogHandler for the specified namespace, if needed."""
        if namespace not in self._handlers:
            handler = SocketIOLogHandler(self._socketio, namespace=namespace)
            
            handler.setLevel(logging.INFO)
            handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
            
            self._handlers[namespace] = handler
            logging.getLogger().addHandler(handler)
            

    def teardown(self):
        """Cleans up resources, such as removing the log handler."""
        for handler in self._handlers.values():
            logging.getLogger().removeHandler(handler)
        self._handlers = {}
        self._socketio = None
        
    def register_namespace(self, run_id):
        """Registriert einen LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        self._ensure_handler_exists(namespace)

    def deregister_namespace(self, run_id):
        """Entfernt den LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        handler = self._handlers.pop(namespace, None)
        if handler:
            logging.getLogger().removeHandler(handler)
            
    def emit_detection(self, run, detection):
        """Logs a detection of a specific run."""
        run_namespace = f'/run_{run.run_id}'
        self._ensure_handler_exists(run_namespace)
        self._socketio.emit('detection', detection, namespace=run_namespace)
        
    def run_server(self, app, host='0.0.0.0', port=5010):
        """Starts the Socket.IO server."""
        self._socketio.run(app, host=host, port=port)

