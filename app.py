import os
import logging
import threading
import eventlet
import sqlite3

# Apply eventlet monkey-patching.
#   Note this has to be done HERE, before importing any other modules. The module throws an
#   exception if not done at the beginning.
#   Without monkey patching, Flask-SocketIO may use blocking standard libraries, which 
#   results in WebSocket messages not being processed correctly. Monkey patching ensures 
#   that all relevant operations are non-blocking and work together with eventlet.
eventlet.monkey_patch()


from flask import Flask, request, render_template, jsonify
from libs.logging_socketio import LoggingSocketIO
from libs.database_manager import DatabaseManager
from libs.book_finder import BookFinder


class BooksOnShelvesApp(Flask):
    def __init__(self, import_name):
        """Initialize the Flask application and its components."""
        super().__init__(import_name)
        self.socketio = LoggingSocketIO(self)
        self.db_manager = DatabaseManager('bookshelves.db')

        # Register routes
        self._register_routes()

    def _register_routes(self):
        """Register all Flask routes."""
        @self.route('/')
        def index():
            return render_template('index.html')

        @self.route('/run', methods=['POST'])
        def run_find_books():
            source = request.form.get('source')
            debug = int(request.form.get('debug', 0))

            if not source or not os.path.exists(source):
                return jsonify({"error": "Invalid or missing source file."}), 400

            try:
                # Create an instance of BookFinder
                book_finder = BookFinder(debug, self.socketio.log_handler)

                # Start the BookFinder execution in a separate thread
                # Note: The trailing comma in args=(source,) is crucial to ensure this is treated as a tuple.
                #       Without the comma, `source` would be interpreted as a string (iterable), causing unexpected behavior.
                thread = threading.Thread(target=book_finder.findBooks, args=(source,), daemon=True)
                thread.start()

                return render_template('run.html')

            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.route('/test_socket')
        def test_socket():
            return self.socketio.test_socket()

        @self.route('/detections', methods=['GET'])
        def get_detections():
            run_id = request.args.get('run_id')  # Run-ID aus den Query-Parametern abrufen
            try:
                detections = self.db_manager.get_detections(run_id)
                return jsonify({"detections": detections})
            except Exception as e:
                return jsonify({"error": str(e)}), 500

        @self.route('/runs', methods=['GET'])
        def get_runs():
            try:
                # Fetch all runs from the database
                runs = self.db_manager.get_all_runs()

                # Format the runs with status
                formatted_runs = []
                for run in runs:
                    status = "running" if run['end_time'] is None else "ended"
                    formatted_runs.append({
                        "run_id": run['run_id'],
                        "start_time": run['start_time'],
                        "end_time": run['end_time'],
                        "books_detected": run['books_detected'],
                        "status": status
                    })

                return jsonify({"runs": formatted_runs})

            except Exception as e:
                return jsonify({"error": str(e)}), 500

    def run(self, host='0.0.0.0', port=5010, debug=True):
        """Run the Flask application."""
        self.socketio.run(self, host=host, port=port, debug=debug)

# Create an instance of the BooksOnShelvesApp class and run the application
if __name__ == '__main__':
    flask_app = BooksOnShelvesApp(__name__)
    flask_app.run()