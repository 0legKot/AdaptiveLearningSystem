from fastapi import FastAPI
from pydantic import BaseModel
from typing import List, Optional
import numpy as np
import pandas as pd
from sklearn.ensemble import IsolationForest
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

app = FastAPI()


# --- MODELS ---

class BktRequest(BaseModel):
    p_known: float  # Попередня ймовірність знання (Theta)
    is_correct: bool


class CheatingRequest(BaseModel):
    time_spent_ms: int
    focus_lost_count: int


class ClusteringRequest(BaseModel):
    student_id: str
    avg_time: float
    avg_score: float


# --- LOGIC ---

# 1. ADAPTIVITY (Bayesian Knowledge Tracing)
@app.post("/predict-knowledge")
def calculate_bkt(data: BktRequest):
    # Стандартні коефіцієнти BKT (можна винести в конфіг)
    p_guess = 0.15
    p_slip = 0.10
    p_learn = 0.15

    prior = data.p_known

    if data.is_correct:
        posterior = (prior * (1 - p_slip)) / (prior * (1 - p_slip) + (1 - prior) * p_guess)
    else:
        posterior = (prior * p_slip) / (prior * p_slip + (1 - prior) * (1 - p_guess))

    p_next = posterior + (1 - posterior) * p_learn

    return {"new_theta": round(p_next, 4)}


# 2. ANTI-CHEAT (Isolation Forest)
# Ми симулюємо навчання на нормальних даних і перевіряємо поточний запит
@app.post("/detect-cheating")
def detect_cheating(current: CheatingRequest):
    # Генеруємо "нормальний" датасет для baseline (так як реального мало)
    # Норма: 10-60 сек, 0-2 втрати фокусу
    rng = np.random.RandomState(42)
    X_train = np.r_[
        rng.uniform(low=10000, high=60000, size=(100, 1)),  # Time
        rng.randint(low=0, high=3, size=(100, 1))  # Focus
    ].reshape(100, 2, order='F')

    clf = IsolationForest(contamination=0.1, random_state=42)
    clf.fit(X_train)

    # Перевіряємо поточного студента
    X_test = [[current.time_spent_ms, current.focus_lost_count]]
    pred = clf.predict(X_test)  # -1 = anomaly, 1 = normal

    is_cheater = pred[0] == -1

    # Додаткова жорстка евристика для демо
    if current.time_spent_ms < 3000 or current.focus_lost_count > 4:
        is_cheater = True

    return {"is_suspicious": bool(is_cheater)}


# 3. CLUSTERING (K-Means)
@app.post("/cluster-students")
def cluster_students(students: List[ClusteringRequest]):
    if not students:
        return []

    df = pd.DataFrame([s.dict() for s in students])
    features = df[['avg_time', 'avg_score']]

    scaler = StandardScaler()
    scaled_features = scaler.fit_transform(features)

    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    df['cluster'] = kmeans.fit_predict(scaled_features)

    # Мапимо кластери на зрозумілі назви (евристично по центроїдах)
    # Це треба, щоб на графіку були підписи типу "High Performers"

    result = []
    for idx, row in df.iterrows():
        result.append({
            "student_id": row['student_id'],
            "cluster_id": int(row['cluster'])
        })

    return result


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)