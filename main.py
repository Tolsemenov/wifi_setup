import subprocess

from wifi_manager import is_wifi_connected, stop_access_point, start_access_point, run_flask_web

if is_wifi_connected():
    print("✅ Wi-Fi подключён")
    stop_access_point()
else:
    print("❌ Wi-Fi не подключён. Запуск точки доступа...")
    start_access_point()
    run_flask_web()  # запускаем Flask веб-интерфейс
