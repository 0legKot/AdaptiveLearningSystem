import pandas as pd
from sklearn.cluster import KMeans
from typing import List, Dict


class QuestionQualityAnalyzer:
    def analyze(self, questions: List[Dict]) -> List[Dict]:
        if len(questions) < 3:
            return []

        df = pd.DataFrame(questions)
        # Features: Declared Difficulty vs Real Error Rate vs Avg Time
        X = df[['difficulty_declared', 'error_rate', 'avg_time_spent']]

        # K-Means train on the fly (тут це ок, бо ми аналізуємо конкретний батч)
        kmeans = KMeans(n_clusters=3, random_state=42, n_init=10)
        df['cluster'] = kmeans.fit_predict(X)

        results = []
        for _, row in df.iterrows():
            status = "Normal"
            # Логіка виявлення аномалій на основі кластера та значень
            if row['difficulty_declared'] < -0.5 and row['error_rate'] > 0.6:
                status = "Anomaly: Harder than declared"
            elif row['difficulty_declared'] > 0.5 and row['error_rate'] < 0.2:
                status = "Anomaly: Easier than declared"
            elif row['error_rate'] > 0.9:
                status = "Broken/Ambiguous"

            results.append({
                "question_id": row['question_id'],
                "cluster_name": status
            })

        return results


analyzer = QuestionQualityAnalyzer()