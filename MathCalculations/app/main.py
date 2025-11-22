from fastapi import FastAPI
from app.schemas import *
from app.services.adaptive import calculate_bkt
from app.services.anticheat import detector
from app.services.mining import mine_rules
from app.services.nlp import find_similar_question
from app.services.prediction import predictor
from app.services.quality_analysis import analyzer as quality_analyzer
from sklearn.cluster import KMeans
from sklearn.preprocessing import StandardScaler
import pandas as pd

app = FastAPI(title="Adaptive Learning ML Core")


@app.on_event("startup")
async def startup_event():
    print("ML Services are warm and ready.")


# 1. BKT (Simple function is fine)
@app.post("/adaptive/predict-knowledge")
def endpoint_bkt(data: BktRequest):
    res = calculate_bkt(data.p_known, data.is_correct)
    return {"new_theta": round(res, 4)}


# 2. Anti-Cheat (Uses Pre-trained Isolation Forest)
@app.post("/security/detect-cheating")
def endpoint_cheating(data: CheatingRequest):
    is_suspicious = detector.detect(data.time_spent_ms, data.focus_lost_count)
    return {"is_suspicious": is_suspicious}


# 3. NLP
@app.post("/nlp/similar-question")
def endpoint_nlp(data: NlpRequest):
    candidates = [c.dict() for c in data.candidate_questions]
    result = find_similar_question(data.failed_question_text, candidates)
    return result if result else {"recommended_id": None}


# 4. Mining
@app.post("/mining/rules")
def endpoint_mining(history: List[HistoryItem]):
    data = [h.dict() for h in history]
    return mine_rules(data)


# 5. Prediction Score (Uses Pre-trained Linear Regression)
@app.post("/prediction/final-score")
def endpoint_prediction(data: PredictionData):
    score = predictor.predict_final_grade(
        data.avg_time_per_question,
        data.current_score_percent,
        data.focus_lost_count
    )
    return {"predicted_score": score}


# 6. Feature Importance (NEW: Random Forest Analysis)
@app.get("/prediction/factors-importance")
def endpoint_factors():
    return predictor.get_feature_importance()


# 7. Question Quality (NEW: K-Means for Questions)
@app.post("/analytics/analyze-questions")
def endpoint_question_quality(questions: List[QuestionStatsRequest]):
    data = [q.dict() for q in questions]
    return quality_analyzer.analyze(data)


# 8. Student Clustering
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