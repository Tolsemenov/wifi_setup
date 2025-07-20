import os
import subprocess

def is_wifi_connected():
    result = os.system("ping -c 1 8.8.8.8 > /dev/null 2>&1")
    return result == 0

def start_access_point():
    os.system("sudo bash setup_ap.sh")

def stop_access_point():
    os.system("sudo bash stop_ap.sh")

def run_flask_web():
    os.system("sudo python3 web_server.py")
