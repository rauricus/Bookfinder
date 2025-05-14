import logging
import eventlet
import os
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
        self._file_handlers = {}  # Speichere FileHandler für jeden Run
        self._default_namespace = '/default'

        # Create separate handlers for app and run-specific logs
        self._create_app_handler()
        
    def _create_app_handler(self):
        """Creates a handler for app-wide logs."""
        handler = SocketIOLogHandler(self._socketio, namespace=self._default_namespace)
        handler.setLevel(logging.INFO)
        handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        handler.addFilter(LogFilter(is_run_specific=False))
        
        self._handlers[self._default_namespace] = handler
        logging.getLogger().addHandler(handler)
        
    def _create_run_handler(self, namespace, run_id, output_dir):
        """Creates handlers for run-specific logs."""
        # Socket.IO Handler für die Web-UI
        socket_handler = SocketIOLogHandler(self._socketio, namespace=namespace)
        socket_handler.setLevel(logging.INFO)
        socket_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        socket_handler.addFilter(LogFilter(is_run_specific=True))
        
        # File Handler für die Run-spezifische Logdatei
        log_file = os.path.join(output_dir, f'run_{run_id}.log')
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
        file_handler.addFilter(LogFilter(is_run_specific=True))
        
        self._handlers[namespace] = socket_handler
        self._file_handlers[namespace] = file_handler
        
        logging.getLogger().addHandler(socket_handler)
        logging.getLogger().addHandler(file_handler)
        
    def register_namespace(self, run_id, output_dir=None):
        """Registriert einen LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        if namespace not in self._handlers:
            if output_dir is None:
                output_dir = os.path.join('output', 'predict', str(run_id))
            os.makedirs(output_dir, exist_ok=True)
            self._create_run_handler(namespace, run_id, output_dir)

    def deregister_namespace(self, run_id):
        """Entfernt den LogHandler für einen Run-Namespace."""
        namespace = f'/run_{run_id}'
        handler = self._handlers.pop(namespace, None)
        file_handler = self._file_handlers.pop(namespace, None)
        
        if handler:
            logging.getLogger().removeHandler(handler)
        if file_handler:
            file_handler.close()  # Wichtig: Schließe die Logdatei ordnungsgemäß
            logging.getLogger().removeHandler(file_handler)
            
    def emit_detection(self, run, detection):
        """Logs a detection of a specific run."""
        run_namespace = f'/run_{run.run_id}'
        if run_namespace not in self._handlers:
            self.register_namespace(run.run_id, run.output_dir)
        self._socketio.emit('detection', detection, namespace=run_namespace)
        
    def teardown(self):
        """Cleans up resources, such as removing the log handler."""
        for handler in self._handlers.values():
            logging.getLogger().removeHandler(handler)
        for file_handler in self._file_handlers.values():
            file_handler.close()  # Wichtig: Schließe alle Logdateien ordnungsgemäß
            logging.getLogger().removeHandler(file_handler)
        self._handlers = {}
        self._file_handlers = {}
        self._socketio = None

    def run_server(self, app, host='0.0.0.0', port=5010):
        """Starts the Socket.IO server."""
        self._socketio.run(app, host=host, port=port)

