# Файл scripts/lesson_58_framework_recommender.py
# Подбор веб-фреймворка под требования проекта SFMShop.

# Оценки фреймворков по критериям (0-5).
FRAMEWORKS = {
    "FastAPI": {"performance": 5, "ready_features": 2, "simplicity": 4, "async": 5},
    "Django": {"performance": 3, "ready_features": 5, "simplicity": 3, "async": 3},
    "Flask": {"performance": 3, "ready_features": 2, "simplicity": 5, "async": 2},
}


def recommend(weights):
    """Вернуть список (фреймворк, балл), отсортированный по убыванию балла.

    Балл = сумма по критериям: оценка_фреймворка * вес_критерия.
    При равенстве баллов фреймворки идут в алфавитном порядке.
    """
    scores = []
    for name in sorted(FRAMEWORKS):
        criteria = FRAMEWORKS[name]
        total = sum(criteria[k] * w for k, w in weights.items())
        scores.append((name, total))
    scores.sort(key=lambda pair: (-pair[1], pair[0]))
    return scores


def main():
    # Требования SFMShop: важна производительность и async, готовые фичи не нужны.
    weights = {"performance": 3, "ready_features": 1, "simplicity": 1, "async": 2}

    ranking = recommend(weights)
    print("Рейтинг фреймворков для SFMShop:")
    for place, (name, total) in enumerate(ranking, start=1):
        print(f"{place}. {name}: {total}")

    winner = ranking[0][0]
    print(f"Рекомендация: {winner}")


if __name__ == "__main__":
    main()