#####################
### Cloud Manager ###
#####################

## Imports ##
import os
import json
import readline
import subprocess
from pathlib import Path
from getpass import getpass
## END ##

## Variabless ##
#proces
cloud_proc = None

#setup config
setup_path = Path("setup.json")

#standart folders
folders = ["images", "videos", "audios", "files"]
## END ##


## Functios setuppers ##
def passwd_F():
    print("making password", "password need to be len(password) > 8", sep=os.linesep)
    while True:
        passwd_first_gtt = getpass("> ")
        if len(passwd_first_gtt) > 8:
            print("same password again")
            passwd_sec_gtt = getpass("> ")
            if passwd_sec_gtt == passwd_first_gtt:
                with open(setup_path, "r+") as jsn:
                    data = json.load(jsn)
                
                    data["password"] = passwd_first_gtt


                    jsn.seek(0)
                    json.dump(data, jsn)
                    jsn.truncate()
                    jsn.close()

                return
            else:
                print("same passwords!")
        else:
            print("make longer password")


def setup_F():
    print("hello its setup for ART_Cloud", "for first enter work path(empty path, please)", sep=os.linesep)
    while True:
        work_path_i = input("> ")
        if Path(work_path_i).exists():
            print("Good!")
            setupic = {
                        "password": "none",
                        "work_path": work_path_i,
                    }

            with open(setup_path, "w") as jsn:
                json.dump(setupic, jsn, indent=4)
                jsn.close()
                
                if setup_path.exists():
                    print("ALL done")
                    return passwd_F()
                else:      
                    print("something wrong with making setup file")
        else:
            print("No path!", "please  ", sep=os.linesep)
## END ##


## Functios commands ##
def cloud_start_F():
    global cloud_proc
    if cloud_proc is None or cloud_proc.poll() is not None:
        cloud_proc = subprocess.Popen(
            ["python3", "app.py"], 
            stdout = open("flask.log", "w", encoding="utf-8", buffering=1), 
            stderr = subprocess.STDOUT,
            text=None
            )
        print("cloud starter")
    else:
        print("failed to start", "check is cloud started with command: cloud status", sep=os.linesep)

def cloud_stop_F():
    global cloud_proc
    if cloud_proc and cloud_proc.poll() is None:
        print("cloud is running")
    else:
        print("cloud is not running")

def cloud_status_F():
    global cloud_proc
    if cloud_proc and cloud_proc.poll() is None:
        cloud_proc.terminate()
        print("cloud is topped")
    else:
        print("cloud is not running")

def folders_check_F():
    if not setup_path.exists():
        print("No config file found! Run setup first.")
        return
    with open(setup_path, "r") as f:
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
            print(f"Missing folder: {folder_path}")
        else:
            print(f"Exists: {folder_path}")

def folders_create_F():
    if not setup_path.exists():
        print("No config file found! Run setup first.")
        return
    with open(setup_path, "r") as f:
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
## END ##


## Command Line ##
def CL():
    if not setup_path.exists():
        setup_F()
    
    print("-H | help")
    while True:
        cl_i = input("> ")

        if cl_i == "-H":
            print("""
            !!! When you start cloud there be created 'flask.log' where you can see flask logs and it be overwtited if you restart cloud!!!
            cloud start        | start cloud
            cloud stop         | stop cloud
            cloud status       | show cloud status
            passwd             | change password
            folder check       | scan media directory to needed folders for work
            folder create      | create needed directories in media foder
            -X                 | stop program
            """)
        elif cl_i == "passwd":
            passwd_F()
        elif cl_i == "cloud start":
            cloud_start_F()
        elif cl_i == "cloud stop":
            cloud_stop_F()
        elif cl_i == "cloud status":
            cloud_status_F()
        elif cl_i == "folder check":
            folders_check_F()
        elif cl_i == "folder create":
            folder_create_()
        elif cl_i == "-X":
            break
        else:
            print(f"no such command as: {cl_i}")
## END ##


## Oth ##
if __name__ == ("__main__"):
    CL()
## END ##