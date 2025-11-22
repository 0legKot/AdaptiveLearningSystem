import numpy as np


def calculate_bkt(p_known: float, is_correct: bool, difficulty: float, total_options: int, topic: str) -> float:
    # 1. P(Guess) - Ймовірність вгадування
    p_guess = 1.0 / max(total_options, 2)

    # Коригування на легкість питання
    if difficulty < -1.0:
        p_guess += 0.15
    elif difficulty > 1.0:
        p_guess -= 0.05

    # 2. P(Slip) - Ймовірність помилки
    # Sigmoid: difficulty -3..3 -> 0..1
    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    # Чим складніше питання, тим вище шанс помилки навіть у знавця
    p_slip = 0.05 + (0.25 * sigmoid(difficulty))

    # 3. P(Learn) - Ймовірність переходу зі стану "Не знаю" в "Знаю"

    # Деякі теми вивчаються швидко (HTML), деякі повільно (C++, Algorithms)

    # Словник "Learning Inertia" (Інерція навчання)
    topic_learning_rates = {
        "HTML": 0.25,
        "CSS": 0.25,
        "SQL": 0.20,
        "Docker": 0.15,
        "C#": 0.15,
        "Algorithms": 0.10,
        "C++": 0.08,
        "Security": 0.12
    }

    base_learn = topic_learning_rates.get(topic, 0.15)

    difficulty_bonus = max(0.0, difficulty * 0.05)
    p_learn = base_learn + difficulty_bonus

    prior = p_known

    if is_correct:
        # P(L|Correct)
        likelihood = prior * (1 - p_slip)
        marginal = likelihood + (1 - prior) * p_guess
        posterior = likelihood / marginal
    else:
        # P(L|Incorrect)
        likelihood = prior * p_slip
        marginal = likelihood + (1 - prior) * (1 - p_guess)
        posterior = likelihood / marginal

    # Прогноз: P(Next) = Posterior + (Chance to learn just now)
    p_next = posterior + (1 - posterior) * p_learn

    # Clamping (щоб не вийти за межі 0-1)
    return round(max(0.01, min(0.99, p_next)), 4)