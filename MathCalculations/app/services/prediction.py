from sklearn.linear_model import LinearRegression
from sklearn.ensemble import RandomForestRegressor
import numpy as np
from typing import Dict


class GradePredictor:
    def __init__(self):
        self.X_train = np.array([
            [15000, 0, 90], [5000, 5, 40], [30000, 0, 80],
            [10000, 2, 70], [45000, 0, 85], [12000, 3, 60],
            [8000, 10, 20], [25000, 1, 95]
        ])
        self.y_train = np.array([95, 40, 85, 70, 88, 75, 25, 98])

        self.lr_model = LinearRegression()
        self.rf_model = RandomForestRegressor(n_estimators=100, random_state=42)

        self._train()

    def _train(self):
        self.lr_model.fit(self.X_train, self.y_train)
        self.rf_model.fit(self.X_train, self.y_train)

    def predict_final_grade(self, avg_time: float, current_score: float, focus_lost: int) -> int:
        prediction = self.lr_model.predict([[avg_time, focus_lost, current_score]])[0]
        return int(max(0, min(100, prediction)))

    def explain_prediction(self, avg_time: float, current_score: float, focus_lost: int) -> Dict[str, float]:
        # Глобальна важливість (0.0 - 1.0)
        global_imp = self.rf_model.feature_importances_

        # Нормалізація даних студента (0.0 - 1.0) відносно "максимумів"
        # Time: 60000ms max, Focus: 10 max, Score: 100 max
        norm_time = min(1.0, avg_time / 60000.0)
        norm_focus = min(1.0, focus_lost / 10.0)
        norm_score = min(1.0, current_score / 100.0)

        # Персоналізований вплив
        # [0]=Time, [1]=Focus, [2]=Score (порядок як у X_train)
        impact_time = global_imp[0] * norm_time
        impact_focus = global_imp[1] * norm_focus
        impact_score = global_imp[2] * norm_score  # Тут навпаки: високий бал = позитив

        # Нормалізуємо, щоб сума була 1 (або 100%) для графіка
        total = impact_time + impact_focus + impact_score + 0.001

        return {
            "TimeSpent": round(impact_time / total, 2),
            "FocusLost": round(impact_focus / total, 2),
            "CurrentScore": round(impact_score / total, 2)
        }


predictor = GradePredictor()