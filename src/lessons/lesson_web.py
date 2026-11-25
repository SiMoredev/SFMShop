# Файл scripts/lesson_54_loading_diagnostics.py
STAGE_NAMES = {
    "dns": "DNS-запрос",
    "tcp": "TCP-подключение",
    "server": "Обработка на сервере",
    "transfer": "Передача данных",
    "render": "Рендеринг на клиенте",
}

measurements = {
    "dns": 0.05,
    "tcp": 0.20,
    "server": 2.50,
    "transfer": 0.80,
    "render": 0.45,
}

# Напиши функцию report(stages), которая печатает отчёт и узкое место
def diagnose_loading(stages: dict):
    total = sum(stages.values())
    bottleneck = max(stages, key=lambda name: stages[name])
    return total, bottleneck

def report(stages):
    total, bottleneck = diagnose_loading(stages)
    print(f"Общее время загрузки: {total:.2f} сек")
    for name in ("dns", "tcp", "server", "transfer", "render"):
        ms = stages[name]
        percent = ms / total * 100
        print(f"{STAGE_NAMES[name]}: {ms:.2f} сек ({percent:.1f}%)")
    print(f"Узкое место: {STAGE_NAMES[bottleneck]}")

report(measurements)


# scripts/measure_api_performance.py
import time
import requests
import socket
from urllib.parse import urlparse

def measure_api_performance(url):
    """Измерить производительность API endpoint"""
    results = {}
    
    # 1. Измерение DNS-запроса
    try:
        hostname = urlparse(url).hostname  # отбрасывает порт: 'localhost:8000' -> 'localhost'
        start = time.time()
        ip = socket.gethostbyname(hostname)
        dns_time = time.time() - start
        results['dns'] = dns_time
    except Exception as e:
        results['dns'] = f"Ошибка: {e}"
    
    # 2. Измерение времени запроса
    start = time.time()
    try:
        response = requests.get(url)
        total_time = time.time() - start
        results['total'] = total_time
        # round-trip до получения и парсинга заголовков (без тела), а не чистое время работы сервера
        results['server'] = response.elapsed.total_seconds()
        results['status'] = response.status_code
        results['size'] = len(response.content)
    except Exception as e:
        results['error'] = str(e)
    
    return results

# Тест
if __name__ == "__main__":
    url = "http://localhost:8000/products"
    results = measure_api_performance(url)
    print("Результаты измерения производительности:")
    for key, value in results.items():
        print(f"{key}: {value}")