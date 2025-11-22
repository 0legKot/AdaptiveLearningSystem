from fastapi import FastAPI
from app.schemas import *
from app.services import adaptive, anticheat, mining, nlp, prediction
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

app = FastAPI(title="Adaptive Learning ML Core")


# 1. Adaptive Testing (BKT)
@app.post("/adaptive/predict-knowledge")
def endpoint_bkt(data: BktRequest):
    res = adaptive.calculate_bkt(data.p_known, data.is_correct)
    return {"new_theta": round(res, 4)}


# 2. Anti-Cheat (Isolation Forest)
@app.post("/security/detect-cheating")
def endpoint_cheating(data: CheatingRequest):
    is_suspicious = anticheat.detect_anomaly(data.time_spent_ms, data.focus_lost_count)
    return {"is_suspicious": is_suspicious}


# 3. NLP Recommendations
@app.post("/nlp/similar-question")
def endpoint_nlp(data: NlpRequest):
    # Перетворюємо Pydantic models в dicts
    candidates = [c.dict() for c in data.candidate_questions]
    result = nlp.find_similar_question(data.failed_question_text, candidates)
    return result if result else {"recommended_id": None}


# 4. Data Mining (Association Rules)
@app.post("/mining/rules")
def endpoint_mining(history: List[HistoryItem]):
    # Convert to list of dicts
    data = [h.dict() for h in history]
    return mining.mine_rules(data)


# 5. Predictive Analytics
@app.post("/prediction/final-score")
def endpoint_prediction(data: PredictionData):
    score = prediction.predict_final_grade(
        data.avg_time_per_question,
        data.current_score_percent,
        data.focus_lost_count
    )
    return {"predicted_score": score}


# 6. Clustering (Залишили тут, бо простий)
@app.post("/analytics/cluster-students")
def endpoint_clustering(students: List[ClusteringRequest]):
    if not students: return []
    df = pd.DataFrame([s.dict() for s in students])
    scaler = StandardScaler()
    scaled = scaler.fit_transform(df[['avg_time', 'avg_score']])
    kmeans = KMeans(n_clusters=3, random_state=42, n_init=10).fit(scaled)

    results = []
    for i, row in df.iterrows():
        results.append({"student_id": row['student_id'], "cluster_id": int(kmeans.labels_[i])})
    return results


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="127.0.0.1", port=8000)