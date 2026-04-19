from flask import Flask, send_from_directory
import os

app = Flask(__name__)

# Directory where index.html, app.js, styles.css live
FRONTEND_DIR = os.path.dirname(os.path.abspath(__file__))


@app.route("/")
def index():
    return send_from_directory(FRONTEND_DIR, "index.html")


@app.route("/<path:filename>")
def static_files(filename):
    return send_from_directory(FRONTEND_DIR, filename)


if __name__ == "__main__":
    print("=" * 45)
    print("  NovaBank server running!")
    print("  Open http://localhost:5000 in your browser")
    print("=" * 45)
    app.run(debug=True, port=5000)
