from pydantic import BaseModel, Field
from datetime import datetime
from typing import Any, Optional
from .constants import Phase


class Answer(BaseModel):
    persona_id: str
    question: str
    response: str
    timestamp: datetime = Field(default_factory=lambda: datetime.now())
    phase: Phase


class Analysis(BaseModel):
    persona_id: str
    question: str
    themes: list[str] = Field(default_factory=list)
    sentiment: float = Field(ge=-1, le=1)
    hypotheses_hit: list[str] = Field(default_factory=list)
    key_quotes: list[str] = Field(default_factory=list)
    confidence: float = Field(default=0.5, ge=0, le=1)


class ClusterReport(BaseModel):
    themes: list[dict[str, list[str]]] = Field(default_factory=list)
    conflicts: list[str] = Field(default_factory=list)
    gaps: list[str] = Field(default_factory=list)
    consensus_points: list[str] = Field(default_factory=list)


class FollowUp(BaseModel):
    persona_id: str
    question: str
    rationale: str
    priority: float = Field(default=0.5, ge=0, le=1)


class BoardState(BaseModel):
    phase: Phase = Phase.WARMUP
    question_index: int = 0
    answers: list[Answer] = Field(default_factory=list)
    analyses: list[Analysis] = Field(default_factory=list)
    hypothesis_coverage: dict[str, float] = Field(default_factory=dict)
    cluster_reports: list[ClusterReport] = Field(default_factory=list)
    follow_ups: list[FollowUp] = Field(default_factory=list)
    
    def coverage_percentage(self) -> float:
        if not self.hypothesis_coverage:
            return 0.0
        return sum(self.hypothesis_coverage.values()) / len(self.hypothesis_coverage)
    
    def add_answer(self, answer: Answer) -> None:
        self.answers.append(answer)
    
    def add_analysis(self, analysis: Analysis) -> None:
        self.analyses.append(analysis)
        for hypothesis in analysis.hypotheses_hit:
            current = self.hypothesis_coverage.get(hypothesis, 0.0)
            self.hypothesis_coverage[hypothesis] = min(1.0, current + 0.3)
    
    def get_phase_answers(self, phase: Phase) -> list[Answer]:
        return [a for a in self.answers if a.phase == phase]
    
    def get_persona_answers(self, persona_id: str) -> list[Answer]:
        return [a for a in self.answers if a.persona_id == persona_id]


# Agent Output Models - Used for structured responses from agents

class ResponseAnalysis(BaseModel):
    """Structured output for response analysis"""
    
    model_config = {"extra": "forbid"}
    
    themes: list[str] = Field(description="Key themes identified in the response")
    sentiment: float = Field(description="Sentiment score from -1 to 1", ge=-1, le=1)
    hypotheses_hit: list[str] = Field(description="Hypothesis IDs addressed in response")
    key_quotes: list[str] = Field(description="Important quotes from the response")
    confidence: float = Field(description="Confidence in analysis from 0 to 1", ge=0, le=1)


class ThemeCluster(BaseModel):
    """Structured output for theme clustering"""
    
    model_config = {"extra": "forbid"}
    
    theme_name: str = Field(description="Name of the theme cluster")
    personas_mentioned: list[str] = Field(description="Personas who mentioned this theme")
    frequency: int = Field(description="Number of mentions")
    representative_quotes: list[str] = Field(description="Representative quotes for this theme")


class BiasCheck(BaseModel):
    """Structured output for bias detection"""
    
    model_config = {"extra": "forbid"}
    
    has_bias: bool = Field(default=False, description="Whether bias was detected")
    bias_type: Optional[str] = Field(default=None, description="Type of bias if detected")
    severity: Optional[str] = Field(default=None, description="Severity: low, medium, high")
    recommendation: Optional[str] = Field(default=None, description="Recommendation to address bias")


class FollowUpQuestion(BaseModel):
    """Structured output for follow-up questions"""
    
    model_config = {"extra": "forbid"}
    
    is_needed: bool = Field(default=False, description="Whether a follow-up question is needed")
    question: str = Field(default="none", description="The follow-up question, or 'none' if no follow-up needed")
    rationale: str = Field(default="No follow-up needed", description="Why this question is important, or reason for no follow-up")
    target_hypothesis: Optional[str] = Field(default=None, description="Hypothesis this question targets")

class PersonaDriftCheck(BaseModel):
    """Structured output for persona drift check"""
    
    model_config = {"extra": "forbid"}
    
    is_drift_detected: bool = Field(default=False, description="Whether persona drift was detected")
    explanation: Optional[str] = Field(default=None, description="Details of the drift if detected")
    recommendation: Optional[str] = Field(default=None, description="Recommendation to address persona drift")

class SessionReport(BaseModel):
    start_time: datetime
    end_time: datetime
    product_name: str
    hypotheses_tested: list[str]
    coverage_achieved: float
    key_insights: list[str]
    recommendations: list[str]
    raw_data: dict[str, Any]
    
    def to_markdown(self) -> str:
        duration = (self.end_time - self.start_time).total_seconds() / 60
        return f"""# Virtual Board Session Report

**Product**: {self.product_name}
**Duration**: {duration:.0f} minutes
**Coverage**: {self.coverage_achieved:.0%}

## Hypotheses Tested
{chr(10).join(f"- {h}" for h in self.hypotheses_tested)}

## Key Insights
{chr(10).join(f"- {i}" for i in self.key_insights)}

## Recommendations
{chr(10).join(f"- {r}" for r in self.recommendations)}
"""