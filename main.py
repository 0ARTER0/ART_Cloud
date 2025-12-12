import os
import json
import readline
import subprocess
import sys
import signal
import time
from pathlib import Path
from getpass import getpass
from cryptography.fernet import Fernet
import base64
import hashlib

config = Path("conf.json")

# Encryption key derivation (must match app.py)
def get_encryption_key():
    """Generate consistent encryption key from machine/config"""
    key_material = "art_cloud_secure".encode()  # Same as app.py
    key = base64.urlsafe_b64encode(hashlib.sha256(key_material).digest())
    return key

ENCRYPT_KEY = get_encryption_key()

def encrypt_password(password):
    """Encrypt a password"""
    f = Fernet(ENCRYPT_KEY)
    return f.encrypt(password.encode()).decode()

def passwd():
    print("passwd create/change")
    while True:
        passwd_first = getpass(">> ")
        passwd_second = getpass(">> ")
        if passwd_second == passwd_first:
            print("done")
            cfg = {}
            if config.exists():
                try:
                    cfg = json.loads(config.read_text())
                except Exception:
                    cfg = {}
            # Store encrypted password
            cfg["password"] = encrypt_password(passwd_first)
            config.write_text(json.dumps(cfg, indent=4))
            return
        else:
            print("something wrong retype your password")
            continue

def config_check():
    if not config.exists():
        print("No config found. Creating new configuration.")
        passwd()
        print("set a media path")
        path_media()
        return

    try:
        cfg = json.loads(config.read_text())
    except Exception:
        cfg = {}

    if "password" not in cfg or not cfg.get("password"):
        print("Password not set in config.")
        passwd()

    if "paths" not in cfg or not isinstance(cfg.get("paths"), dict):
        print("Media paths not set in config.")
        print("set a media path")
        path_media()


def cloud_start():
    # Start app.py as a detached background process and save its PID in conf.json
    if not Path("app.py").exists():
        print("app.py not found in current directory.")
        return

    # check existing pid
    cfg = {}
    if config.exists():
        try:
            cfg = json.loads(config.read_text())
        except Exception:
            cfg = {}

    pid = cfg.get("cloud_pid")
    if pid:
        # check if process still alive
        try:
            os.kill(pid, 0)
            print(f"Cloud already running (pid={pid}).")
            return
        except Exception:
            # stale pid, continue to start
            pass

    logf = open("app.log", "a")
    try:
        proc = subprocess.Popen([sys.executable, "app.py"], stdout=logf, stderr=logf, preexec_fn=os.setsid)
    except Exception as e:
        print(f"Failed to start app.py: {e}")
        try:
            logf.close()
        except Exception:
            pass
        return

    cfg["cloud_pid"] = proc.pid
    cfg["cloud_started_at"] = int(time.time())
    try:
        config.write_text(json.dumps(cfg, indent=4))
    except Exception as e:
        print(f"Failed to save PID to config: {e}")

    print(f"Started app.py (pid={proc.pid}). Logs -> app.log")

def cloud_stop():
    # Stop the background app.py process recorded in conf.json
    if not config.exists():
        print("No config file found.")
        return
    try:
        cfg = json.loads(config.read_text())
    except Exception:
        print("Could not read config file.")
        return

    pid = cfg.get("cloud_pid")
    if not pid:
        print("Cloud is not running (no PID in config).")
        return

    try:
        # send SIGTERM to the process group
        os.killpg(pid, signal.SIGTERM)
        time.sleep(1)
        # if still alive, SIGKILL
        try:
            os.kill(pid, 0)
            os.killpg(pid, signal.SIGKILL)
        except Exception:
            pass
    except ProcessLookupError:
        print("Process not found; cleaning up config.")
    except Exception as e:
        print(f"Failed to stop process: {e}")

    # remove pid from config
    cfg.pop("cloud_pid", None)
    cfg.pop("cloud_started_at", None)
    try:
        config.write_text(json.dumps(cfg, indent=4))
    except Exception as e:
        print(f"Failed to update config: {e}")
    print("Cloud stopped (if it was running).")

def cloud_check():
    # Report whether the background app.py process is running
    if not config.exists():
        print("No config file found.")
        return
    try:
        cfg = json.loads(config.read_text())
    except Exception:
        print("Could not read config file.")
        return

    pid = cfg.get("cloud_pid")
    if not pid:
        print("Cloud is not running (no PID recorded).")
        return

    try:
        os.kill(pid, 0)
        started_at = cfg.get("cloud_started_at")
        if started_at:
            ts = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(started_at))
            print(f"Cloud running (pid={pid}), started at {ts}.")
        else:
            print(f"Cloud running (pid={pid}).")
    except Exception:
        print("Cloud PID recorded but process not found (stale PID).")

def path_media():
    while True:
        print("use one path for all media files? [Y/N]")
        qestion_a = input(">> ")
        if qestion_a == "Y":
            while True:
                print("set path for all media files")
                path = input(">> ")
                if Path(path).exists():
                    p = os.path.abspath(os.path.expanduser(path))
                    # load existing config
                    cfg = {}
                    if config.exists():
                        try:
                            cfg = json.loads(config.read_text())
                        except Exception:
                            cfg = {}
                    cfg_paths = {"videos": p, "images": p, "audios": p, "documents": p, "other": p}
                    cfg["paths"] = cfg_paths
                    try:
                        config.write_text(json.dumps(cfg, indent=4))
                        print("path exist. Setting path")
                    except Exception as e:
                        print(f"Failed to save config: {e}")
                    return
                else:
                    continue
        if qestion_a == "N":
            while True:
                video_path = input("videos path >> ")
                if Path(video_path).exists():
                    video_path = os.path.abspath(os.path.expanduser(video_path))
                    print("path exist. Setting path")
                else:
                    continue
                image_path = input("images path >> ")
                if Path(image_path).exists():
                    image_path = os.path.abspath(os.path.expanduser(image_path))
                    print("path exist. Setting path")
                else:
                    continue
                audio_path = input("audio path >> ")
                if Path(audio_path).exists():   
                    audio_path = os.path.abspath(os.path.expanduser(audio_path))
                    print("path exist. Setting path")
                else:
                    continue
                docs_path = input("documents path >> ")
                if Path(docs_path).exists():    
                    docs_path = os.path.abspath(os.path.expanduser(docs_path))
                    print("path exist. Setting path")
                else:
                    continue
                other_path = input("other files path >> ")
                if Path(other_path).exists():    
                    other_path = os.path.abspath(os.path.expanduser(other_path))
                    print("path exist. Setting path")
                    # all paths collected - save to config
                    cfg = {}
                    if config.exists():
                        try:
                            cfg = json.loads(config.read_text())
                        except Exception:
                            cfg = {}
                    cfg_paths = {
                        "videos": video_path,
                        "images": image_path,
                        "audios": audio_path,
                        "documents": docs_path,
                        "other": other_path,
                    }
                    cfg["paths"] = cfg_paths
                    try:
                        config.write_text(json.dumps(cfg, indent=4))
                        print("media paths saved to config.")
                    except Exception as e:
                        print(f"Failed to save config: {e}")
                    return
                else:
                    continue
        else:
            continue

def path_media_check():
    if not config.exists():
        print("No config file found.")
        return
    try:
        cfg = json.loads(config.read_text())
    except Exception:
        print("Could not read config file.")
        return
    paths = cfg.get("paths") or {}
    if not paths:
        print("No media paths configured.")
        return
    print("Configured media paths:")
    for k, v in paths.items():
        print(f"- {k}: {v}")

def command_help():
    print("""
        passwd >>> change password
        cloud-start >>> start cloud
        cloud-stop >>> stop cloud
        cloud-check >>> check cloud status
        set-media-path, s-m-p >>> set path for media and files
        media-path-check, -m-p-c >>> check path to media and folders
    """)

def cMd():
    print("-h for help")
    while True:
        cmd_entry = input(":: ")

        if cmd_entry == "-h":
            command_help()
        elif cmd_entry == "passwd":
            passwd()
        elif cmd_entry == "cloud-start":
            cloud_start()
        elif cmd_entry == "cloud-stop":
            cloud_stop()
        elif cmd_entry == "cloud-check":
            cloud_check()
        elif cmd_entry in ("set-media-path", "s-m-p"):
            path_media()
        elif cmd_entry in ("media-path-check", "m-p-c"):
            path_media_check()
        elif cmd_entry == "exit":
            break
        else:
            print(f"no command like: {cmd_entry} type -h for help if needed")
if __name__ == "__main__":
    config_check()
    cMd()
