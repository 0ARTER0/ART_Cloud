###Imports ###
import os
import readline
import subprocess
import json
from pathlib import Path
from getpass import getpass
### --end ###

### Variables ###
cloud_proc = None

config_path = Path('config.json')

folders = ["music", "video", "images", "files"]
## --end ###

### Tasks ###
def setup():
    print("configure setup", f"you need to make somewhere folder with name 'media' and in this folder you need to make a {folders} or make after setup by command", sep=os.linesep)
    work_path = input("Enter folder for media: ").strip()
    port = input("set port(if you want default type 5000): ")
    while True:
        password = getpass("password (bigger that len(urpassword) <= 8): ").strip()
        if len(password) > 8:
            password_sec = getpass("you need enter password twice: ")
            if password_sec == password:
                config = {
                    "work_path": work_path,
                    "password": password,
                }

                with open("config.json", "w") as f:
                    json.dump(config, f, indent=4)
                    f.close()
                
                if config_path.exists():
                    print("You done!")
                    return
            else:
                print("password not same!!! Do Again")
        else:
            print("Password must be bigger that len(urpassword) <= 8")

def passwd():
    print("Password changer")
    with open(config_path, "r") as f:
        try:
            conf = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return

    while True:
        print("Type new password (len > 8):")
        fir_passwd = getpass(": ").strip()
        if len(fir_passwd) > 8:
            print("Type same password again:")
            sec_passwd = getpass(": ").strip()
            if sec_passwd == fir_passwd:
                conf["password"] = fir_passwd
                try:
                    with open(config_path, "w") as f:
                        json.dump(conf, f, indent=4)
                    print("Done! Password changed.")
                except Exception as e:
                    print(f"Error saving config: {e}")
                return
            else:
                print("Passwords do not match! Try again.")
        else:
            print("Password must be longer than 8 characters.")


def cloud_start():
    global cloud_proc
    if cloud_proc and cloud_proc.poll() is None:
        cloud_proc.terminate()
        print("cloud is topped")
    else:
        print("cloud is not running")

def cloud_stop():
    global cloud_proc
    if cloud_proc and cloud_proc.poll() is None:
        cloud_proc.terminate()
        print("cloud is topped")
    else:
        print("cloud is not running")

def cloud_status():
    global cloud_proc
    if cloud_proc and cloud_proc.poll() is None:
        print("cloud is running")
    else:
        print("cloud is not running")


def folder_checker():
    if not config_path.exists():
        print("No config file found! Run setup first.")
        return
    with open(config_path, "r") as f:
        try:
            conf = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return
    work_path = conf.get("work_path")
    if not work_path:
        print("No work_path in config!")
        return
    all_exist = True
    for folder in folders:
        folder_path = os.path.join(work_path, folder)
        if not os.path.isdir(folder_path):
            print(f"Missing folder: {folder_path}")
            all_exist = False
        else:
            print(f"Exists: {folder_path}")
    if all_exist:
        print("All required folders exist.")
    else:
        print("Some required folders are missing.")

def folder_create():
    if not config_path.exists():
        print("No config file found! Run setup first.")
        return
    with open(config_path, "r") as f:
        try:
            conf = json.load(f)
        except Exception as e:
            print(f"Error loading config: {e}")
            return
    work_path = conf.get("work_path")
    if not work_path:
        print("No work_path in config!")
        return
    for folder in folders:
        folder_path = os.path.join(work_path, folder)
        if not os.path.isdir(folder_path):
            try:
                os.makedirs(folder_path, exist_ok=True)
                print(f"Created: {folder_path}")
            except Exception as e:
                print(f"Failed to create {folder_path}: {e}")
        else:
            print(f"Exists: {folder_path}")
    print("Folder creation complete.")
### --end ###

#Cmd
def Cmd_Module():
    if not config_path.exists():
        setup()
    
    print("-H | help")
    while True:
        cmd = input("> ")

        if cmd == "-H":
            print("""
            !!! When you start cloud there be created 'flask.log' where you can see flask logs and it be all time overwtited !!!
            cloud start        | start cloud
            cloud stop         | stop cloud
            cloud status       | show cloud status
            passwd             | change password
            folder check       | scan media directory to needed folders for work
            folder create      | create needed directories in media foder
            -X                 | stop program
            """)
        elif cmd == "passwd":
            passwd()
        elif cmd == "cloud start":
            cloud_start()
        elif cmd == "cloud stop":
            cloud_stop()
        elif cmd == "cloud status":
            cloud_status()
        elif cmd == "folder check":
            folder_checker()
        elif cmd == "folder create":
            folder_create()
        elif cmd == "-X":
            break
        else:
            print(f"no such command as: {cmd}")
### --end ###

# Oth #
if __name__ == "__main__":
    Cmd_Module()