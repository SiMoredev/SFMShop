# План: переход с psycopg2 на SQLAlchemy ORM

Текущий этап. Большой план на будущее лежит в `refactoring_plan.md`, сейчас он не нужен.

После каждого шага: запустить `uvicorn src.api.main:app --reload`, проверить ручки в `/docs`, сделать коммит.

---

## Шаг 1. Починить баги, которые мешают проверять

<!-- - [ ] `main.py`, `lifespan`: удалить второй `yield` в конце функции. Он должен быть один. -->
<!-- - [ ] Кэш товара: `set_product` пишет в ключ `product:{id}`, а `get_product_by_id` читает `products:{id}`. Ключи должны совпадать. -->
<!-- - [ ] Кэш списка: `GET /products` читает через `get_products_page(limit, offset)` (ключ `products:{limit}:{offset}`), а пишет через `set_products` (ключ `products:all`). Записывать нужно в тот же ключ, из которого читаем. -->
<!-- - [ ] `GET /products`: пустая страница — не ошибка. Вернуть `[]` со статусом 200 вместо 404. -->
<!-- - [ ] `DELETE /products/{id}`: `if deleted == 0` → `if not deleted`. -->

## Шаг 2. Доделать ORM-версии запросов

`main.py` уже работает через `queries_orm.py`. Осталось проверить, что каждая ORM-функция корректна.

- [ ] Пройти по `queries_orm.py` и проверить каждую функцию:
  <!-- - сессия всегда закрывается (`finally: session.close()`);
  - при ошибке записи вызывается `rollback()`, и исключение пробрасывается дальше (`raise`); -->
  - если объект не найден, возвращается `None` или `False`, а не падение на `None.name`.
<!-- - [ ] Удалить лишний импорт `from http.client import TOO_EARLY` в `queries_orm.py`. -->
- [ ] Если понадобится удаление заказа, написать `delete_order(order_id)` на ORM. Позиции удалятся сами: у `Order.order_items` стоит `cascade="all, delete-orphan"`.

## Шаг 3. Убрать psycopg2

- [ ] `cache_service.py`: из `src.database.connection` импортируется `get_product_by_id`, `get_all_products`, `connect_to_db`, но они не используются. Оставить только `redis_client`.
- [ ] `queries.py`: старые запросы на сыром SQL через `connect_to_db`. Если в `main.py` они не используются, удалить файл.
- [ ] `connection.py`: удалить функции с `conn` и `cur.execute(...)`. Оставить только `redis_client`, его позже можно перенести в `cache_service.py`.
- [ ] Проверить, что больше никто не импортирует psycopg2-функции:
  ```bash
  grep -rn "connect_to_db\|from src.database.connection import" src
  ```

---

## Шаг 4. Правильное оформление заказа (`create_order`)

### Как устроены данные

```
Order       — шапка заказа: кто купил, когда, итоговая сумма, статус
OrderItems  — строки заказа: какой товар, сколько штук, по какой цене
```

Заказ из двух товаров — это одна запись `Order` и две записи `OrderItems`.

### 4.1 Схема запроса (`schemas.py`)

Сейчас `OrderCreate` принимает один `product_id` без количества. Нужен список позиций:

- [ ] Класс `OrderItemCreate`: `product_id: int`, `quantity: int = Field(gt=0)`.
- [ ] `OrderCreate`: `user_id: int`, `items: list[OrderItemCreate] = Field(min_length=1)`.

Пример тела запроса:

```json
{"user_id": 1, "items": [{"product_id": 2, "quantity": 3}, {"product_id": 5, "quantity": 1}]}
```

### 4.2 Исключения (`exceptions.py`)

- [ ] Добавить `UserNotFoundError` и `ProductNotFoundError` по образцу существующих.
- [ ] `InsufficientStockError` уже есть, его и использовать.

### 4.3 Функция `create_order(user_id, items)` в `queries_orm.py`

Главное правило: **всё в одной сессии и одним `commit`.** Если любой шаг падает → `rollback`, и в базе ничего не меняется.

- [ ] Открыть одну сессию.
- [ ] Найти пользователя через `session.get(User, user_id)`. Если `None`, бросить `UserNotFoundError`.
- [ ] Загрузить все товары **одним запросом** с блокировкой:
  ```python
  select(Product).where(Product.id.in_(ids)).order_by(Product.id).with_for_update()
  ```
  - `with_for_update()` — пока транзакция не закончится, другой заказ этих товаров будет ждать. Так два покупателя не купят последнюю штуку одновременно.
  - `order_by(Product.id)` — блокировки всегда берутся в одном порядке, иначе два заказа могут ждать друг друга вечно (deadlock).
- [ ] Если какого-то `product_id` нет среди найденных, бросить `ProductNotFoundError`.
- [ ] Создать `Order(user_id=..., total=Decimal("0"))`.
- [ ] Для каждой позиции:
  - если `product.stock < quantity`, бросить `InsufficientStockError`;
  - уменьшить `product.stock -= quantity`;
  - добавить позицию: `order.order_items.append(OrderItems(product=product, quantity=quantity, price=product.price))`;
  - прибавить к сумме `product.price * quantity`.
- [ ] Записать `order.total`, вызвать `session.add(order)` и `session.commit()`, вернуть `order.id`.
- [ ] Обернуть в `try / except: rollback; raise / finally: close`.

### Вопросы для самопроверки

- Почему `price` сохраняется в `OrderItems`, если она уже есть в `Product`?
  → Цена товара может поменяться завтра, а в заказе должна остаться та, по которой купили.
- Почему не нужно указывать `order_id` у `OrderItems`?
  → `order.order_items.append(...)` связывает их через `relationship`, и SQLAlchemy сам подставит `id` при сохранении.
- Почему `total` считается на сервере, а не приходит от клиента?
  → Иначе клиент может прислать любую сумму.
- Что будет со `stock` первого товара, если второго не хватило?
  → Ничего: `rollback` отменит все изменения транзакции.

### 4.4 Эндпоинт `POST /orders` в `main.py`

Эндпоинт только вызывает функцию и превращает ошибки в HTTP-коды:

- [ ] `UserNotFoundError`, `ProductNotFoundError` → 404.
- [ ] `InsufficientStockError` → 409.
- [ ] После успешного заказа сбросить кэш изменённых товаров (`stock` изменился).
- [ ] Убрать старую логику: `Product.from_dict(row)`, `get_total_price`, `order_obj`.

### 4.5 Проверка в `/docs`

- [ ] Заказ из двух товаров → 201. В базе одна строка в `orders`, две в `order_items`, `stock` товаров уменьшился.
- [ ] Количество больше, чем на складе → 409. `stock` **не** изменился, заказ **не** создан.
- [ ] Несуществующий `product_id` → 404.
- [ ] Несуществующий `user_id` → 404.
- [ ] `quantity: 0` или пустой `items` → 422 (это проверяет Pydantic).

Проверить базу после заказа:

```sql
SELECT * FROM orders ORDER BY id DESC LIMIT 1;
SELECT * FROM order_items WHERE order_id = <id заказа>;
SELECT id, name, stock FROM products WHERE id IN (2, 5);
```
