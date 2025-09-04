from __future__ import annotations

"""Metrics computation between summaries."""

from rouge_score import rouge_scorer
from nltk.translate.bleu_score import sentence_bleu, SmoothingFunction
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from shared_utils.data_models import Metrics, ExtractiveSummary, AbstractiveSummary
from shared_utils.logging import get_logger

_LOGGER = get_logger(__name__)


class MetricsComputer:  # noqa: D101
    def __call__(
        self, extractive: ExtractiveSummary, abstractive: AbstractiveSummary
    ) -> Metrics:  # noqa: D401
        rouge = self._compute_rouge(extractive, abstractive)
        bleu = self._compute_bleu(extractive, abstractive)
        semantic_similarity = self._compute_semantic_similarity(extractive, abstractive)
        return Metrics(
            rouge_1=rouge["rouge1"].fmeasure,
            rouge_l=rouge["rougeL"].fmeasure,
            bleu=bleu,
            semantic_similarity=semantic_similarity,
        )

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    @staticmethod
    def _compute_rouge(extractive: ExtractiveSummary, abstractive: AbstractiveSummary):
        scorer = rouge_scorer.RougeScorer(["rouge1", "rougeL"], use_stemmer=True)
        return scorer.score(" ".join(extractive.sentences), abstractive.summary)

    @staticmethod
    def _compute_bleu(extractive: ExtractiveSummary, abstractive: AbstractiveSummary) -> float:
        reference = [token for sent in extractive.sentences for token in sent.split()]
        hypothesis = abstractive.summary.split()
        smooth = SmoothingFunction().method1
        return sentence_bleu([reference], hypothesis, smoothing_function=smooth)

    @staticmethod
    def _compute_semantic_similarity(
        extractive: ExtractiveSummary, abstractive: AbstractiveSummary
    ) -> float:
        vect = TfidfVectorizer().fit_transform(
            [" ".join(extractive.sentences), abstractive.summary]
        )
        sim = cosine_similarity(vect[0:1], vect[1:2])[0][0]
        return sim
