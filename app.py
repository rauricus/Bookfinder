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

from flask import Flask, request, render_template, jsonify, redirect, send_file, abort
from flask_socketio import SocketIO

from libs.logging import get_logger, SocketManager
from libs.database_manager import DatabaseManager
from libs.utils.general_utils import get_next_directory
from libs.book_finder_thread import BookFinderThread
from libs.run_manager import RunManager

import config


# Module-specific logger that uses the module name as a prefix for log messages
logger = get_logger(__name__)

class BooksOnShelvesApp(Flask):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

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
        self.route("/image/<run_id>")(self.serve_image)
        self.route("/log/<run_id>")(self.get_log_content)

        # Thread-Lock for creating output directories
        self._output_dir_lock = threading.Lock()

    def __get_next_output_directory(self):
        """Thread-safe method to create the next output directory."""
        with self._output_dir_lock:
            output_dir = get_next_directory(config.OUTPUT_DIR)
            os.makedirs(os.path.join(output_dir, "book"), exist_ok=True)
            return output_dir


    def index(self):
        return render_template("index.html")


    def run_page(self):
        # POST request means we're starting a new run
        if request.method == 'POST':
            # Get parameters from the request
            source = request.form.get("source")
            debug = request.form.get("debug", "0")
            
            if not source:
                return jsonify({"error": "No source given"}), 400

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
                
                logger.info("🔍 Starting book detection...")
                finder_thread.start()

                # Watch for the thread to end
                def watcher():
                    finder_thread.join()
                    # Stop the run when the thread is done
                    self.run_manager.stop_run(run_context.run_id)
                    logger.info("✅ Book detection finished.")
                    
                threading.Thread(target=watcher, daemon=True).start()

                # We use the Post/Redirect/Get (PRG) pattern here for several important reasons:
                # 1. Prevents duplicate form submissions if the user refreshes the page
                # 2. Allows proper browser history/bookmarking with the run_id in the URL
                # 3. Follows REST principles (POST for creation, GET for retrieval)
                # 
                # We add the live=true parameter to indicate this is a new run that should
                # be in live mode (with socket.io connection for auto-updates)
                return redirect(f"/run?run_id={run_context.run_id}&live=true")
                
                # Alternative approach would be to render the template directly:
                # return render_template("run.html", run_id=run_context.run_id, log_content="", view_mode=False)
                # But this would cause issues with browser refreshes potentially starting new runs
            except Exception as e:
                logging.error(f"Error during startup of book detection: {str(e)}")
                return jsonify({"error": str(e)}), 500
                
        # GET request means we're viewing an existing run
        else:
            run_id = request.args.get('run_id')
            if not run_id:
                return jsonify({"error": "No Run ID provided"}), 400
                
            # Get run details from database
            run_details = self.db_manager.get_run_details(run_id)
            if not run_details:
                return jsonify({"error": f"Run ID {run_id} not found"}), 404
                
            # Get log content for this run
            log_content = ""
            if run_details['output_dir']:
                try:
                    # Handle relative paths
                    output_dir = run_details['output_dir']
                    if not os.path.isabs(output_dir):
                        output_dir = os.path.join(config.HOME_DIR, output_dir)
                    
                    # Use the specific log file naming convention: run_<run-id>.log
                    log_path = os.path.join(output_dir, f"run_{run_id}.log")
                    
                    if os.path.exists(log_path) and os.path.isfile(log_path):
                        with open(log_path, 'r') as f:
                            log_content = f.read()
                            logger.debug(f"Found log file: {log_path}")
                    else:
                        logger.warning(f"Log file not found: {log_path}")
                except Exception as e:
                    logger.error(f"Error reading log file: {str(e)}")
            
            # Check if this is a live run (new run) or a view of a past run
            # If live=true is in the query parameters, this is a new run that should be in live mode
            live_mode = request.args.get('live', 'false').lower() == 'true'
            
            # For GET requests, we're in view mode unless live=true is specified
            view_mode = not live_mode
            
            logger.debug(f"Rendering run page for run {run_id} in {'view' if view_mode else 'live'} mode")
                    
            # Render the run page with run details, log content, and view mode
            return render_template("run.html", run_id=run_id, log_content=log_content, view_mode=view_mode)

    def get_runs(self):
        """Returns a list of all runs."""
        try:
            runs = self.db_manager.get_all_runs()
            return jsonify({"runs": runs})
        except Exception as e:
            logging.error(f"Error on retrieving runs: {str(e)}")
            return jsonify({"error": str(e)}), 500

    def get_bookspines(self, run_id):
        """Returns all detected bookspines for a specific run."""
        try:
            bookspines = self.db_manager.get_bookspines_for_run(run_id)
            return jsonify(bookspines)
        except Exception as e:
            logging.error(f"Error on retrieving bookspines: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    def get_log_content(self, run_id):
        """Returns the log content for a specific run."""
        try:
            # Get run details from database
            run_details = self.db_manager.get_run_details(run_id)
            if not run_details:
                return jsonify({"error": f"Run ID {run_id} not found"}), 404
                
            # Check if output directory exists
            if not run_details['output_dir']:
                return jsonify({"error": "No output directory found for this run"}), 404
                
            # Handle relative paths
            output_dir = run_details['output_dir']
            if not os.path.isabs(output_dir):
                output_dir = os.path.join(config.HOME_DIR, output_dir)
                
            # Use the specific log file naming convention: run_<run-id>.log
            log_path = os.path.join(output_dir, f"run_{run_id}.log")
            
            if os.path.exists(log_path) and os.path.isfile(log_path):
                with open(log_path, 'r') as f:
                    log_content = f.read()
                    logger.info(f"Found log file: {log_path}")
                return jsonify({"log_content": log_content})
            else:
                logger.warning(f"Log file not found: {log_path}")
                return jsonify({"error": "Log file not found"}), 404
                
        except Exception as e:
            logging.error(f"Error retrieving log content: {str(e)}")
            return jsonify({"error": str(e)}), 500
            
    def serve_image(self, run_id):
        """Serves an image file based on the run_id and path."""
        try:
            # Get the image path from the query parameters
            image_path = request.args.get('path')
            if not image_path:
                return jsonify({"error": "No image path provided"}), 400
                
            # For security, ensure the path doesn't contain '..' to prevent directory traversal
            if '..' in image_path:
                return jsonify({"error": "Invalid image path"}), 400
                
            # Check if the path is absolute or relative
            if os.path.isabs(image_path):
                # If absolute, use it directly
                full_path = image_path
            else:
                # If relative, resolve it relative to the project root
                full_path = os.path.join(config.HOME_DIR, image_path)
                
            # Check if the file exists
            if not os.path.isfile(full_path):
                logger.error(f"Image file not found: {full_path}")
                return jsonify({"error": "Image file not found"}), 404
                
            # Determine the MIME type based on the file extension
            _, ext = os.path.splitext(full_path)
            mime_type = {
                '.jpg': 'image/jpeg',
                '.jpeg': 'image/jpeg',
                '.png': 'image/png',
                '.gif': 'image/gif'
            }.get(ext.lower(), 'application/octet-stream')
            
            # Serve the file
            return send_file(full_path, mimetype=mime_type)
            
        except Exception as e:
            logger.error(f"Error serving image: {str(e)}")
            return jsonify({"error": str(e)}), 500


# Register signal handler for SIGINT when app is shut down using Ctrl/Cmd-C
def handle_sigint(signal_received, frame):
    """Handles SIGINT (Ctrl-C) to clean up resources."""
    logging.info("Execution interrupted. Freeing resources...")
    
    if hasattr(flask_app, 'run_manager'):
        flask_app.run_manager.cleanup()
    
    if hasattr(flask_app, 'socket_manager'):
        flask_app.socket_manager.teardown()
    
    flask_app.logger.info("📘 Bookfinder Server stopped.")
    exit(0)

signal.signal(signal.SIGINT, handle_sigint)

# Create an instance of the BooksOnShelvesApp class and run the application
if __name__ == '__main__':
    flask_app = BooksOnShelvesApp(__name__)
    
    flask_app.logger.info("📘 Bookfinder Server started and listening for requests on http://0.0.0.0:5010")
    flask_app.socket_manager.run_server(flask_app, host='0.0.0.0', port=5010)
