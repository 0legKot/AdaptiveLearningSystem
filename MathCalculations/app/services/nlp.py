from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import linear_kernel
from typing import List, Dict, Optional


def find_similar_question(failed_text: str, candidates: List[Dict]) -> Optional[Dict]:
    if not candidates:
        return None

    # Корпус: [Текст помилки, Кандидат 1, Кандидат 2...]
    candidate_texts = [c['text'] for c in candidates]
    corpus = [failed_text] + candidate_texts

    # Векторизація
    tfidf = TfidfVectorizer(stop_words='english')
    try:
        tfidf_matrix = tfidf.fit_transform(corpus)
    except ValueError:
        return None  # Якщо пустий текст

    # Косинусна схожість (Cosine Similarity)
    # Порівнюємо 1-й елемент (помилку) з усіма іншими
    cosine_sim = linear_kernel(tfidf_matrix[0:1], tfidf_matrix[1:]).flatten()

    if len(cosine_sim) == 0:
        return None

    # Знаходимо індекс найкращого співпадіння
    best_idx = cosine_sim.argmax()
    best_score = cosine_sim[best_idx]

    # Поріг схожості (щоб не радити будь-що)
    if best_score < 0.1:
        return None

    return {
        "recommended_id": candidates[best_idx]['id'],
        "similarity": float(best_score)
    }