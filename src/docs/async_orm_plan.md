# План: переход на асинхронный SQLAlchemy + уборка проекта

Цель: в проекте остаётся **один** способ работать с PostgreSQL — асинхронный SQLAlchemy
(`AsyncSession` + драйвер `asyncpg`). Всё, что дублирует это (psycopg2-функции, sync-движок,
сырой пул asyncpg), удаляется.

Правило на весь план: **после каждого шага приложение запускается** (`uvicorn src.api.main:app --reload`)
и эндпоинты отвечают. Делай коммит после каждого шага — так легко откатиться.

---

## Что сейчас в проекте (стартовая точка)

| Что | Где | Проблема |
|---|---|---|
| Sync-движок + `get_session()` | `src/database/models.py` | Модели и подключение смешаны в одном файле |
| Async-движок + `AsyncSessionLocal` | `src/services/async_service.py` | Второй движок, живёт в «сервисе», а не в `database/` |
| Пул `asyncpg.create_pool` | `src/api/main.py` (lifespan) | Нигде не используется; к тому же закрывается **до** `yield` |
| Функции на psycopg2 | `src/database/connection.py` | Старый слой, ORM его заменил |
| Сырой SQL | `src/database/queries.py` | Старый слой, ORM его заменил |
| Sync ORM-запросы | `src/database/queries_orm.py` | Это и переписываем на async |
| Строка подключения к БД | в 4 местах (`models.py`, `async_service.py`, `main.py`, `migrations/env.py`) | Копипаста |
| Redis-клиент | `src/database/connection.py` | Из-за него `cache_service` тянет весь psycopg2-модуль |

---

## Шаг 0. Подготовка

- [ ] Закоммить текущие изменения (`src/api/main.py` и новые файлы уроков), чтобы начать с чистого состояния.
- [ ] Создай ветку под эту работу, например `feature/async-orm`.
- [ ] Проверь `requirements.txt`: там **нет `SQLAlchemy`**, хотя он используется. Добавь его
  (`pip freeze | grep -i sqlalchemy` покажет установленную версию).
- [ ] Запусти приложение и пройдись по эндпоинтам в `/docs` — запомни, как всё работает «до».

---

## Шаг 1. Один модуль подключения к БД

Создай `src/database/session.py` — единственное место, где создаётся движок.

- [ ] Собери URL **один раз** (строку `postgresql+asyncpg://...` из `.env`).
- [ ] `create_async_engine(...)` и `async_sessionmaker(engine, expire_on_commit=False)`.
  - Подумай: зачем `expire_on_commit=False`? (Подсказка: что будет, если после `commit()`
    обратиться к `user.id` в async-коде?)
- [ ] Напиши dependency для FastAPI — **асинхронный генератор** `get_session()`, который
  открывает сессию через `async with` и делает `yield session`.
- [ ] Из `src/services/async_service.py` убери свой `engine` и `AsyncSessionLocal` —
  импортируй их из `session.py`.
- [ ] Из `src/database/models.py` **пока не трогай** sync-движок — он ещё нужен старым запросам.

✅ Проверка: `python -c "from src.database.session import get_session"` без ошибок.

---

## Шаг 2. Переписать `queries_orm.py` на async

Идти по одной функции, начиная с простых. Для каждой:

- [ ] `def` → `async def`.
- [ ] Сессию **не создавать внутри**, а принимать параметром: `async def get_user_by_id(session: AsyncSession, user_id: int)`.
  Тогда `try/finally/close()` больше не нужны — сессией управляет dependency.
- [ ] Всё, что ходит в БД, — через `await`: `await session.get(...)`, `await session.execute(...)`,
  `await session.commit()`, `await session.delete(...)`, `await session.rollback()`.
  - `session.add(...)` — без `await` (он ничего не отправляет в БД). Почему так?
- [ ] Ленивые связи (`user.orders`, `order.order_items`) в async **не работают** — получишь
  `MissingGreenlet`. Связи грузи явно через `selectinload`/`joinedload` в запросе.

Порядок (от простого к сложному):

1. [ ] `get_user_by_id`, `get_product_by_id`
2. [ ] `get_users`, `get_products_page` (обрати внимание: `get_users` возвращает `None`, если пусто — а должен `[]`)
3. [ ] `create_user`, `add_product`, `update_product`, `delete_product`
4. [ ] `get_user_orders`, `get_all_orders_with_users`, `get_orders_with_products`
5. [ ] `get_order` — сейчас возвращает ORM-объект после закрытия сессии. Верни `dict`, как в остальных функциях.
6. [ ] `create_order` — с `with_for_update=True`, проверь, что блокировки работают так же.
7. [ ] `process_order` — async-версия уже есть в `async_service.py`. Оставь **одну** (в `queries_orm.py`),
   а в `async_service.py` её импортируй.

Мелочь по ходу: в начале `queries_orm.py` есть `from requests import session` — это мусор, удали.

✅ Проверка: маленький скрипт с `asyncio.run(...)`, который открывает сессию и вызывает пару функций.

---

## Шаг 3. Эндпоинты в `main.py` на async

- [ ] Каждый эндпоинт, который ходит в БД: `def` → `async def`.
- [ ] Добавь параметр `session: AsyncSession = Depends(get_session)` и передавай его в функции запросов.
- [ ] Перед каждым вызовом запроса — `await`.
- [ ] Почини `lifespan`: сейчас ресурсы закрываются **до** `yield`, то есть сразу при старте.
  Всё, что «при остановке», должно идти **после** `yield`.
- [ ] Удали `asyncpg.create_pool` и `db_pool` из lifespan — его заменил движок SQLAlchemy.
- [ ] В lifespan при остановке вызови `await engine.dispose()`.
- [ ] Переменная `resources: dict = {}` не используется — удали.

Вопрос для себя: что будет, если оставить `def` эндпоинт, но внутри вызвать `async`-функцию без `await`?
А если сделать `async def` эндпоинт и вызвать внутри **sync**-запрос к БД?

✅ Проверка: все эндпоинты в `/docs` работают как в шаге 0. `test_api()` в конце `main.py` проходит.

---

## Шаг 4. Redis и кэш

- [ ] Перенеси создание Redis-клиента из `connection.py` в `cache_service.py` (или в отдельный `src/database/redis.py`).
- [ ] Убери из `cache_service.py` импорт `get_product_by_id, get_all_products, connect_to_db` — они там не используются.
- [ ] (Опционально, но логично) перейди на `redis.asyncio` — тогда методы `CacheService` станут `async`,
  а в эндпоинтах появится `await cache_service...`. Библиотека та же `redis`, ставить ничего не нужно.
- [ ] Найди баг с ключами: `set_product` пишет `products:{id}`, а `invalidate_product_cache` удаляет `product:{id}`.
  Аналогично `invalidate_products_cache` удаляет `products:all`, которого никто не создаёт.
- [ ] Вызывай инвалидацию в `update_product_endpoint` и `delete_product_endpoint` — сейчас кэш после изменения товара не сбрасывается.

✅ Проверка: обнови товар через PUT → GET возвращает новые данные, а не старые из кэша.

---

## Шаг 5. Уборка: удалить старый слой

Удалять только после того, как шаги 1–4 работают. Перед удалением каждого файла —
`grep -rn "имя_модуля" src scripts migrations`, чтобы убедиться, что его никто не импортирует.

- [ ] `src/database/connection.py` — psycopg2-функции, PRIMARY/REPLICA конфиги.
- [ ] `src/database/queries.py` — сырой SQL.
- [ ] Из `src/database/models.py` убери `create_engine`, `Sessionlocal`, `get_session`, `load_dotenv`, `os` —
  в файле остаются **только модели**.
- [ ] `scripts/seed_perf_data.py` импортирует `engine` из `models.py` — переведи на новый модуль
  (или на свой sync-движок прямо в скрипте, если не хочешь делать его async).
- [ ] В `src/services/async_service.py`:
  - дублирующиеся импорты (`asyncio`, `time`, `create_async_engine` по два раза);
  - `main()` сравнивает с sync-версией `process_order_orm` — после удаления sync её не будет, перепиши или убери блок.
- [ ] `src/api/main.py`: `ModelRegistryMeta` используется только в `__main__`-блоке — реши, нужен ли он там.
- [ ] Закоммиченный мусор: `src/__pycache__/*.pyc`, `src/.DS_Store`, `src/api/models/.DS_Store`.
  Они уже в git, поэтому `.gitignore` их не спасает — нужен `git rm --cached`. Добавь `.DS_Store` в `.gitignore`.

---

## Шаг 6. Зависимости

- [ ] `psycopg2-binary` — нужен ли ещё? Он остаётся нужен **только** если Alembic работает через sync-URL
  `postgresql://` (так сейчас в `migrations/env.py`). Это нормальный вариант — Alembic может оставаться синхронным.
  Решение за тобой: оставить так или перевести `env.py` на async-шаблон (`alembic init -t async`).
- [ ] `types-psycopg2` — не нужен, если psycopg2 только для Alembic.
- [ ] `asyncio==4.0.0` — **удалить**. `asyncio` входит в стандартную библиотеку, а этот пакет — старый мусор с PyPI.
- [ ] Проверь пакеты, которые выглядят случайными: `exception`, `detect-installer`, `httpcore2`, `httpx2`.
  `pip show <пакет>` → поле `Required-by`: если пусто и в коде не импортируется — удалить.
- [ ] `aiohttp` и `httpx` делают одно и то же. В `main.py` уже есть `httpx.AsyncClient` — можно
  оставить только `httpx` и переписать `async_service.py` на него. (Если aiohttp нужен для урока — оставь.)

✅ Проверка: новое виртуальное окружение → `pip install -r requirements.txt` → приложение стартует.

---

## Шаг 7. Финальная проверка

- [ ] `grep -rn "psycopg2\|Sessionlocal\|create_engine(" src` — ничего лишнего не осталось.
- [ ] `alembic upgrade head` работает.
- [ ] Все эндпоинты работают, `test_api()` проходит.
- [ ] `python -m src.services.async_service` (бенчмарк) работает.
- [ ] Обнови `src/docs/orm_plan.md` / `refactoring_plan.md`, если там описан старый слой.

---

## Итоговая структура `src/database/`

```
src/database/
├── models.py        # только ORM-модели
├── session.py       # engine, async_sessionmaker, get_session (dependency)
└── queries_orm.py   # async-функции, принимают session параметром
```

## Частые ошибки, которые ты встретишь

- `MissingGreenlet` — обращение к ленивой связи или к атрибуту после `commit()`. Лечится `selectinload` и `expire_on_commit=False`.
- `coroutine was never awaited` — забыл `await`.
- Эндпоинт «висит» — внутри `async def` остался синхронный вызов БД/Redis, он блокирует event loop.
- `InterfaceError: another operation is in progress` — одна сессия используется в `asyncio.gather` параллельно.
  Одна `AsyncSession` = одна задача. Поэтому в `process_orders_async` каждая задача открывает свою сессию.
