# app/wifi_setup/web_server.py

import os
import json
import subprocess
from quart import Quart, render_template, request, redirect

from app.logs.logger_helper import log_event

app = Quart(__name__)
NETWORKS_FILE = 'known_networks.json'


async def load_networks():
    if not os.path.exists(NETWORKS_FILE):
        return []
    async with await app.loop.run_in_executor(None, open, NETWORKS_FILE, 'r') as f:
        content = await app.loop.run_in_executor(None, f.read)
        return json.loads(content)


async def save_networks(networks):
    json_data = json.dumps(networks, indent=2, ensure_ascii=False)
    async with await app.loop.run_in_executor(None, open, NETWORKS_FILE, 'w', encoding='utf-8') as f:
        await app.loop.run_in_executor(None, f.write, json_data)


@app.route('/')
async def index():
    networks = await load_networks()
    return await render_template('index.html', networks=networks)


@app.route('/connect', methods=['POST'])
async def connect():
    form = await request.form
    ssid = form['ssid']
    password = form['password']

    await log_event("INFO", f"Пользователь выбрал сеть: {ssid}", action="WIFI_SELECT", target=ssid)

    networks = await load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    networks.append({'ssid': ssid, 'password': password})
    await save_networks(networks)

    await log_event("INFO", f"Сохранён Wi-Fi профиль: {ssid}", action="WIFI_SAVE", target=ssid)

    # subprocess остаётся синхронным
    subprocess.call(['sudo', 'bash', 'save_wifi.sh', ssid, password])
    subprocess.call(['sudo', 'bash', 'stop_ap.sh'])

    await log_event("INFO", f"Точка доступа выключена, попытка подключения к {ssid}", action="WIFI_CONNECT",
                    target=ssid)

    subprocess.call(['/home/pi/relay_control/venv/bin/python', '/home/pi/relay_control/app/main.py'])

    return "✅ Подключение запущено. Можно закрыть эту страницу."


@app.route('/delete/<ssid>')
async def delete(ssid):
    networks = await load_networks()
    networks = [n for n in networks if n['ssid'] != ssid]
    await save_networks(networks)

    await log_event("INFO", f"Удалена сохранённая сеть: {ssid}", action="WIFI_DELETE", target=ssid)

    return redirect('/')


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80)
