import nltk
from sklearn.feature_extraction.text import TfidfVectorizer
import numpy as np
import random

nltk.download('punkt', quiet=True)


def extractive_summary(text: str, ratio: float = 0.2, seed: int = 42) -> str:
    random.seed(seed)
    np.random.seed(seed)
    # Разбиваем текст на предложения
    sentences = nltk.sent_tokenize(text)
    if len(sentences) == 0:
        return ""
    n_select = max(1, int(len(sentences) * ratio))
    # TF-IDF по предложениям
    vectorizer = TfidfVectorizer()
    tfidf_matrix = vectorizer.fit_transform(sentences)
    scores = tfidf_matrix.sum(axis=1).A1
    # Сортируем по убыванию веса
    ranked = np.argsort(scores)[::-1]
    selected = sorted(ranked[:n_select])  # Сохраняем порядок в тексте
    summary = " ".join([sentences[i] for i in selected])
    return summary

if __name__ == "__main__":
    with open("summarization_agent/data/raw/anthropic_multi_agent.txt", encoding="utf-8") as f:
        text = f.read()
    print(extractive_summary(text, ratio=0.2)) 