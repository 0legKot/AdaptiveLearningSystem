import numpy as np
from sklearn.ensemble import IsolationForest


def detect_anomaly(time_ms: int, focus_lost: int) -> bool:
    # Синтетичне тренування "норми"
    rng = np.random.RandomState(42)
    X_train = np.r_[
        rng.uniform(low=10000, high=60000, size=(100, 1)),  # Normal time
        rng.randint(low=0, high=3, size=(100, 1))  # Normal focus
    ].reshape(100, 2, order='F')

    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(X_train)

    pred = clf.predict([[time_ms, focus_lost]])

    # Додаткова евристика для демо
    is_anomaly = (pred[0] == -1) or (time_ms < 3000) or (focus_lost > 4)
    return bool(is_anomaly)