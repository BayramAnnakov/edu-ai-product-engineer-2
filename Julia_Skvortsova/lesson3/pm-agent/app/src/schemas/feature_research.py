"""
Pydantic schemas for feature research and competitor analysis
"""
from typing import List, Optional, Literal
from pydantic import BaseModel, Field, HttpUrl
from datetime import datetime

# Import centralized constants  
from src.constants import ResearchConfidence, FeaturePriority, ApprovalStatus


# ============================================================================
# RESEARCH PLANNING SCHEMAS
# ============================================================================

class CompetitorResearchTask(BaseModel):
    """Individual research task for competitor analysis"""
    description: str = Field(..., description="What to research")
    queries: List[str] = Field(..., description="Search queries to execute")
    target_domains: List[str] = Field(default_factory=list, description="Preferred domains for official sources")
    must_answer: List[str] = Field(..., description="Key questions this task must answer")


class FeatureResearchPlan(BaseModel):
    """Complete research plan for feature analysis"""
    goals: List[str] = Field(..., description="Research objectives")
    competitors: List[str] = Field(..., description="Competitors to analyze")
    features_of_interest: List[str] = Field(..., description="Specific features to investigate")
    tasks: List[CompetitorResearchTask] = Field(..., description="Research tasks to execute")
    estimated_time_minutes: int = Field(default=30, description="Estimated research time")


# ============================================================================
# WEB SEARCH RESULT SCHEMAS
# ============================================================================

class WebSearchResult(BaseModel):
    """Raw search result from web"""
    url: HttpUrl
    title: str
    snippet: str
    domain: str
    search_query: str


class CompetitorFinding(BaseModel):
    """Validated finding about a competitor's feature"""
    competitor: str = Field(..., description="Name of the competitor")
    feature: str = Field(..., description="Feature being analyzed")
    claim: str = Field(..., description="Concise statement about the feature")
    evidence_url: HttpUrl = Field(..., description="Source URL for the claim")
    evidence_snippet: str = Field(..., description="Quoted text supporting the claim")
    confidence: ResearchConfidence = Field(..., description="Confidence in the finding")
    date_found: Optional[str] = Field(None, description="Date when the information was published")
    is_official_source: bool = Field(default=False, description="Whether from official website/docs")


# ============================================================================
# ANALYSIS OUTPUT SCHEMAS
# ============================================================================

class CompetitorFeatureAnalysis(BaseModel):
    """Analysis of a single competitor's feature implementation"""
    competitor: str
    feature: str
    has_feature: bool = Field(..., description="Whether competitor has this feature")
    implementation_details: Optional[str] = Field(None, description="How they implement it")
    pricing_tier: Optional[str] = Field(None, description="Which pricing tier includes this feature")
    limitations: Optional[List[str]] = Field(default_factory=list, description="Known limitations")
    strengths: Optional[List[str]] = Field(default_factory=list, description="Notable strengths")
    proof_urls: List[HttpUrl] = Field(..., description="Supporting evidence URLs")
    last_updated: Optional[str] = Field(None, description="When feature was last updated")


class FeatureComparisonMatrix(BaseModel):
    """Matrix comparing feature across all competitors"""
    feature_name: str
    analysis_date: str = Field(default_factory=lambda: datetime.now().isoformat())
    rows: List[CompetitorFeatureAnalysis] = Field(..., description="One row per competitor")
    market_insights: Optional[str] = Field(None, description="Overall market trends observed")
    gaps_identified: Optional[List[str]] = Field(default_factory=list, description="Market gaps found")


# ============================================================================
# FINAL DELIVERABLE SCHEMAS
# ============================================================================

class FeatureSpecification(BaseModel):
    """Detailed feature specification based on research"""
    name: str = Field(..., description="Feature name")
    problem: str = Field(..., description="Problem this feature solves")
    user_stories: List[str] = Field(..., description="User stories for the feature")
    acceptance_criteria: List[str] = Field(..., description="Testable acceptance criteria")
    differentiation_notes: str = Field(..., description="How we'll differentiate from competitors")
    risks: List[str] = Field(default_factory=list, description="Implementation risks identified")
    priority: FeaturePriority = Field(default=FeaturePriority.MEDIUM)
    estimated_effort: Optional[str] = Field(None, description="T-shirt size or story points")


class CompetitorResearchReport(BaseModel):
    """Complete research report for PM approval"""
    summary: str = Field(..., description="Executive summary of findings")
    competitor_matrix: FeatureComparisonMatrix = Field(..., description="Feature comparison across competitors")
    feature_spec: FeatureSpecification = Field(..., description="Proposed feature specification")
    recommendations: Optional[List[str]] = Field(default_factory=list, description="Strategic recommendations")
    appendix_sources: List[HttpUrl] = Field(..., description="All sources used in research")
    research_quality_score: Optional[float] = Field(None, description="Self-assessed quality score 0-1")
    requires_further_research: bool = Field(default=False)
    approval_status: ApprovalStatus = Field(default=ApprovalStatus.PENDING)


# ============================================================================
# HELPER FUNCTIONS FOR SCHEMA FORMATTING
# ============================================================================

def get_feature_research_plan_schema() -> dict:
    """Get JSON schema for FeatureResearchPlan"""
    return FeatureResearchPlan.model_json_schema()


def get_competitor_finding_schema() -> dict:
    """Get JSON schema for CompetitorFinding"""
    return CompetitorFinding.model_json_schema()


def get_feature_comparison_matrix_schema() -> dict:
    """Get JSON schema for FeatureComparisonMatrix"""
    return FeatureComparisonMatrix.model_json_schema()


def get_competitor_research_report_schema() -> dict:
    """Get JSON schema for CompetitorResearchReport"""
    return CompetitorResearchReport.model_json_schema()


def get_feature_research_plan_schema_formatted() -> str:
    """Get formatted JSON schema string for prompts"""
    import json
    return json.dumps(get_feature_research_plan_schema(), indent=2)


def get_competitor_finding_schema_formatted() -> str:
    """Get formatted JSON schema string for prompts"""
    import json
    return json.dumps(get_competitor_finding_schema(), indent=2)


def get_feature_comparison_matrix_schema_formatted() -> str:
    """Get formatted JSON schema string for prompts"""
    import json
    return json.dumps(get_feature_comparison_matrix_schema(), indent=2)


def get_competitor_research_report_schema_formatted() -> str:
    """Get formatted JSON schema string for prompts"""
    import json
    return json.dumps(get_competitor_research_report_schema(), indent=2)


# ============================================================================
# VALIDATION AND QUALITY CHECKS
# ============================================================================

class ResearchQualityMetrics(BaseModel):
    """Metrics for assessing research quality"""
    total_sources: int
    official_sources: int
    unique_competitors: int
    evidence_per_claim_ratio: float
    high_confidence_findings: int
    low_confidence_findings: int
    research_duration_minutes: int
    completeness_score: float = Field(..., ge=0, le=1, description="0-1 score for completeness")


def validate_research_quality(report: CompetitorResearchReport) -> ResearchQualityMetrics:
    """Validate the quality of a research report"""
    total_sources = len(report.appendix_sources)
    unique_competitors = len(set(row.competitor for row in report.competitor_matrix.rows))
    
    # Count findings by confidence
    all_findings = []
    for row in report.competitor_matrix.rows:
        all_findings.extend(row.proof_urls)
    
    # Calculate metrics
    metrics = ResearchQualityMetrics(
        total_sources=total_sources,
        official_sources=sum(1 for row in report.competitor_matrix.rows if row.proof_urls),
        unique_competitors=unique_competitors,
        evidence_per_claim_ratio=len(all_findings) / max(len(report.competitor_matrix.rows), 1),
        high_confidence_findings=sum(1 for row in report.competitor_matrix.rows if row.has_feature),
        low_confidence_findings=sum(1 for row in report.competitor_matrix.rows if not row.has_feature),
        research_duration_minutes=0,  # Would be calculated from timestamps
        completeness_score=min(total_sources / 10, 1.0)  # Simple heuristic
    )
    
    return metrics