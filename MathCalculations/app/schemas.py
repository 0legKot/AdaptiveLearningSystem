from pydantic import BaseModel
from typing import List, Optional, Dict

# --- BKT ---
class BktRequest(BaseModel):
    p_known: float
    is_correct: bool

# --- Anti-Cheat ---
class CheatingRequest(BaseModel):
    time_spent_ms: int
    focus_lost_count: int

# --- Clustering ---
class ClusteringRequest(BaseModel):
    student_id: str
    avg_time: float
    avg_score: float

# --- NLP (Content-Based Recs) ---
class QuestionCandidate(BaseModel):
    id: str
    text: str

class NlpRequest(BaseModel):
    failed_question_text: str
    candidate_questions: List[QuestionCandidate]

# --- Mining (Association Rules) ---
class HistoryItem(BaseModel):
    student_id: str
    failed_topics: List[str]

# --- Prediction ---
class PredictionData(BaseModel):
    avg_time_per_question: float
    current_score_percent: float
    focus_lost_count: int