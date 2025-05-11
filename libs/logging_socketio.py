import logging
import eventlet

from flask_socketio import SocketIO
from libs.socketio_log_handler import SocketIOLogHandler

class LoggingSocketIO:
    """
    A class for managing Socket.IO logging.
    """
    def __init__(self, app, namespace='/default'):
        """Initializes the Socket.IO instance with a Flask app and a namespace."""
        self._socketio = SocketIO(app, async_mode='eventlet', namespace=namespace)
        
        self._log_handler = SocketIOLogHandler(self._socketio, namespace=namespace)
        self._log_handler.setLevel(logging.INFO)
        self._log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))
        logging.getLogger().addHandler(self._log_handler)

    def teardown(self):
        """Cleans up resources, such as removing the log handler."""
        logging.getLogger().removeHandler(self._log_handler)
        self._log_handler = None
        self._socketio = None
        
        
    def run_server(self, app, host='0.0.0.0', port=5010):
        """Starts the Socket.IO server."""
        self._socketio.run(app, host=host, port=port)

    def emit_log_message(self, message):
        """Emits a log message to the current namespace."""
        self._socketio.emit('log_message', {'data': message}, namespace=self._log_handler.namespace)

    def emit(self, event, data, namespace=None):
        """Sendet ein Event über Socket.IO."""
        if namespace is None:
            namespace = self._log_handler.namespace
        self._socketio.emit(event, data, namespace=namespace)



    def test_socket(self):
        """Sendet eine Test-Nachricht über Socket.IO."""
        self.emit('log_message', {'data': 'Test message from server'})
        return "Test message sent to WebSocket. Check the browser console.", 200

