# Архитектура микросервисов для проекта SFMShop

## payment-service

### Структура:

payment-service/

src/

api/

main.py # FastAPI приложение

routes/

payments.py # Endpoints для платежей

models/

payment.py # Модели платежей

services/

payment_service.py # Бизнес-логика платежей

database/

connection.py # Подключение к БД

models.py # ORM модели

config.py # Конфигурация

tests/

test_payments.py # Тесты

requirements.txt

Dockerfile

README.md

### Ответственность:
- Обработка платежей
- Проверка баланса пользователя
- Возврат средств
- История платежей

### Endpoints:
- POST /api/v1/payments - создать платеж (201 Created)
 - Body: {order_id: int, amount: float, user_id: int}
 - Response: {id: int, status: str, transaction_id: str}

- GET /api/v1/payments/{id} - получить платеж по ID (200 OK или 404)
 - Response: {id: int, order_id: int, amount: float, status: str}

- GET /api/v1/payments/user/{user_id} - получить платежи пользователя (200 OK)
 - Response: {payments: [...]}

### Взаимодействие:
- order-service вызывает payment-service для обработки платежа
- HTTP POST запрос к /api/v1/payments
- Передача order_id, amount, user_id
- Получение результата обработки платежа

### Развертывание:
- Порт: 8002
- URL: http://payment-service:8002
- Независимое развертывание через Docker
- Собственная БД для платежей

Описана полная структура микросервиса. Указаны все endpoints с методами и статусами. Описано взаимодействие с другими сервисами. Указаны настройки развертывания.