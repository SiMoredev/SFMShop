# План рефакторинга SFMShop: разделение на слои

Цель — чтобы у каждого слоя была одна задача:

| Слой | Где | Что делает | Чего НЕ делает |
|---|---|---|---|
| Роутеры | `src/api/routers/` | HTTP: принять запрос, вызвать сервис, вернуть ответ | SQL, бизнес-правила |
| Сервисы | `src/services/` | Бизнес-логика: проверки, расчёты, кэш, события | `HTTPException`, `status_code` |
| Репозитории | `src/database/repositories/` | Чтение и запись в БД через ORM | `commit`, `close`, бизнес-правила |
| Схемы | `src/schemas/` | Формат входных и выходных данных API | Логика |

Порядок этапов выбран так, чтобы после каждого приложение запускалось.
После каждого этапа: запустить `uvicorn src.api.main:app --reload`, проверить ручки в `/docs`, сделать коммит.

## Целевая структура

```
src/
├── core/
│   ├── config.py           # настройки из .env
│   └── exceptions.py       # доменные исключения (UserNotFoundError, ...)
├── database/
│   ├── session.py          # engine, SessionLocal
│   ├── models.py           # только ORM-модели
│   └── repositories/
│       ├── users.py
│       ├── products.py
│       └── orders.py
├── services/
│   ├── product_service.py
│   ├── order_service.py
│   ├── user_service.py
│   ├── cache_service.py
│   └── log_service.py
├── schemas/
│   ├── products.py
│   ├── users.py
│   └── orders.py
└── api/
    ├── main.py             # app, lifespan, middleware, include_router
    ├── dependencies.py     # get_db, get_*_service
    ├── exception_handlers.py
    └── routers/
        ├── products.py
        ├── users.py
        └── orders.py
tests/
```

---

## Этап 0. Починить то, что сломано сейчас

- [ ] В `lifespan` в `main.py` два `yield`. Второй нужно удалить, иначе при остановке сервера будет `RuntimeError: generator didn't stop`.
- [ ] `GET /products`: читает кэш через `get_products_page(limit, offset)` (ключ `products:{limit}:{offset}`), а пишет через `set_products` (ключ `products:all`). Ключи не совпадают, кэш никогда не срабатывает. Нужно писать через `set_products_page(limit, offset, data)`.
- [ ] `GET /products` на пустой странице возвращает 404. Правильно вернуть 200 и пустой список.
- [ ] `DELETE /products`: заменить `if deleted == 0` на `if not deleted`; добавить `passive_deletes="all"` у `Product.order_items` и ответ 409, если товар есть в заказах.
- [ ] `POST /orders`: сумма считается как `price * stock` (весь склад). Временно, до этапа 5, считать от количества из запроса.
- [ ] Убрать лишние импорты: `from http.client import TOO_EARLY` в `queries_orm.py`, `TestClient`, `ModelRegistryMeta`, `Product` в `main.py`.
- [ ] Добавить в `.gitignore` строку `.DS_Store` и выполнить `git rm --cached src/api/models/.DS_Store`.

## Этап 1. Настройки и подключения в одном месте

Сейчас строка подключения к Postgres собирается в трёх местах (`models.py`, `connection.py`, `lifespan`), а Redis-клиент лежит в `connection.py`.

- [ ] `src/core/config.py`: класс `Settings` (через `pydantic-settings`) с полями `DB_*`, `REDIS_*`, `MONGO_*` и свойством `database_url`.
- [ ] `src/database/session.py`: перенести сюда `engine` и `SessionLocal` из `models.py`. В `models.py` остаются только модели.
- [ ] Redis-клиент перенести из `connection.py` в `cache_service.py` (или `src/core/redis.py`).
- [ ] Решить судьбу `asyncpg`-пула в `lifespan`. Если ручки работают через синхронный SQLAlchemy, пул не нужен: удалить его вместе с `db_pool`. Оставить можно только для учебной ручки `/products/{id}/full`.
- [ ] Обновить `migrations/env.py`, чтобы он брал URL из `settings`.

## Этап 2. Сессия на запрос через `Depends`

- [ ] `src/api/dependencies.py`: функция `get_db()`. Открывает сессию, делает `commit` после успешного запроса и `rollback` при ошибке, всегда `close`.
- [ ] В `lifespan` вместо закрытия пулов: `engine.dispose()`.
- [ ] Удалить глобальный `conn` и все вызовы `get_session()` внутри функций запросов.

## Этап 3. Репозитории вместо `queries_orm.py`

Каждая функция из `queries_orm.py` переезжает в метод класса. Правила для всех репозиториев:
- сессия приходит в `__init__`, `get_session()` внутри не вызывается;
- нет `commit`, `rollback`, `close` (только `flush`, если нужен `id`);
- возвращаются ORM-объекты, а не `dict`.

- [ ] `UserRepository`: `get_by_id`, `get_by_email`, `list(limit, offset)`, `add`.
- [ ] `ProductRepository`: `get_by_id`, `list(limit, offset)`, `count`, `add`, `delete`, `get_many_for_update(ids)`.
- [ ] `OrderRepository`: `add`, `get_by_id` (с `selectinload` позиций), `list_by_user(user_id)`.
- [ ] Удалить `queries_orm.py`, `queries.py` и функции сырого SQL из `connection.py`.

## Этап 4. Схемы для ответов

Сейчас словари для ответа собираются вручную, с `float(...)` и `isoformat()`.

- [ ] Разделить `schemas.py` по файлам: `products.py`, `users.py`, `orders.py`.
- [ ] Для каждой сущности: `Create`, `Update` (поля `Optional`), `Read` с `model_config = ConfigDict(from_attributes=True)`.
- [ ] `OrderCreate`: `user_id` и `items: list[OrderItemCreate]` (`product_id`, `quantity > 0`).
- [ ] `OrderRead` с вложенным списком позиций.
- [ ] В роутерах указать `response_model=...` и возвращать ORM-объект. Pydantic сам сериализует `Decimal` и `datetime`.

## Этап 5. Сервисы с бизнес-логикой

- [ ] Перенести исключения из `src/api/models/exceptions.py` в `src/core/exceptions.py` и добавить `UserNotFoundError`, `ProductNotFoundError`, `ProductInUseError`, `InsufficientFundsError`.
- [ ] `ProductService`: создание, обновление, удаление (с инвалидацией кэша), чтение с кэшем. Кэш хранить через `ProductRead.model_dump(mode="json")`.
- [ ] `UserService`: создание с проверкой уникального email (`NotUniqueEmailError`).
- [ ] `OrderService.create_order(user_id, items)`:
  - [ ] пользователь существует;
  - [ ] товары загружены одним запросом `FOR UPDATE`, отсортированы по `id`;
  - [ ] на складе достаточно товара, `stock` уменьшен;
  - [ ] у позиций `OrderItems` своя `price` (цена на момент покупки);
  - [ ] `total` посчитан на сервере;
  - [ ] (опционально) проверен и списан `balance` пользователя.
- [ ] Событие `order_created` в MongoDB и сброс кэша товаров делать в сервисе после успешного оформления.

## Этап 6. Роутеры и тонкий `main.py`

- [ ] `src/api/routers/products.py`, `users.py`, `orders.py` через `APIRouter(prefix=..., tags=[...])`.
- [ ] Эндпоинт делает только три вещи: получает сервис через `Depends`, вызывает метод, возвращает результат.
- [ ] `src/api/exception_handlers.py`: обработчики доменных исключений, по одному месту на тип вместо `try/except` в каждом эндпоинте:
  - `*NotFoundError` → 404
  - `InsufficientStockError`, `ProductInUseError`, `NotUniqueEmailError` → 409
  - `InsufficientFundsError` → 402
  - `Exception` → 500 (как сейчас, с записью в MongoDB)
- [ ] В `main.py` оставить только `app`, `lifespan`, middleware логирования, подключение обработчиков и `app.include_router(...)`.

## Этап 7. Тесты

- [ ] Перенести `test_api()` из `main.py` в `tests/test_products.py` (pytest).
- [ ] Отдельная тестовая база и `app.dependency_overrides[get_db]` для подмены сессии.
- [ ] Тесты `OrderService` без HTTP: успешный заказ, нехватка склада (склад не изменился), несуществующий товар.
- [ ] Тест конкурентного заказа: два потока покупают последнюю единицу, успешен только один.

## Этап 8. Уборка

- [ ] `src/api/models/` (ООП-модели с дескрипторами, метаклассами, стратегиями) — это учебный код, не слой API. Перенести в `src/lessons/` или `src/domain/`, если будет использоваться в сервисах.
- [ ] `src/utils/calculations.py`, `product_calculator.py`: оставить только то, что вызывается из сервисов.
- [ ] Проверить, что `connection.py` удалён или в нём не осталось кода.
- [ ] Обновить `src/docs/database_architecture.md` под новую структуру.

---

## Проверка «куда положить код»

- Есть `HTTPException`, `status_code`, `Request` → роутер или обработчик исключений.
- Есть правило бизнеса («хватает ли», «можно ли», «сколько стоит») → сервис.
- Есть `select`, `session.add`, `session.get` → репозиторий.
- Описывает форму JSON → схема.
