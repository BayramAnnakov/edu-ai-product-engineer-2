"""
Bug Submission Assessment schemas for LLM-as-a-judge
"""
from typing import List
from pydantic import BaseModel, Field


class BugSubmissionAssessment(BaseModel):
    """Structured output for bug submission assessment"""
    
    needs_approval: bool = Field(description="Whether this bug report needs human approval")
    confidence_score: float = Field(ge=0.0, le=1.0, description="Confidence in the assessment (0-1)")
    
    # Uncertainty indicators
    duplicate_uncertainty: bool = Field(description="Whether there's uncertainty about duplicates")
    duplicate_similarity_score: float = Field(default=0.0, ge=0.0, le=100.0, description="Similarity score mentioned (0-100)")
    
    critical_priority: bool = Field(description="Whether this appears to be a critical/urgent bug")
    
    reasoning: str = Field(description="Clear explanation of why approval is/isn't needed")
    risk_level: str = Field(description="Risk level: LOW, MEDIUM, or HIGH")
    
    # Extracted information
    bug_summary: str = Field(description="Brief summary of the bug being reported")
    mentioned_keywords: List[str] = Field(default_factory=list, description="Key uncertainty indicators found")


def get_bug_submission_assessment_schema_formatted() -> str:
    """Get formatted schema for LLM prompts"""
    return BugSubmissionAssessment.model_json_schema()