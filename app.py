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
from libs.book_finder_thread import BookFinderThread
from libs.database_manager import DatabaseManager
from libs.logging_socketio import LoggingSocketIO


class BooksOnShelvesApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        
        # Initialize SocketIO as Singleton with a namespace for the current run
        run_namespace = '/run_default'  # This can later be dynamically set per run
        LoggingSocketIO.initialize(self, namespace=run_namespace)
        
        # Initialize database manager as a singleton
        self.db_manager = DatabaseManager(os.path.join(os.getcwd(), "bookshelves.db"))
        
        # Register routes
        self.route("/")(self.index)
        self.route("/run", methods=['GET', 'POST'])(self.run_page)
        self.route("/runs")(self.get_runs)
        self.route("/runs/<run_id>/detections")(self.get_detections)

    def index(self):
        return render_template("index.html")

    def run_page(self):
        if request.method == 'POST':
            # Get parameters from the request
            source = request.form.get("source")
            debug = request.form.get("debug", "0")
            
            if not source:
                return jsonify({"error": "Keine Quelle angegeben"}), 400

            try:
                # Starte BookFinder in einem separaten Thread
                finder_thread = BookFinderThread(self, source, self.db_manager)
                finder_thread.start()
                
                # Weiterleitung zur run.html, die die Live-Updates anzeigt
                return render_template("run.html")
            except Exception as e:
                logging.error(f"Fehler beim Starten der Bucherkennung: {str(e)}")
                return jsonify({"error": str(e)}), 500
                
        # GET request
        return render_template("run.html")

    def get_runs(self):
        """Gibt eine Liste aller Runs zurück."""
        try:
            runs = self.db_manager.get_all_runs()
            return jsonify({"runs": runs})
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Runs: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def get_detections(self, run_id):
        """Gibt alle Detections für einen bestimmten Run zurück."""
        try:
            detections = self.db_manager.get_detections_for_run(run_id)
            return jsonify(detections)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Detections: {str(e)}")
            return jsonify({"error": str(e)}), 500


# Create an instance of the BooksOnShelvesApp class and run the application
if __name__ == '__main__':
    flask_app = BooksOnShelvesApp(__name__)
    # Verwende die Singleton-Instanz von SocketIO
    LoggingSocketIO.get_socketio().run(flask_app, host='0.0.0.0', port=5010)