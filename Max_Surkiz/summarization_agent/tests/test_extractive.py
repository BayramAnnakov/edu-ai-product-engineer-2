import pytest
from summarization_agent.src.pipelines.extractive import extractive_summary
import nltk
import sys, os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..')))

nltk.download('punkt', quiet=True)

def test_extractive_summary_sentence_count():
    text = "Sentence one. Sentence two. Sentence three. Sentence four. Sentence five."
    summary = extractive_summary(text, ratio=0.4, seed=42)
    sentences = nltk.sent_tokenize(summary)
    assert len(sentences) == 2  # 40% от 5 = 2 