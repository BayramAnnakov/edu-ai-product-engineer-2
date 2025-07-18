"""Data models for summarization results."""

from dataclasses import dataclass
from typing import Dict, Any, Optional


@dataclass
class SummaryResult:
    """Structure for storing summary results."""
    summary_type: str
    text: str
    word_count: int
    sentence_count: int
    processing_time: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert summary result to dictionary."""
        return {
            'summary_type': self.summary_type,
            'text': self.text,
            'word_count': self.word_count,
            'sentence_count': self.sentence_count,
            'processing_time': self.processing_time
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SummaryResult':
        """Create summary result from dictionary."""
        return cls(
            summary_type=data.get('summary_type', ''),
            text=data.get('text', ''),
            word_count=data.get('word_count', 0),
            sentence_count=data.get('sentence_count', 0),
            processing_time=data.get('processing_time', 0.0)
        )


@dataclass
class ComparisonMetrics:
    """Metrics for comparing summaries."""
    content_overlap: float
    length_ratio: float
    readability_score: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary."""
        return {
            'content_overlap': self.content_overlap,
            'length_ratio': self.length_ratio,
            'readability_score': self.readability_score
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComparisonMetrics':
        """Create metrics from dictionary."""
        return cls(
            content_overlap=data.get('content_overlap', 0.0),
            length_ratio=data.get('length_ratio', 0.0),
            readability_score=data.get('readability_score', 0.0)
        )


@dataclass
class EvaluationReport:
    """Evaluation report from GPT analysis."""
    analysis: Dict[str, Any]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert evaluation to dictionary."""
        return {
            'analysis': self.analysis
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EvaluationReport':
        """Create evaluation from dictionary."""
        return cls(analysis=data.get('analysis', {}))
    
    def get_preferred_summary(self) -> Optional[str]:
        """Get preferred summary type."""
        return self.analysis.get('preferred_summary')
    
    def get_reasoning(self) -> str:
        """Get evaluation reasoning."""
        return self.analysis.get('reasoning', '')


@dataclass
class ComparisonResult:
    """Complete comparison result structure."""
    extractive_summary: SummaryResult
    abstractive_summary: SummaryResult
    comparison_metrics: ComparisonMetrics
    evaluation_report: EvaluationReport
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert comparison result to dictionary."""
        return {
            'extractive_summary': self.extractive_summary.to_dict(),
            'abstractive_summary': self.abstractive_summary.to_dict(),
            'comparison_metrics': self.comparison_metrics.to_dict(),
            'evaluation_report': self.evaluation_report.to_dict()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ComparisonResult':
        """Create comparison result from dictionary."""
        return cls(
            extractive_summary=SummaryResult.from_dict(data.get('extractive_summary', {})),
            abstractive_summary=SummaryResult.from_dict(data.get('abstractive_summary', {})),
            comparison_metrics=ComparisonMetrics.from_dict(data.get('comparison_metrics', {})),
            evaluation_report=EvaluationReport.from_dict(data.get('evaluation_report', {}))
        )