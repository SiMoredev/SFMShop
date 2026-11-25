# Файл src/api/limiter.py
from slowapi import Limiter
from slowapi.util import get_remote_address


# Клиента различаем по IP-адресу
limiter = Limiter(key_func=get_remote_address)