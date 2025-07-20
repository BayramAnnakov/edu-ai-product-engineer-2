from typing import List, Dict, Any
import re
import numpy as np
from sklearn.cluster import KMeans
from sentence_transformers import SentenceTransformer

# Initialize the model once and reuse it
model = SentenceTransformer("sentence-transformers/all-MiniLM-L6-v2")

def theme_extract(texts: List[str], n_clusters: int = 3) -> List[Dict[str, Any]]:
    """Extracts themes from texts using embeddings and k-means clustering."""
    if not texts or len(texts) < n_clusters:
        return []

    embeddings = model.encode(texts, show_progress_bar=False)

    # Use n_init='auto' to avoid FutureWarning
    kmeans = KMeans(n_clusters=n_clusters, random_state=42, n_init='auto')
    kmeans.fit(embeddings)

    themes = []
    theme_names = ["Praise", "Pain", "Request"]  # As per PRD

    for i in range(n_clusters):
        cluster_indices = np.where(kmeans.labels_ == i)[0]
        if len(cluster_indices) == 0:
            continue

        cluster_embeddings = embeddings[cluster_indices]
        centroid = kmeans.cluster_centers_[i]
        distances = np.linalg.norm(cluster_embeddings - centroid, axis=1)
        
        closest_sentence_index_in_cluster = np.argmin(distances)
        original_index = cluster_indices[closest_sentence_index_in_cluster]
        
        theme_name = theme_names[i] if i < len(theme_names) else f"Theme {i + 1}"

        themes.append({
            "name": theme_name,
            "quote": texts[original_index]
        })

    return themes


THEME_KEYWORDS = {
    "Praise": ['удобно', 'вкусно', 'быстро', 'спасибо', 'отлично', 'супер', 'нравится', 'хорошо', 'класс', 'молодцы', 'рекомендую', 'плюс', 'лучший', 'понятно', 'просто', 'качественно', 'прекрасно', 'доволен', 'рады'],
    "Pain": ['проблема', 'не работает', 'ужасно', 'плохо', 'не могу', 'ошибка', 'баг', 'дорого', 'минус', 'глючит', 'долго', 'неудобно', 'виснет', 'вылетает', 'жалоба', 'сложно', 'невозможно', 'тормозит', 'зависает'],
    "Request": ['почините', 'добавьте', 'верните', 'хотелось бы', 'сделайте', 'улучшите', 'прошу', 'нужно', 'надо', 'пожалуйста', 'предлагаю', 'расширьте', 'хочется']
}

def calculate_theme_distribution_by_keywords(text: str) -> Dict[str, float]:
    """Calculates the percentage distribution of themes based on keyword counts in sentences."""
    sentences = text.split('.')
    if not sentences: return {}

    theme_counts = {"Praise": 0, "Pain": 0, "Request": 0, "Neutral": 0}

    for sentence in sentences:
        if not sentence.strip():
            continue

        scores = {theme: 0 for theme in THEME_KEYWORDS}
        for theme, kws in THEME_KEYWORDS.items():
            for kw in kws:
                if kw in sentence.lower():
                    scores[theme] += 1
        
        max_score = 0
        best_theme = "Neutral"
        for theme, score in scores.items():
            if score > max_score:
                max_score = score
                best_theme = theme
        
        if max_score > 0:
            theme_counts[best_theme] += 1
        else:
            theme_counts["Neutral"] += 1
            
    total_sentences = len(sentences)
    distribution = {theme: (count / total_sentences) * 100 for theme, count in theme_counts.items()}
    return distribution

def extract_themes_by_keywords(full_text: str) -> List[Dict[str, str]]:
    """Extracts themes by finding sentences with the highest count of keywords for each theme."""
    sentences = re.split(r'[.!?]', full_text)
    if not sentences:
        return []

    themes = []
    found_quotes = set()

    for theme_name, keywords in THEME_KEYWORDS.items():
        best_sentence = ""
        max_score = 0
        for sentence in sentences:
            # Simple scoring: count occurrences of keywords
            score = sum(1 for keyword in keywords if keyword in sentence.lower())
            if score > max_score and sentence not in found_quotes:
                max_score = score
                best_sentence = sentence.strip()
        
        if best_sentence:
            themes.append({"name": theme_name, "quote": best_sentence})
            found_quotes.add(best_sentence) # Ensure the same quote isn't used for multiple themes

    return themes
