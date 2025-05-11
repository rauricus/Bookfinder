import logging
import eventlet

from flask_socketio import SocketIO
from libs.socketio_log_handler import SocketIOLogHandler

class LoggingSocketIO:
    """
    Ein Singleton für Socket.IO-Logging.
    """
    _instance = None
    _socketio = None
    _log_handler = None

    @classmethod
    def initialize(cls, app, namespace='/default'):
        """Initialisiert die Socket.IO-Instanz mit einer Flask-App und einem Namespace."""
        if not cls._instance:
            cls._instance = cls()
            cls._socketio = SocketIO(app, async_mode='eventlet', namespace=namespace)

            cls._log_handler = SocketIOLogHandler(cls._socketio, namespace=namespace)
            cls._log_handler.setLevel(logging.INFO)
            cls._log_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))


    @classmethod
    def get_instance(cls):
        """Gibt die Socket.IO-Instanz zurück."""
        if not cls._instance:
            raise RuntimeError("LoggingSocketIO muss zuerst mit initialize() initialisiert werden")
        return cls._instance

    @classmethod
    def get_socketio(cls):
        """Gibt die Socket.IO-Instanz zurück."""
        if not cls._socketio:
            raise RuntimeError("LoggingSocketIO muss zuerst mit initialize() initialisiert werden")
        return cls._socketio

    @classmethod
    def get_log_handler(cls):
        """Gibt den Log-Handler zurück."""
        if not cls._log_handler:
            raise RuntimeError("LoggingSocketIO muss zuerst mit initialize() initialisiert werden")
        return cls._log_handler

    @classmethod
    def create_namespace(cls, namespace):
        """Erstellt einen neuen Namespace für eine spezifische Run-ID."""
        if not cls._socketio:
            raise RuntimeError("LoggingSocketIO muss zuerst mit initialize() initialisiert werden")
        return cls._socketio.namespace_handlers.get(namespace, None) or cls._socketio.on_namespace(namespace)

    def emit(self, event, data):
        """Sendet ein Event über Socket.IO."""
        if not self._socketio:
            raise RuntimeError("LoggingSocketIO muss zuerst mit initialize() initialisiert werden")
        self._socketio.emit(event, data)

    def test_socket(self):
        """Sendet eine Test-Nachricht über Socket.IO."""
        self.emit('log_message', {'data': 'Test message from server'})
        return "Test message sent to WebSocket. Check the browser console.", 200