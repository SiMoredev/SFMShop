# Файл scripts/lesson_56_rest_router.py
class ProductAPI:
    """Мини REST-роутер для товаров SFMShop (in-memory, без сервера)."""

    def __init__(self):
        self._products = {}
        self._next_id = 1

    def handle(self, method, path, body={}):
        """Вернуть (status_code, payload) для запроса (method, path)."""
        parts = [p for p in path.strip("/").split("/") if p]

        # Коллекция: /products
        if parts == ["products"]:
            if method == "GET":
                return (200, {"products": list(self._products.values())})
            if method == "POST":
                product = {"id": self._next_id, **body}
                self._products[self._next_id] = product
                self._next_id += 1
                return (201, product)
            return (405, {"error": "method not allowed"})

        # Элемент: /products/{id}
        if len(parts) == 2 and parts[0] == "products" and parts[1].isdigit():
            pid = int(parts[1])
            if pid not in self._products:
                return (404, {"error": f"Товар с ID {pid} не найден"})
            if method == "GET":
                return (200, self._products[pid])
            if method == "PUT":
                self._products[pid] = {"id": pid, **body}
                return (200, self._products[pid])
            if method == "DELETE":
                del self._products[pid]
                return (204, None)
            return (405, {"error": "method not allowed"})

        return (404, {"error": "ресурс не найден"})


api = ProductAPI()

requests = [
    ("POST", "/products", {"name": "Ноутбук", "price": 50000}),
    ("POST", "/products", {"name": "Мышь", "price": 1200}),
    ("GET", "/products", None),
    ("GET", "/products/1", None),
    ("PUT", "/products/2", {"name": "Мышь", "price": 990}),
    ("DELETE", "/products/1", None),
    ("GET", "/products/1", None),
    ("GET", "/products", None),
]

for method, path, body in requests:
    status, payload = api.handle(method, path, body)
    print(f"{method} {path} -> {status} {payload}")