from typing import List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.schemas import ClusteringRequest


def clustering(students: List[ClusteringRequest]):
    if not students: return []

    df = pd.DataFrame([s.dict() for s in students])

    # Нормалізація даних (Z-score)
    scaler = StandardScaler()
    # Перетворюємо в numpy array, щоб уникнути Warning про feature names
    X = scaler.fit_transform(df[['avg_time', 'avg_score']].values)

    # Тренуємо K-Means
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    internal_labels = kmeans.fit_predict(X)

    # --- SMART MAPPING (Визначаємо, хто є хто) ---
    # Отримуємо центри кластерів: [Time, Score]
    centers = kmeans.cluster_centers_

    # 1. Знаходимо Чітера: Це кластер з найменшим часом (найбільш від'ємний Z-score по часу)
    cheater_cluster_idx = np.argmin(centers[:, 0])

    # 2. Розбираємося з іншими двома
    remaining_indices = [i for i in range(3) if i != cheater_cluster_idx]

    # Серед тих, хто залишився: у кого вищий бал - той Сеньйор
    idx_a, idx_b = remaining_indices
    if centers[idx_a, 1] > centers[idx_b, 1]:
        senior_cluster_idx = idx_a
        junior_cluster_idx = idx_b
    else:
        senior_cluster_idx = idx_b
        junior_cluster_idx = idx_a

    # Створюємо мапу перекладу: Внутрішній ID -> Наш Бізнес ID
    # 0 = Cheater/Risk, 1 = Junior/Avg, 2 = Senior/Top
    label_map = {
        cheater_cluster_idx: 0,
        junior_cluster_idx: 1,
        senior_cluster_idx: 2
    }

    results = []
    for i, row in df.iterrows():
        internal_label = internal_labels[i]
        business_label = label_map[internal_label]

        results.append({
            "student_id": row['student_id'],
            "cluster_id": business_label
        })

    return results