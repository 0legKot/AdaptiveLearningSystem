from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from typing import Dict


class GradePredictor:
    def __init__(self):
        # 1. Синтетичні дані для тренування (Baseline)
        # X = [AvgTime (ms), FocusLost, CurrentScore %]
        # Y = FinalScore
        self.X_train = np.array([
            [15000, 0, 90], [5000, 5, 40], [30000, 0, 80],
            [10000, 2, 70], [45000, 0, 85], [12000, 3, 60],
            [8000, 10, 20], [25000, 1, 95]
        ])
        self.y_train = np.array([95, 40, 85, 70, 88, 75, 25, 98])

        # 2. Ініціалізація та тренування моделей
        self.lr_model = LinearRegression()
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)

        self._train()

    def _train(self):
        print("Training Prediction Models...")
        self.lr_model.fit(self.X_train, self.y_train)
        self.rf_model.fit(self.X_train, self.y_train)

    def predict_final_grade(self, avg_time: float, current_score: float, focus_lost: int) -> int:
        # Використовуємо вже навчену Linear Regression
        # Модель приймає [AvgTime, FocusLost, CurrentScore] (змінив порядок для логіки)
        prediction = self.lr_model.predict([[avg_time, focus_lost, current_score]])[0]
        return int(max(0, min(100, prediction)))

    def get_feature_importance(self) -> Dict[str, float]:
        # Використовуємо Random Forest для пояснення
        importances = self.rf_model.feature_importances_
        return {
            "TimeSpent": round(importances[0], 2),
            "FocusLost": round(importances[1], 2),
            "CurrentScore": round(importances[2], 2)
        }


# Створюємо екземпляр (Singleton)
predictor = GradePredictor()