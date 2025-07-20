from flask import Flask, render_template, request, redirect
import json
import subprocess
import os

from app.logs.logger_helper import log_event

app = Flask(__name__)
NETWORKS_FILE = 'known_networks.json'

def load_networks():
    if not os.path.exists(NETWORKS_FILE):
        return []
    with open(NETWORKS_FILE, 'r') as f:
        return json.load(f)

def save_networks(networks):
    with open(NETWORKS_FILE, 'w') as f:
        json.dump(networks, f, indent=2)

@app.route('/')
def index():
    networks = load_networks()
    return render_template('index.html', networks=networks)

@app.route('/connect', methods=['POST'])
def connect():
    ssid = request.form['ssid']
    password = request.form['password']

    log_event("INFO", f"Пользователь выбрал сеть: {ssid}", action="WIFI_SELECT", target=ssid)

    # Обновляем список сохранённых сетей
    networks = load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    networks.append({'ssid': ssid, 'password': password})
    save_networks(networks)

    log_event("INFO", f"Сохранён Wi-Fi профиль: {ssid}", action="WIFI_SAVE", target=ssid)

    # Сохраняем в wpa_supplicant
    subprocess.call(['sudo', 'bash', 'save_wifi.sh', ssid, password])

    # Отключаем точку доступа
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])

    log_event("INFO", f"Точка доступа выключена, попытка подключения к {ssid}", action="WIFI_CONNECT", target=ssid)

    # Запускаем повторную попытку подключения
    subprocess.call(['/home/pi/relay_control/venv/bin/python', '/home/pi/relay_control/app/main.py'])

    return "✅ Подключение запущено. Можно закрыть эту страницу."

@app.route('/delete/<ssid>')
def delete(ssid):
    networks = load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    save_networks(networks)
    log_event("INFO", f"Удалена сохранённая сеть: {ssid}", action="WIFI_DELETE", target=ssid)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
