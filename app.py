#############
### Cloud ###
#############

## Imports ##
import os
import json
import random
import string
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from functools import wraps
## END ##

## Variables ##
setup_folder = Path("setup.json")

folders = ["images", "videos", "audios", "files"]

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "".join([random.choice(string.ascii_letters + string.digits  ) for n in 
range(32)]))
## END ##

## Work stuff ##
def load_setup_F():
    if setup_folder.exists():
        with open(setup_folder, "r") as jsn:
            return json.load(jsn)

def get_passwd_F():
    setup = load_setup_F()
    return setup.get("password", "")

def get_media_folder_F():
    setup = load_setup_F()
    return Path(setup.get("work_path", "media"))

def password_exists_F():
    return bool(get_passwd_F())

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not password_exists_F():
            return "Password not created, create config in main.py by starting it!"
        if not session.get("authenticated"):
            return redirect(url_for("lock_page"))
        return f(*args, **kwargs)
    return decorated_function
## END ##

## Pages ##
@app.before_request
def require_password_and_login():
    endpoint = request.endpoint or ""
    open_endpoints = {"lock_page", "static", "logout"}
    if endpoint in open_endpoints:
        return None
    if not password_exists_F() or not session.get("authenticated"):
        return redirect(url_for("lock_page"))
    return None

@app.route("/", methods=["GET", "POST"])
def lock_page():
    if not password_exists_F():
        return "Password not created, create config in main.py by starting it!"
    error = None
    if request.method == "POST":
        entered_password = request.form.get("password")
        if entered_password == get_passwd_F():
            session["authenticated"] = True
            return redirect(url_for("home_page"))
        else:
            error = " wrong password!"
    return render_template("lock_page.html", error=error)

@app.route("/home")
@login_required
def home_page():
    filter_type = request.args.get("filter")
    media_dir = get_media_folder_F()
    images = os.listdir(media_dir / "images") if (media_dir / "images").exists() else []
    videos = os.listdir(media_dir / "videos") if (media_dir / "videos").exists() else []
    audios = os.listdir(media_dir / "audios") if (media_dir / "audios").exists() else []
    files = os.listdir(media_dir / "files") if (media_dir / "files").exists() else []

    if filter_type == "images":
        videos, audios, files = [], [], []
    elif filter_type == "videos":
        images, audios, files = [], [], []
    elif filter_type == "audios":
        images, videos, files = [], [], []
    elif filter_type == "files":
        images, videos, audios = [], [], []

    return render_template("home_page.html",
                           images=images,
                           videos=videos,
                           audios=audios,
                           files=files,
                           filter=filter_type)


@app.route("/media/<folder>/<filename>")
@login_required
def media_file(folder, filename):
    # use the configured media folder from setup.json
    media_dir = get_media_folder_F()
    # send_from_directory expects a filesystem path (string) for the directory
    return send_from_directory(str(media_dir / folder), filename)

@app.route("/media_viewer/<folder>/<filename>")
@login_required
def viewer(folder, filename):
    """Render media viewer.

    For files in the configured `files` folder, provide a plain-text preview for
    small `.txt` and `.md` files. Large or binary files will not be previewed and
    a download link will be shown instead.
    """
    # default values
    file_is_text = False
    file_content = None
    file_exists = False
    file_size = None

    if folder == "files":
        media_dir = get_media_folder_F()
        file_path = media_dir / folder / filename
        try:
            if file_path.exists() and file_path.is_file():
                file_exists = True
                file_size = file_path.stat().st_size
                ext = file_path.suffix.lower()
                # only preview these text-like extensions
                if ext in {".txt", ".md"}:
                    # limit preview size to 1 MB to avoid huge reads
                    max_preview = 1 * 1024 * 1024
                    size = file_path.stat().st_size
                    if size <= max_preview:
                        with open(file_path, "r", encoding="utf-8", errors="replace") as fh:
                            file_content = fh.read()
                    else:
                        file_content = f"File too large to preview ({size} bytes)."
                    file_is_text = True
        except Exception as e:
            # surface a small error message in the preview area
            file_is_text = True
            file_content = f"Error reading file: {e}"

    return render_template("media_viewer.html", folder=folder, filename=filename,
                           file_is_text=file_is_text, file_content=file_content,
                           file_exists=file_exists, file_size=file_size)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("lock_page"))
## END ##

## Oth ##
if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)


## END ##