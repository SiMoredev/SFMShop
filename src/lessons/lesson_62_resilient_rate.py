# Файл scripts/lesson_62_resilient_rate.py
from typing import Optional


class ApiUnavailableError(Exception):
    """Имитация ошибки недоступности внешнего API."""
    pass


class FakeRatesApi:
    """Заглушка внешнего API: падает первые fail_times раз, потом отдаёт курс."""

    def __init__(self, rate: float, fail_times: int):
        self.rate = rate
        self.fail_times = fail_times
        self.calls = 0

    def fetch_rate(self, base: str, target: str) -> float:
        self.calls += 1
        if self.calls <= self.fail_times:
            raise ApiUnavailableError("сервис недоступен")
        return self.rate


class ResilientRateClient:
    """Клиент с retry-логикой и обработкой ошибок поверх заглушки API."""

    def __init__(self, api: FakeRatesApi, max_retries: int = 3):
        self.api = api
        self.max_retries = max_retries

    def get_rate(self, base: str, target: str) -> Optional[float]:
        for attempt in range(self.max_retries):
            try:
                rate = self.api.fetch_rate(base=base, target=target)
                print(f"Попытка {attempt + 1}: успех, курс {base}->{target} = {rate}")
                return rate
            except ApiUnavailableError:
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    print(f"Попытка {attempt + 1}: ошибка, повтор через {delay} сек")
                else:
                    print(f"Попытка {attempt + 1}: ошибка, попытки исчерпаны")
                    return None
        return None

    def convert(self, price: float, base: str, target: str) -> Optional[float]:
        rate = self.get_rate(base=base, target=target)
        if rate is None:
            return None
        return round(price * rate, 2)


# Сценарий 1: API падает 2 раза, затем отвечает (курс USD->RUB = 90.0)
api1 = FakeRatesApi(rate=90.0, fail_times=2)
client1 = ResilientRateClient(api1, max_retries=3)
result1 = client1.convert(1500.0, "USD", "RUB")
print(f"Цена товара SFMShop: 1500 USD = {result1} RUB")

print("---")

# Сценарий 2: API недоступен всегда — все попытки исчерпаны
api2 = FakeRatesApi(rate=90.0, fail_times=5)
client2 = ResilientRateClient(api2, max_retries=3)
result2 = client2.convert(1500.0, "USD", "RUB")
print(f"Результат конвертации: {result2}")