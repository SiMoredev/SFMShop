from datetime import datetime, timedelta
import os
import logging
from dotenv import load_dotenv
from pymongo import MongoClient
from pymongo.errors import PyMongoError

load_dotenv()

logger = logging.getLogger(__name__)

client = MongoClient(
    host=os.getenv("MONGO_HOST", "localhost"),
    port=int(os.getenv("MONGO_PORT", 27017)),
    serverSelectionTimeoutMS=1000,  # ждать сервер не дольше 1 секунды
    connectTimeoutMS=1000,
    socketTimeoutMS=2000,
)

db = client["sfmshop_logs"]
logs_collection = db["logs"]


def init_logs_indexes():
    """Создать индексы. Вызывается при старте приложения, не при импорте."""
    try:
        logs_collection.create_index("timestamp", expireAfterSeconds=60 * 60 * 24 * 30)
    except PyMongoError:
        logger.warning("MongoDB недоступна, индексы логов не созданы")


def save_log(log_data):
    if "timestamp" not in log_data:
        log_data["timestamp"] = datetime.now()
    try:
        return logs_collection.insert_one(log_data).inserted_id
    except PyMongoError:
        # запасной вариант: обычный лог в консоль / файл
        logger.warning("MongoDB недоступна, лог: %s", log_data)
        return None

def get_logs_by_status_code(min_status, max_status):
    logs = logs_collection.find({
        "status_code": {"$gte": min_status, "$lt": max_status}
    })
    return list(logs)

def get_logs_by_date_range(start_date, end_date):
    logs = logs_collection.find({
        "timestamp": {"$gte": start_date, "$lt": end_date}
    })
    return list(logs)

def get_logs_by_ip(ip):
    logs = logs_collection.find({"ip": ip})
    return list(logs)

def get_logs_statistics():
    type_status = logs_collection.aggregate([
        {"$group": {"_id": "$type", "count": {"$sum": 1}}}
    ])
    status_stats = logs_collection.aggregate([
        {"$group": {"_id": "$status_code", "count": {"$sum": 1}}}
    ])

    return {
        "by_type": list(type_status),
        "by_status": list(status_stats),
        "total": logs_collection.count_documents({})
    }


# Тестирование
if __name__ == "__main__":

    logs_collection.insert_one({"type": "error", "message": "Сбой оплаты заказа", "status_code": 500, "timestamp": datetime.now()})
    logs_collection.insert_one({"type": "access", "endpoint": "/api/products", "status_code": 200, "timestamp": datetime.now()})
    logs_collection.insert_one({"type": "access", "endpoint": "/api/cart", "status_code": 404, "timestamp": datetime.now()})
    logs_collection.insert_one({"type": "error", "message": "Товар не найден", "status_code": 404})
    logs_collection.insert_one({"type": "access", "endpoint": "/api/orders", "status_code": 503})


    # Статистика
    stats = get_logs_statistics()
    print(f"Статистика: {stats}")
    
    # Поиск по статус-коду
    error_logs = get_logs_by_status_code(400, 500)
    print(f"Логов с ошибками: {len(error_logs)}")
    
    # Поиск по дате
    yesterday = datetime.now() - timedelta(days=1)
    today_logs = get_logs_by_date_range(yesterday, datetime.now())
    print(f"Логов за сегодня: {len(today_logs)}")