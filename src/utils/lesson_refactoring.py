# # Файл src/main.py
# def process_order(order_data):
#     """Обработка заказа - делает слишком много"""
#     # Валидация
#     validate_order_data(order_data)

    
#     # Расчет стоимости

    
#     # Применение скидки
#     discount = 0
#     if total > 10000:
#         discount = 0.15
#     elif total > 5000:
#         discount = 0.10
#     elif total > 1000:
#         discount = 0.05
#     final_total = total * (1 - discount)
    
#     # Проверка баланса пользователя
#     user_balance = get_user_balance(order_data["user_id"])
#     if user_balance < final_total:
#         raise ValueError("Недостаточно средств")
    
#     # Сохранение заказа
#     order_id = save_order_to_db(order_data["user_id"], order_data["items"], final_total)
    
#     # Отправка уведомления
#     user_email = get_user_email(order_data["user_id"])
#     send_email(user_email, f"Заказ #{order_id} оформлен на сумму {final_total}")
    
#     # Логирование
#     print(f"Заказ {order_id} обработан: пользователь {order_data['user_id']}, сумма {final_total}")
    
#     return {
#         "order_id": order_id,
#         "total": final_total,
#         "discount": discount
#     }

# def validate_order_data(order_data):

#     if not order_data.get("user_id"):
#         raise ValueError("Нет user_id")
#     if not order_data.get("items"):
#         raise ValueError("Нет товаров")
#     if len(order_data.get("items", [])) == 0:
#         raise ValueError("Список товаров пуст")

#     return order_data


# def calculate_order_total(order_data):
#     total = 0
#     for item in order_data["items"]:
#         if not item.get("price"):
#             raise ValueError("Нет цены товара")
#         if not item.get("quantity"):
#             raise ValueError("Нет количества")
#         if item["price"] < 0:
#             raise ValueError("Цена не может быть отрицательной")
#         if item["quantity"] <= 0:
#             raise ValueError("Количество должно быть положительным")
#         total += item["price"] * item["quantity"]



# def calculate_discount():
#     ...
# def check_user_balance():
#     ...
# def create_order():
#     ...
# def notify_user():
#     ...
# def process_order():
#     ...
