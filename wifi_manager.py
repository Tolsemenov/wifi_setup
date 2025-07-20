# app/wifi_setup/wifi_manager.py
import asyncio
import os
import subprocess
import platform
from app.logs.logger_helper import log_event

IS_WINDOWS = platform.system() == "Windows"

def safe_log(level: str, message: str, action: str = "", target: str = None):
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        # нет активного event loop → можно безопасно вызвать run()
        return asyncio.run(log_event(level, message, action, target))

    # если event loop активен (например, в Quart) — создаём фоновую задачу
    loop.create_task(log_event(level, message, action, target))


def is_wifi_connected():
    result = os.system("ping -c 1 8.8.8.8 >nul 2>&1" if IS_WINDOWS else "ping -c 1 8.8.8.8 > /dev/null 2>&1")
    return result == 0

def start_access_point():
    if IS_WINDOWS:
        print("⚠️ Не могу запустить AP на Windows")
        safe_log("WARNING", "Попытка запуска точки доступа на Windows", action="WIFI_AP_SKIP")
        return
    subprocess.call(['sudo', 'bash', 'setup_ap.sh'])

def stop_access_point():
    if IS_WINDOWS:
        return
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])

def run_flask_web():
    if IS_WINDOWS:
        base_dir = os.path.dirname(os.path.abspath(__file__))
        path = os.path.join(base_dir, "web_server.py")
        cmd = ['python', path]
    else:
        cmd = ['sudo', 'python3', 'web_server.py']
    subprocess.call(cmd)
