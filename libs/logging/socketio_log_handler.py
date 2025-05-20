import logging

class SocketIOLogHandler(logging.Handler):
    """
    A logging handler that buffers log messages and emits them via a SocketIO connection.

    This handler is designed to work with Flask-SocketIO. It maintains an internal log buffer to store
    log messages that are generated before a WebSocket connection is established. Once a connection
    is established, the buffered log messages are sent to the client via the WebSocket.

    Key Features:
    - Buffers log messages if no active WebSocket connection exists.
    - Automatically flushes the buffer when a WebSocket connection is established.
    - Emits log messages in real-time to connected WebSocket clients.
    """
    def __init__(self, socketio, namespace='/default'):
        super().__init__()
        self.socketio = socketio
        self.namespace = namespace
        self.log_buffer = []  # Internal log buffer for this handler
        self.log_buffer.append('\n')

        # Register the connect event to flush the buffer
        @self.socketio.on('connect', namespace=self.namespace)
        def flush_buffer_on_connect():
            self.flush_buffer()

    def emit(self, record):
        log_message = self.format(record)
        event_data = {
            'timestamp': record.asctime if hasattr(record, 'asctime') else record.created,
            'level': record.levelname,
            'message': record.message
        }
        if self.socketio.server.eio.sockets:
            self.socketio.emit('log_message', event_data, namespace=self.namespace)
        else:
            self.log_buffer.append(event_data)  # Buffer the log message if no WebSocket connection exists

    def flush_buffer(self):
        """Flush the log buffer to the WebSocket."""
        for event_data in self.log_buffer:
            self.socketio.emit('log_message', event_data, namespace=self.namespace)
        self.log_buffer.clear()