from flask import Flask, request, render_template, jsonify
import subprocess
import os

app = Flask(__name__)

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
        # Construct the command with the appropriate number of -d flags
        debug_flags = ["-d"] * debug
        command = ["python3", "find_books.py", source] + debug_flags

        # Run the find_books.py script
        result = subprocess.run(
            command,
            capture_output=True, text=True
        )

        if result.returncode != 0:
            return jsonify({"error": result.stderr}), 500

        return jsonify({"output": result.stdout})

    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(debug=True)