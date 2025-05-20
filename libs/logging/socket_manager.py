"""Base Socket.IO Manager for handling different namespaces."""

import eventlet
from dataclasses import asdict
from flask_socketio import SocketIO
from typing import Union, Any

from .socket_events import EventType, LogEvent, DetectionEvent, RunStatusEvent

class SocketManager:
    """Base class for Socket.IO management."""
    
    def __init__(self, app):
        """Initialize the Socket.IO instance."""
        self._socketio = SocketIO(app, async_mode='eventlet')
        self._namespaces = {}
    
    def run_server(self, app, host='0.0.0.0', port=5010):
        """Start the Socket.IO server."""
        self._socketio.run(app, host=host, port=port)
        
    def emit_event(self, event_type: EventType, event_data: Union[LogEvent, DetectionEvent, RunStatusEvent], namespace='/'):
        """
        Emit a typed event to a specific namespace.
        
        Args:
            event_type: The type of event to emit
            event_data: The event data, must match the event type
            namespace: The namespace to emit to
        """
        # Validate event type matches data type
        if not self._validate_event(event_type, event_data):
            raise ValueError(f"Event data {type(event_data)} does not match event type {event_type}")
            
        # Convert dataclass to dict for JSON serialization
        data = asdict(event_data)
        self._socketio.emit(event_type.value, data, namespace=namespace)
        
    def _validate_event(self, event_type: EventType, event_data: Any) -> bool:
        """Validate that the event data matches the event type."""
        return (
            (event_type == EventType.LOG and isinstance(event_data, LogEvent)) or
            (event_type == EventType.DETECTION and isinstance(event_data, DetectionEvent)) or
            (event_type == EventType.RUN_STATUS and isinstance(event_data, RunStatusEvent))
        )
    
    def register_namespace(self, namespace, handler):
        """Register a new namespace with its handler."""
        if namespace not in self._namespaces:
            self._namespaces[namespace] = handler

            # Register Socket.IO event handlers for this namespace
            def on_connect():
                # Flush any buffered messages
                if hasattr(handler, 'flush_buffer'):
                    handler.flush_buffer()
                # Send initial status if available
                if hasattr(handler, 'send_initial_state'):
                    handler.send_initial_state()

            def on_disconnect():
                # Notify handler about disconnect
                if hasattr(handler, 'on_client_disconnect'):
                    handler.on_client_disconnect()

            # Store the handlers so we can remove them later
            handler._connect_handler = on_connect
            handler._disconnect_handler = on_disconnect

            # Register the handlers
            self._socketio.on('connect', namespace=namespace)(on_connect)
            self._socketio.on('disconnect', namespace=namespace)(on_disconnect)

    def deregister_namespace(self, namespace):
        """Remove a namespace and its handler."""
        if namespace in self._namespaces:
            handler = self._namespaces.pop(namespace)
            
            # In Flask-SocketIO handlers werden automatisch aufgeräumt
            # wenn der namespace entfernt wird
            
            # Cleanup the handler
            handler.cleanup()
            
    def teardown(self):
        """Clean up all namespaces and handlers."""
        for handler in self._namespaces.values():
            handler.cleanup()
        self._namespaces.clear()
        if self._socketio:
            self._socketio.stop()
        self._socketio = None