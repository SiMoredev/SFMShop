
import requests
import time
from requests.exceptions import RequestException, Timeout, ConnectionError
from typing import Optional


class ExchangeClient:
    """Клиент для работы с API курсов валют"""

    def __init__(self, base_url: str = "https://api.exchangerate-api.com/v4/latest"):
        self.base_url = base_url
        self.timeout = 5
        self.max_retries = 3

    def get_exchange_rate(self, base_currency: str, target_currency: str) -> Optional[float]:

        for attempt in range(self.max_retries):
            try:
                response = requests.get(
                    f"{self.base_url}/{base_currency}",
                    timeout=self.timeout
                    )
                response.raise_for_status()
                data = response.json()

                if target_currency in data.get("rates", {}):
                    return data["rates"][target_currency]
                else:
                    print(f"Валюта {target_currency} не найдена")
                    return None
                
            except Timeout:
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    print(f"Таймаут, повтор через {delay} сек...")
                    time.sleep(delay)
                else:
                    print("Превышено время ожидания после всех попыток")
                    return None

            except ConnectionError:
                if attempt < self.max_retries - 1:
                    delay = 2 ** attempt
                    print(f"Ошибка подключения, повтор через {delay} сек...")
                    time.sleep(delay)
                else:
                    print("Ошибка подключения после всех попыток")
                    return None

            except RequestException as e:
                print(f"Ошибка запроса: {e}")
                return None


rate = ExchangeClient().get_exchange_rate("USD", "RUB")
print(f"Курс USD->RUB: {rate}")