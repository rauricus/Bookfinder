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


# Add a log buffer to store early log messages.
#   This is necessary because the SocketIO connection may not be established when the log messages are generated.
#   The log messages will be sent to the WebSocket once a connection is established.
log_buffer = []
log_buffer.append('\n')

class BufferedSocketIOHandler(logging.Handler):
    def __init__(self, socketio):
        super().__init__()
        self.socketio = socketio

    def emit(self, record):
        log_message = self.format(record)
        if self.socketio.server.eio.sockets:
            self.socketio.emit('log_message', {'data': log_message})
        else:
            log_buffer.append(log_message)  # Buffer the log message if no WebSocket connection exists

app = Flask(__name__)

socketio = SocketIO(app, async_mode='eventlet') # Use eventlet for real-time streaming of logs

# Flush the log buffer when a WebSocket connection is established
@socketio.on('connect')
def flush_log_buffer():
    for message in log_buffer:
        socketio.emit('log_message', {'data': message})
    log_buffer.clear()

# Add the custom SocketIOHandler to the root logger
# TODO: I believe setting the level and formatter here is not necessary, as the logger should already be configured
# in config.py. However, this is not the case: the level and format from basicConfig are not inherited by the
# SocketIOHandler. So we set them here. We should maybe call basicConfig later, after all handlers have been added.
socketio_handler = BufferedSocketIOHandler(socketio)
socketio_handler.setLevel(logging.INFO)
socketio_handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(message)s'))

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/run', methods=['POST'])
def run_find_books():
    source = request.form.get('source')
    debug = int(request.form.get('debug', 0))

    if not source or not os.path.exists(source):
        return jsonify({"error": "Invalid or missing source file."}), 400

    try:
        # Pass the SocketIOHandler to the main function
        thread = threading.Thread(target=find_books_main, args=(source, debug, socketio_handler), daemon=True)
        thread.start()

        return render_template('run.html')

    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/test_socket')
def test_socket():
    socketio.emit('log_message', {'data': 'Test message from server'})
    return "Test message sent to WebSocket. Check the browser console.", 200

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5010, debug=True)