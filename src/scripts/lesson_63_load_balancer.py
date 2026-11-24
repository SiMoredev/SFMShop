# Файл scripts/lesson_63_load_balancer.py
class LoadBalancer:
    """Балансировщик нагрузки по алгоритму Least Connections."""

    def __init__(self, servers):
        self._connections = {name: 0 for name in servers}
        self._order = list(servers)

    def route(self) -> str:
        """Выбрать сервер с минимумом соединений и занять слот."""
        best = min(self._order, key=lambda name: self._connections[name])
        self._connections[best] +=1
        return best

    def release(self, server: str) -> None:
        """Соединение завершено — освободить слот."""
        if self._connections.get(server, 0) > 0:
            self._connections[server] -= 1

    def stats(self) -> dict:
        """Текущее число активных соединений по серверам."""
        return dict(self._connections)


if __name__ == "__main__":
    lb = LoadBalancer(["api1", "api2", "api3"])
    routed = [lb.route() for _ in range(5)]
    print("Маршрутизация 5 запросов:", routed)
    print("Активные соединения:", lb.stats())
    lb.release("api1")
    lb.release("api1")
    print("После release api1 x2:", lb.stats())
    nxt = lb.route()
    print("Следующий запрос ушёл на:", nxt)
    print("Итоговые соединения:", lb.stats())