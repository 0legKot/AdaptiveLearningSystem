import pandas as pd
import numpy as np
from sklearn.cluster import KMeans
from typing import List, Dict


class QuestionQualityAnalyzer:
    def __init__(self):
        # 1. Визначаємо "Канонічні" центроїди для кластерів
        # Features: [Difficulty (-1.5 to 1.5), ErrorRate (0.0 to 1.0), Time (scaled 0.0-1.0)]

        # Ми створюємо навчальний датасет, який представляє нашу "картину світу"
        X_train = np.array([
            [-1.5, 0.1, 0.2],  # Cluster 0: Easy & Well known (Normal)
            [1.5, 0.6, 0.8],  # Cluster 1: Hard & Frequent errors (Normal)
            [0.0, 0.3, 0.5],  # Cluster 2: Medium (Normal)
            [-1.5, 0.95, 0.3]  # Cluster 3: Easy BUT High Error (ANOMALY/BROKEN)
        ])

        # Тренуємо модель із фіксованими центроїдами (init=X_train)
        # Це змушує K-Means запам'ятати саме ці зони
        self.kmeans = KMeans(n_clusters=4, init=X_train, n_init=1, max_iter=300, random_state=42)
        self.kmeans.fit(X_train)

        # Зберігаємо індекс кластера аномалій (той, де ErrorRate високий при низькій складності)
        # У нашому X_train це останній елемент (індекс 3)
        self.anomaly_cluster_idx = 3
        self.hard_cluster_idx = 1

    def analyze(self, questions: List[Dict]) -> List[Dict]:
        if not questions:
            return []

        df = pd.DataFrame(questions)

        df['time_scaled'] = df['avg_time_spent'] / 60000.0
        df['time_scaled'] = df['time_scaled'].clip(0, 1)

        # FIX: Додали .values, щоб прибрати UserWarning
        X = df[['difficulty_declared', 'error_rate', 'time_scaled']].values

        labels = self.kmeans.predict(X)

        results = []
        for i, label in enumerate(labels):
            row = df.iloc[i]

            if label == self.anomaly_cluster_idx:
                status = "Anomaly: High Error Rate on Easy Question"
            elif label == self.hard_cluster_idx:
                status = "Hard Question (Normal)"
            else:
                status = "Normal"

            results.append({
                "question_id": row['question_id'],
                "cluster_name": status
            })

        return results


analyzer = QuestionQualityAnalyzer()