import os
import sys
import logging
import threading
import eventlet
import sqlite3
import signal
from datetime import datetime

# Apply eventlet monkey-patching.
#   Note this has to be done HERE, before importing any other modules. The module throws an
#   exception if not done at the beginning.
#   Without monkey patching, Flask-SocketIO may use blocking standard libraries, which 
#   results in WebSocket messages not being processed correctly. Monkey patching ensures 
#   that all relevant operations are non-blocking and work together with eventlet.
eventlet.monkey_patch()

from flask import Flask, request, render_template, jsonify, redirect
from flask_socketio import SocketIO

from libs.logging import get_logger, SocketManager
from libs.database_manager import DatabaseManager
from libs.utils.general_utils import get_next_directory
from libs.book_finder_thread import BookFinderThread
from libs.run_manager import RunManager

import config


# Modul-spezifischer Logger
logger = get_logger(__name__)

class BooksOnShelvesApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Initialize logging
        logging.basicConfig(level=logging.INFO)
        
        # Initialize SocketManager and RunManager
        self.socket_manager = SocketManager(self)
        self.run_manager = RunManager(self.socket_manager)
        
        # Initialize database manager as a singleton
        self.db_manager = DatabaseManager(os.path.join(os.getcwd(), "bookshelves.db"))
        
        # Register routes
        self.route("/")(self.index)
        self.route("/run", methods=['GET', 'POST'])(self.run_page)
        self.route("/runs")(self.get_runs)
        self.route("/runs/<run_id>/bookspines")(self.get_bookspines)

        # Thread-Lock für die Output Directory Erstellung
        self._output_dir_lock = threading.Lock()

    def __get_next_output_directory(self):
        """Thread-safe Methode zur Erstellung des nächsten Output Directories."""
        with self._output_dir_lock:
            output_dir = get_next_directory(config.OUTPUT_DIR)
            os.makedirs(os.path.join(output_dir, "book"), exist_ok=True)
            return output_dir


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
                output_dir = self.__get_next_output_directory()
                
                # Create run context with output directory
                run_context = self.db_manager.create_run(
                    start_time=datetime.now().isoformat(),
                )
                
                # Start a new run with the run manager
                self.run_manager.start_run(
                    run_id=run_context.run_id,
                    output_dir=output_dir
                )
                
                # Start BookFinder in new thread
                finder_thread = BookFinderThread(
                    self,
                    source=source,
                    output_dir=output_dir,
                    run_context=run_context,
                    debug=int(debug)
                )
                
                logger.info("🔍 Starte Bucherkennung...")
                finder_thread.start()

                # Watch for the thread to end
                def watcher():
                    finder_thread.join()
                    # Stop the run when the thread is done
                    self.run_manager.stop_run(run_context.run_id)
                    logger.info("✅ Bucherkennung abgeschlossen")
                    
                threading.Thread(target=watcher, daemon=True).start()

                # Weiterleitung zur /run-Route mit Run-ID als Query-Parameter
                return redirect(f"/run?run_id={run_context.run_id}")
            except Exception as e:
                logging.error(f"Fehler beim Starten der Bucherkennung: {str(e)}")
                return jsonify({"error": str(e)}), 500
                
        # GET request
        run_id = request.args.get('run_id')
        if not run_id:
            return jsonify({"error": "Keine Run-ID angegeben"}), 400
        return render_template("run.html", run_id=run_id)

    def get_runs(self):
        """Gibt eine Liste aller Runs zurück."""
        try:
            runs = self.db_manager.get_all_runs()
            return jsonify({"runs": runs})
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Runs: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def get_bookspines(self, run_id):
        """Gibt alle Detections für einen bestimmten Run zurück."""
        try:
            bookspines = self.db_manager.get_bookspines_for_run(run_id)
            return jsonify(bookspines)
        except Exception as e:
            logging.error(f"Fehler beim Abrufen der Detections: {str(e)}")
            return jsonify({"error": str(e)}), 500


# Signal-Handler für SIGINT registrieren
def handle_sigint(signal_received, frame):
    """Handles SIGINT (Ctrl-C) to clean up resources."""
    logging.info("Ausführung unterbrochen. Geben Ressourcen frei...")
    
    if hasattr(flask_app, 'run_manager'):
        flask_app.run_manager.cleanup()
    
    if hasattr(flask_app, 'socket_manager'):
        flask_app.socket_manager.teardown()
    
    flask_app.logger.info("📘 Bookfinder Server heruntergefahren.")
    exit(0)

signal.signal(signal.SIGINT, handle_sigint)

# Create an instance of the BooksOnShelvesApp class and run the application
if __name__ == '__main__':
    flask_app = BooksOnShelvesApp(__name__)
    
    flask_app.logger.info("📘 Bookfinder Server startet auf und hört auf Anfragen unter http://0.0.0.0:5010")
    flask_app.socket_manager.run_server(flask_app, host='0.0.0.0', port=5010)

