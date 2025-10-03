
import os
import json
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from functools import wraps

# Load config.json for password and media path
CONFIG_PATH = Path("config.json")
FOLDERS = ["music", "video", "images", "files"]

def load_config():
    if CONFIG_PATH.exists():
        with open(CONFIG_PATH, "r") as f:
            return json.load(f)
    return {}

def get_password():
    conf = load_config()
    return conf.get("password", "")

def get_media_dir():
    conf = load_config()
    return Path(conf.get("work_path", "media"))

def password_exists():
    return bool(get_password())

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_key_for_dev")

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not password_exists():
            return "Password not created, create config in main.py by starting it!"
        if not session.get("authenticated"):
            return redirect(url_for("lock_page"))
        return f(*args, **kwargs)
    return decorated_function

@app.before_request
def require_password_and_login():
    endpoint = request.endpoint or ""
    open_endpoints = {"lock_page", "static", "logout"}
    if endpoint in open_endpoints:
        return None
    if not password_exists() or not session.get("authenticated"):
        return redirect(url_for("lock_page"))
    return None

@app.route("/", methods=["GET", "POST"])
def lock_page():
    if not password_exists():
        return "Password not created, create config in main.py by starting it!"
    error = None
    if request.method == "POST":
        entered_password = request.form.get("password")
        if entered_password == get_password():
            session["authenticated"] = True
            return redirect(url_for("main_page"))
        else:
            error = " wrong password!"
    return render_template("lock_page.html", error=error)

@app.route("/home")
@login_required
def main_page():
    return render_template("main_page.html")

@app.route("/gallery")
@login_required
def gallery():
    filter_type = request.args.get("filter")
    media_dir = get_media_dir()
    images = os.listdir(media_dir / "images") if (media_dir / "images").exists() else []
    videos = os.listdir(media_dir / "video") if (media_dir / "video").exists() else []
    music = os.listdir(media_dir / "music") if (media_dir / "music").exists() else []
    files = os.listdir(media_dir / "files") if (media_dir / "files").exists() else []

    # Filtering logic for gallery
    if filter_type == "images":
        videos, music, files = [], [], []
    elif filter_type == "video":
        images, music, files = [], [], []
    elif filter_type == "music":
        images, videos, files = [], [], []
    elif filter_type == "files":
        images, videos, music = [], [], []

    return render_template("gallery_page.html",
                           images=images,
                           videos=videos,
                           music=music,
                           files=files,
                           filter=filter_type)


@app.route("/media/<folder>/<filename>")
@login_required
def media_file(folder, filename):
    media_dir = get_media_dir()
    return send_from_directory(media_dir / folder, filename)

@app.route("/viewer/<folder>/<filename>")
@login_required
def viewer(folder, filename):
    return render_template("viewer.html", folder=folder, filename=filename)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("lock_page"))

if __name__ == "__main__":
    conf = load_config()
    port = int(conf.get("flask_port", 5000)) if "flask_port" in conf else 5000
    app.run(debug=True, host="0.0.0.0", port=port)
