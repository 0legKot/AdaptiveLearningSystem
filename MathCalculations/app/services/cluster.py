from typing import List

import numpy as np
import pandas as pd
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler

from app.schemas import ClusteringRequest


def clustering(students: List[ClusteringRequest]):
    if not students: return []

    df = pd.DataFrame([s.dict() for s in students])

    scaler = StandardScaler()
    x = scaler.fit_transform(df[['avg_time', 'avg_score']].values)

    # Тренуємо K-Means
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
    internal_labels = kmeans.fit_predict(x)

    centers = kmeans.cluster_centers_

    cheater_cluster_idx = np.argmin(centers[:, 0])

    remaining_indices = [i for i in range(3) if i != cheater_cluster_idx]

    idx_a, idx_b = remaining_indices
    if centers[idx_a, 1] > centers[idx_b, 1]:
        senior_cluster_idx = idx_a
        junior_cluster_idx = idx_b
    else:
        senior_cluster_idx = idx_b
        junior_cluster_idx = idx_a

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