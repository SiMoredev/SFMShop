import requests
from typing import Optional, List
from requests.exceptions import RequestException, Timeout
import time

class MultiExchangeClient:
    """Клиент для работы с несколькими API курсов валют"""
    
    def __init__(self, api_urls: List[str]):
        self.api_urls = api_urls
        self.timeout = 5
        self.max_attempts = 2

    def get_exchange_rate(self, base: str, target: str) -> Optional[float]:

        for api_url in self.api_urls:
            print(f"Попытка получить курс из {api_url}")
            for attempt in range(self.max_attempts):
                try:
                    response = requests.get(
                        f"{api_url}/{base}",
                        timeout=self.timeout
                        )
                    response.raise_for_status()
                    data = response.json()

                    if target in data.get("rates", {}):
                        rate = data["rates"][target]
                        print(f"Курс получен из {api_url}: {rate}")
                        return rate
                    else:
                        print(f"Валюта {target} не найдена в {api_url}")
                        break

                except (Timeout, ConnectionError) as e:
                    if attempt < self.max_attempts - 1:
                        delay = 2 ** attempt
                        print(f"Ошибка {api_url}, повтор через {delay} сек...")
                        time.sleep(delay)
                    else:
                        print(f"API {api_url} недоступен, пробуем следующий")
                        break
                
                except RequestException as e:
                        print(f"Ошибка запроса к {api_url}: {e}")
                        break
        print("Все API недоступны")
        return None

    # Использование:
client = MultiExchangeClient([
    "https://api.exchangerate-api.com/v4/latest",
    "https://api.currencyapi.com/v3/latest",
    "https://api.fixer.io/latest"
])

rate = client.get_exchange_rate("USD", "RUB")