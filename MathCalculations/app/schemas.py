from pydantic import BaseModel
from typing import List, Optional, Dict

class BktRequest(BaseModel):
    p_known: float
    is_correct: bool

class CheatingRequest(BaseModel):
    time_spent_ms: int
    focus_lost_count: int

class ClusteringRequest(BaseModel):
    student_id: str
    avg_time: float
    avg_score: float

class QuestionCandidate(BaseModel):
    id: str
    text: str

class NlpRequest(BaseModel):
    failed_question_text: str
    candidate_questions: List[QuestionCandidate]

class HistoryItem(BaseModel):
    student_id: str
    failed_topics: List[str]

class PredictionData(BaseModel):
    avg_time_per_question: float
    current_score_percent: float
    focus_lost_count: int

# --- НОВЕ ДЛЯ ЯКОСТІ ПИТАНЬ ---
class QuestionStatsRequest(BaseModel):
    question_id: str
    difficulty_declared: float
    avg_time_spent: float
    error_rate: float