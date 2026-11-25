# Структура REST API для проекта SFMShop

Товары (`/products`):
- `GET /products` - получить список товаров (`200 OK`)
- `GET /products/{id}` - получить товар по ID (`200 OK` или `404 Not Found`)
- `POST /products` - создать товар (`201 Created` или `400 Bad Request`)
- `PUT /products/{id}` - полностью обновить товар (`200 OK` или `404 Not Found`)
- `PATCH /products/{id}` - частично обновить товар (`200 OK` или `404 Not Found`)
- `DELETE /products/{id}` - удалить товар (`204 No Content` или `404 Not Found`)

Пользователи (`/users`):
- `GET /users` - получить список пользователей (`200 OK`)
- `GET /users/{id}` - получить пользователя по ID (`200 OK` или `404 Not Found`)
- `POST /users` - создать пользователя (`201 Created` или `400 Bad Request`)
- `PUT /users/{id}` - полностью обновить пользователя (`200 OK` или `404 Not Found`)
- `DELETE /users/{id}` - удалить пользователя (`204 No Content` или `404 Not Found`)

Заказы (`/orders`):
- `GET /orders` - получить список заказов (`200 OK`)
- `GET /orders/{id}` - получить заказ по ID (`200 OK` или `404 Not Found`)
- `POST /orders` - создать заказ (`201 Created` или `400 Bad Request`)
- `PUT /orders/{id}` - полностью обновить заказ (`200 OK` или `404 Not Found`)
- `DELETE /orders/{id}` - удалить заказ (`204 No Content` или `404 Not Found`)

Вложенные ресурсы:
- `GET /users/{user_id}/orders` - получить заказы пользователя (`200 OK`)
- `GET /users/{user_id}/orders/{order_id}` - получить заказ пользователя (`200 OK` или `404`)
- `POST /users/{user_id}/orders` - создать заказ для пользователя (`201 Created`)

Пагинация:
- `GET /products?page=1&per_page=10` - получить товары с пагинацией
- `GET /orders?page=1&per_page=20` - получить заказы с пагинацией