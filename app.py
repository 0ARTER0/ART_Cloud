import os
from pathlib import Path
from flask import Flask, render_template, request, redirect, url_for, session, send_from_directory
from functools import wraps

app = Flask(__name__)
app.secret_key = os.environ.get("FLASK_SECRET_KEY", "fallback_key_for_dev")

password_file = Path("passwd")
MEDIA_DIR = Path("media")

def get_password():
    if password_file.exists():
        return password_file.read_text(encoding="utf-8").strip()
    return ""

def password_exists():
    return password_file.exists() and get_password() != ""

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not password_exists():
            return "⚠️ Пароль ще не створений. Створи його у main.py."
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
        return "⚠️ Пароль ще не створений. Створи його у main.py."
    
    error = None
    if request.method == "POST":
        entered_password = request.form.get("password")
        if entered_password == get_password():
            session["authenticated"] = True
            return redirect(url_for("main_page"))
        else:
            error = "❌ Невірний пароль"
    return render_template("lock_page.html", error=error)

@app.route("/home")
@login_required
def main_page():
    return render_template("main_page.html")

@app.route("/gallery")
@login_required
def gallery():
    filter_type = request.args.get("filter")

    images = os.listdir(MEDIA_DIR / "images") if (MEDIA_DIR / "images").exists() else []
    videos = os.listdir(MEDIA_DIR / "video") if (MEDIA_DIR / "video").exists() else []
    audios = os.listdir(MEDIA_DIR / "audio") if (MEDIA_DIR / "audio").exists() else []

    if filter_type == "images":
        videos, audios = [], []
    elif filter_type == "video":
        images, audios = [], []
    elif filter_type == "audio":
        images, videos = [], []

    return render_template("gallery_page.html",
                           images=images,
                           videos=videos,
                           audios=audios,
                           filter=filter_type)

@app.route("/media/<folder>/<filename>")
@login_required
def media_file(folder, filename):
    return send_from_directory(MEDIA_DIR / folder, filename)

@app.route("/media_player/<folder>/<filename>")
@login_required
def media_player(folder, filename):
    return render_template("media_player.html", folder=folder, filename=filename)

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("lock_page"))

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)
