# app/wifi_setup/button_listener.py


from app.logs.logger_helper import log_event
try:
    import RPi.GPIO as GPIO
    GPIO_AVAILABLE = True
except (ImportError, RuntimeError):
    print("⚠️ GPIO недоступен (не Raspberry Pi / Orange Pi?). Работа кнопки отключена.")
    GPIO_AVAILABLE = False
import time
import subprocess
import threading
import asyncio



BUTTON_PIN = 17                # Пин, к которому подключена кнопка
HOLD_SECONDS = 3               # Время удержания для активации
CHECK_CLIENTS_EVERY = 10       # Частота проверки активности
TIMEOUT_NO_CLIENTS = 300       # 5 минут в секундах

last_client_time = time.time()




def log_async(level: str, message: str, action: str = "", target: str = None):
    try:
        asyncio.run(log_event(level, message, action, target))
    except RuntimeError:
        loop = asyncio.get_event_loop()
        loop.create_task(log_event(level, message, action, target))

def setup_gpio():
    if not GPIO_AVAILABLE:
        return
    GPIO.setmode(GPIO.BCM)
    GPIO.setup(BUTTON_PIN, GPIO.IN, pull_up_down=GPIO.PUD_UP)

def start_ap_and_web():
    global last_client_time


    last_client_time = time.time()
    print("🔧 Запуск точки доступа и веб-интерфейса...")
    log_async("INFO", "Кнопка нажата — запуск точки доступа", action="WIFI_AP_START")

    # Запускаем AP
    subprocess.call(['sudo', 'bash', 'setup_ap.sh'])

    # Flask-сервер в фоне
    flask_thread = threading.Thread(
        target=lambda: subprocess.call(['sudo', 'python3', 'web_server.py']))
    flask_thread.start()

    # Мониторим подключения
    monitor_thread = threading.Thread(target=monitor_ap_clients)
    monitor_thread.start()

def monitor_ap_clients():
    global last_client_time
    print("⏳ Ожидаем подключения к точке доступа...")
    log_async("INFO", "Ожидание подключения к точке доступа", action="WIFI_AP_MONITOR")


    while True:
        if has_connected_clients():
            last_client_time = time.time()
            print("📶 Обнаружено подключение к AP.")
            log_async("INFO", "Обнаружено подключение клиента к AP", action="WIFI_CLIENT_CONNECTED")

        elif time.time() - last_client_time > TIMEOUT_NO_CLIENTS:
            print("❌ Никто не подключался к AP за 5 минут — выключаем.")
            log_async("WARNING", "Никто не подключился за 5 минут. Выключаем AP.", action="WIFI_AP_TIMEOUT")

            subprocess.call(['sudo', 'bash', 'stop_ap.sh'])
            subprocess.call(['sudo', 'python3', 'main.py'])
            break
        time.sleep(CHECK_CLIENTS_EVERY)

def has_connected_clients():
    # Проверяем наличие подключенных клиентов к точке доступа
    output = subprocess.getoutput("nmcli dev wifi list ifname wlan0")
    return "AutoPoliv" in output and "yes" in output

def listen_button():
    if not GPIO_AVAILABLE:
        print("⏭️ Пропуск прослушивания кнопки — GPIO недоступен")
        return
    pressed_time = 0
    while True:
        if GPIO.input(BUTTON_PIN) == GPIO.LOW:
            if pressed_time == 0:
                pressed_time = time.time()
            elif time.time() - pressed_time >= HOLD_SECONDS:
                print("🔘 Кнопка удерживалась — включаем режим настройки Wi-Fi.")
                start_ap_and_web()
                pressed_time = 0
                time.sleep(TIMEOUT_NO_CLIENTS + 5)
        else:
            pressed_time = 0
        time.sleep(0.1)

if __name__ == '__main__':
    try:
        setup_gpio()
        listen_button()
    except KeyboardInterrupt:
        GPIO.cleanup()
