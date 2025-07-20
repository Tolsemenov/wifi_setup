from flask import Flask, render_template, request, redirect
import json
import subprocess
import os

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

    # Обновляем список сохранённых сетей
    networks = load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    networks.append({'ssid': ssid, 'password': password})
    save_networks(networks)

    # Сохраняем в wpa_supplicant
    subprocess.call(['sudo', 'bash', 'save_wifi.sh', ssid, password])

    # Отключаем точку доступа
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])

    # Запускаем повторную попытку подключения
    subprocess.call(['sudo', 'python3', 'main.py'])

    return "✅ Подключение запущено. Можно закрыть эту страницу."

@app.route('/delete/<ssid>')
def delete(ssid):
    networks = load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    save_networks(networks)
    return redirect('/')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
