from flask import Flask, render_template, request, redirect, url_for, session, send_file, abort
import os
import json
from pathlib import Path
from werkzeug.utils import secure_filename
from cryptography.fernet import Fernet
import base64
import hashlib

APP_DIR = Path(__file__).parent
CONFIG_PATH = APP_DIR / "conf.json"

# Encryption key derivation
def get_encryption_key():
    """Generate consistent encryption key from machine/config"""
    key_material = "art_cloud_secure".encode()  # You can make this more unique
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return key

ENCRYPT_KEY = get_encryption_key()

def encrypt_password(password):
    """Encrypt a password"""
    f = Fernet(ENCRYPT_KEY)
    return f.encrypt(password.encode()).decode()

def decrypt_password(encrypted_password):
    """Decrypt a password"""
    f = Fernet(ENCRYPT_KEY)
    return f.decrypt(encrypted_password.encode()).decode()

# File extensions for each media type
MEDIA_EXTENSIONS = {
    "videos": {".mp4", ".mkv", ".avi", ".mov", ".flv", ".wmv", ".webm"},
    "images": {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".svg", ".webp", ".tiff"},
    "audios": {".mp3", ".wav", ".flac", ".aac", ".ogg", ".m4a", ".opus", ".wma"},
    "documents": {".txt", ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx", ".md"},
    "other": set(),  # catch-all
}

app = Flask(__name__)


def load_config():
    cfg = {}
    if CONFIG_PATH.exists():
        try:
            cfg = json.loads(CONFIG_PATH.read_text())
        except Exception:
            cfg = {}
    return cfg


def save_config(cfg):
    CONFIG_PATH.write_text(json.dumps(cfg, indent=4))


def get_secret_key():
    cfg = load_config()
    key = cfg.get("secret_key")
    if not key:
        # create and persist a secret key
        import secrets

        key = secrets.token_hex(24)
        cfg["secret_key"] = key
        try:
            save_config(cfg)
        except Exception:
            pass
    return key


app.secret_key = get_secret_key()


def load_formats():
    """Load formats from config, convert lists to sets, and update MEDIA_EXTENSIONS"""
    cfg = load_config()
    formats_raw = cfg.get("formats")
    if formats_raw and isinstance(formats_raw, dict):
        for t, exts in formats_raw.items():
            if isinstance(exts, list):
                MEDIA_EXTENSIONS[t] = set(exts)
            elif isinstance(exts, set):
                MEDIA_EXTENSIONS[t] = exts


# Load custom formats from config on startup
load_formats()


def is_authenticated():
    return session.get("auth") is True


@app.route("/", methods=["GET"])
def index():
    if is_authenticated():
        return redirect(url_for("main"))
    return render_template("lock_page.html")


@app.route("/login", methods=["POST"])
def login():
    cfg = load_config()
    encrypted_pw = cfg.get("password")
    form_pw = request.form.get("password", "")
    
    if not encrypted_pw:
        return "Password not configured on server.", 500
    
    try:
        decrypted_pw = decrypt_password(encrypted_pw)
        if form_pw == decrypted_pw:
            session["auth"] = True
            return redirect(url_for("main"))
    except Exception:
        pass
    
    return render_template("lock_page.html", error="Invalid password")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("index"))


@app.route("/main")
def main():
    if not is_authenticated():
        return redirect(url_for("index"))

    cfg = load_config()
    paths = cfg.get("paths") or {}

    media = {}
    for t, p in paths.items():
        try:
            pth = Path(p)
            if pth.exists() and pth.is_dir():
                media[t] = []
                exts = MEDIA_EXTENSIONS.get(t, set())
                for fn in sorted(os.listdir(p)):
                    fp = os.path.join(p, fn)
                    # skip directories
                    if os.path.isdir(fp):
                        continue
                    # if "documents" category, also include files with no extension (plain text)
                    if t == "documents":
                        ext = Path(fn).suffix.lower()
                        if ext in exts or ext == "":
                            media[t].append({"name": fn})
                    # if "other" category, include everything not in other categories
                    elif t == "other":
                        ext = Path(fn).suffix.lower()
                        # check if file matches any other category
                        is_other = True
                        for other_t, other_exts in MEDIA_EXTENSIONS.items():
                            if other_t != "other" and other_t != "documents" and ext in other_exts:
                                is_other = False
                                break
                        # also exclude plain text files (no extension) from "other"
                        if is_other and ext == "":
                            is_other = False
                        if is_other:
                            media[t].append({"name": fn})
                    # for other types, filter by extension
                    elif exts:
                        ext = Path(fn).suffix.lower()
                        if ext in exts:
                            media[t].append({"name": fn})
            else:
                media[t] = []
        except Exception:
            media[t] = []

    return render_template("main_page.html", media=media)


def safe_path_for(media_type, filename):
    cfg = load_config()
    paths = cfg.get("paths") or {}
    base = paths.get(media_type)
    if not base:
        return None
    base = os.path.abspath(os.path.expanduser(base))
    # construct full and ensure it's inside base
    full = os.path.abspath(os.path.join(base, filename))
    try:
        if os.path.commonpath([base, full]) != base:
            return None
    except Exception:
        return None
    if not os.path.exists(full):
        return None
    return full


@app.route("/media/<media_type>/<path:filename>")
def media_file(media_type, filename):
    full = safe_path_for(media_type, filename)
    if not full:
        abort(404)
    return send_file(full)


@app.route("/view/<media_type>/<path:filename>")
def view_media(media_type, filename):
    full = safe_path_for(media_type, filename)
    if not full:
        abort(404)
    # choose template by media_type
    if media_type in ("videos", "images"):
        return render_template("media_view_page.html", media_url=url_for("media_file", media_type=media_type, filename=filename), filename=filename, media_type=media_type)
    if media_type == "audios":
        return render_template("audio_player.html", audio_url=url_for("media_file", media_type=media_type, filename=filename), filename=filename)
    if media_type == "documents":
        # try to read text (handles both files with extensions and plain text files)
        try:
            with open(full, "r", encoding="utf-8") as f:
                content = f.read()
            return render_template("text_editor.html", filename=filename, content=content)
        except (UnicodeDecodeError, Exception):
            # if not readable as text, fall back to download
            try:
                return send_file(full, as_attachment=True)
            except Exception:
                abort(500)
    # other -> download or info
    return send_file(full, as_attachment=True)


@app.route("/save/<path:filename>", methods=["POST"])
def save_document(filename):
    if not is_authenticated():
        abort(403)
    full = safe_path_for("documents", filename)
    if not full:
        abort(404)
    
    content = request.form.get("content", "")
    try:
        with open(full, "w", encoding="utf-8") as f:
            f.write(content)
        return "OK", 200
    except Exception as e:
        return f"Error: {e}", 500


@app.route("/list/<media_type>")
def list_media(media_type):
    if not is_authenticated():
        return redirect(url_for("index"))
    cfg = load_config()
    paths = cfg.get("paths") or {}
    base = paths.get(media_type)
    if not base:
        return "No path configured for this media type", 404
    try:
        files = sorted(os.listdir(base))
    except Exception:
        files = []
    return render_template("main_page.html", media={media_type: [{"name": fn} for fn in files]})


@app.route("/settings", methods=["GET", "POST"])
def settings_page():
    if not is_authenticated():
        return redirect(url_for("index"))
    
    cfg = load_config()
    paths = cfg.get("paths") or {}
    formats_raw = cfg.get("formats") or MEDIA_EXTENSIONS.copy()
    # Convert lists back to sets for display
    formats = {t: set(exts) if isinstance(exts, list) else exts for t, exts in formats_raw.items()}
    
    if request.method == "POST":
        action = request.form.get("action")
        
        # Change password
        if action == "change_password":
            old_pw = request.form.get("old_password", "")
            new_pw = request.form.get("new_password", "")
            new_pw_confirm = request.form.get("new_password_confirm", "")
            
            encrypted_pw = cfg.get("password")
            if encrypted_pw:
                try:
                    decrypted_pw = decrypt_password(encrypted_pw)
                    if decrypted_pw != old_pw:
                        return render_template("settings_page.html", paths=paths, formats=formats, error="Old password incorrect")
                except Exception:
                    return render_template("settings_page.html", paths=paths, formats=formats, error="Password decryption failed")
            
            if new_pw != new_pw_confirm:
                return render_template("settings_page.html", paths=paths, formats=formats, error="New passwords do not match")
            
            cfg["password"] = encrypt_password(new_pw)
            try:
                save_config(cfg)
                return render_template("settings_page.html", paths=paths, formats=formats, success="Password changed successfully")
            except Exception as e:
                return render_template("settings_page.html", paths=paths, formats=formats, error=f"Failed to save: {e}")
        
        # Update paths
        elif action == "update_paths":
            for t in ("videos", "images", "audios", "documents", "other"):
                p = request.form.get(f"path_{t}", "").strip()
                if p:
                    p = os.path.abspath(os.path.expanduser(p))
                    if not os.path.exists(p):
                        try:
                            os.makedirs(p, exist_ok=True)
                        except Exception:
                            pass
                    paths[t] = p
            cfg["paths"] = paths
            try:
                save_config(cfg)
                return render_template("settings_page.html", paths=paths, formats=formats, success="Paths updated")
            except Exception as e:
                return render_template("settings_page.html", paths=paths, formats=formats, error=f"Failed to save: {e}")
        
        # Update formats
        elif action == "update_formats":
            new_formats = {}
            for t in ("videos", "images", "audios", "documents", "other"):
                ext_str = request.form.get(f"formats_{t}", "").strip()
                if ext_str:
                    exts = {f".{e.strip().lstrip('.')}" for e in ext_str.split(",") if e.strip()}
                    new_formats[t] = exts
                else:
                    new_formats[t] = set()
            # Convert sets to lists for JSON serialization
            cfg["formats"] = {t: list(exts) for t, exts in new_formats.items()}
            # update global MEDIA_EXTENSIONS (keep as sets for runtime)
            for t in new_formats:
                MEDIA_EXTENSIONS[t] = new_formats[t]
            try:
                save_config(cfg)
                return render_template("settings_page.html", paths=paths, formats=new_formats, success="Formats updated")
            except Exception as e:
                return render_template("settings_page.html", paths=paths, formats=formats, error=f"Failed to save: {e}")
    
    return render_template("settings_page.html", paths=paths, formats=formats)


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)


