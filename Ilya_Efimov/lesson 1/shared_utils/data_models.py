from __future__ import annotations

"""Pydantic models used across the summarization pipeline."""

from typing import List, Optional, Dict

from pydantic import BaseModel, Field, constr, validator


class TextInput(BaseModel):
    """Schema for raw text input."""

    text: constr(min_length=1)  # noqa: F722


class ExtractiveSummary(BaseModel):
    """Schema for the output of the extractive summarizer."""

    sentences: List[str] = Field(..., min_items=1)


class AbstractiveSummary(BaseModel):
    """Schema for the output of the abstractive summarizer."""

    summary: constr(min_length=1)  # noqa: F722


class Metrics(BaseModel):
    """Quantitative comparison metrics between summaries."""

    rouge_1: float
    rouge_l: float
    bleu: float
    semantic_similarity: float

    @validator("rouge_1", "rouge_l", "bleu", "semantic_similarity")
    def _score_range(cls, v: float) -> float:  # noqa: N805
        if not 0 <= v <= 1:
            raise ValueError("Scores must be between 0 and 1.")
        return v


class ComparisonReport(BaseModel):
    """Final report schema combining summaries and metrics."""

    extractive: ExtractiveSummary
    abstractive: AbstractiveSummary
    metrics: Metrics
    qualitative_analysis: str
    recommendations: Optional[str] = None
