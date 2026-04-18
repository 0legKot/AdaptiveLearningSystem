import numpy as np


def calculate_bkt(p_known: float, is_correct: bool, difficulty: float, total_options: int, topic: str) -> float:
    p_guess = 1.0 / max(total_options, 2)

    if difficulty < -1.0:
        p_guess += 0.15
    elif difficulty > 1.0:
        p_guess -= 0.05

    def sigmoid(x):
        return 1 / (1 + np.exp(-x))

    p_slip = 0.05 + (0.25 * sigmoid(difficulty))

    # P(Learn) - Ймовірність переходу зі стану "Не знаю" в "Знаю"

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
        likelihood = prior * (1 - p_slip)
        marginal = likelihood + (1 - prior) * p_guess
        posterior = likelihood / marginal
    else:
        likelihood = prior * p_slip
        marginal = likelihood + (1 - prior) * (1 - p_guess)
        posterior = likelihood / marginal

    p_next = posterior + (1 - posterior) * p_learn

    return round(max(0.01, min(0.99, p_next)), 4)