from sklearn.linear_model import LinearRegression
import numpy as np


def predict_final_grade(avg_time: float, current_score: float, focus_lost: int) -> int:
    # Синтетичне тренування (в реальності - дані з БД)
    # X = [Time, Focus] -> y = [FinalScore]
    X_train = [
        [15000, 0], [5000, 5], [30000, 0], [10000, 2], [20000, 1], [40000, 0]
    ]
    y_train = [95, 40, 85, 70, 88, 75]

    model = LinearRegression()
    model.fit(X_train, y_train)

    # Прогноз на основі поведінки
    behavior_score = model.predict([[avg_time, focus_lost]])[0]
    behavior_score = max(0, min(100, behavior_score))

    # Комбінована оцінка: 70% поточні знання, 30% прогноз поведінки
    final_prediction = (current_score * 0.7) + (behavior_score * 0.3)

    return int(final_prediction)