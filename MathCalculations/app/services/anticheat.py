import numpy as np
from sklearn.ensemble import IsolationForest


class AnomalyDetector:
    def __init__(self):
        self.model = IsolationForest(contamination=0.1, random_state=42)
        self._train_baseline()

    def _train_baseline(self):
        print("Training Anti-Cheat Model...")
        rng = np.random.RandomState(42)
        x_train = np.r_[
            rng.uniform(low=10000, high=60000, size=(200, 1)),
            rng.randint(low=0, high=3, size=(200, 1))
        ].reshape(200, 2, order='F')

        self.model.fit(x_train)

    def detect(self, time_ms: int, focus_lost: int) -> bool:
        pred = self.model.predict([[time_ms, focus_lost]])

        is_ml_anomaly = (pred[0] == -1)

        is_heuristic_anomaly = (time_ms < 3000) or (focus_lost > 4)

        return bool(is_ml_anomaly or is_heuristic_anomaly)


# Singleton
detector = AnomalyDetector()