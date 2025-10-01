import os
import readline
import subprocess
from pathlib import Path
from getpass import getpass

passwd_path = Path("passwd")
proc = None

folders = ["media", "media/video", "media/images", "media/audio"]

def passwd_F():
    print("password maker")
    while True:
        print("type password", "len(your_password) > 8", sep=os.linesep)
        fir_passwd = getpass(": ")

        if len(fir_passwd) > 8:
            print("type same password again")
            sec_passwd = getpass(": ")

            if sec_passwd == fir_passwd:
                with open("passwd", "w", encoding="utf-8") as f:
                    f.write(fir_passwd)
                    f.close()
                print("done", "you make password", sep=os.linesep)
                return
            else:
                continue
        else:
            continue

def sart_server_F():
    global proc
    if proc is None or proc.poll() is not None:
        proc = subprocess.Popen(
            ["python", "app.py"],
            stdout=open("server.log", "w", encoding="utf-8", buffering=1),
            stderr=subprocess.STDOUT,
            text=None
        )
        print("server is started")
    else:
        print("server is started already")

def stop_server_F():
    global proc
    if proc and proc.poll() is None:
        proc.terminate()
        print("server is topped")
    else:
        print("server is not running")

def status_server_F():
    global proc
    if proc and proc.poll() is None:
        print("server is running")
    else:
        print("server is not running")

def file_check_F():
    for i in folders:
        if Path(i).exists():
            print(i, ": Exist")
        else:
            print(i, ": Not exist")

def file_restore_F():
    for i in folders:
        if not Path(i).exists():
            print(f"{i} : not exist", "restoring", sep=os.linesep)
            os.mkdir(i)
            if Path(i).exists():
                print(i, ": restored")
            else:
                print(i, ": filed to restore")
        else:
            print(i, ": exist")

def main_F():
    if not passwd_path.exists():
        print("please create password is not safety")
        passwd_F()
    
    print("-H to help")
    while True:
        cmd = input(">> ")

        if cmd == "-H":
            print("""
            !!!Logs be saved and overwrited on server.log if there information what you need please copy logs!!!
            
            --Flask 
            server start        | start server press two times Return
            server stop         | stop server
            server status       | show server status
                  
            passwd              | change password 
            
            files check         | check if all directories in medea/ exist
            files restore       | make directories if some does not exist
            
            -X, CTRL+C          | stop main.py !!!if server worked when you stop manager server will don't stop!!! 
            """)
        elif cmd == "server start":
            sart_server_F()
        elif cmd == "server stop":
            stop_server_F()
        elif cmd == "server status":
            status_server_F()
        elif cmd == "files check":
            file_check_F()
        elif cmd == "files restore":
            file_restore_F()
        elif cmd == "passwd":
            passwd_F()
        elif cmd == "-X":
            break
        else:
            print(f"no such comand as: {cmd}", "type -H for help", sep=os.linesep)

if __name__ == "__main__":
    main_F()
