from __future__ import annotations

"""Deterministic extractive summarizer using a TextRank-like algorithm."""

import nltk
from nltk.tokenize import sent_tokenize
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from shared_utils.config import auto_env_settings as settings
from shared_utils.data_models import ExtractiveSummary, TextInput
from shared_utils.logging import get_logger

# Ensure NLTK assets are downloaded (sent_tokenize requires punkt)
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:  # pragma: no cover
    nltk.download("punkt")

_LOGGER = get_logger(__name__)


class ExtractiveSummarizer:  # noqa: D101
    def __init__(self, max_sentences: int | None = None) -> None:
        self.max_sentences = max_sentences or settings.extraction_max_sentences

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------
    def __call__(self, text_input: TextInput) -> ExtractiveSummary:  # noqa: D401
        """Return top-N sentences as extractive summary."""
        try:
            sentences = sent_tokenize(text_input.text)
        except LookupError:
            _LOGGER.warning("NLTK punkt not available; using regex sentence splitter.")
            sentences = self._simple_split(text_input.text)

        if len(sentences) <= self.max_sentences:
            _LOGGER.debug("Input has %d sentences ≤ max; returning all.", len(sentences))
            return ExtractiveSummary(sentences=sentences)

        scores = self._rank_sentences(sentences)
        top_indices = np.argsort(scores)[-self.max_sentences :][::-1]
        summary_sentences = [sentences[i] for i in sorted(top_indices)]
        return ExtractiveSummary(sentences=summary_sentences)

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _simple_split(text: str) -> list[str]:
        """Basic sentence splitter using regex when NLTK data unavailable."""
        import re

        candidates = re.split(r"(?<=[.!?])\s+", text.strip())
        return [s for s in candidates if s]

    def _rank_sentences(self, sentences: list[str]) -> np.ndarray:  # noqa: D401
        vectorizer = TfidfVectorizer().fit_transform(sentences)
        similarity_matrix = cosine_similarity(vectorizer)

        # Graph-based ranking (simplified TextRank via power method)
        scores = np.ones(len(sentences)) / len(sentences)
        damping = 0.85
        for _ in range(50):
            scores = (1 - damping) + damping * similarity_matrix.dot(scores)
        _LOGGER.debug("Computed sentence scores: %s", scores)
        return scores
