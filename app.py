import os
import logging
import threading
import eventlet

# Apply eventlet monkey-patching.
#   Note this has to be done here, before importing any other modules. The module throws an
#   exception if not done at the beginning.
#   Without monkey patching, Flask-SocketIO may use blocking standard libraries, which 
#   results in WebSocket messages not being processed correctly. Monkey patching ensures 
#   that all relevant operations are non-blocking and work together with eventlet.
eventlet.monkey_patch()

import config  # Ensure logging is configured early

from flask import Flask, request, render_template, jsonify
from flask_socketio import SocketIO, emit

from find_books import main as find_books_main
from libs.socketio_log_handler import SocketIOLogHandler


class FlaskApp:
    def __init__(self):
        """Initialize the Flask application and its components."""
        self.app = Flask(__name__)
        self.socketio = SocketIO(self.app, async_mode='eventlet')
        self.socketio_handler = SocketIOLogHandler(self.socketio)
        self.socketio_handler.setLevel(logging.INFO)
        self.socketio_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all Flask routes."""
        
        @self.app.route('/')
        def index():
            return render_template('index.html')


        @self.app.route('/run', methods=['POST'])
        def run_find_books():
            source = request.form.get('source')
            debug = int(request.form.get('debug', 0))

            if not source or not os.path.exists(source):
                return jsonify({"error": "Invalid or missing source file."}), 400

            try:
                # Pass the SocketIOHandler to the main function
                thread = threading.Thread(target=find_books_main, args=(source, debug, self.socketio_handler), daemon=True)
                thread.start()

                return render_template('run.html')

            except Exception as e:
                return jsonify({"error": str(e)}), 500


        @self.app.route('/test_socket')
        def test_socket():
            self.socketio.emit('log_message', {'data': 'Test message from server'})
            return "Test message sent to WebSocket. Check the browser console.", 200

    def run(self, host='0.0.0.0', port=5010, debug=True):
        """Run the Flask application."""
        self.socketio.run(self.app, host=host, port=port, debug=debug)


# Create an instance of the FlaskApp class and run the application
if __name__ == '__main__':
    flask_app = FlaskApp()
    flask_app.run()