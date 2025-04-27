import logging
import eventlet

from flask_socketio import SocketIO
from libs.socketio_log_handler import SocketIOLogHandler

class LoggingSocketIO(SocketIO):
    """
    An enhanced version of SocketIO that includes a log handler for buffering
    and emitting log messages.

    This class extends the functionality of Flask-SocketIO by integrating a
    SocketIOLogHandler for managing log messages.
    """
    def __init__(self, app, async_mode='eventlet', **kwargs):
        """Initialize the EnhancedLogging with a Flask app."""
        
        super().__init__(app, async_mode=async_mode, **kwargs)
        
        self.log_handler = SocketIOLogHandler(self)
        self.log_handler.setLevel('INFO')
        self.log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

    def test_socket(self):
        """Emit a test message to the WebSocket."""
        self.emit('log_message', {'data': 'Test message from server'})
        return "Test message sent to WebSocket. Check the browser console.", 200